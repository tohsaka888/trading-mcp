from __future__ import annotations

from models.mcp_tools import FundFlowIndividualEmResponse, FundFlowIndividualRankEmResponse
from utils.mcp_formatting.common import format_table_response


def format_fund_flow_individual_em_response(
    response: FundFlowIndividualEmResponse,
) -> str:
    return format_table_response(
        "trading_fund_flow_individual_em",
        response,
        metadata=[f"Symbol: `{response.symbol}`"],
    )


def format_fund_flow_individual_rank_em_response(
    response: FundFlowIndividualRankEmResponse,
) -> str:
    return format_table_response(
        "trading_fund_flow_individual_rank_em",
        response,
        metadata=[f"Indicator: `{response.indicator}`"],
    )
