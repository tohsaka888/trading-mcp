from __future__ import annotations

from pydantic import Field, field_validator

from models.mcp_tools.common import DateRangeRequest, DatedTableResponse, TableRequest, TableResponse

_INDUSTRY_HIST_PERIODS = {"日k", "周k", "月k"}
_INDUSTRY_HIST_ADJUSTS = {"", "qfq", "hfq"}
_INDUSTRY_HIST_MIN_PERIODS = {"1", "5", "15", "30", "60"}


class IndustryIndexThsRequest(DateRangeRequest, TableRequest):
    symbol: str = Field(..., min_length=1, description="THS industry board symbol")


class IndustryHistEmRequest(DateRangeRequest, TableRequest):
    symbol: str = Field(..., min_length=1, description="EM industry board symbol")
    period: str = Field("日k", description="K-line period: 日k, 周k, 月k")
    adjust: str = Field("", description="Adjust type: '', qfq, hfq")

    @field_validator("period")
    @classmethod
    def _validate_industry_hist_period(cls, value: str) -> str:
        if value not in _INDUSTRY_HIST_PERIODS:
            raise ValueError("period must be one of: 日k, 周k, 月k")
        return value

    @field_validator("adjust")
    @classmethod
    def _validate_industry_hist_adjust(cls, value: str) -> str:
        if value not in _INDUSTRY_HIST_ADJUSTS:
            raise ValueError("adjust must be one of: '', qfq, hfq")
        return value


class IndustryHistMinEmRequest(TableRequest):
    symbol: str = Field(..., min_length=1, description="EM industry board symbol")
    period: str = Field("5", description="Minute period: 1, 5, 15, 30, 60")

    @field_validator("period")
    @classmethod
    def _validate_industry_hist_min_period(cls, value: str) -> str:
        if value not in _INDUSTRY_HIST_MIN_PERIODS:
            raise ValueError("period must be one of: 1, 5, 15, 30, 60")
        return value


class IndustryIndexThsResponse(DatedTableResponse):
    symbol: str = Field(..., min_length=1, description="THS industry board symbol")


class IndustryHistEmResponse(DatedTableResponse):
    symbol: str = Field(..., min_length=1, description="EM industry board symbol")
    period: str = Field(..., description="K-line period")
    adjust: str = Field(..., description="Adjust type")


class IndustryHistMinEmResponse(TableResponse):
    symbol: str = Field(..., min_length=1, description="EM industry board symbol")
    period: str = Field(..., description="Minute period")
