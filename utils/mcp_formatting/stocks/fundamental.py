from __future__ import annotations

from models.mcp_tools import (
    FundamentalCnIndicatorsResponse,
    FundamentalUsIndicatorsResponse,
    FundamentalUsReportResponse,
)
from utils.mcp_formatting.common import format_table_response


def format_fundamental_cn_indicators_response(
    response: FundamentalCnIndicatorsResponse,
) -> str:
    return format_table_response(
        "trading_fundamental_cn_indicators",
        response,
        metadata=[
            f"Symbol: `{response.symbol}`",
            f"Indicator: `{response.indicator}`",
        ],
    )


def format_fundamental_us_report_response(response: FundamentalUsReportResponse) -> str:
    return format_table_response(
        "trading_fundamental_us_report",
        response,
        metadata=[
            f"Stock: `{response.stock}`",
            f"Report: `{response.symbol}` | Indicator: `{response.indicator}`",
        ],
    )


def format_fundamental_us_indicators_response(
    response: FundamentalUsIndicatorsResponse,
) -> str:
    return format_table_response(
        "trading_fundamental_us_indicators",
        response,
        metadata=[
            f"Symbol: `{response.symbol}`",
            f"Indicator: `{response.indicator}`",
        ],
    )
