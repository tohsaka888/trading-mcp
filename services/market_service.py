from __future__ import annotations

from datetime import datetime
from typing import Iterable, Sequence, SupportsFloat, TypeVar, cast

import pandas as pd
from pandas.api.types import is_scalar

from data.client import MarketDataClient, MarketDataError
from indicators import IndicatorEngine
from models.mcp_tools import (
    KlineBar,
    KlineRequest,
    KlineResponse,
    MacdPoint,
    MacdRequest,
    MacdResponse,
    MaPoint,
    MaRequest,
    MaResponse,
    RsiPoint,
    RsiRequest,
    RsiResponse,
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
    timestamp = pd.to_datetime([value], errors="coerce")[0]
    if pd.isna(timestamp):
        raise MarketDataError("Timestamp is missing or invalid")
    if isinstance(timestamp, pd.Timestamp):
        return timestamp.to_pydatetime()
    if isinstance(timestamp, datetime):
        return timestamp
    raise MarketDataError("Timestamp is missing or invalid")


def _is_missing(value: object) -> bool:
    if not is_scalar(value):
        return False
    return bool(pd.isna(value))


def _coerce_required_float(value: object, field: str) -> float:
    if _is_missing(value):
        raise MarketDataError(f"Missing required field: {field}")
    try:
        return float(cast(SupportsFloat, value))
    except (TypeError, ValueError) as exc:
        raise MarketDataError(f"Invalid numeric field: {field}") from exc


def _coerce_optional_float(value: object) -> float | None:
    if _is_missing(value):
        return None
    try:
        return float(cast(SupportsFloat, value))
    except (TypeError, ValueError):
        return None


def _round_optional_float(value: float | None, *, ndigits: int = 3) -> float | None:
    if value is None:
        return None
    return round(value, ndigits)


def _extract_timestamps(frame: pd.DataFrame) -> pd.Series:
    date_col = _find_column(frame.columns, _DATE_COLUMNS)
    if date_col is None:
        return pd.Series(
            pd.to_datetime(frame.index, errors="coerce"), index=frame.index
        )
    return pd.to_datetime(frame[date_col], errors="coerce")


def _extract_close_series(frame: pd.DataFrame) -> pd.Series:
    close_col = _find_column(frame.columns, _CLOSE_COLUMNS)
    if close_col is None:
        for name in frame.columns:
            if pd.api.types.is_numeric_dtype(frame[name]):
                series = frame[name]
                if isinstance(series, pd.Series):
                    return series
                return series.iloc[:, 0]
        raise MarketDataError("No numeric close series found")
    series = frame[close_col]
    if isinstance(series, pd.Series):
        return series
    return series.iloc[:, 0]


T = TypeVar("T")


def _paginate_latest(
    items: Sequence[T],
    limit: int,
    offset: int,
) -> tuple[list[T], int, int, bool, int | None]:
    total = len(items)
    if total == 0 or limit <= 0:
        return [], total, 0, False, None

    if offset >= total:
        return [], total, 0, False, None

    end = total - offset
    start = max(end - limit, 0)
    sliced = list(items[start:end])
    count = len(sliced)
    has_more = start > 0
    next_offset = offset + limit if has_more else None
    return sliced, total, count, has_more, next_offset


def build_kline_bars(frame: pd.DataFrame) -> list[KlineBar]:
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

    return bars


def build_rsi_points(timestamps: pd.Series, values: pd.Series) -> list[RsiPoint]:
    points = [
        RsiPoint(
            timestamp=_coerce_timestamp(ts),
            rsi=_round_optional_float(_coerce_optional_float(val)),
        )
        for ts, val in zip(timestamps, values, strict=True)
    ]
    return points


def build_ma_points(timestamps: pd.Series, values: pd.Series) -> list[MaPoint]:
    points = [
        MaPoint(
            timestamp=_coerce_timestamp(ts),
            ma=_round_optional_float(_coerce_optional_float(val)),
        )
        for ts, val in zip(timestamps, values, strict=True)
    ]
    return points


def build_macd_points(timestamps: pd.Series, values: pd.DataFrame) -> list[MacdPoint]:
    points = [
        MacdPoint(
            timestamp=_coerce_timestamp(ts),
            macd=_round_optional_float(_coerce_optional_float(row["macd"])),
            signal=_round_optional_float(_coerce_optional_float(row["signal"])),
            histogram=_round_optional_float(_coerce_optional_float(row["histogram"])),
        )
        for ts, (_, row) in zip(timestamps, values.iterrows(), strict=True)
    ]
    return points


class MarketService:
    def __init__(self, client: MarketDataClient, engine: IndicatorEngine) -> None:
        self._client = client
        self._engine = engine

    def kline(self, request: KlineRequest) -> KlineResponse:
        frame = self._client.fetch(request.symbol, request.start_date, request.end_date)
        bars = build_kline_bars(frame)
        items, total, count, has_more, next_offset = _paginate_latest(
            bars, request.limit, request.offset
        )
        return KlineResponse(
            symbol=request.symbol,
            items=items,
            count=count,
            total=total,
            limit=request.limit,
            offset=request.offset,
            has_more=has_more,
            next_offset=next_offset,
            start_date=request.start_date,
            end_date=request.end_date,
        )

    def rsi(self, request: RsiRequest) -> RsiResponse:
        frame = self._client.fetch(request.symbol, request.start_date, request.end_date)
        if frame is None or frame.empty:
            return RsiResponse(
                symbol=request.symbol,
                items=[],
                count=0,
                total=0,
                limit=request.limit,
                offset=request.offset,
                has_more=False,
                next_offset=None,
                start_date=request.start_date,
                end_date=request.end_date,
            )
        timestamps = _extract_timestamps(frame)
        close_series = _extract_close_series(frame)
        values = self._engine.compute("rsi", close_series, timeperiod=request.period)
        points = build_rsi_points(timestamps, values)
        items, total, count, has_more, next_offset = _paginate_latest(
            points, request.limit, request.offset
        )
        return RsiResponse(
            symbol=request.symbol,
            items=items,
            count=count,
            total=total,
            limit=request.limit,
            offset=request.offset,
            has_more=has_more,
            next_offset=next_offset,
            start_date=request.start_date,
            end_date=request.end_date,
        )

    def ma(self, request: MaRequest) -> MaResponse:
        frame = self._client.fetch(request.symbol, request.start_date, request.end_date)
        if frame is None or frame.empty:
            return MaResponse(
                symbol=request.symbol,
                items=[],
                count=0,
                total=0,
                limit=request.limit,
                offset=request.offset,
                has_more=False,
                next_offset=None,
                start_date=request.start_date,
                end_date=request.end_date,
            )
        timestamps = _extract_timestamps(frame)
        close_series = _extract_close_series(frame)
        if request.ma_type == "ema":
            values = self._engine.compute(
                "ema", close_series, timeperiod=request.period
            )
        elif request.ma_type == "sma":
            values = self._engine.compute(
                "sma", close_series, timeperiod=request.period
            )
        else:
            values = self._engine.compute_ma(close_series, timeperiod=request.period)
        points = build_ma_points(timestamps, values)
        items, total, count, has_more, next_offset = _paginate_latest(
            points, request.limit, request.offset
        )
        return MaResponse(
            symbol=request.symbol,
            items=items,
            count=count,
            total=total,
            limit=request.limit,
            offset=request.offset,
            has_more=has_more,
            next_offset=next_offset,
            start_date=request.start_date,
            end_date=request.end_date,
        )

    def macd(self, request: MacdRequest) -> MacdResponse:
        frame = self._client.fetch(request.symbol, request.start_date, request.end_date)
        if frame is None or frame.empty:
            return MacdResponse(
                symbol=request.symbol,
                items=[],
                count=0,
                total=0,
                limit=request.limit,
                offset=request.offset,
                has_more=False,
                next_offset=None,
                start_date=request.start_date,
                end_date=request.end_date,
            )
        timestamps = _extract_timestamps(frame)
        close_series = _extract_close_series(frame)
        values = self._engine.compute_macd(
            close_series,
            fastperiod=request.fast_period,
            slowperiod=request.slow_period,
            signalperiod=request.signal_period,
        )
        points = build_macd_points(timestamps, values)
        items, total, count, has_more, next_offset = _paginate_latest(
            points, request.limit, request.offset
        )
        return MacdResponse(
            symbol=request.symbol,
            items=items,
            count=count,
            total=total,
            limit=request.limit,
            offset=request.offset,
            has_more=has_more,
            next_offset=next_offset,
            start_date=request.start_date,
            end_date=request.end_date,
        )
