from __future__ import annotations

from datetime import date, datetime
import re
from typing import Any, Iterable, Protocol, Sequence, SupportsFloat, TypeVar, cast

import pandas as pd
from pandas.api.types import is_scalar
import talib

from data.client import MarketDataClient, MarketDataError
from models.mcp_tools import (
    BoardChangeEmRequest,
    BoardChangeEmResponse,
    FundFlowIndividualEmRequest,
    FundFlowIndividualEmResponse,
    FundFlowIndividualRankEmRequest,
    FundFlowIndividualRankEmResponse,
    FundFlowSectorRankEmRequest,
    FundFlowSectorRankEmResponse,
    FundFlowSectorSummaryEmRequest,
    FundFlowSectorSummaryEmResponse,
    FundamentalCnIndicatorsRequest,
    FundamentalCnIndicatorsResponse,
    FundamentalUsIndicatorsRequest,
    FundamentalUsIndicatorsResponse,
    FundamentalUsReportRequest,
    FundamentalUsReportResponse,
    IndustryConsEmRequest,
    IndustryConsEmResponse,
    IndustryHistEmRequest,
    IndustryHistEmResponse,
    IndustryHistMinEmRequest,
    IndustryHistMinEmResponse,
    IndustryIndexThsRequest,
    IndustryIndexThsResponse,
    IndustryNameEmRequest,
    IndustryNameEmResponse,
    IndustrySpotEmRequest,
    IndustrySpotEmResponse,
    IndustrySummaryThsRequest,
    IndustrySummaryThsResponse,
    InfoGlobalEmRequest,
    InfoGlobalEmResponse,
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
    VolumePoint,
    VolumeRequest,
    VolumeResponse,
)

_DATE_COLUMNS = ("date", "日期", "交易日期", "trade_date", "datetime", "time")
_OPEN_COLUMNS = ("open", "开盘")
_HIGH_COLUMNS = ("high", "最高")
_LOW_COLUMNS = ("low", "最低")
_CLOSE_COLUMNS = ("close", "收盘")
_VOLUME_COLUMNS = ("volume", "vol", "成交量")
_AMOUNT_COLUMNS = ("amount", "成交额")
_TURNOVER_RATE_COLUMNS = ("turnover_rate", "换手率")
_FUNDAMENTAL_DATE_COLUMNS = (
    "REPORT_DATE",
    "STD_REPORT_DATE",
    "FINANCIAL_DATE",
    "NOTICE_DATE",
    "date",
    "日期",
    "交易日期",
    "trade_date",
    "datetime",
    "time",
)

_US_CODE_PATTERN = re.compile(r"^\d{3}\.[A-Z0-9.-]+$")
_US_SUFFIX = ".US"
_US_TICKER_PATTERN = re.compile(r"^[A-Z][A-Z.-]*$")
_US_EXCHANGE_SUFFIXES = (".NYSE", ".NASDAQ", ".AMEX")


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


def _coerce_sort_number(value: object) -> float | None:
    if _is_missing(value):
        return None
    if isinstance(value, str):
        cleaned = value.strip().replace(",", "")
        if cleaned.endswith("%"):
            cleaned = cleaned[:-1]
        if not cleaned:
            return None
        try:
            return float(cleaned)
        except ValueError:
            return None
    return _coerce_optional_float(value)


def _round_optional_float(value: float | None, *, ndigits: int = 3) -> float | None:
    if value is None:
        return None
    return round(value, ndigits)


def _coerce_filter_date(value: str | None) -> pd.Timestamp | None:
    if value is None:
        return None
    cleaned = value.strip()
    if not cleaned:
        return None
    if "-" in cleaned:
        cleaned = cleaned.replace("-", "")
    return pd.to_datetime(cleaned, format="%Y%m%d", errors="coerce")


def _find_fundamental_date_column(columns: Iterable[str]) -> str | None:
    for name in _FUNDAMENTAL_DATE_COLUMNS:
        if name in columns:
            return name
    return None


