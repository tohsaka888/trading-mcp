from __future__ import annotations

from models.mcp_tools import FundFlowSectorRankEmResponse, FundFlowSectorSummaryEmResponse
from utils.mcp_formatting.common import format_table_response


def format_fund_flow_sector_rank_em_response(
    response: FundFlowSectorRankEmResponse,
) -> str:
    return format_table_response(
        "trading_fund_flow_sector_rank_em",
        response,
        metadata=[
            f"Indicator: `{response.indicator}`",
            f"Sector type: `{response.sector_type}`",
            f"Sort by: `{response.sort_by}`",
        ],
    )


def format_fund_flow_sector_summary_em_response(
    response: FundFlowSectorSummaryEmResponse,
) -> str:
    return format_table_response(
        "trading_fund_flow_sector_summary_em",
        response,
        metadata=[
            f"Symbol: `{response.symbol}`",
            f"Indicator: `{response.indicator}`",
        ],
    )
