from __future__ import annotations

from datetime import datetime
from typing import Iterable

import pandas as pd

from data.client import MarketDataClient, MarketDataError
from indicators import IndicatorEngine
from models.mcp_tools import (
    KlineBar,
    KlineRequest,
    MacdPoint,
    MacdRequest,
    MaPoint,
    MaRequest,
    RsiPoint,
    RsiRequest,
)

_DATE_COLUMNS = ("date", "日期", "交易日期", "trade_date", "datetime", "time")
_OPEN_COLUMNS = ("open", "开盘")
_HIGH_COLUMNS = ("high", "最高")
_LOW_COLUMNS = ("low", "最低")
_CLOSE_COLUMNS = ("close", "收盘")
_VOLUME_COLUMNS = ("volume", "vol", "成交量")


def _find_column(columns: Iterable[str], candidates: Iterable[str]) -> str | None:
    for name in candidates:
        if name in columns:
            return name
    return None


def _coerce_timestamp(value: object) -> datetime:
    timestamp = pd.to_datetime(value, errors="coerce")
    if pd.isna(timestamp):
        raise MarketDataError("Timestamp is missing or invalid")
    if isinstance(timestamp, pd.Timestamp):
        return timestamp.to_pydatetime()
    return timestamp


def _coerce_required_float(value: object, field: str) -> float:
    if pd.isna(value):
        raise MarketDataError(f"Missing required field: {field}")
    return float(value)


def _coerce_optional_float(value: object) -> float | None:
    if pd.isna(value):
        return None
    return float(value)


def _extract_timestamps(frame: pd.DataFrame) -> pd.Series:
    date_col = _find_column(frame.columns, _DATE_COLUMNS)
    if date_col is None:
        return pd.to_datetime(frame.index, errors="coerce")
    return pd.to_datetime(frame[date_col], errors="coerce")


def _extract_close_series(frame: pd.DataFrame) -> pd.Series:
    close_col = _find_column(frame.columns, _CLOSE_COLUMNS)
    if close_col is None:
        for name in frame.columns:
            if pd.api.types.is_numeric_dtype(frame[name]):
                return frame[name]
        raise MarketDataError("No numeric close series found")
    return frame[close_col]


def _slice_tail(items: list[object], limit: int) -> list[object]:
    if limit <= 0:
        return []
    return items[-limit:]


def build_kline_bars(frame: pd.DataFrame, limit: int) -> list[KlineBar]:
    if frame is None or frame.empty:
        return []

    timestamps = _extract_timestamps(frame)
    open_col = _find_column(frame.columns, _OPEN_COLUMNS)
    high_col = _find_column(frame.columns, _HIGH_COLUMNS)
    low_col = _find_column(frame.columns, _LOW_COLUMNS)
    close_col = _find_column(frame.columns, _CLOSE_COLUMNS)
    volume_col = _find_column(frame.columns, _VOLUME_COLUMNS)

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

    bars: list[KlineBar] = []
    for idx in range(len(frame)):
        bars.append(
            KlineBar(
                timestamp=_coerce_timestamp(timestamps.iloc[idx]),
                open=_coerce_required_float(frame[open_col].iloc[idx], "open"),
                high=_coerce_required_float(frame[high_col].iloc[idx], "high"),
                low=_coerce_required_float(frame[low_col].iloc[idx], "low"),
                close=_coerce_required_float(frame[close_col].iloc[idx], "close"),
                volume=(
                    _coerce_optional_float(frame[volume_col].iloc[idx])
                    if volume_col is not None
                    else None
                ),
            )
        )

    return _slice_tail(bars, limit)


def build_rsi_points(
    timestamps: pd.Series, values: pd.Series, limit: int
) -> list[RsiPoint]:
    points = [
        RsiPoint(timestamp=_coerce_timestamp(ts), rsi=_coerce_optional_float(val))
        for ts, val in zip(timestamps, values, strict=True)
    ]
    return _slice_tail(points, limit)


def build_ma_points(
    timestamps: pd.Series, values: pd.Series, limit: int
) -> list[MaPoint]:
    points = [
        MaPoint(timestamp=_coerce_timestamp(ts), ma=_coerce_optional_float(val))
        for ts, val in zip(timestamps, values, strict=True)
    ]
    return _slice_tail(points, limit)


def build_macd_points(
    timestamps: pd.Series, values: pd.DataFrame, limit: int
) -> list[MacdPoint]:
    points = [
        MacdPoint(
            timestamp=_coerce_timestamp(ts),
            macd=_coerce_optional_float(row["macd"]),
            signal=_coerce_optional_float(row["signal"]),
            histogram=_coerce_optional_float(row["histogram"]),
        )
        for ts, (_, row) in zip(timestamps, values.iterrows(), strict=True)
    ]
    return _slice_tail(points, limit)


class MarketService:
    def __init__(self, client: MarketDataClient, engine: IndicatorEngine) -> None:
        self._client = client
        self._engine = engine

    def kline(self, request: KlineRequest) -> list[KlineBar]:
        frame = self._client.fetch(request.symbol)
        return build_kline_bars(frame, request.limit)

    def rsi(self, request: RsiRequest) -> list[RsiPoint]:
        frame = self._client.fetch(request.symbol)
        if frame is None or frame.empty:
            return []
        timestamps = _extract_timestamps(frame)
        close_series = _extract_close_series(frame)
        values = self._engine.compute("rsi", close_series, timeperiod=request.period)
        return build_rsi_points(timestamps, values, request.limit)

    def ma(self, request: MaRequest) -> list[MaPoint]:
        frame = self._client.fetch(request.symbol)
        if frame is None or frame.empty:
            return []
        timestamps = _extract_timestamps(frame)
        close_series = _extract_close_series(frame)
        if request.ma_type == "ema":
            values = self._engine.compute("ema", close_series, timeperiod=request.period)
        elif request.ma_type == "sma":
            values = self._engine.compute("sma", close_series, timeperiod=request.period)
        else:
            values = self._engine.compute_ma(close_series, timeperiod=request.period)
        return build_ma_points(timestamps, values, request.limit)

    def macd(self, request: MacdRequest) -> list[MacdPoint]:
        frame = self._client.fetch(request.symbol)
        if frame is None or frame.empty:
            return []
        timestamps = _extract_timestamps(frame)
        close_series = _extract_close_series(frame)
        values = self._engine.compute_macd(
            close_series,
            fastperiod=request.fast_period,
            slowperiod=request.slow_period,
            signalperiod=request.signal_period,
        )
        return build_macd_points(timestamps, values, request.limit)