def _normalize_fundamental_frame(frame: pd.DataFrame) -> pd.DataFrame:
    if frame is None or frame.empty:
        return frame

    date_col = _find_fundamental_date_column(frame.columns)
    if date_col is None:
        return frame.reset_index(drop=True)

    normalized = frame.copy()
    normalized[date_col] = pd.to_datetime(normalized[date_col], errors="coerce")
    normalized = normalized.sort_values(date_col).reset_index(drop=True)
    return normalized


def _filter_fundamental_frame_by_dates(
    frame: pd.DataFrame,
    start_date: str | None,
    end_date: str | None,
) -> pd.DataFrame:
    if frame is None or frame.empty:
        return frame

    start_ts = _coerce_filter_date(start_date)
    end_ts = _coerce_filter_date(end_date)
    if start_ts is None and end_ts is None:
        return frame

    date_col = _find_fundamental_date_column(frame.columns)
    if date_col is None:
        return frame

    dates = pd.to_datetime(frame[date_col], errors="coerce")
    mask = pd.Series(True, index=frame.index)
    if start_ts is not None:
        mask &= dates >= start_ts
    if end_ts is not None:
        mask &= dates <= end_ts
    return frame.loc[mask]


def _to_json_friendly_value(value: object) -> Any:
    if _is_missing(value):
        return None
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if hasattr(value, "item"):
        try:
            return value.item()  # type: ignore[no-any-return]
        except Exception:
            return value
    return value


def build_fundamental_records(
    frame: pd.DataFrame,
) -> tuple[list[str], list[dict[str, Any]]]:
    if frame is None or frame.empty:
        return [], []

    columns = [str(col) for col in frame.columns]
    records: list[dict[str, Any]] = []
    for _, row in frame.iterrows():
        record: dict[str, Any] = {}
        for column in frame.columns:
            record[str(column)] = _to_json_friendly_value(row[column])
        records.append(record)
    return columns, records


def _build_table_records(
    frame: pd.DataFrame,
    *,
    start_date: str | None = None,
    end_date: str | None = None,
) -> tuple[list[str], list[dict[str, Any]]]:
    filtered = _filter_fundamental_frame_by_dates(frame, start_date, end_date)
    normalized = _normalize_fundamental_frame(filtered)
    return build_fundamental_records(normalized)


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


def _is_us_symbol(symbol: str) -> bool:
    upper = symbol.strip().upper()
    if not upper:
        return False
    if upper.endswith(_US_EXCHANGE_SUFFIXES):
        return False
    return (
        bool(_US_CODE_PATTERN.match(upper))
        or upper.endswith(_US_SUFFIX)
        or bool(_US_TICKER_PATTERN.match(upper))
    )


T = TypeVar("T")


class IndicatorCalculator(Protocol):
    def compute(
        self, name: str, series: Sequence[float] | pd.Series, **kwargs: object
    ) -> pd.Series: ...

    def compute_ma(
        self,
        series: Sequence[float] | pd.Series,
        *,
        timeperiod: int = 20,
        matype: talib.MA_Type = talib.MA_Type.SMA,
    ) -> pd.Series: ...

    def compute_macd(
        self,
        series: Sequence[float] | pd.Series,
        *,
        fastperiod: int = 12,
        slowperiod: int = 26,
        signalperiod: int = 9,
    ) -> pd.DataFrame: ...


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


def _paginate_head(
    items: Sequence[T],
    limit: int,
    offset: int,
) -> tuple[list[T], int, int, bool, int | None]:
    total = len(items)
    if total == 0 or limit <= 0:
        return [], total, 0, False, None

    if offset >= total:
        return [], total, 0, False, None

    end = min(offset + limit, total)
    sliced = list(items[offset:end])
    count = len(sliced)
    has_more = end < total
    next_offset = end if has_more else None
    return sliced, total, count, has_more, next_offset


def _resolve_sector_rank_sort_candidates(
    indicator: str,
    sort_by: str,
) -> tuple[str, ...]:
    if sort_by == "涨跌幅":
        return (f"{indicator}涨跌幅", "今天涨跌幅", "阶段涨跌幅", "涨跌幅")
    if sort_by == "主力净流入":
        return (f"{indicator}主力净流入-净额", "主力净流入-净额", "净额")
    raise MarketDataError(f"Unsupported sector rank sort_by: {sort_by}")


