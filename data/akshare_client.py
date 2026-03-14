from __future__ import annotations

from datetime import date, datetime
import re
import time
from typing import Any, Iterable

import akshare as ak
import pandas as pd
import requests

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
_EM_CLIST_URL = "https://push2.eastmoney.com/api/qt/clist/get"
_EM_FUND_FLOW_DAY_URL = "https://push2his.eastmoney.com/api/qt/stock/fflow/daykline/get"
_EM_TIMEOUT_SECONDS = 15.0
_EM_UT = "b2884a393a59ad64002292a3e90d46a5"
_EM_BOARD_UT = "8dec03ba335b81bf4ebdf7b29ec27d15"
_THS_FUND_FLOW_INDIVIDUAL_RANK_MAP = {
    "今日": "即时",
    "3日": "3日排行",
    "5日": "5日排行",
    "10日": "10日排行",
}
_THS_FUND_FLOW_SECTOR_RANK_MAP = {
    "今日": "即时",
    "5日": "5日排行",
    "10日": "10日排行",
}
_EM_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    )
}
_FUND_FLOW_INDIVIDUAL_RANK_CONFIG: dict[str, dict[str, Any]] = {
    "今日": {
        "fid": "f62",
        "fields": "f12,f14,f2,f3,f62,f184,f66,f69,f72,f75,f78,f81,f84,f87",
        "rename": {
            "f12": "代码",
            "f14": "名称",
            "f2": "最新价",
            "f3": "今日涨跌幅",
            "f62": "今日主力净流入-净额",
            "f184": "今日主力净流入-净占比",
            "f66": "今日超大单净流入-净额",
            "f69": "今日超大单净流入-净占比",
            "f72": "今日大单净流入-净额",
            "f75": "今日大单净流入-净占比",
            "f78": "今日中单净流入-净额",
            "f81": "今日中单净流入-净占比",
            "f84": "今日小单净流入-净额",
            "f87": "今日小单净流入-净占比",
        },
        "columns": [
            "序号",
            "代码",
            "名称",
            "最新价",
            "今日涨跌幅",
            "今日主力净流入-净额",
            "今日主力净流入-净占比",
            "今日超大单净流入-净额",
            "今日超大单净流入-净占比",
            "今日大单净流入-净额",
            "今日大单净流入-净占比",
            "今日中单净流入-净额",
            "今日中单净流入-净占比",
            "今日小单净流入-净额",
            "今日小单净流入-净占比",
        ],
    },
    "3日": {
        "fid": "f267",
        "fields": "f12,f14,f2,f127,f267,f268,f269,f270,f271,f272,f273,f274,f275,f276",
        "rename": {
            "f12": "代码",
            "f14": "名称",
            "f2": "最新价",
            "f127": "3日涨跌幅",
            "f267": "3日主力净流入-净额",
            "f268": "3日主力净流入-净占比",
            "f269": "3日超大单净流入-净额",
            "f270": "3日超大单净流入-净占比",
            "f271": "3日大单净流入-净额",
            "f272": "3日大单净流入-净占比",
            "f273": "3日中单净流入-净额",
            "f274": "3日中单净流入-净占比",
            "f275": "3日小单净流入-净额",
            "f276": "3日小单净流入-净占比",
        },
        "columns": [
            "序号",
            "代码",
            "名称",
            "最新价",
            "3日涨跌幅",
            "3日主力净流入-净额",
            "3日主力净流入-净占比",
            "3日超大单净流入-净额",
            "3日超大单净流入-净占比",
            "3日大单净流入-净额",
            "3日大单净流入-净占比",
            "3日中单净流入-净额",
            "3日中单净流入-净占比",
            "3日小单净流入-净额",
            "3日小单净流入-净占比",
        ],
    },
    "5日": {
        "fid": "f164",
        "fields": "f12,f14,f2,f109,f164,f165,f166,f167,f168,f169,f170,f171,f172,f173",
        "rename": {
            "f12": "代码",
            "f14": "名称",
            "f2": "最新价",
            "f109": "5日涨跌幅",
            "f164": "5日主力净流入-净额",
            "f165": "5日主力净流入-净占比",
            "f166": "5日超大单净流入-净额",
            "f167": "5日超大单净流入-净占比",
            "f168": "5日大单净流入-净额",
            "f169": "5日大单净流入-净占比",
            "f170": "5日中单净流入-净额",
            "f171": "5日中单净流入-净占比",
            "f172": "5日小单净流入-净额",
            "f173": "5日小单净流入-净占比",
        },
        "columns": [
            "序号",
            "代码",
            "名称",
            "最新价",
            "5日涨跌幅",
            "5日主力净流入-净额",
            "5日主力净流入-净占比",
            "5日超大单净流入-净额",
            "5日超大单净流入-净占比",
            "5日大单净流入-净额",
            "5日大单净流入-净占比",
            "5日中单净流入-净额",
            "5日中单净流入-净占比",
            "5日小单净流入-净额",
            "5日小单净流入-净占比",
        ],
    },
    "10日": {
        "fid": "f174",
        "fields": "f12,f14,f2,f160,f174,f175,f176,f177,f178,f179,f180,f181,f182,f183",
        "rename": {
            "f12": "代码",
            "f14": "名称",
            "f2": "最新价",
            "f160": "10日涨跌幅",
            "f174": "10日主力净流入-净额",
            "f175": "10日主力净流入-净占比",
            "f176": "10日超大单净流入-净额",
            "f177": "10日超大单净流入-净占比",
            "f178": "10日大单净流入-净额",
            "f179": "10日大单净流入-净占比",
            "f180": "10日中单净流入-净额",
            "f181": "10日中单净流入-净占比",
            "f182": "10日小单净流入-净额",
            "f183": "10日小单净流入-净占比",
        },
        "columns": [
            "序号",
            "代码",
            "名称",
            "最新价",
            "10日涨跌幅",
            "10日主力净流入-净额",
            "10日主力净流入-净占比",
            "10日超大单净流入-净额",
            "10日超大单净流入-净占比",
            "10日大单净流入-净额",
            "10日大单净流入-净占比",
            "10日中单净流入-净额",
            "10日中单净流入-净占比",
            "10日小单净流入-净额",
            "10日小单净流入-净占比",
        ],
    },
}
_FUND_FLOW_SECTOR_TYPE_MAP = {"行业资金流": "2", "概念资金流": "3", "地域资金流": "1"}
_FUND_FLOW_SECTOR_RANK_CONFIG: dict[str, dict[str, Any]] = {
    "今日": {
        "fid": "f62",
        "stat": "1",
        "fields": "f12,f14,f3,f62,f184,f66,f69,f72,f75,f78,f81,f84,f87,f204,f205",
        "rename": {
            "f12": "代码",
            "f14": "名称",
            "f3": "今日涨跌幅",
            "f62": "今日主力净流入-净额",
            "f184": "今日主力净流入-净占比",
            "f66": "今日超大单净流入-净额",
            "f69": "今日超大单净流入-净占比",
            "f72": "今日大单净流入-净额",
            "f75": "今日大单净流入-净占比",
            "f78": "今日中单净流入-净额",
            "f81": "今日中单净流入-净占比",
            "f84": "今日小单净流入-净额",
            "f87": "今日小单净流入-净占比",
            "f204": "今日主力净流入最大股",
            "f205": "今日主力净流入最大股代码",
        },
        "columns": [
            "序号",
            "名称",
            "今日涨跌幅",
            "今日主力净流入-净额",
            "今日主力净流入-净占比",
            "今日超大单净流入-净额",
            "今日超大单净流入-净占比",
            "今日大单净流入-净额",
            "今日大单净流入-净占比",
            "今日中单净流入-净额",
            "今日中单净流入-净占比",
            "今日小单净流入-净额",
            "今日小单净流入-净占比",
            "今日主力净流入最大股",
        ],
        "sort": "今日主力净流入-净额",
    },
    "5日": {
        "fid": "f164",
        "stat": "5",
        "fields": "f12,f14,f109,f164,f165,f166,f167,f168,f169,f170,f171,f172,f173,f257,f258",
        "rename": {
            "f12": "代码",
            "f14": "名称",
            "f109": "5日涨跌幅",
            "f164": "5日主力净流入-净额",
            "f165": "5日主力净流入-净占比",
            "f166": "5日超大单净流入-净额",
            "f167": "5日超大单净流入-净占比",
            "f168": "5日大单净流入-净额",
            "f169": "5日大单净流入-净占比",
            "f170": "5日中单净流入-净额",
            "f171": "5日中单净流入-净占比",
            "f172": "5日小单净流入-净额",
            "f173": "5日小单净流入-净占比",
            "f257": "5日主力净流入最大股",
            "f258": "5日主力净流入最大股代码",
        },
        "columns": [
            "序号",
            "名称",
            "5日涨跌幅",
            "5日主力净流入-净额",
            "5日主力净流入-净占比",
            "5日超大单净流入-净额",
            "5日超大单净流入-净占比",
            "5日大单净流入-净额",
            "5日大单净流入-净占比",
            "5日中单净流入-净额",
            "5日中单净流入-净占比",
            "5日小单净流入-净额",
            "5日小单净流入-净占比",
            "5日主力净流入最大股",
        ],
        "sort": "5日主力净流入-净额",
    },
    "10日": {
        "fid": "f174",
        "stat": "10",
        "fields": "f12,f14,f160,f174,f175,f176,f177,f178,f179,f180,f181,f182,f183,f260,f261",
        "rename": {
            "f12": "代码",
            "f14": "名称",
            "f160": "10日涨跌幅",
            "f174": "10日主力净流入-净额",
            "f175": "10日主力净流入-净占比",
            "f176": "10日超大单净流入-净额",
            "f177": "10日超大单净流入-净占比",
            "f178": "10日大单净流入-净额",
            "f179": "10日大单净流入-净占比",
            "f180": "10日中单净流入-净额",
            "f181": "10日中单净流入-净占比",
            "f182": "10日小单净流入-净额",
            "f183": "10日小单净流入-净占比",
            "f260": "10日主力净流入最大股",
            "f261": "10日主力净流入最大股代码",
        },
        "columns": [
            "序号",
            "名称",
            "10日涨跌幅",
            "10日主力净流入-净额",
            "10日主力净流入-净占比",
            "10日超大单净流入-净额",
            "10日超大单净流入-净占比",
            "10日大单净流入-净额",
            "10日大单净流入-净占比",
            "10日中单净流入-净额",
            "10日中单净流入-净占比",
            "10日小单净流入-净额",
            "10日小单净流入-净占比",
            "10日主力净流入最大股",
        ],
        "sort": "10日主力净流入-净额",
    },
}
_FUND_FLOW_SECTOR_SUMMARY_CONFIG: dict[str, dict[str, Any]] = {
    "今日": {
        "fid": "f62",
        "fields": "f12,f14,f2,f3,f62,f184,f66,f69,f72,f75,f78,f81,f84,f87",
        "rename": {
            "f12": "代码",
            "f14": "名称",
            "f2": "最新价",
            "f3": "今天涨跌幅",
            "f62": "今日主力净流入-净额",
            "f184": "今日主力净流入-净占比",
            "f66": "今日超大单净流入-净额",
            "f69": "今日超大单净流入-净占比",
            "f72": "今日大单净流入-净额",
            "f75": "今日大单净流入-净占比",
            "f78": "今日中单净流入-净额",
            "f81": "今日中单净流入-净占比",
            "f84": "今日小单净流入-净额",
            "f87": "今日小单净流入-净占比",
        },
        "columns": [
            "序号",
            "代码",
            "名称",
            "最新价",
            "今天涨跌幅",
            "今日主力净流入-净额",
            "今日主力净流入-净占比",
            "今日超大单净流入-净额",
            "今日超大单净流入-净占比",
            "今日大单净流入-净额",
            "今日大单净流入-净占比",
            "今日中单净流入-净额",
            "今日中单净流入-净占比",
            "今日小单净流入-净额",
            "今日小单净流入-净占比",
        ],
    },
    "5日": {
        "fid": "f164",
        "fields": "f12,f14,f2,f109,f164,f165,f166,f167,f168,f169,f170,f171,f172,f173",
        "rename": {
            "f12": "代码",
            "f14": "名称",
            "f2": "最新价",
            "f109": "5日涨跌幅",
            "f164": "5日主力净流入-净额",
            "f165": "5日主力净流入-净占比",
            "f166": "5日超大单净流入-净额",
            "f167": "5日超大单净流入-净占比",
            "f168": "5日大单净流入-净额",
            "f169": "5日大单净流入-净占比",
            "f170": "5日中单净流入-净额",
            "f171": "5日中单净流入-净占比",
            "f172": "5日小单净流入-净额",
            "f173": "5日小单净流入-净占比",
        },
        "columns": [
            "序号",
            "代码",
            "名称",
            "最新价",
            "5日涨跌幅",
            "5日主力净流入-净额",
            "5日主力净流入-净占比",
            "5日超大单净流入-净额",
            "5日超大单净流入-净占比",
            "5日大单净流入-净额",
            "5日大单净流入-净占比",
            "5日中单净流入-净额",
            "5日中单净流入-净占比",
            "5日小单净流入-净额",
            "5日小单净流入-净占比",
        ],
    },
    "10日": {
        "fid": "f174",
        "fields": "f12,f14,f2,f160,f174,f175,f176,f177,f178,f179,f180,f181,f182,f183",
        "rename": {
            "f12": "代码",
            "f14": "名称",
            "f2": "最新价",
            "f160": "10日涨跌幅",
            "f174": "10日主力净流入-净额",
            "f175": "10日主力净流入-净占比",
            "f176": "10日超大单净流入-净额",
            "f177": "10日超大单净流入-净占比",
            "f178": "10日大单净流入-净额",
            "f179": "10日大单净流入-净占比",
            "f180": "10日中单净流入-净额",
            "f181": "10日中单净流入-净占比",
            "f182": "10日小单净流入-净额",
            "f183": "10日小单净流入-净占比",
        },
        "columns": [
            "序号",
            "代码",
            "名称",
            "最新价",
            "10日涨跌幅",
            "10日主力净流入-净额",
            "10日主力净流入-净占比",
            "10日超大单净流入-净额",
            "10日超大单净流入-净占比",
            "10日大单净流入-净额",
            "10日大单净流入-净占比",
            "10日中单净流入-净额",
            "10日中单净流入-净占比",
            "10日小单净流入-净额",
            "10日小单净流入-净占比",
        ],
    },
}


