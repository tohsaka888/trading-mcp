from __future__ import annotations

from datetime import date, datetime
import re
import time
from typing import Iterable

import akshare as ak
import pandas as pd

from .client import DateLike, MarketDataError


_DATE_COLUMNS = ("date", "日期", "交易日期", "trade_date")
_US_CODE_PATTERN = re.compile(r"^\d{3}\.[A-Z0-9.-]+$")
_US_SUFFIX = ".US"
_US_TICKER_PATTERN = re.compile(r"^[A-Z][A-Z.-]*$")
_US_EXCHANGE_SUFFIXES = (".NYSE", ".NASDAQ", ".AMEX")
_US_CACHE_TTL_SECONDS = 24 * 60 * 60


def _to_ak_date(value: DateLike | None) -> str | None:
    if value is None:
        return None
    if isinstance(value, (date, datetime)):
        return value.strftime("%Y%m%d")
    if isinstance(value, str):
        cleaned = value.strip()
        if not cleaned:
            return None
        if "-" in cleaned:
            return cleaned.replace("-", "")
        return cleaned
    raise TypeError(f"Unsupported date type: {type(value)!r}")


def _coerce_date(value: DateLike | None) -> pd.Timestamp | None:
    if value is None:
        return None
    if isinstance(value, (date, datetime)):
        return pd.Timestamp(value)
    if isinstance(value, str):
        cleaned = value.strip()
        if not cleaned:
            return None
        if "-" in cleaned:
            cleaned = cleaned.replace("-", "")
        return pd.to_datetime(cleaned, format="%Y%m%d", errors="coerce")
    return None


def _normalize_symbol(symbol: str) -> tuple[str, str | None]:
    cleaned = symbol.strip()
    if not cleaned:
        raise MarketDataError("Symbol is missing or invalid")

    upper = cleaned.upper()
    exchange: str | None = None
    if "SZ" in upper:
        exchange = "sz"
    elif "SH" in upper:
        exchange = "sh"
    elif "BJ" in upper:
        exchange = "bj"

    digits = "".join(ch for ch in upper if ch.isdigit())
    code = digits[-6:] if len(digits) >= 6 else digits or cleaned

    if exchange is None and digits:
        if code.startswith(("0", "2", "3")):
            exchange = "sz"
        elif code.startswith(("6", "9")):
            exchange = "sh"
        elif code.startswith(("4", "8")):
            exchange = "bj"

    return code, exchange


def _find_date_column(columns: Iterable[str]) -> str | None:
    for name in _DATE_COLUMNS:
        if name in columns:
            return name
    return None


def _normalize_us_symbol(symbol: str) -> tuple[str, str | None]:
    cleaned = symbol.strip()
    if not cleaned:
        raise MarketDataError("Symbol is missing or invalid")

    upper = cleaned.upper()
    for suffix in _US_EXCHANGE_SUFFIXES:
        if upper.endswith(suffix):
            raise MarketDataError(
                "Exchange suffix not supported. Use .US or a raw ticker like AAPL."
            )

    if _US_CODE_PATTERN.match(upper):
        _, ticker = upper.split(".", 1)
        return ticker, upper

    if upper.endswith(_US_SUFFIX):
        ticker = upper[: -len(_US_SUFFIX)]
        if not ticker:
            raise MarketDataError("Symbol is missing or invalid")
        if not _US_TICKER_PATTERN.match(ticker):
            raise MarketDataError("Symbol is missing or invalid")
        return ticker, None

    if _US_TICKER_PATTERN.match(upper):
        return upper, None

    raise MarketDataError("Symbol is missing or invalid")


def _filter_frame_by_dates(
    frame: pd.DataFrame, start: DateLike | None, end: DateLike | None
) -> pd.DataFrame:
    if frame is None or frame.empty:
        return frame

    start_ts = _coerce_date(start)
    end_ts = _coerce_date(end)
    if start_ts is None and end_ts is None:
        return frame

    date_col = _find_date_column(frame.columns)
    if date_col is None:
        dates = pd.to_datetime(frame.index, errors="coerce")
    else:
        dates = pd.to_datetime(frame[date_col], errors="coerce")

    mask = pd.Series(True, index=frame.index)
    if start_ts is not None:
        mask &= dates >= start_ts
    if end_ts is not None:
        mask &= dates <= end_ts
    return frame.loc[mask]


def _normalize_frame(frame: pd.DataFrame) -> pd.DataFrame:
    if frame is None or frame.empty:
        return frame

    date_col = _find_date_column(frame.columns)
    if date_col is not None:
        normalized = frame.copy()
        normalized[date_col] = pd.to_datetime(normalized[date_col], errors="coerce")
        normalized = normalized.sort_values(date_col).reset_index(drop=True)
        return normalized

    return frame.sort_index()