def _sort_table_records_desc(
    columns: Sequence[str],
    records: Sequence[dict[str, Any]],
    *,
    candidate_columns: Sequence[str],
) -> tuple[list[dict[str, Any]], str]:
    sort_column = next((column for column in candidate_columns if column in columns), None)
    if sort_column is None:
        raise MarketDataError(
            "No matching sort column found. "
            f"Candidates: {', '.join(candidate_columns)}"
        )

    def sort_key(record: dict[str, Any]) -> tuple[int, float]:
        sort_value = _coerce_sort_number(record.get(sort_column))
        if sort_value is None:
            return (1, 0.0)
        return (0, -sort_value)

    return sorted(records, key=sort_key), sort_column


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


def build_volume_points(frame: pd.DataFrame) -> list[VolumePoint]:
    if frame is None or frame.empty:
        return []

    timestamps = _extract_timestamps(frame)
    volume_col = _find_column(frame.columns, _VOLUME_COLUMNS)
    amount_col = _find_column(frame.columns, _AMOUNT_COLUMNS)
    turnover_rate_col = _find_column(frame.columns, _TURNOVER_RATE_COLUMNS)

    points: list[VolumePoint] = []
    for idx in range(len(frame)):
        points.append(
            VolumePoint(
                timestamp=_coerce_timestamp(timestamps.iloc[idx]),
                volume=(
                    _coerce_optional_float(frame[volume_col].iloc[idx])
                    if volume_col is not None
                    else None
                ),
                amount=(
                    _coerce_optional_float(frame[amount_col].iloc[idx])
                    if amount_col is not None
                    else None
                ),
                turnover_rate=(
                    _coerce_optional_float(frame[turnover_rate_col].iloc[idx])
                    if turnover_rate_col is not None
                    else None
                ),
            )
        )

    return points


