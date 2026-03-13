from __future__ import annotations

from datetime import date, datetime
import re
import time
from typing import Iterable

import akshare as ak
import requests
import pandas as pd

from .client import DateLike, MarketDataError


_DATE_COLUMNS = ("date", "日期", "交易日期", "trade_date", "datetime", "time")
_OPEN_COLUMNS = ("open", "开盘")
_HIGH_COLUMNS = ("high", "最高")
_LOW_COLUMNS = ("low", "最低")
_CLOSE_COLUMNS = ("close", "收盘")
_VOLUME_COLUMNS = ("volume", "vol", "成交量")
_AMOUNT_COLUMNS = ("amount", "成交额")
_TURNOVER_RATE_COLUMNS = ("turnover_rate", "换手率")
_US_CODE_PATTERN = re.compile(r"^\d{3}\.[A-Z0-9.-]+$")
_US_SUFFIX = ".US"
_US_TICKER_PATTERN = re.compile(r"^[A-Z][A-Z.-]*$")
_US_FUNDAMENTAL_TICKER_PATTERN = re.compile(r"^[A-Z][A-Z0-9_]*$")
_US_EXCHANGE_SUFFIXES = (".NYSE", ".NASDAQ", ".AMEX")
_US_CACHE_TTL_SECONDS = 24 * 60 * 60
_TX_KLINE_URL = "https://proxy.finance.qq.com/ifzqgtimg/appstock/app/newfqkline/get"
_TX_AMOUNT_SCALE = 10000.0
_TX_TIMEOUT_SECONDS = 10.0


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


def _resolve_tx_date_range(
    start_date: str | None,
    end_date: str | None,
) -> tuple[str, str]:
    resolved_start = start_date or "19000101"
    resolved_end = end_date or date.today().strftime("%Y%m%d")
    return resolved_start, resolved_end


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


def _normalize_cn_financial_symbol(symbol: str) -> str:
    code, exchange = _normalize_symbol(symbol)
    if exchange == "bj":
        raise MarketDataError(
            "Beijing Stock Exchange symbols are not supported by "
            "stock_financial_analysis_indicator_em."
        )
    if exchange not in {"sz", "sh"}:
        raise MarketDataError("Unable to infer A-share exchange suffix for symbol")
    return f"{code}.{exchange.upper()}"


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


