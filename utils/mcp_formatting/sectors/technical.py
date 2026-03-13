from __future__ import annotations

from models.mcp_tools import (
    IndustryHistEmResponse,
    IndustryHistMinEmResponse,
    IndustryIndexThsResponse,
)
from utils.mcp_formatting.common import format_table_response


def format_industry_index_ths_response(response: IndustryIndexThsResponse) -> str:
    return format_table_response(
        "trading_industry_index_ths",
        response,
        metadata=[f"Symbol: `{response.symbol}`"],
    )


def format_industry_hist_em_response(response: IndustryHistEmResponse) -> str:
    return format_table_response(
        "trading_industry_hist_em",
        response,
        metadata=[
            f"Symbol: `{response.symbol}`",
            f"Period: `{response.period}` | Adjust: `{response.adjust or 'none'}`",
        ],
    )


def format_industry_hist_min_em_response(response: IndustryHistMinEmResponse) -> str:
    return format_table_response(
        "trading_industry_hist_min_em",
        response,
        metadata=[
            f"Symbol: `{response.symbol}`",
            f"Period: `{response.period}`",
        ],
    )