class MarketService:
    def __init__(self, client: MarketDataClient, engine: IndicatorCalculator) -> None:
        self._client = client
        self._engine = engine

    def kline(self, request: KlineRequest) -> KlineResponse:
        frame = self._client.fetch(
            request.symbol,
            request.start_date,
            request.end_date,
            period_type=request.period_type,
        )
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
            period_type=request.period_type,
            start_date=request.start_date,
            end_date=request.end_date,
        )

    def rsi(self, request: RsiRequest) -> RsiResponse:
        frame = self._client.fetch(
            request.symbol,
            request.start_date,
            request.end_date,
            period_type=request.period_type,
        )
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
                period_type=request.period_type,
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
            period_type=request.period_type,
            start_date=request.start_date,
            end_date=request.end_date,
        )

    def ma(self, request: MaRequest) -> MaResponse:
        frame = self._client.fetch(
            request.symbol,
            request.start_date,
            request.end_date,
            period_type=request.period_type,
        )
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
                period_type=request.period_type,
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
            period_type=request.period_type,
            start_date=request.start_date,
            end_date=request.end_date,
        )

    def macd(self, request: MacdRequest) -> MacdResponse:
        frame = self._client.fetch(
            request.symbol,
            request.start_date,
            request.end_date,
            period_type=request.period_type,
        )
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
                period_type=request.period_type,
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
            period_type=request.period_type,
            start_date=request.start_date,
            end_date=request.end_date,
        )

    def volume(self, request: VolumeRequest) -> VolumeResponse:
        frame = self._client.fetch(
            request.symbol,
            request.start_date,
            request.end_date,
            period_type=request.period_type,
        )
        is_us = _is_us_symbol(request.symbol)
        volume_unit = "share" if is_us else "lot"
        default_amount_unit = "USD" if is_us else "CNY"

        if frame is None or frame.empty:
            return VolumeResponse(
                symbol=request.symbol,
                items=[],
                count=0,
                total=0,
                limit=request.limit,
                offset=request.offset,
                has_more=False,
                next_offset=None,
                period_type=request.period_type,
                start_date=request.start_date,
                end_date=request.end_date,
                volume_unit=volume_unit,
                amount_unit=default_amount_unit,
                turnover_rate_unit="percent",
            )

        amount_unit = (
            default_amount_unit
            if _find_column(frame.columns, _AMOUNT_COLUMNS) is not None
            else None
        )
        points = build_volume_points(frame)
        items, total, count, has_more, next_offset = _paginate_latest(
            points, request.limit, request.offset
        )
        return VolumeResponse(
            symbol=request.symbol,
            items=items,
            count=count,
            total=total,
            limit=request.limit,
            offset=request.offset,
            has_more=has_more,
            next_offset=next_offset,
            period_type=request.period_type,
            start_date=request.start_date,
            end_date=request.end_date,
            volume_unit=volume_unit,
            amount_unit=amount_unit,
            turnover_rate_unit="percent",
        )

    def fund_flow_individual_em(
        self, request: FundFlowIndividualEmRequest
    ) -> FundFlowIndividualEmResponse:
        frame = self._client.fetch_fund_flow_individual_em(
            request.symbol,
            request.start_date,
            request.end_date,
        )
        columns, records = _build_table_records(
            frame,
            start_date=request.start_date,
            end_date=request.end_date,
        )
        items, total, count, has_more, next_offset = _paginate_latest(
            records, request.limit, request.offset
        )
        return FundFlowIndividualEmResponse(
            symbol=request.symbol,
            items=items,
            columns=columns,
            count=count,
            total=total,
            limit=request.limit,
            offset=request.offset,
            has_more=has_more,
            next_offset=next_offset,
            start_date=request.start_date,
            end_date=request.end_date,
        )

    def fund_flow_individual_rank_em(
        self, request: FundFlowIndividualRankEmRequest
    ) -> FundFlowIndividualRankEmResponse:
        frame = self._client.fetch_fund_flow_individual_rank_em(request.indicator)
        columns, records = _build_table_records(frame)
        items, total, count, has_more, next_offset = _paginate_head(
            records, request.limit, request.offset
        )
        return FundFlowIndividualRankEmResponse(
            indicator=request.indicator,
            items=items,
            columns=columns,
            count=count,
            total=total,
            limit=request.limit,
            offset=request.offset,
            has_more=has_more,
            next_offset=next_offset,
        )

    def fund_flow_sector_rank_em(
        self, request: FundFlowSectorRankEmRequest
    ) -> FundFlowSectorRankEmResponse:
        frame = self._client.fetch_fund_flow_sector_rank_em(
            request.indicator,
            request.sector_type,
        )
        columns, records = _build_table_records(frame)
        try:
            sorted_records, _ = _sort_table_records_desc(
                columns,
                records,
                candidate_columns=_resolve_sector_rank_sort_candidates(
                    request.indicator,
                    request.sort_by,
                ),
            )
        except MarketDataError as exc:
            raise MarketDataError(
                "Sector rank sorting failed "
                f"for indicator={request.indicator}, "
                f"sector_type={request.sector_type}, sort_by={request.sort_by}; "
                f"cause={exc}"
            ) from exc
        items, total, count, has_more, next_offset = _paginate_head(
            sorted_records, request.limit, request.offset
        )
        return FundFlowSectorRankEmResponse(
            indicator=request.indicator,
            sector_type=request.sector_type,
            sort_by=request.sort_by,
            items=items,
            columns=columns,
            count=count,
            total=total,
            limit=request.limit,
            offset=request.offset,
            has_more=has_more,
            next_offset=next_offset,
        )

    def fund_flow_sector_summary_em(
        self, request: FundFlowSectorSummaryEmRequest
    ) -> FundFlowSectorSummaryEmResponse:
        frame = self._client.fetch_fund_flow_sector_summary_em(
            request.symbol,
            request.indicator,
        )
        columns, records = _build_table_records(frame)
        items, total, count, has_more, next_offset = _paginate_head(
            records, request.limit, request.offset
        )
        return FundFlowSectorSummaryEmResponse(
            symbol=request.symbol,
            indicator=request.indicator,
            items=items,
            columns=columns,
            count=count,
            total=total,
            limit=request.limit,
            offset=request.offset,
            has_more=has_more,
            next_offset=next_offset,
        )

    def industry_summary_ths(
        self, request: IndustrySummaryThsRequest
    ) -> IndustrySummaryThsResponse:
        frame = self._client.fetch_industry_summary_ths()
        columns, records = _build_table_records(frame)
        items, total, count, has_more, next_offset = _paginate_latest(
            records, request.limit, request.offset
        )
        return IndustrySummaryThsResponse(
            items=items,
            columns=columns,
            count=count,
            total=total,
            limit=request.limit,
            offset=request.offset,
            has_more=has_more,
            next_offset=next_offset,
        )

    def industry_index_ths(
        self, request: IndustryIndexThsRequest
    ) -> IndustryIndexThsResponse:
        frame = self._client.fetch_industry_index_ths(
            request.symbol,
            request.start_date,
            request.end_date,
        )
        columns, records = _build_table_records(
            frame,
            start_date=request.start_date,
            end_date=request.end_date,
        )
        items, total, count, has_more, next_offset = _paginate_latest(
            records, request.limit, request.offset
        )
        return IndustryIndexThsResponse(
            symbol=request.symbol,
            items=items,
            columns=columns,
            count=count,
            total=total,
            limit=request.limit,
            offset=request.offset,
            has_more=has_more,
            next_offset=next_offset,
            start_date=request.start_date,
            end_date=request.end_date,
        )

    def industry_name_em(
        self, request: IndustryNameEmRequest
    ) -> IndustryNameEmResponse:
        frame = self._client.fetch_industry_name_em()
        columns, records = _build_table_records(frame)
        items, total, count, has_more, next_offset = _paginate_latest(
            records, request.limit, request.offset
        )
        return IndustryNameEmResponse(
            items=items,
            columns=columns,
            count=count,
            total=total,
            limit=request.limit,
            offset=request.offset,
            has_more=has_more,
            next_offset=next_offset,
        )

    def board_change_em(
        self, request: BoardChangeEmRequest
    ) -> BoardChangeEmResponse:
        frame = self._client.fetch_board_change_em()
        columns, records = _build_table_records(frame)
        items, total, count, has_more, next_offset = _paginate_latest(
            records, request.limit, request.offset
        )
        return BoardChangeEmResponse(
            items=items,
            columns=columns,
            count=count,
            total=total,
            limit=request.limit,
            offset=request.offset,
            has_more=has_more,
            next_offset=next_offset,
        )

    def industry_spot_em(
        self, request: IndustrySpotEmRequest
    ) -> IndustrySpotEmResponse:
        frame = self._client.fetch_industry_spot_em(request.symbol)
        columns, records = _build_table_records(frame)
        items, total, count, has_more, next_offset = _paginate_latest(
            records, request.limit, request.offset
        )
        return IndustrySpotEmResponse(
            symbol=request.symbol,
            items=items,
            columns=columns,
            count=count,
            total=total,
            limit=request.limit,
            offset=request.offset,
            has_more=has_more,
            next_offset=next_offset,
        )

    def industry_cons_em(
        self, request: IndustryConsEmRequest
    ) -> IndustryConsEmResponse:
        frame = self._client.fetch_industry_cons_em(request.symbol)
        columns, records = _build_table_records(frame)
        items, total, count, has_more, next_offset = _paginate_latest(
            records, request.limit, request.offset
        )
        return IndustryConsEmResponse(
            symbol=request.symbol,
            items=items,
            columns=columns,
            count=count,
            total=total,
            limit=request.limit,
            offset=request.offset,
            has_more=has_more,
            next_offset=next_offset,
        )

    def industry_hist_em(
        self, request: IndustryHistEmRequest
    ) -> IndustryHistEmResponse:
        frame = self._client.fetch_industry_hist_em(
            request.symbol,
            request.start_date,
            request.end_date,
            request.period,
            request.adjust,
        )
        columns, records = _build_table_records(
            frame,
            start_date=request.start_date,
            end_date=request.end_date,
        )
        items, total, count, has_more, next_offset = _paginate_latest(
            records, request.limit, request.offset
        )
        return IndustryHistEmResponse(
            symbol=request.symbol,
            period=request.period,
            adjust=request.adjust,
            items=items,
            columns=columns,
            count=count,
            total=total,
            limit=request.limit,
            offset=request.offset,
            has_more=has_more,
            next_offset=next_offset,
            start_date=request.start_date,
            end_date=request.end_date,
        )

    def industry_hist_min_em(
        self, request: IndustryHistMinEmRequest
    ) -> IndustryHistMinEmResponse:
        frame = self._client.fetch_industry_hist_min_em(request.symbol, request.period)
        columns, records = _build_table_records(frame)
        items, total, count, has_more, next_offset = _paginate_latest(
            records, request.limit, request.offset
        )
        return IndustryHistMinEmResponse(
            symbol=request.symbol,
            period=request.period,
            items=items,
            columns=columns,
            count=count,
            total=total,
            limit=request.limit,
            offset=request.offset,
            has_more=has_more,
            next_offset=next_offset,
        )

    def info_global_em(
        self, request: InfoGlobalEmRequest
    ) -> InfoGlobalEmResponse:
        frame = self._client.fetch_info_global_em()
        columns, records = _build_table_records(frame)
        items, total, count, has_more, next_offset = _paginate_latest(
            records, request.limit, request.offset
        )
        return InfoGlobalEmResponse(
            items=items,
            columns=columns,
            count=count,
            total=total,
            limit=request.limit,
            offset=request.offset,
            has_more=has_more,
            next_offset=next_offset,
        )

    def fundamental_cn_indicators(
        self, request: FundamentalCnIndicatorsRequest
    ) -> FundamentalCnIndicatorsResponse:
        frame = self._client.fetch_cn_financial_indicators(
            request.symbol,
            request.indicator,
        )
        columns, records = _build_table_records(
            frame,
            start_date=request.start_date,
            end_date=request.end_date,
        )
        items, total, count, has_more, next_offset = _paginate_latest(
            records, request.limit, request.offset
        )
        return FundamentalCnIndicatorsResponse(
            symbol=request.symbol,
            indicator=request.indicator,
            items=items,
            columns=columns,
            count=count,
            total=total,
            limit=request.limit,
            offset=request.offset,
            has_more=has_more,
            next_offset=next_offset,
            start_date=request.start_date,
            end_date=request.end_date,
        )

    def fundamental_us_report(
        self, request: FundamentalUsReportRequest
    ) -> FundamentalUsReportResponse:
        frame = self._client.fetch_us_financial_report(
            request.stock,
            request.symbol,
            request.indicator,
        )
        columns, records = _build_table_records(
            frame,
            start_date=request.start_date,
            end_date=request.end_date,
        )
        items, total, count, has_more, next_offset = _paginate_latest(
            records, request.limit, request.offset
        )
        return FundamentalUsReportResponse(
            stock=request.stock,
            symbol=request.symbol,
            indicator=request.indicator,
            items=items,
            columns=columns,
            count=count,
            total=total,
            limit=request.limit,
            offset=request.offset,
            has_more=has_more,
            next_offset=next_offset,
            start_date=request.start_date,
            end_date=request.end_date,
        )

    def fundamental_us_indicators(
        self, request: FundamentalUsIndicatorsRequest
    ) -> FundamentalUsIndicatorsResponse:
        frame = self._client.fetch_us_financial_indicators(
            request.symbol,
            request.indicator,
        )
        columns, records = _build_table_records(
            frame,
            start_date=request.start_date,
            end_date=request.end_date,
        )
        items, total, count, has_more, next_offset = _paginate_latest(
            records, request.limit, request.offset
        )
        return FundamentalUsIndicatorsResponse(
            symbol=request.symbol,
            indicator=request.indicator,
            items=items,
            columns=columns,
            count=count,
            total=total,
            limit=request.limit,
            offset=request.offset,
            has_more=has_more,
            next_offset=next_offset,
            start_date=request.start_date,
            end_date=request.end_date,
        )
