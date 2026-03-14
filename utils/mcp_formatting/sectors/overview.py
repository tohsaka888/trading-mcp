from __future__ import annotations

from models.mcp_tools import (
    BoardChangeEmResponse,
    IndustryConsEmResponse,
    IndustryNameEmResponse,
    IndustrySpotEmResponse,
    IndustrySummaryThsResponse,
)
from utils.mcp_formatting.common import format_table_response


def format_industry_summary_ths_response(response: IndustrySummaryThsResponse) -> str:
    return format_table_response("trading_industry_summary_ths", response)


def format_industry_name_em_response(response: IndustryNameEmResponse) -> str:
    return format_table_response("trading_industry_name_em", response)


def format_board_change_em_response(response: BoardChangeEmResponse) -> str:
    return format_table_response("trading_board_change_em", response)


def format_industry_spot_em_response(response: IndustrySpotEmResponse) -> str:
    return format_table_response(
        "trading_industry_spot_em",
        response,
        metadata=[f"Symbol: `{response.symbol}`"],
    )


def format_industry_cons_em_response(response: IndustryConsEmResponse) -> str:
    return format_table_response(
        "trading_industry_cons_em",
        response,
        metadata=[f"Symbol: `{response.symbol}`"],
    )
