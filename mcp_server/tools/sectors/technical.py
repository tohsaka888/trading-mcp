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
    IndustryHistEmRequest,
    IndustryHistEmResponse,
    IndustryHistMinEmRequest,
    IndustryHistMinEmResponse,
    IndustryIndexThsRequest,
    IndustryIndexThsResponse,
)
from utils.mcp_formatting import (
    format_industry_hist_em_response,
    format_industry_hist_min_em_response,
    format_industry_index_ths_response,
)


def register_tools(mcp: FastMCP, context: ServerContext) -> list[ToolMeta]:
    service = context.service

    @mcp.tool(
        description=(
            "Return THS industry board index records with pagination metadata. "
            "Supports start_date and end_date in YYYY-MM-DD or YYYYMMDD format."
        ),
        annotations=context.annotations,
    )
    def trading_industry_index_ths(
        symbol: Annotated[
            str,
            Field(..., min_length=1, description="THS industry board symbol"),
        ],
        limit: Annotated[
            int, Field(30, ge=1, description="Number of recent records to return")
        ] = 30,
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
    ) -> Annotated[CallToolResult, IndustryIndexThsResponse]:
        request = IndustryIndexThsRequest(
            symbol=symbol,
            limit=limit,
            offset=offset,
            start_date=start_date,
            end_date=end_date,
        )
        try:
            response = service.industry_index_ths(request)
        except MarketDataError as exc:
            return structured_error_result(
                f"Error: {exc}. Check the board symbol, date range, and upstream connectivity.",
                empty_table_response(
                    IndustryIndexThsResponse,
                    limit=limit,
                    offset=offset,
                    start_date=start_date,
                    end_date=end_date,
                    symbol=symbol,
                ),
            )
        return success_result(
            response, response_format, format_industry_index_ths_response
        )

    @mcp.tool(
        description=(
            "Return EM industry board historical K-line records with pagination metadata. "
            "period enum: '日k', '周k', '月k'; adjust enum: 'none', 'qfq', 'hfq'. "
            "'none' means no price adjustment."
        ),
        annotations=context.annotations,
    )
    def trading_industry_hist_em(
        symbol: Annotated[
            str,
            Field(..., min_length=1, description="EM industry board symbol"),
        ],
        period: Annotated[
            Literal["日k", "周k", "月k"],
            Field("日k", description="K-line period"),
        ] = "日k",
        adjust: Annotated[
            Literal["none", "qfq", "hfq"],
            Field("none", description="Adjust type; use 'none' for no adjustment"),
        ] = "none",
        limit: Annotated[
            int, Field(30, ge=1, description="Number of recent records to return")
        ] = 30,
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
    ) -> Annotated[CallToolResult, IndustryHistEmResponse]:
        request = IndustryHistEmRequest(
            symbol=symbol,
            period=period,
            adjust="" if adjust == "none" else adjust,
            limit=limit,
            offset=offset,
            start_date=start_date,
            end_date=end_date,
        )
        try:
            response = service.industry_hist_em(request)
        except MarketDataError as exc:
            return structured_error_result(
                f"Error: {exc}. Check the board symbol, date range, adjust option, and upstream connectivity.",
                empty_table_response(
                    IndustryHistEmResponse,
                    limit=limit,
                    offset=offset,
                    start_date=start_date,
                    end_date=end_date,
                    symbol=symbol,
                    period=period,
                    adjust="" if adjust == "none" else adjust,
                ),
            )
        return success_result(
            response, response_format, format_industry_hist_em_response
        )

    @mcp.tool(
        description=(
            "Return EM industry board intraday historical records with pagination metadata. "
            "period enum: '1', '5', '15', '30', '60'."
        ),
        annotations=context.annotations,
    )
    def trading_industry_hist_min_em(
        symbol: Annotated[
            str,
            Field(..., min_length=1, description="EM industry board symbol"),
        ],
        period: Annotated[
            Literal["1", "5", "15", "30", "60"],
            Field("5", description="Minute period"),
        ] = "5",
        limit: Annotated[
            int, Field(30, ge=1, description="Number of recent records to return")
        ] = 30,
        offset: Annotated[
            int, Field(0, ge=0, description="Number of most recent records to skip")
        ] = 0,
        response_format: Annotated[
            ResponseFormat,
            Field("markdown", description="Response format"),
        ] = "markdown",
    ) -> Annotated[CallToolResult, IndustryHistMinEmResponse]:
        request = IndustryHistMinEmRequest(
            symbol=symbol,
            period=period,
            limit=limit,
            offset=offset,
        )
        try:
            response = service.industry_hist_min_em(request)
        except MarketDataError as exc:
            return structured_error_result(
                f"Error: {exc}. Check the board symbol, period, and upstream connectivity.",
                empty_table_response(
                    IndustryHistMinEmResponse,
                    limit=limit,
                    offset=offset,
                    symbol=symbol,
                    period=period,
                ),
            )
        return success_result(
            response, response_format, format_industry_hist_min_em_response
        )

    return [
        ToolMeta(
            name="trading_industry_index_ths",
            signature=(
                "trading_industry_index_ths(symbol, limit=30, offset=0, "
                "start_date=None, end_date=None, response_format='markdown'): "
                "return THS industry index records."
            ),
            resource_description="THS industry board index records",
            resource_fields=["columns", "items", "symbol", "start_date", "end_date"],
        ),
        ToolMeta(
            name="trading_industry_hist_em",
            signature=(
                "trading_industry_hist_em(symbol, period='日k', adjust='none', "
                "limit=30, offset=0, start_date=None, end_date=None, "
                "response_format='markdown'): return EM industry historical K-line "
                "records."
            ),
            resource_description="EM industry board historical K-line records",
            resource_fields=[
                "columns",
                "items",
                "symbol",
                "period",
                "adjust",
                "start_date",
                "end_date",
            ],
        ),
        ToolMeta(
            name="trading_industry_hist_min_em",
            signature=(
                "trading_industry_hist_min_em(symbol, period='5', limit=30, "
                "offset=0, response_format='markdown'): return EM industry intraday "
                "history records."
            ),
            resource_description="EM industry board intraday historical records",
            resource_fields=["columns", "items", "symbol", "period"],
        ),
    ]