class AkshareMarketDataClient:
    """Akshare-backed market data client."""

    def __init__(self, *, adjust: str | None = None) -> None:
        self._adjust = adjust or ""
        self._us_symbol_cache: dict[str, list[str]] | None = None
        self._us_symbol_cache_at: float | None = None

    def _get_us_symbol_map(self) -> dict[str, list[str]]:
        now = time.time()
        if (
            self._us_symbol_cache is not None
            and self._us_symbol_cache_at is not None
            and now - self._us_symbol_cache_at < _US_CACHE_TTL_SECONDS
        ):
            return self._us_symbol_cache

        try:
            frame = ak.stock_us_spot_em()
        except Exception:
            frame = None
        mapping: dict[str, list[str]] = {}
        if frame is not None and not frame.empty:
            code_col = "代码" if "代码" in frame.columns else None
            if code_col is None:
                for name in frame.columns:
                    if name.lower() == "code":
                        code_col = name
                        break
            if code_col is None:
                code_col = frame.columns[0]

            for raw_code in frame[code_col].astype(str):
                upper = raw_code.strip().upper()
                if not upper or "." not in upper:
                    continue
                _, ticker = upper.split(".", 1)
                mapping.setdefault(ticker, []).append(upper)

        self._us_symbol_cache = mapping
        self._us_symbol_cache_at = now
        return mapping

    def _resolve_us_code(self, ticker: str) -> str | None:
        mapping = self._get_us_symbol_map()
        codes = mapping.get(ticker)
        if not codes:
            return None
        for prefix in ("105.", "106.", "107."):
            candidate = f"{prefix}{ticker}"
            if candidate in codes:
                return candidate
        return codes[0]

    def _fetch_us(
        self, symbol: str, start: DateLike | None, end: DateLike | None
    ) -> pd.DataFrame:
        start_date = _to_ak_date(start)
        end_date = _to_ak_date(end)
        ticker, explicit_code = _normalize_us_symbol(symbol)
        code = explicit_code or self._resolve_us_code(ticker)

        primary_frame: pd.DataFrame | None = None
        primary_error: Exception | None = None
        if code:
            try:
                primary_frame = ak.stock_us_hist(
                    symbol=code,
                    period="daily",
                    start_date=start_date or "",
                    end_date=end_date or "",
                    adjust=self._adjust,
                )
            except Exception as exc:  # pragma: no cover - network/data issues
                primary_error = exc
            else:
                primary_error = None

            if primary_frame is not None and not primary_frame.empty:
                return _normalize_frame(primary_frame)

        fallback_frame: pd.DataFrame | None = None
        try:
            fallback_frame = ak.stock_us_daily(symbol=ticker, adjust=self._adjust)
        except Exception:
            fallback_frame = None

        if fallback_frame is not None and not fallback_frame.empty:
            filtered = _filter_frame_by_dates(fallback_frame, start, end)
            return _normalize_frame(filtered)

        if primary_frame is not None:
            return _normalize_frame(primary_frame)

        if fallback_frame is not None:
            return _normalize_frame(fallback_frame)

        if primary_error is not None:
            raise MarketDataError(f"Akshare US fetch failed for symbol={symbol}") from primary_error

        return pd.DataFrame()

    def fetch(
        self, symbol: str, start: DateLike | None = None, end: DateLike | None = None
    ) -> pd.DataFrame:
        cleaned = symbol.strip()
        if _US_CODE_PATTERN.match(cleaned.upper()) or cleaned.upper().endswith(
            _US_SUFFIX
        ) or _US_TICKER_PATTERN.match(cleaned.upper()):
            return self._fetch_us(symbol, start, end)

        start_date = _to_ak_date(start)
        end_date = _to_ak_date(end)
        normalized_symbol, exchange = _normalize_symbol(symbol)

        primary_frame: pd.DataFrame | None = None
        try:
            primary_frame = ak.stock_zh_a_hist(
                symbol=normalized_symbol,
                start_date=start_date or "",
                end_date=end_date or "",
                adjust=self._adjust,
            )
        except Exception as exc:  # pragma: no cover - network/data issues
            primary_error = exc
        else:
            primary_error = None

        if primary_frame is not None and not primary_frame.empty:
            return _normalize_frame(primary_frame)

        fallback_frame: pd.DataFrame | None = None
        if exchange is not None:
            try:
                fallback_frame = ak.stock_zh_a_hist_tx(
                    symbol=f"{exchange}{normalized_symbol}",
                    start_date=start_date or "",
                    end_date=end_date or "",
                    adjust=self._adjust,
                )
            except Exception:
                fallback_frame = None

        if fallback_frame is not None and not fallback_frame.empty:
            return _normalize_frame(fallback_frame)

        if primary_frame is not None:
            return _normalize_frame(primary_frame)

        if fallback_frame is not None:
            return _normalize_frame(fallback_frame)

        if primary_error is not None:
            raise MarketDataError(f"Akshare fetch failed for symbol={symbol}") from primary_error

        return pd.DataFrame()
