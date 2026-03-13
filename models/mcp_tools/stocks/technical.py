from __future__ import annotations

from pydantic import Field, ValidationInfo, field_validator

from models.mcp_tools.common import (
    KlineBar,
    MacdPoint,
    MaPoint,
    RsiPoint,
    ToolRequest,
    ToolResponse,
    VolumePoint,
)


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


class VolumeRequest(ToolRequest):
    pass


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
