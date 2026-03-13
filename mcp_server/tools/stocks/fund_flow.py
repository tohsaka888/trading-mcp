from __future__ import annotations

from typing import Annotated, Literal

from data.client import MarketDataError
from mcp.server.fastmcp import FastMCP
from mcp.types import CallToolResult
from pydantic import Field

from mcp_server.context import ServerContext
from mcp_server.metadata import ToolMeta
from mcp_server.results import error_result, success_result
from mcp_server.tools.common import ResponseFormat
from models.mcp_tools import (
    FundFlowIndividualEmRequest,
    FundFlowIndividualEmResponse,
    FundFlowIndividualRankEmRequest,
    FundFlowIndividualRankEmResponse,
)
from utils.mcp_formatting import (
    format_fund_flow_individual_em_response,
    format_fund_flow_individual_rank_em_response,
)


def register_tools(mcp: FastMCP, context: ServerContext) -> list[ToolMeta]:
    service = context.service

    @mcp.tool(
        description=(
            "Return Eastmoney individual stock fund-flow records with pagination metadata. "
            "Supports start_date and end_date in YYYY-MM-DD or YYYYMMDD format."
        ),
        annotations=context.annotations,
    )
    def trading_fund_flow_individual_em(
        symbol: Annotated[
            str,
            Field(
                ...,
                min_length=1,
                description="A-share stock symbol (e.g. 000001, 600519.SH, 830799.BJ)",
            ),
        ],
        limit: Annotated[
            int, Field(200, ge=1, description="Number of recent records to return")
        ] = 200,
        offset: Annotated[
            int, Field(0, ge=0, description="Number of most recent records to skip")
        ] = 0,
        start_date: Annotated[
            str | None, Field(None, description="Start date (YYYY-MM-DD or YYYYMMDD)")
        ] = None,
        end_date: Annotated[
            str | None, Field(None, description="End date (YYYY-MM-DD or YYYYMMDD)")
        ] = None,
        response_format: Annotated[
            ResponseFormat,
            Field("markdown", description="Response format"),
        ] = "markdown",
    ) -> Annotated[CallToolResult, FundFlowIndividualEmResponse]:
        request = FundFlowIndividualEmRequest(
            symbol=symbol,
            limit=limit,
            offset=offset,
            start_date=start_date,
            end_date=end_date,
        )
        try:
            response = service.fund_flow_individual_em(request)
        except MarketDataError as exc:
            return error_result(
                f"Error: {exc}. Check the A-share symbol and date range."
            )
        return success_result(
            response, response_format, format_fund_flow_individual_em_response
        )

    @mcp.tool(
        description=(
            "Return Eastmoney individual stock fund-flow rankings with pagination metadata. "
            "indicator enum: '今日', '3日', '5日', '10日'."
        ),
        annotations=context.annotations,
    )
    def trading_fund_flow_individual_rank_em(
        indicator: Annotated[
            Literal["今日", "3日", "5日", "10日"],
            Field("5日", description="Ranking window"),
        ] = "5日",
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
    ) -> Annotated[CallToolResult, FundFlowIndividualRankEmResponse]:
        request = FundFlowIndividualRankEmRequest(
            indicator=indicator,
            limit=limit,
            offset=offset,
        )
        try:
            response = service.fund_flow_individual_rank_em(request)
        except MarketDataError as exc:
            return error_result(f"Error: {exc}. Check the indicator window.")
        return success_result(
            response, response_format, format_fund_flow_individual_rank_em_response
        )

    return [
        ToolMeta(
            name="trading_fund_flow_individual_em",
            signature=(
                "trading_fund_flow_individual_em(symbol, limit=200, offset=0, "
                "start_date=None, end_date=None, response_format='markdown'): "
                "return Eastmoney individual stock fund-flow records."
            ),
            resource_description="Eastmoney individual stock fund-flow records",
            resource_fields=["columns", "items", "symbol", "start_date", "end_date"],
        ),
        ToolMeta(
            name="trading_fund_flow_individual_rank_em",
            signature=(
                "trading_fund_flow_individual_rank_em(indicator='5日', limit=200, "
                "offset=0, response_format='markdown'): return Eastmoney individual "
                "stock fund-flow rankings."
            ),
            resource_description="Eastmoney individual stock fund-flow rankings",
            resource_fields=["columns", "items", "indicator"],
        ),
    ]
