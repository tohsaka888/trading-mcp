from __future__ import annotations

from typing import Annotated, Literal

from data.client import MarketDataError
from mcp.server.fastmcp import FastMCP
from mcp.types import CallToolResult
from pydantic import Field

from mcp_server.context import ServerContext
from mcp_server.metadata import ToolMeta
from mcp_server.results import (
    empty_table_response,
    structured_error_result,
    success_result,
)
from mcp_server.tools.common import ResponseFormat
from models.mcp_tools import (
    FundFlowSectorRankEmRequest,
    FundFlowSectorRankEmResponse,
    FundFlowSectorSummaryEmRequest,
    FundFlowSectorSummaryEmResponse,
)
from utils.mcp_formatting import (
    format_fund_flow_sector_rank_em_response,
    format_fund_flow_sector_summary_em_response,
)


def register_tools(mcp: FastMCP, context: ServerContext) -> list[ToolMeta]:
    service = context.service

    @mcp.tool(
        description=(
            "Return Eastmoney sector fund-flow rankings with pagination metadata. "
            "indicator enum: '今日', '5日', '10日'; "
            "sector_type enum: '行业资金流', '概念资金流', '地域资金流'."
        ),
        annotations=context.annotations,
    )
    def trading_fund_flow_sector_rank_em(
        indicator: Annotated[
            Literal["今日", "5日", "10日"],
            Field("今日", description="Ranking window"),
        ] = "今日",
        sector_type: Annotated[
            Literal["行业资金流", "概念资金流", "地域资金流"],
            Field("行业资金流", description="Sector ranking group"),
        ] = "行业资金流",
        limit: Annotated[
            int, Field(200, ge=1, description="Number of ranked records to return")
        ] = 200,
        offset: Annotated[
            int, Field(0, ge=0, description="Number of ranked records to skip")
        ] = 0,
        response_format: Annotated[
            ResponseFormat,
            Field("markdown", description="Response format"),
        ] = "markdown",
    ) -> Annotated[CallToolResult, FundFlowSectorRankEmResponse]:
        request = FundFlowSectorRankEmRequest(
            indicator=indicator,
            sector_type=sector_type,
            limit=limit,
            offset=offset,
        )
        try:
            response = service.fund_flow_sector_rank_em(request)
        except MarketDataError as exc:
            return structured_error_result(
                (
                    "Error: "
                    f"{exc}. Request failed for indicator={indicator}, "
                    f"sector_type={sector_type}. Check the indicator, sector_type, "
                    "and Eastmoney network connectivity."
                ),
                empty_table_response(
                    FundFlowSectorRankEmResponse,
                    limit=limit,
                    offset=offset,
                    indicator=indicator,
                    sector_type=sector_type,
                ),
            )
        return success_result(
            response, response_format, format_fund_flow_sector_rank_em_response
        )

    @mcp.tool(
        description=(
            "Return Eastmoney constituent stock fund-flow records for a board with pagination metadata. "
            "indicator enum: '今日', '5日', '10日'."
        ),
        annotations=context.annotations,
    )
    def trading_fund_flow_sector_summary_em(
        symbol: Annotated[
            str,
            Field(..., min_length=1, description="Eastmoney board name, e.g. 电源设备"),
        ],
        indicator: Annotated[
            Literal["今日", "5日", "10日"],
            Field("今日", description="Ranking window"),
        ] = "今日",
        limit: Annotated[
            int, Field(200, ge=1, description="Number of constituent records to return")
        ] = 200,
        offset: Annotated[
            int, Field(0, ge=0, description="Number of constituent records to skip")
        ] = 0,
        response_format: Annotated[
            ResponseFormat,
            Field("markdown", description="Response format"),
        ] = "markdown",
    ) -> Annotated[CallToolResult, FundFlowSectorSummaryEmResponse]:
        request = FundFlowSectorSummaryEmRequest(
            symbol=symbol,
            indicator=indicator,
            limit=limit,
            offset=offset,
        )
        try:
            response = service.fund_flow_sector_summary_em(request)
        except MarketDataError as exc:
            return structured_error_result(
                f"Error: {exc}. Check the board symbol, indicator, and Eastmoney network connectivity.",
                empty_table_response(
                    FundFlowSectorSummaryEmResponse,
                    limit=limit,
                    offset=offset,
                    symbol=symbol,
                    indicator=indicator,
                ),
            )
        return success_result(
            response, response_format, format_fund_flow_sector_summary_em_response
        )

    return [
        ToolMeta(
            name="trading_fund_flow_sector_rank_em",
            signature=(
                "trading_fund_flow_sector_rank_em(indicator='今日', "
                "sector_type='行业资金流', limit=200, offset=0, "
                "response_format='markdown'): return Eastmoney sector fund-flow "
                "rankings."
            ),
            resource_description="Eastmoney sector fund-flow rankings",
            resource_fields=["columns", "items", "indicator", "sector_type"],
        ),
        ToolMeta(
            name="trading_fund_flow_sector_summary_em",
            signature=(
                "trading_fund_flow_sector_summary_em(symbol, indicator='今日', "
                "limit=200, offset=0, response_format='markdown'): return Eastmoney "
                "board constituent fund-flow records."
            ),
            resource_description="Eastmoney board constituent fund-flow records",
            resource_fields=["columns", "items", "symbol", "indicator"],
        ),
    ]
