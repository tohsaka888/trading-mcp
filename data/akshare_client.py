from __future__ import annotations

from datetime import date, datetime
import re
import time
from typing import Iterable

import akshare as ak
import pandas as pd

from .client import DateLike, MarketDataError


_DATE_COLUMNS = ("date", "日期", "交易日期", "trade_date", "datetime", "time")
_OPEN_COLUMNS = ("open", "开盘")
_HIGH_COLUMNS = ("high", "最高")
_LOW_COLUMNS = ("low", "最低")
_CLOSE_COLUMNS = ("close", "收盘")
_VOLUME_COLUMNS = ("volume", "vol", "成交量")
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


def _find_column(columns: Iterable[str], candidates: Iterable[str]) -> str | None:
    for name in candidates:
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


_PERIOD_MAP = {"1d": "daily", "1w": "weekly", "1m": "monthly"}
_PERIOD_RULES = {"1w": "W-FRI", "1m": "ME"}


def _period_to_ak(period_type: str) -> str:
    mapped = _PERIOD_MAP.get(period_type)
    if mapped is None:
        raise MarketDataError(f"Unsupported period_type: {period_type}")
    return mapped


def _period_to_rule(period_type: str) -> str:
    rule = _PERIOD_RULES.get(period_type)
    if rule is None:
        raise MarketDataError(f"Unsupported period_type: {period_type}")
    return rule


