from __future__ import annotations

from datetime import date, datetime, timezone
import re
from typing import Any

from pydantic import (
    BaseModel,
    Field,
    ValidationInfo,
    field_serializer,
    field_validator,
    model_validator,
)


_DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_COMPACT_DATE_PATTERN = re.compile(r"^\d{8}$")
_PERIOD_TYPES = {"1d", "1w", "1m"}
_AGGREGATED_PERIOD_TYPES = {"1w", "1m"}
_CN_FINANCIAL_INDICATORS = {"按报告期", "按单季度"}
_US_FINANCIAL_REPORT_SYMBOLS = {"资产负债表", "综合损益表", "现金流量表"}
_US_FINANCIAL_INDICATORS = {"年报", "单季报", "累计季报"}


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
    limit: int = Field(..., ge=1, description="Number of recent data points to return")
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


class KlineRequest(ToolRequest):
    limit: int = Field(30, ge=1, description="Number of recent data points to return")


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


class VolumeRequest(ToolRequest):
    pass


class FundamentalCnIndicatorsRequest(DateRangeRequest):
    symbol: str = Field(..., min_length=1, description="A-share stock symbol")
    indicator: str = Field(
        "按报告期",
        description="Indicator mode: 按报告期 or 按单季度",
    )
    limit: int = Field(200, ge=1, description="Number of recent records to return")
    offset: int = Field(0, ge=0, description="Number of most recent records to skip")

    @field_validator("indicator")
    @classmethod
    def _validate_indicator(cls, value: str) -> str:
        if value not in _CN_FINANCIAL_INDICATORS:
            raise ValueError("indicator must be one of: 按报告期, 按单季度")
        return value


class FundamentalUsReportRequest(DateRangeRequest):
    stock: str = Field(..., min_length=1, description="US stock symbol")
    symbol: str = Field(
        "资产负债表",
        description="Report type: 资产负债表, 综合损益表, 现金流量表",
    )
    indicator: str = Field(
        "年报",
        description="Indicator type: 年报, 单季报, 累计季报",
    )
    limit: int = Field(200, ge=1, description="Number of recent records to return")
    offset: int = Field(0, ge=0, description="Number of most recent records to skip")

    @field_validator("symbol")
    @classmethod
    def _validate_symbol(cls, value: str) -> str:
        if value not in _US_FINANCIAL_REPORT_SYMBOLS:
            raise ValueError("symbol must be one of: 资产负债表, 综合损益表, 现金流量表")
        return value

    @field_validator("indicator")
    @classmethod
    def _validate_indicator(cls, value: str) -> str:
        if value not in _US_FINANCIAL_INDICATORS:
            raise ValueError("indicator must be one of: 年报, 单季报, 累计季报")
        return value


class FundamentalUsIndicatorsRequest(DateRangeRequest):
    symbol: str = Field(..., min_length=1, description="US stock symbol")
    indicator: str = Field(
        "年报",
        description="Indicator type: 年报, 单季报, 累计季报",
    )
    limit: int = Field(200, ge=1, description="Number of recent records to return")
    offset: int = Field(0, ge=0, description="Number of most recent records to skip")

    @field_validator("indicator")
    @classmethod
    def _validate_indicator(cls, value: str) -> str:
        if value not in _US_FINANCIAL_INDICATORS:
            raise ValueError("indicator must be one of: 年报, 单季报, 累计季报")
        return value


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


class VolumeResponse(ToolResponse):
    items: list[VolumePoint] = Field(default_factory=list)
    volume_unit: str = Field(..., description="Volume unit: lot or share")
    amount_unit: str | None = Field(None, description="Amount unit: CNY, USD or null")
    turnover_rate_unit: str = Field(..., description="Turnover rate unit: percent")


class FundamentalResponse(BaseModel):
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


class FundamentalCnIndicatorsResponse(FundamentalResponse):
    symbol: str = Field(..., min_length=1, description="A-share stock symbol")
    indicator: str = Field(..., description="Indicator mode")


class FundamentalUsReportResponse(FundamentalResponse):
    stock: str = Field(..., min_length=1, description="US stock symbol")
    symbol: str = Field(..., description="Report type")
    indicator: str = Field(..., description="Indicator type")


class FundamentalUsIndicatorsResponse(FundamentalResponse):
    symbol: str = Field(..., min_length=1, description="US stock symbol")
    indicator: str = Field(..., description="Indicator type")
