from __future__ import annotations

from pydantic import Field, field_validator

from models.mcp_tools.common import DateRangeRequest, FundamentalResponse

_CN_FINANCIAL_INDICATORS = {"按报告期", "按单季度"}
_US_FINANCIAL_REPORT_SYMBOLS = {"资产负债表", "综合损益表", "现金流量表"}
_US_FINANCIAL_INDICATORS = {"年报", "单季报", "累计季报"}


class FundamentalCnIndicatorsRequest(DateRangeRequest):
    symbol: str = Field(..., min_length=1, description="A-share stock symbol")
    indicator: str = Field(
        "按报告期",
        description="Indicator mode: 按报告期 or 按单季度",
    )
    limit: int = Field(30, ge=1, description="Number of recent records to return")
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
    limit: int = Field(30, ge=1, description="Number of recent records to return")
    offset: int = Field(0, ge=0, description="Number of most recent records to skip")

    @field_validator("symbol")
    @classmethod
    def _validate_symbol(cls, value: str) -> str:
        if value not in _US_FINANCIAL_REPORT_SYMBOLS:
            raise ValueError(
                "symbol must be one of: 资产负债表, 综合损益表, 现金流量表"
            )
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
    limit: int = Field(30, ge=1, description="Number of recent records to return")
    offset: int = Field(0, ge=0, description="Number of most recent records to skip")

    @field_validator("indicator")
    @classmethod
    def _validate_indicator(cls, value: str) -> str:
        if value not in _US_FINANCIAL_INDICATORS:
            raise ValueError("indicator must be one of: 年报, 单季报, 累计季报")
        return value


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
