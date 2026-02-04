from __future__ import annotations

from datetime import datetime, timezone
import re

from pydantic import BaseModel, Field, ValidationInfo, field_serializer, field_validator


_DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_COMPACT_DATE_PATTERN = re.compile(r"^\d{8}$")
_PERIOD_TYPES = {"1d", "1w", "1m"}


class ToolRequest(BaseModel):
    symbol: str = Field(..., min_length=1, description="Market symbol identifier")
    limit: int = Field(..., ge=1, description="Number of recent data points to return")
    offset: int = Field(0, ge=0, description="Number of most recent points to skip")
    period_type: str = Field(
        "1d",
        description="Data interval: 1d, 1w, 1m",
    )
    start_date: str | None = Field(
        None,
        description="Start date (YYYY-MM-DD or YYYYMMDD)",
    )
    end_date: str | None = Field(
        None,
        description="End date (YYYY-MM-DD or YYYYMMDD)",
    )

    @field_validator("start_date", "end_date")
    @classmethod
    def _validate_date(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        if not cleaned:
            return None
        if _DATE_PATTERN.match(cleaned) or _COMPACT_DATE_PATTERN.match(cleaned):
            return cleaned
        raise ValueError("Date must be in YYYY-MM-DD or YYYYMMDD format")

    @field_validator("period_type")
    @classmethod
    def _validate_period_type(cls, value: str) -> str:
        normalized = value.lower()
        if normalized not in _PERIOD_TYPES:
            raise ValueError("period_type must be one of: 1d, 1w, 1m")
        return normalized


class KlineRequest(ToolRequest):
    pass


class RsiRequest(ToolRequest):
    period: int = Field(14, ge=1, description="RSI lookback period")


class MaRequest(ToolRequest):
    period: int = Field(20, ge=1, description="MA lookback period")
    ma_type: str = Field("sma", description="Moving average type: sma or ema")

    @field_validator("ma_type")
    @classmethod
    def _validate_ma_type(cls, value: str) -> str:
        normalized = value.lower()
        if normalized not in {"sma", "ema"}:
            raise ValueError("ma_type must be either 'sma' or 'ema'")
        return normalized


class MacdRequest(ToolRequest):
    fast_period: int = Field(12, ge=1, description="MACD fast EMA period")
    slow_period: int = Field(26, ge=1, description="MACD slow EMA period")
    signal_period: int = Field(9, ge=1, description="MACD signal period")

    @field_validator("slow_period")
    @classmethod
    def _validate_slow_period(cls, value: int, info: ValidationInfo) -> int:
        fast = info.data.get("fast_period")
        if fast is not None and value <= fast:
            raise ValueError("slow_period must be greater than fast_period")
        return value


class KlineBar(BaseModel):
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float | None = None

    @field_serializer("timestamp", when_used="json")
    def _serialize_timestamp(self, value: datetime) -> str:
        if value.tzinfo is None or value.tzinfo.utcoffset(value) is None:
            return value.replace(tzinfo=timezone.utc).isoformat()
        return value.isoformat()


class RsiPoint(BaseModel):
    timestamp: datetime
    rsi: float | None = None

    @field_serializer("timestamp", when_used="json")
    def _serialize_timestamp(self, value: datetime) -> str:
        if value.tzinfo is None or value.tzinfo.utcoffset(value) is None:
            return value.replace(tzinfo=timezone.utc).isoformat()
        return value.isoformat()


class MaPoint(BaseModel):
    timestamp: datetime
    ma: float | None = None

    @field_serializer("timestamp", when_used="json")
    def _serialize_timestamp(self, value: datetime) -> str:
        if value.tzinfo is None or value.tzinfo.utcoffset(value) is None:
            return value.replace(tzinfo=timezone.utc).isoformat()
        return value.isoformat()


class MacdPoint(BaseModel):
    timestamp: datetime
    macd: float | None = None
    signal: float | None = None
    histogram: float | None = None

    @field_serializer("timestamp", when_used="json")
    def _serialize_timestamp(self, value: datetime) -> str:
        if value.tzinfo is None or value.tzinfo.utcoffset(value) is None:
            return value.replace(tzinfo=timezone.utc).isoformat()
        return value.isoformat()


class ToolResponse(BaseModel):
    symbol: str = Field(..., min_length=1, description="Market symbol identifier")
    count: int = Field(..., ge=0, description="Number of items in this response")
    total: int = Field(..., ge=0, description="Total items available before pagination")
    limit: int = Field(..., ge=1, description="Requested page size")
    offset: int = Field(..., ge=0, description="Number of most recent points skipped")
    has_more: bool = Field(..., description="Whether older data is available")
    next_offset: int | None = Field(None, ge=0, description="Offset for the next page")
    period_type: str = Field(..., description="Applied data interval: 1d, 1w, 1m")
    start_date: str | None = Field(None, description="Applied start date filter")
    end_date: str | None = Field(None, description="Applied end date filter")

    model_config = {"extra": "ignore"}


class KlineResponse(ToolResponse):
    items: list[KlineBar] = Field(default_factory=list)


class RsiResponse(ToolResponse):
    items: list[RsiPoint] = Field(default_factory=list)


class MaResponse(ToolResponse):
    items: list[MaPoint] = Field(default_factory=list)


class MacdResponse(ToolResponse):
    items: list[MacdPoint] = Field(default_factory=list)