def _expected_columns_present(frame: pd.DataFrame, columns: Iterable[str]) -> bool:
    return (
        frame is not None
        and not frame.empty
        and all(column in frame.columns for column in columns)
    )


def _exception_summary(exc: BaseException) -> str:
    detail = str(exc).strip()
    if not detail:
        return exc.__class__.__name__
    if detail.startswith(f"{exc.__class__.__name__}:"):
        return detail
    return f"{exc.__class__.__name__}: {detail}"


def _normalize_rank_frame_from_ths(
    frame: pd.DataFrame | None,
    rename: dict[str, str],
    *,
    code_column: str | None = "代码",
) -> pd.DataFrame:
    if frame is None or frame.empty:
        return pd.DataFrame()

    normalized = frame.rename(columns=rename).reset_index(drop=True)
    if code_column and code_column in normalized.columns:
        normalized[code_column] = (
            normalized[code_column]
            .astype(str)
            .str.replace(r"\.0$", "", regex=True)
            .str.zfill(6)
        )
    return normalized


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


def _with_optional_ak_dates(
    params: dict[str, Any],
    *,
    start_date: DateLike | None = None,
    end_date: DateLike | None = None,
) -> dict[str, Any]:
    normalized = dict(params)
    resolved_start = _to_ak_date(start_date)
    resolved_end = _to_ak_date(end_date)
    if resolved_start is not None:
        normalized["start_date"] = resolved_start
    if resolved_end is not None:
        normalized["end_date"] = resolved_end
    return normalized


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
        indexed
        .resample(rule, label="right", closed="right")
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
            init_start = str(stock_hist_tx.get_tx_start_year(symbol=symbol)).replace(
                "-", ""
            )
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

        frame = pd.DataFrame({
            "date": pd.to_datetime(raw.iloc[:, 0], errors="coerce"),
            "open": pd.to_numeric(raw.iloc[:, 1], errors="coerce"),
            "close": pd.to_numeric(raw.iloc[:, 2], errors="coerce"),
            "high": pd.to_numeric(raw.iloc[:, 3], errors="coerce"),
            "low": pd.to_numeric(raw.iloc[:, 4], errors="coerce"),
            "volume": pd.to_numeric(raw.iloc[:, 5], errors="coerce"),
        })
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
                primary_frame = ak.stock_us_hist(**_with_optional_ak_dates(
                    {
                        "symbol": code,
                        "period": period,
                        "adjust": self._adjust,
                    },
                    start_date=start,
                    end_date=end,
                ))
                used_native_period = True
            except TypeError:
                if period == "daily":
                    try:
                        primary_frame = ak.stock_us_hist(**_with_optional_ak_dates(
                            {
                                "symbol": code,
                                "adjust": self._adjust,
                            },
                            start_date=start,
                            end_date=end,
                        ))
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
                    resampled = _resample_ohlcv(filtered, _period_to_rule(period_type))
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
            raise MarketDataError(
                f"Akshare US fetch failed for symbol={symbol}"
            ) from primary_error

        return pd.DataFrame()

    def _request_json(self, url: str, params: dict[str, object]) -> dict[str, Any]:
        response = requests.get(
            url,
            params=params,
            headers=_EM_HEADERS,
            timeout=_EM_TIMEOUT_SECONDS,
        )
        raise_for_status = getattr(response, "raise_for_status", None)
        if callable(raise_for_status):
            raise_for_status()
        return response.json()

    def _fetch_clist_pages(self, params: dict[str, object]) -> list[dict[str, Any]]:
        initial = self._request_json(_EM_CLIST_URL, params)
        data = initial.get("data") or {}
        total = int(data.get("total") or 0)
        first_rows = data.get("diff") or []
        if total == 0:
            return list(first_rows)

        page_size = int(params.get("pz") or 100)
        total_pages = max((total + page_size - 1) // page_size, 1)
        rows: list[dict[str, Any]] = list(first_rows)
        for page in range(2, total_pages + 1):
            paged_params = dict(params)
            paged_params["pn"] = str(page)
            page_json = self._request_json(_EM_CLIST_URL, paged_params)
            page_data = page_json.get("data") or {}
            rows.extend(page_data.get("diff") or [])
        return rows

    @staticmethod
    def _finalize_rank_frame(
        frame: pd.DataFrame,
        columns: list[str],
        numeric_columns: Iterable[str],
        *,
        code_column: str | None = "代码",
    ) -> pd.DataFrame:
        if frame is None or frame.empty:
            return pd.DataFrame(columns=columns)

        normalized = frame.copy()
        if code_column and code_column in normalized.columns:
            normalized[code_column] = normalized[code_column].astype(str).str.zfill(6)

        for column in numeric_columns:
            if column in normalized.columns:
                normalized[column] = pd.to_numeric(normalized[column], errors="coerce")

        normalized.insert(0, "序号", range(1, len(normalized) + 1))
        return normalized[columns]

    def _fetch_fund_flow_individual_em_fallback(
        self,
        symbol: str,
        start_date: DateLike | None = None,
        end_date: DateLike | None = None,
    ) -> pd.DataFrame:
        stock, market = _normalize_symbol(symbol)
        if market is None:
            raise MarketDataError("Unable to infer A-share exchange for symbol")

        market_map = {"sh": 1, "sz": 0, "bj": 0}
        data_json = self._request_json(
            _EM_FUND_FLOW_DAY_URL,
            {
                "lmt": "0",
                "klt": "101",
                "secid": f"{market_map[market]}.{stock}",
                "fields1": "f1,f2,f3,f7",
                "fields2": "f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61,f62,f63,f64,f65",
                "ut": _EM_UT,
                "_": int(time.time() * 1000),
            },
        )
        klines = ((data_json.get("data") or {}).get("klines")) or []
        if not klines:
            return pd.DataFrame()

        frame = pd.DataFrame([item.split(",") for item in klines])
        if frame.shape[1] < 13:
            raise MarketDataError(
                "Eastmoney individual fund-flow response is malformed"
            )

        frame.columns = [
            "日期",
            "主力净流入-净额",
            "小单净流入-净额",
            "中单净流入-净额",
            "大单净流入-净额",
            "超大单净流入-净额",
            "主力净流入-净占比",
            "小单净流入-净占比",
            "中单净流入-净占比",
            "大单净流入-净占比",
            "超大单净流入-净占比",
            "收盘价",
            "涨跌幅",
            *[f"unused_{index}" for index in range(frame.shape[1] - 13)],
        ]
        frame = frame[
            [
                "日期",
                "收盘价",
                "涨跌幅",
                "主力净流入-净额",
                "主力净流入-净占比",
                "超大单净流入-净额",
                "超大单净流入-净占比",
                "大单净流入-净额",
                "大单净流入-净占比",
                "中单净流入-净额",
                "中单净流入-净占比",
                "小单净流入-净额",
                "小单净流入-净占比",
            ]
        ]
        for column in frame.columns:
            if column != "日期":
                frame[column] = pd.to_numeric(frame[column], errors="coerce")
        frame["日期"] = pd.to_datetime(frame["日期"], errors="coerce")
        frame = frame.dropna(subset=["日期"]).sort_values("日期").reset_index(drop=True)
        return _filter_frame_by_dates(frame, start_date, end_date).reset_index(
            drop=True
        )

    def _fetch_fund_flow_individual_rank_em_fallback(
        self, indicator: str
    ) -> pd.DataFrame:
        config = _FUND_FLOW_INDIVIDUAL_RANK_CONFIG[indicator]
        rows = self._fetch_clist_pages({
            "fid": config["fid"],
            "po": "1",
            "pz": "100",
            "pn": "1",
            "np": "1",
            "fltt": "2",
            "invt": "2",
            "ut": _EM_UT,
            "fs": (
                "m:0+t:6+f:!2,m:0+t:13+f:!2,m:0+t:80+f:!2,"
                "m:1+t:2+f:!2,m:1+t:23+f:!2,m:0+t:7+f:!2,m:1+t:3+f:!2"
            ),
            "fields": config["fields"],
        })
        frame = pd.DataFrame(rows)
        if frame.empty:
            return pd.DataFrame(columns=config["columns"])
        renamed = frame.rename(columns=config["rename"])
        payload = renamed[
            [column for column in config["columns"] if column != "序号"]
        ].copy()
        numeric_columns = [
            column for column in payload.columns if column not in {"代码", "名称"}
        ]
        return self._finalize_rank_frame(payload, config["columns"], numeric_columns)

    def _fetch_fund_flow_individual_rank_ths(self, indicator: str) -> pd.DataFrame:
        ths_indicator = _THS_FUND_FLOW_INDIVIDUAL_RANK_MAP[indicator]
        try:
            frame = ak.stock_fund_flow_individual(symbol=ths_indicator)
        except Exception as exc:
            raise MarketDataError(
                "Akshare THS individual fund-flow ranking fetch failed "
                f"for indicator={indicator}"
            ) from exc
        return _normalize_rank_frame_from_ths(
            frame,
            {
                "股票代码": "代码",
                "股票简称": "名称",
            },
        )

    def _fetch_fund_flow_sector_rank_em_raw(
        self,
        indicator: str,
        sector_type: str,
    ) -> pd.DataFrame:
        config = _FUND_FLOW_SECTOR_RANK_CONFIG[indicator]
        rows = self._fetch_clist_pages({
            "pn": "1",
            "pz": "100",
            "po": "1",
            "np": "1",
            "ut": _EM_UT,
            "fltt": "2",
            "invt": "2",
            "fid0": config["fid"],
            "fs": f"m:90 t:{_FUND_FLOW_SECTOR_TYPE_MAP[sector_type]}",
            "stat": config["stat"],
            "fields": config["fields"],
            "rt": "52975239",
            "_": int(time.time() * 1000),
        })
        return pd.DataFrame(rows)

    def _fetch_fund_flow_sector_rank_em_fallback(
        self,
        indicator: str,
        sector_type: str,
    ) -> pd.DataFrame:
        config = _FUND_FLOW_SECTOR_RANK_CONFIG[indicator]
        frame = self._fetch_fund_flow_sector_rank_em_raw(indicator, sector_type)
        if frame.empty:
            return pd.DataFrame(columns=config["columns"])

        renamed = frame.rename(columns=config["rename"])
        payload = renamed[
            [column for column in config["columns"] if column != "序号"]
        ].copy()
        sort_column = config["sort"]
        payload[sort_column] = pd.to_numeric(payload[sort_column], errors="coerce")
        payload = payload.sort_values(sort_column, ascending=False).reset_index(
            drop=True
        )
        numeric_columns = [column for column in payload.columns if column != "名称"]
        return self._finalize_rank_frame(
            payload,
            config["columns"],
            numeric_columns,
            code_column=None,
        )

    def _fetch_fund_flow_sector_rank_ths(
        self,
        indicator: str,
        sector_type: str,
    ) -> pd.DataFrame:
        ths_indicator = _THS_FUND_FLOW_SECTOR_RANK_MAP[indicator]
        fetcher_map = {
            "行业资金流": ak.stock_fund_flow_industry,
            "概念资金流": ak.stock_fund_flow_concept,
        }
        fetcher = fetcher_map.get(sector_type)
        if fetcher is None:
            raise MarketDataError(
                f"No THS sector fund-flow ranking fallback for sector_type={sector_type}"
            )
        try:
            frame = fetcher(symbol=ths_indicator)
        except Exception as exc:
            raise MarketDataError(
                "Akshare THS sector fund-flow ranking fetch failed "
                f"for indicator={indicator}, sector_type={sector_type}"
            ) from exc
        return _normalize_rank_frame_from_ths(
            frame,
            {"行业": "名称"},
            code_column=None,
        )

    def _resolve_sector_board_code(self, symbol: str) -> str:
        raw = self._fetch_fund_flow_sector_rank_em_raw("今日", "行业资金流")
        if raw.empty:
            raise MarketDataError("Unable to load Eastmoney sector board mapping")

        normalized = raw.rename(columns={"f12": "代码", "f14": "名称"})
        matched = normalized.loc[
            normalized["名称"].astype(str).str.strip() == symbol.strip()
        ]
        if matched.empty:
            raise MarketDataError(f"Unknown Eastmoney board symbol: {symbol}")
        return str(matched.iloc[0]["代码"]).strip()

    def _fetch_fund_flow_sector_summary_em_fallback(
        self,
        symbol: str,
        indicator: str,
    ) -> pd.DataFrame:
        config = _FUND_FLOW_SECTOR_SUMMARY_CONFIG[indicator]
        board_code = self._resolve_sector_board_code(symbol)
        data_json = self._request_json(
            _EM_CLIST_URL,
            {
                "fid": config["fid"],
                "po": "1",
                "pz": "50000",
                "pn": "1",
                "np": "2",
                "fltt": "2",
                "invt": "2",
                "ut": _EM_BOARD_UT,
                "fs": f"b:{board_code}",
                "fields": config["fields"],
            },
        )
        rows = ((data_json.get("data") or {}).get("diff")) or []
        frame = pd.DataFrame(rows)
        if frame.empty:
            return pd.DataFrame(columns=config["columns"])

        renamed = frame.rename(columns=config["rename"])
        payload = renamed[
            [column for column in config["columns"] if column != "序号"]
        ].copy()
        numeric_columns = [
            column for column in payload.columns if column not in {"代码", "名称"}
        ]
        return self._finalize_rank_frame(payload, config["columns"], numeric_columns)

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

    def fetch_fund_flow_individual_em(
        self,
        symbol: str,
        start_date: DateLike | None = None,
        end_date: DateLike | None = None,
    ) -> pd.DataFrame:
        stock, market = _normalize_symbol(symbol)
        if market is None:
            raise MarketDataError("Unable to infer A-share exchange for symbol")
        try:
            frame = ak.stock_individual_fund_flow(stock=stock, market=market)
        except Exception:
            frame = None

        expected = [
            "日期",
            "收盘价",
            "涨跌幅",
            "主力净流入-净额",
            "主力净流入-净占比",
        ]
        if _expected_columns_present(frame, expected):
            filtered = _filter_frame_by_dates(frame, start_date, end_date)
            return _normalize_frame(filtered)

        try:
            return self._fetch_fund_flow_individual_em_fallback(
                symbol,
                start_date,
                end_date,
            )
        except Exception as exc:
            if isinstance(exc, MarketDataError):
                raise
            raise MarketDataError(
                f"Eastmoney individual fund-flow fetch failed for symbol={symbol}"
            ) from exc

    def fetch_fund_flow_individual_rank_em(self, indicator: str) -> pd.DataFrame:
        try:
            frame = ak.stock_individual_fund_flow_rank(indicator=indicator)
        except Exception:
            frame = None

        config = _FUND_FLOW_INDIVIDUAL_RANK_CONFIG[indicator]
        if _expected_columns_present(frame, config["columns"]):
            return frame.reset_index(drop=True)

        try:
            return self._fetch_fund_flow_individual_rank_em_fallback(indicator)
        except Exception as exc:
            try:
                return self._fetch_fund_flow_individual_rank_ths(indicator)
            except Exception as ths_exc:
                raise MarketDataError(
                    "Eastmoney individual fund-flow ranking fetch failed "
                    f"for indicator={indicator}; "
                    f"eastmoney_cause={_exception_summary(exc)}; "
                    f"ths_cause={_exception_summary(ths_exc)}"
                ) from ths_exc

    def fetch_fund_flow_sector_rank_em(
        self,
        indicator: str,
        sector_type: str,
    ) -> pd.DataFrame:
        try:
            frame = ak.stock_sector_fund_flow_rank(
                indicator=indicator,
                sector_type=sector_type,
            )
        except Exception:
            frame = None

        config = _FUND_FLOW_SECTOR_RANK_CONFIG[indicator]
        if _expected_columns_present(frame, config["columns"]):
            return frame.reset_index(drop=True)

        try:
            return self._fetch_fund_flow_sector_rank_em_fallback(indicator, sector_type)
        except Exception as exc:
            if sector_type in {"行业资金流", "概念资金流"}:
                try:
                    return self._fetch_fund_flow_sector_rank_ths(indicator, sector_type)
                except Exception as ths_exc:
                    raise MarketDataError(
                        "Eastmoney sector fund-flow ranking fetch failed "
                        f"for indicator={indicator}, sector_type={sector_type}; "
                        f"eastmoney_cause={_exception_summary(exc)}; "
                        f"ths_cause={_exception_summary(ths_exc)}"
                    ) from ths_exc
            raise MarketDataError(
                "Eastmoney sector fund-flow ranking fetch failed "
                f"for indicator={indicator}, sector_type={sector_type}; "
                f"cause={_exception_summary(exc)}"
            ) from exc

    def fetch_fund_flow_sector_summary_em(
        self,
        symbol: str,
        indicator: str,
    ) -> pd.DataFrame:
        try:
            frame = ak.stock_sector_fund_flow_summary(
                symbol=symbol.strip(), indicator=indicator
            )
        except Exception:
            frame = None

        config = _FUND_FLOW_SECTOR_SUMMARY_CONFIG[indicator]
        if _expected_columns_present(frame, config["columns"]):
            return frame.reset_index(drop=True)

        try:
            return self._fetch_fund_flow_sector_summary_em_fallback(symbol, indicator)
        except Exception as exc:
            if isinstance(exc, MarketDataError):
                raise
            raise MarketDataError(
                "Eastmoney sector constituent fund-flow fetch failed "
                f"for symbol={symbol}, indicator={indicator}"
            ) from exc

    def fetch_industry_index_ths(
        self,
        symbol: str,
        start_date: DateLike | None = None,
        end_date: DateLike | None = None,
    ) -> pd.DataFrame:
        try:
            frame = ak.stock_board_industry_index_ths(**_with_optional_ak_dates(
                {"symbol": symbol.strip()},
                start_date=start_date,
                end_date=end_date,
            ))
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

    def fetch_board_change_em(self) -> pd.DataFrame:
        try:
            frame = ak.stock_board_change_em()
        except Exception as exc:
            raise MarketDataError("Akshare board change fetch failed") from exc
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
            frame = ak.stock_board_industry_hist_em(**_with_optional_ak_dates(
                {
                    "symbol": symbol.strip(),
                    "period": period,
                    "adjust": adjust,
                },
                start_date=start_date,
                end_date=end_date,
            ))
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

    def fetch_info_global_em(self) -> pd.DataFrame:
        try:
            frame = ak.stock_info_global_em()
        except Exception as exc:
            raise MarketDataError("Akshare global finance news fetch failed") from exc
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
        if (
            _US_CODE_PATTERN.match(cleaned.upper())
            or cleaned.upper().endswith(_US_SUFFIX)
            or _US_TICKER_PATTERN.match(cleaned.upper())
        ):
            return self._fetch_us(symbol, start, end, period_type)

        start_date = _to_ak_date(start)
        end_date = _to_ak_date(end)
        period = _period_to_ak(period_type)
        normalized_symbol, exchange = _normalize_symbol(symbol)

        primary_frame: pd.DataFrame | None = None
        primary_used_native_period = False
        try:
            primary_frame = ak.stock_zh_a_hist(**_with_optional_ak_dates(
                {
                    "symbol": normalized_symbol,
                    "period": period,
                    "adjust": self._adjust,
                },
                start_date=start,
                end_date=end,
            ))
            primary_used_native_period = True
        except TypeError:
            if period == "daily":
                try:
                    primary_frame = ak.stock_zh_a_hist(**_with_optional_ak_dates(
                        {
                            "symbol": normalized_symbol,
                            "adjust": self._adjust,
                        },
                        start_date=start,
                        end_date=end,
                    ))
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
                resampled = _resample_ohlcv(filtered, _period_to_rule(period_type))
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
                resampled = _resample_ohlcv(filtered, _period_to_rule(period_type))
                resampled = _filter_frame_by_dates(resampled, start, end)
                return _normalize_frame(resampled)
            return _normalize_frame(fallback_frame)

        if primary_frame is not None:
            return _normalize_frame(primary_frame)

        if fallback_frame is not None:
            return _normalize_frame(fallback_frame)

        if primary_error is not None:
            raise MarketDataError(
                f"Akshare fetch failed for symbol={symbol}"
            ) from primary_error

        return pd.DataFrame()
