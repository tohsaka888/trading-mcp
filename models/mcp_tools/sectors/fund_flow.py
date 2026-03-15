from __future__ import annotations

from pydantic import Field, field_validator

from models.mcp_tools.common import TableRequest, TableResponse

_FUND_FLOW_SECTOR_RANK_INDICATORS = {"今日", "5日", "10日"}
_FUND_FLOW_SECTOR_TYPES = {"行业资金流", "概念资金流", "地域资金流"}
_FUND_FLOW_SECTOR_SORT_OPTIONS = {"涨跌幅", "主力净流入"}


class FundFlowSectorRankEmRequest(TableRequest):
    indicator: str = Field(
        "今日",
        description="Ranking window: 今日, 5日, 10日",
    )
    sector_type: str = Field(
        "行业资金流",
        description="Sector type: 行业资金流, 概念资金流, 地域资金流",
    )
    sort_by: str = Field(
        "涨跌幅",
        description="Sort field: 涨跌幅, 主力净流入",
    )

    @field_validator("indicator")
    @classmethod
    def _validate_indicator(cls, value: str) -> str:
        if value not in _FUND_FLOW_SECTOR_RANK_INDICATORS:
            raise ValueError("indicator must be one of: 今日, 5日, 10日")
        return value

    @field_validator("sector_type")
    @classmethod
    def _validate_sector_type(cls, value: str) -> str:
        if value not in _FUND_FLOW_SECTOR_TYPES:
            raise ValueError(
                "sector_type must be one of: 行业资金流, 概念资金流, 地域资金流"
            )
        return value

    @field_validator("sort_by")
    @classmethod
    def _validate_sort_by(cls, value: str) -> str:
        if value not in _FUND_FLOW_SECTOR_SORT_OPTIONS:
            raise ValueError("sort_by must be one of: 涨跌幅, 主力净流入")
        return value


class FundFlowSectorSummaryEmRequest(TableRequest):
    symbol: str = Field(..., min_length=1, description="Eastmoney board name")
    indicator: str = Field(
        "今日",
        description="Ranking window: 今日, 5日, 10日",
    )

    @field_validator("indicator")
    @classmethod
    def _validate_indicator(cls, value: str) -> str:
        if value not in _FUND_FLOW_SECTOR_RANK_INDICATORS:
            raise ValueError("indicator must be one of: 今日, 5日, 10日")
        return value


class FundFlowSectorRankEmResponse(TableResponse):
    indicator: str = Field(..., description="Ranking window")
    sector_type: str = Field(..., description="Sector type")
    sort_by: str = Field(..., description="Applied sort field")


class FundFlowSectorSummaryEmResponse(TableResponse):
    symbol: str = Field(..., min_length=1, description="Eastmoney board name")
    indicator: str = Field(..., description="Ranking window")