def _normalize_us_financial_symbol(symbol: str) -> str:
    cleaned = symbol.strip()
    if not cleaned:
        raise MarketDataError("Symbol is missing or invalid")

    upper = cleaned.upper()
    for suffix in _US_EXCHANGE_SUFFIXES:
        if upper.endswith(suffix):
            raise MarketDataError(
                "Exchange suffix not supported. Use .US or a raw ticker like AAPL."
            )

    ticker = upper
    if _US_CODE_PATTERN.match(upper):
        _, ticker = upper.split(".", 1)
    elif upper.endswith(_US_SUFFIX):
        ticker = upper[: -len(_US_SUFFIX)]

    ticker = ticker.replace("-", "_").replace(".", "_")
    if not _US_FUNDAMENTAL_TICKER_PATTERN.match(ticker):
        raise MarketDataError("Symbol is missing or invalid")
    return ticker


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
    amount_col = _find_column(indexed.columns, _AMOUNT_COLUMNS)
    turnover_rate_col = _find_column(indexed.columns, _TURNOVER_RATE_COLUMNS)

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
    if amount_col is not None:
        agg[amount_col] = "sum"
    if turnover_rate_col is not None:
        agg[turnover_rate_col] = "sum"

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
    if amount_col is not None:
        rename_map[amount_col] = "amount"
    if turnover_rate_col is not None:
        rename_map[turnover_rate_col] = "turnover_rate"

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

    def _fetch_cn_tx_extended(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
    ) -> pd.DataFrame:
        try:
            from akshare.stock_feature import stock_hist_tx
        except Exception:
            return pd.DataFrame()

        resolved_start = start_date.replace("-", "")
        resolved_end = end_date.replace("-", "")
        try:
            init_start = str(stock_hist_tx.get_tx_start_year(symbol=symbol)).replace("-", "")
            if int(resolved_start) < int(init_start):
                resolved_start = init_start
        except Exception:
            pass

        try:
            range_start = int(resolved_start[:4])
            range_end = int(resolved_end[:4]) + 1
        except (TypeError, ValueError):
            return pd.DataFrame()

        upper_year = min(range_end, date.today().year + 1)
        chunks: list[pd.DataFrame] = []
        for year in range(range_start, upper_year):
            params = {
                "_var": f"kline_day{self._adjust}{year}",
                "param": f"{symbol},day,{year}-01-01,{year + 1}-12-31,640,{self._adjust}",
                "r": "0.8205512681390605",
            }
            try:
                response = requests.get(
                    _TX_KLINE_URL,
                    params=params,
                    timeout=_TX_TIMEOUT_SECONDS,
                )
                text = response.text
                payload_start = text.find("={")
                if payload_start < 0:
                    continue
                parsed = stock_hist_tx.demjson.decode(text[payload_start + 1 :])
                raw_symbol = parsed["data"][symbol]
                if "day" in raw_symbol:
                    raw_rows = raw_symbol["day"]
                elif "hfqday" in raw_symbol:
                    raw_rows = raw_symbol["hfqday"]
                else:
                    raw_rows = raw_symbol.get("qfqday", [])
            except Exception:
                continue

            chunk = pd.DataFrame(raw_rows)
            if chunk.empty:
                continue
            chunks.append(chunk)

        if not chunks:
            return pd.DataFrame()

        raw = pd.concat(chunks, ignore_index=True)
        if raw.empty or raw.shape[1] < 6:
            return pd.DataFrame()

        frame = pd.DataFrame(
            {
                "date": pd.to_datetime(raw.iloc[:, 0], errors="coerce"),
                "open": pd.to_numeric(raw.iloc[:, 1], errors="coerce"),
                "close": pd.to_numeric(raw.iloc[:, 2], errors="coerce"),
                "high": pd.to_numeric(raw.iloc[:, 3], errors="coerce"),
                "low": pd.to_numeric(raw.iloc[:, 4], errors="coerce"),
                "volume": pd.to_numeric(raw.iloc[:, 5], errors="coerce"),
            }
        )
        if raw.shape[1] > 7:
            frame["turnover_rate"] = pd.to_numeric(raw.iloc[:, 7], errors="coerce")
        if raw.shape[1] > 8:
            # Tencent field index 8 is transaction amount in 10k CNY.
            frame["amount"] = (
                pd.to_numeric(raw.iloc[:, 8], errors="coerce") * _TX_AMOUNT_SCALE
            )

        frame = frame.dropna(subset=["date"]).drop_duplicates(subset=["date"])
        frame = frame.sort_values("date")
        filtered = _filter_frame_by_dates(frame, resolved_start, resolved_end)
        return filtered.reset_index(drop=True)

    @staticmethod
    def _normalize_cn_tx_legacy(frame: pd.DataFrame) -> pd.DataFrame:
        if frame is None or frame.empty:
            return frame

        normalized = frame.copy()
        volume_col = _find_column(normalized.columns, _VOLUME_COLUMNS)
        if volume_col is None and "amount" in normalized.columns:
            normalized = normalized.rename(columns={"amount": "volume"})
        return normalized

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

    def fetch_cn_financial_indicators(
        self,
        symbol: str,
        indicator: str,
    ) -> pd.DataFrame:
        normalized_symbol = _normalize_cn_financial_symbol(symbol)
        try:
            frame = ak.stock_financial_analysis_indicator_em(
                symbol=normalized_symbol,
                indicator=indicator,
            )
        except Exception as exc:
            raise MarketDataError(
                "Akshare CN financial indicators fetch failed "
                f"for symbol={normalized_symbol}, indicator={indicator}"
            ) from exc
        if frame is None:
            return pd.DataFrame()
        return frame

    def fetch_us_financial_report(
        self,
        stock: str,
        symbol: str,
        indicator: str,
    ) -> pd.DataFrame:
        normalized_stock = _normalize_us_financial_symbol(stock)
        try:
            frame = ak.stock_financial_us_report_em(
                stock=normalized_stock,
                symbol=symbol,
                indicator=indicator,
            )
        except Exception as exc:
            raise MarketDataError(
                "Akshare US financial report fetch failed "
                f"for stock={normalized_stock}, symbol={symbol}, indicator={indicator}"
            ) from exc
        if frame is None:
            return pd.DataFrame()
        return frame

    def fetch_us_financial_indicators(
        self,
        symbol: str,
        indicator: str,
    ) -> pd.DataFrame:
        normalized_symbol = _normalize_us_financial_symbol(symbol)
        try:
            frame = ak.stock_financial_us_analysis_indicator_em(
                symbol=normalized_symbol,
                indicator=indicator,
            )
        except Exception as exc:
            raise MarketDataError(
                "Akshare US financial indicators fetch failed "
                f"for symbol={normalized_symbol}, indicator={indicator}"
            ) from exc
        if frame is None:
            return pd.DataFrame()
        return frame

    def fetch_industry_summary_ths(self) -> pd.DataFrame:
        try:
            frame = ak.stock_board_industry_summary_ths()
        except Exception as exc:
            raise MarketDataError("Akshare THS industry summary fetch failed") from exc
        if frame is None:
            return pd.DataFrame()
        return frame

    def fetch_industry_index_ths(
        self,
        symbol: str,
        start_date: DateLike | None = None,
        end_date: DateLike | None = None,
    ) -> pd.DataFrame:
        try:
            frame = ak.stock_board_industry_index_ths(
                symbol=symbol.strip(),
                start_date=_to_ak_date(start_date) or "",
                end_date=_to_ak_date(end_date) or "",
            )
        except Exception as exc:
            raise MarketDataError(
                "Akshare THS industry index fetch failed "
                f"for symbol={symbol}, start_date={start_date}, end_date={end_date}"
            ) from exc
        if frame is None:
            return pd.DataFrame()
        return frame

    def fetch_industry_name_em(self) -> pd.DataFrame:
        try:
            frame = ak.stock_board_industry_name_em()
        except Exception as exc:
            raise MarketDataError("Akshare EM industry names fetch failed") from exc
        if frame is None:
            return pd.DataFrame()
        return frame

    def fetch_industry_spot_em(self, symbol: str) -> pd.DataFrame:
        try:
            frame = ak.stock_board_industry_spot_em(symbol=symbol.strip())
        except Exception as exc:
            raise MarketDataError(
                f"Akshare EM industry spot fetch failed for symbol={symbol}"
            ) from exc
        if frame is None:
            return pd.DataFrame()
        return frame

    def fetch_industry_cons_em(self, symbol: str) -> pd.DataFrame:
        try:
            frame = ak.stock_board_industry_cons_em(symbol=symbol.strip())
        except Exception as exc:
            raise MarketDataError(
                f"Akshare EM industry constituents fetch failed for symbol={symbol}"
            ) from exc
        if frame is None:
            return pd.DataFrame()
        return frame

    def fetch_industry_hist_em(
        self,
        symbol: str,
        start_date: DateLike | None = None,
        end_date: DateLike | None = None,
        period: str = "日k",
        adjust: str = "",
    ) -> pd.DataFrame:
        try:
            frame = ak.stock_board_industry_hist_em(
                symbol=symbol.strip(),
                start_date=_to_ak_date(start_date) or "",
                end_date=_to_ak_date(end_date) or "",
                period=period,
                adjust=adjust,
            )
        except Exception as exc:
            raise MarketDataError(
                "Akshare EM industry history fetch failed "
                f"for symbol={symbol}, period={period}, adjust={adjust}"
            ) from exc
        if frame is None:
            return pd.DataFrame()
        return frame

    def fetch_industry_hist_min_em(
        self,
        symbol: str,
        period: str = "5",
    ) -> pd.DataFrame:
        try:
            frame = ak.stock_board_industry_hist_min_em(
                symbol=symbol.strip(),
                period=period,
            )
        except Exception as exc:
            raise MarketDataError(
                "Akshare EM industry intraday history fetch failed "
                f"for symbol={symbol}, period={period}"
            ) from exc
        if frame is None:
            return pd.DataFrame()
        return frame

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
            tx_start_date, tx_end_date = _resolve_tx_date_range(start_date, end_date)
            tx_symbol = f"{exchange}{normalized_symbol}"
            fallback_frame = self._fetch_cn_tx_extended(
                tx_symbol,
                tx_start_date,
                tx_end_date,
            )
            try:
                if fallback_frame is None or fallback_frame.empty:
                    fallback_frame = ak.stock_zh_a_hist_tx(
                        symbol=tx_symbol,
                        start_date=tx_start_date,
                        end_date=tx_end_date,
                        adjust=self._adjust,
                    )
                    fallback_frame = self._normalize_cn_tx_legacy(fallback_frame)
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
