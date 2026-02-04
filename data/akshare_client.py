from __future__ import annotations

from datetime import date, datetime
from typing import Iterable

import akshare as ak
import pandas as pd

from .client import DateLike, MarketDataError


_DATE_COLUMNS = ("date", "日期", "交易日期", "trade_date")


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


def _find_date_column(columns: Iterable[str]) -> str | None:
    for name in _DATE_COLUMNS:
        if name in columns:
            return name
    return None


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

    def fetch(
        self, symbol: str, start: DateLike | None = None, end: DateLike | None = None
    ) -> pd.DataFrame:
        start_date = _to_ak_date(start)
        end_date = _to_ak_date(end)

        try:
            frame = ak.stock_zh_a_hist(
                symbol=symbol,
                start_date=start_date or "",
                end_date=end_date or "",
                adjust=self._adjust,
            )
        except Exception as exc:  # pragma: no cover - network/data issues
            raise MarketDataError(f"Akshare fetch failed for symbol={symbol}") from exc

        return _normalize_frame(frame)
