from __future__ import annotations

from pydantic import Field, field_validator

from models.mcp_tools.common import DateRangeRequest, DatedTableResponse, TableRequest, TableResponse

_FUND_FLOW_INDIVIDUAL_RANK_INDICATORS = {"今日", "3日", "5日", "10日"}


class FundFlowIndividualEmRequest(DateRangeRequest, TableRequest):
    symbol: str = Field(..., min_length=1, description="A-share stock symbol")


class FundFlowIndividualRankEmRequest(TableRequest):
    indicator: str = Field(
        "5日",
        description="Ranking window: 今日, 3日, 5日, 10日",
    )

    @field_validator("indicator")
    @classmethod
    def _validate_indicator(cls, value: str) -> str:
        if value not in _FUND_FLOW_INDIVIDUAL_RANK_INDICATORS:
            raise ValueError("indicator must be one of: 今日, 3日, 5日, 10日")
        return value


class FundFlowIndividualEmResponse(DatedTableResponse):
    symbol: str = Field(..., min_length=1, description="A-share stock symbol")


class FundFlowIndividualRankEmResponse(TableResponse):
    indicator: str = Field(..., description="Ranking window")