def _resample_ohlcv(frame: pd.DataFrame, rule: str) -> pd.DataFrame:
    if frame is None or frame.empty:
        return frame

    date_col = _find_date_column(frame.columns)
    if date_col is None:
        indexed = frame.copy()
        indexed.index = pd.to_datetime(indexed.index, errors="coerce")
    else:
        indexed = frame.copy()
        indexed[date_col] = pd.to_datetime(indexed[date_col], errors="coerce")
        indexed = indexed.dropna(subset=[date_col])
        indexed = indexed.set_index(date_col)

    indexed = indexed.sort_index()
    open_col = _find_column(indexed.columns, _OPEN_COLUMNS)
    high_col = _find_column(indexed.columns, _HIGH_COLUMNS)
    low_col = _find_column(indexed.columns, _LOW_COLUMNS)
    close_col = _find_column(indexed.columns, _CLOSE_COLUMNS)
    volume_col = _find_column(indexed.columns, _VOLUME_COLUMNS)

    missing = [
        name
        for name, col in (
            ("open", open_col),
            ("high", high_col),
            ("low", low_col),
            ("close", close_col),
        )
        if col is None
    ]
    if missing:
        raise MarketDataError(f"Missing required columns: {', '.join(missing)}")

    agg = {
        open_col: "first",
        high_col: "max",
        low_col: "min",
        close_col: "last",
    }
    if volume_col is not None:
        agg[volume_col] = "sum"

    resampled = (
        indexed.resample(rule, label="right", closed="right")
        .agg(agg)
        .dropna(subset=[close_col])
    )

    rename_map = {
        open_col: "open",
        high_col: "high",
        low_col: "low",
        close_col: "close",
    }
    if volume_col is not None:
        rename_map[volume_col] = "volume"

    resampled = resampled.rename(columns=rename_map)
    index_name = resampled.index.name or "index"
    resampled = resampled.reset_index().rename(columns={index_name: "date"})
    return resampled


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
        self,
        symbol: str,
        start: DateLike | None,
        end: DateLike | None,
        period_type: str,
    ) -> pd.DataFrame:
        start_date = _to_ak_date(start)
        end_date = _to_ak_date(end)
        period = _period_to_ak(period_type)
        ticker, explicit_code = _normalize_us_symbol(symbol)
        code = explicit_code or self._resolve_us_code(ticker)

        primary_frame: pd.DataFrame | None = None
        primary_error: Exception | None = None
        used_native_period = False
        if code:
            try:
                primary_frame = ak.stock_us_hist(
                    symbol=code,
                    period=period,
                    start_date=start_date or "",
                    end_date=end_date or "",
                    adjust=self._adjust,
                )
                used_native_period = True
            except TypeError:
                if period == "daily":
                    try:
                        primary_frame = ak.stock_us_hist(
                            symbol=code,
                            start_date=start_date or "",
                            end_date=end_date or "",
                            adjust=self._adjust,
                        )
                    except Exception as exc:  # pragma: no cover - network/data issues
                        primary_error = exc
                    else:
                        primary_error = None
                else:
                    primary_error = None
            except Exception as exc:  # pragma: no cover - network/data issues
                primary_error = exc
            else:
                primary_error = None

            if primary_frame is not None and not primary_frame.empty:
                if period_type != "1d" and not used_native_period:
                    filtered = _filter_frame_by_dates(primary_frame, start, end)
                    resampled = _resample_ohlcv(
                        filtered, _period_to_rule(period_type)
                    )
                    resampled = _filter_frame_by_dates(resampled, start, end)
                    return _normalize_frame(resampled)
                return _normalize_frame(primary_frame)

        fallback_frame: pd.DataFrame | None = None
        try:
            fallback_frame = ak.stock_us_daily(symbol=ticker, adjust=self._adjust)
        except Exception:
            fallback_frame = None

        if fallback_frame is not None and not fallback_frame.empty:
            filtered = _filter_frame_by_dates(fallback_frame, start, end)
            if period_type != "1d":
                resampled = _resample_ohlcv(filtered, _period_to_rule(period_type))
                resampled = _filter_frame_by_dates(resampled, start, end)
                return _normalize_frame(resampled)
            return _normalize_frame(filtered)

        if primary_frame is not None:
            return _normalize_frame(primary_frame)

        if fallback_frame is not None:
            return _normalize_frame(fallback_frame)

        if primary_error is not None:
            raise MarketDataError(f"Akshare US fetch failed for symbol={symbol}") from primary_error

        return pd.DataFrame()

    def fetch(
        self,
        symbol: str,
        start: DateLike | None = None,
        end: DateLike | None = None,
        period_type: str = "1d",
    ) -> pd.DataFrame:
        cleaned = symbol.strip()
        if _US_CODE_PATTERN.match(cleaned.upper()) or cleaned.upper().endswith(
            _US_SUFFIX
        ) or _US_TICKER_PATTERN.match(cleaned.upper()):
            return self._fetch_us(symbol, start, end, period_type)

        start_date = _to_ak_date(start)
        end_date = _to_ak_date(end)
        period = _period_to_ak(period_type)
        normalized_symbol, exchange = _normalize_symbol(symbol)

        primary_frame: pd.DataFrame | None = None
        primary_used_native_period = False
        try:
            primary_frame = ak.stock_zh_a_hist(
                symbol=normalized_symbol,
                period=period,
                start_date=start_date or "",
                end_date=end_date or "",
                adjust=self._adjust,
            )
            primary_used_native_period = True
        except TypeError:
            if period == "daily":
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
            else:
                primary_error = None
        except Exception as exc:  # pragma: no cover - network/data issues
            primary_error = exc
        else:
            primary_error = None

        if primary_frame is not None and not primary_frame.empty:
            if period_type != "1d" and not primary_used_native_period:
                filtered = _filter_frame_by_dates(primary_frame, start, end)
                resampled = _resample_ohlcv(
                    filtered, _period_to_rule(period_type)
                )
                resampled = _filter_frame_by_dates(resampled, start, end)
                return _normalize_frame(resampled)
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
            if period_type != "1d":
                filtered = _filter_frame_by_dates(fallback_frame, start, end)
                resampled = _resample_ohlcv(
                    filtered, _period_to_rule(period_type)
                )
                resampled = _filter_frame_by_dates(resampled, start, end)
                return _normalize_frame(resampled)
            return _normalize_frame(fallback_frame)

        if primary_frame is not None:
            return _normalize_frame(primary_frame)

        if fallback_frame is not None:
            return _normalize_frame(fallback_frame)

        if primary_error is not None:
            raise MarketDataError(f"Akshare fetch failed for symbol={symbol}") from primary_error

        return pd.DataFrame()
