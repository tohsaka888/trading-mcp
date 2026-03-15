from __future__ import annotations

from datetime import date, datetime, timezone
import re
from typing import Any

from pydantic import (
    BaseModel,
    Field,
    field_serializer,
    field_validator,
    model_validator,
)

_DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_COMPACT_DATE_PATTERN = re.compile(r"^\d{8}$")
_PERIOD_TYPES = {"1d", "1w", "1m"}
_AGGREGATED_PERIOD_TYPES = {"1w", "1m"}


class DateRangeRequest(BaseModel):
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


class ToolRequest(DateRangeRequest):
    symbol: str = Field(..., min_length=1, description="Market symbol identifier")
    limit: int = Field(30, ge=1, description="Number of recent data points to return")
    offset: int = Field(0, ge=0, description="Number of most recent points to skip")
    period_type: str = Field(
        "1d",
        description="Data interval: 1d, 1w, 1m",
    )

    @field_validator("period_type")
    @classmethod
    def _validate_period_type(cls, value: str) -> str:
        normalized = value.lower()
        if normalized not in _PERIOD_TYPES:
            raise ValueError("period_type must be one of: 1d, 1w, 1m")
        return normalized

    @model_validator(mode="after")
    def _default_end_date_for_aggregated_periods(self) -> "ToolRequest":
        if self.period_type in _AGGREGATED_PERIOD_TYPES and self.end_date is None:
            self.end_date = date.today().isoformat()
        return self


class TableRequest(BaseModel):
    limit: int = Field(30, ge=1, description="Number of recent records to return")
    offset: int = Field(0, ge=0, description="Number of most recent records to skip")


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


class TableResponse(BaseModel):
    count: int = Field(..., ge=0, description="Number of items in this response")
    total: int = Field(..., ge=0, description="Total items available before pagination")
    limit: int = Field(..., ge=1, description="Requested page size")
    offset: int = Field(..., ge=0, description="Number of most recent records skipped")
    has_more: bool = Field(..., description="Whether older records are available")
    next_offset: int | None = Field(None, ge=0, description="Offset for the next page")
    start_date: str | None = Field(None, description="Applied start date filter")
    end_date: str | None = Field(None, description="Applied end date filter")
    columns: list[str] = Field(default_factory=list, description="Column names")
    items: list[dict[str, Any]] = Field(default_factory=list, description="Raw records")

    model_config = {"extra": "ignore"}


class DatedTableResponse(TableResponse):
    start_date: str | None = Field(None, description="Applied start date filter")
    end_date: str | None = Field(None, description="Applied end date filter")


class FundamentalResponse(TableResponse):
    start_date: str | None = Field(None, description="Applied start date filter")
    end_date: str | None = Field(None, description="Applied end date filter")


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


class VolumePoint(BaseModel):
    timestamp: datetime
    volume: float | None = None
    amount: float | None = None
    turnover_rate: float | None = None

    @field_serializer("timestamp", when_used="json")
    def _serialize_timestamp(self, value: datetime) -> str:
        if value.tzinfo is None or value.tzinfo.utcoffset(value) is None:
            return value.replace(tzinfo=timezone.utc).isoformat()
        return value.isoformat()
