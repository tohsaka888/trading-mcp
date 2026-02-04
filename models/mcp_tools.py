from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class ToolRequest(BaseModel):
    symbol: str = Field(..., min_length=1, description="Market symbol identifier")
    limit: int = Field(..., ge=1, description="Number of recent data points to return")


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
    def _validate_slow_period(cls, value: int, info) -> int:
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


class RsiPoint(BaseModel):
    timestamp: datetime
    rsi: float | None = None


class MaPoint(BaseModel):
    timestamp: datetime
    ma: float | None = None


class MacdPoint(BaseModel):
    timestamp: datetime
    macd: float | None = None
    signal: float | None = None
    histogram: float | None = None
