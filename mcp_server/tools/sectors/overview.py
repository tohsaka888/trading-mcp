from __future__ import annotations

from typing import Annotated

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
    BoardChangeEmRequest,
    BoardChangeEmResponse,
    IndustryConsEmRequest,
    IndustryConsEmResponse,
    IndustryNameEmRequest,
    IndustryNameEmResponse,
    IndustrySpotEmRequest,
    IndustrySpotEmResponse,
    IndustrySummaryThsRequest,
    IndustrySummaryThsResponse,
)
from utils.mcp_formatting import (
    format_board_change_em_response,
    format_industry_cons_em_response,
    format_industry_name_em_response,
    format_industry_spot_em_response,
    format_industry_summary_ths_response,
)


def register_tools(mcp: FastMCP, context: ServerContext) -> list[ToolMeta]:
    service = context.service

    @mcp.tool(
        description="Return THS industry board summary records with pagination metadata.",
        annotations=context.annotations,
    )
    def trading_industry_summary_ths(
        limit: Annotated[
            int, Field(200, ge=1, description="Number of recent records to return")
        ] = 200,
        offset: Annotated[
            int, Field(0, ge=0, description="Number of most recent records to skip")
        ] = 0,
        response_format: Annotated[
            ResponseFormat,
            Field("markdown", description="Response format"),
        ] = "markdown",
    ) -> Annotated[CallToolResult, IndustrySummaryThsResponse]:
        request = IndustrySummaryThsRequest(limit=limit, offset=offset)
        try:
            response = service.industry_summary_ths(request)
        except MarketDataError as exc:
            return structured_error_result(
                f"Error: {exc}. Check the THS industry summary source and upstream connectivity.",
                empty_table_response(
                    IndustrySummaryThsResponse,
                    limit=limit,
                    offset=offset,
                ),
            )
        return success_result(
            response, response_format, format_industry_summary_ths_response
        )

    @mcp.tool(
        description="Return EM industry board name records with pagination metadata.",
        annotations=context.annotations,
    )
    def trading_industry_name_em(
        limit: Annotated[
            int, Field(200, ge=1, description="Number of recent records to return")
        ] = 200,
        offset: Annotated[
            int, Field(0, ge=0, description="Number of most recent records to skip")
        ] = 0,
        response_format: Annotated[
            ResponseFormat,
            Field("markdown", description="Response format"),
        ] = "markdown",
    ) -> Annotated[CallToolResult, IndustryNameEmResponse]:
        request = IndustryNameEmRequest(limit=limit, offset=offset)
        try:
            response = service.industry_name_em(request)
        except MarketDataError as exc:
            return structured_error_result(
                f"Error: {exc}. Check the EM industry board source and upstream connectivity.",
                empty_table_response(
                    IndustryNameEmResponse,
                    limit=limit,
                    offset=offset,
                ),
            )
        return success_result(
            response, response_format, format_industry_name_em_response
        )

    @mcp.tool(
        description="Return Eastmoney board change detail records with pagination metadata.",
        annotations=context.annotations,
    )
    def trading_board_change_em(
        limit: Annotated[
            int, Field(200, ge=1, description="Number of recent records to return")
        ] = 200,
        offset: Annotated[
            int, Field(0, ge=0, description="Number of most recent records to skip")
        ] = 0,
        response_format: Annotated[
            ResponseFormat,
            Field("markdown", description="Response format"),
        ] = "markdown",
    ) -> Annotated[CallToolResult, BoardChangeEmResponse]:
        request = BoardChangeEmRequest(limit=limit, offset=offset)
        try:
            response = service.board_change_em(request)
        except MarketDataError as exc:
            return structured_error_result(
                f"Error: {exc}. Check the Eastmoney board change source and upstream connectivity.",
                empty_table_response(
                    BoardChangeEmResponse,
                    limit=limit,
                    offset=offset,
                ),
            )
        return success_result(
            response, response_format, format_board_change_em_response
        )

    @mcp.tool(
        description="Return EM industry board spot records with pagination metadata.",
        annotations=context.annotations,
    )
    def trading_industry_spot_em(
        symbol: Annotated[
            str,
            Field(..., min_length=1, description="EM industry board symbol"),
        ],
        limit: Annotated[
            int, Field(200, ge=1, description="Number of recent records to return")
        ] = 200,
        offset: Annotated[
            int, Field(0, ge=0, description="Number of most recent records to skip")
        ] = 0,
        response_format: Annotated[
            ResponseFormat,
            Field("markdown", description="Response format"),
        ] = "markdown",
    ) -> Annotated[CallToolResult, IndustrySpotEmResponse]:
        request = IndustrySpotEmRequest(symbol=symbol, limit=limit, offset=offset)
        try:
            response = service.industry_spot_em(request)
        except MarketDataError as exc:
            return structured_error_result(
                f"Error: {exc}. Check the board symbol and upstream connectivity.",
                empty_table_response(
                    IndustrySpotEmResponse,
                    limit=limit,
                    offset=offset,
                    symbol=symbol,
                ),
            )
        return success_result(
            response, response_format, format_industry_spot_em_response
        )

    @mcp.tool(
        description="Return EM industry board constituent records with pagination metadata.",
        annotations=context.annotations,
    )
    def trading_industry_cons_em(
        symbol: Annotated[
            str,
            Field(..., min_length=1, description="EM industry board symbol"),
        ],
        limit: Annotated[
            int, Field(200, ge=1, description="Number of recent records to return")
        ] = 200,
        offset: Annotated[
            int, Field(0, ge=0, description="Number of most recent records to skip")
        ] = 0,
        response_format: Annotated[
            ResponseFormat,
            Field("markdown", description="Response format"),
        ] = "markdown",
    ) -> Annotated[CallToolResult, IndustryConsEmResponse]:
        request = IndustryConsEmRequest(symbol=symbol, limit=limit, offset=offset)
        try:
            response = service.industry_cons_em(request)
        except MarketDataError as exc:
            return structured_error_result(
                f"Error: {exc}. Check the board symbol and upstream connectivity.",
                empty_table_response(
                    IndustryConsEmResponse,
                    limit=limit,
                    offset=offset,
                    symbol=symbol,
                ),
            )
        return success_result(
            response, response_format, format_industry_cons_em_response
        )

    return [
        ToolMeta(
            name="trading_industry_summary_ths",
            signature=(
                "trading_industry_summary_ths(limit=200, offset=0, "
                "response_format='markdown'): return THS industry board summary records."
            ),
            resource_description="THS industry board summary records",
            resource_fields=["columns", "items"],
        ),
        ToolMeta(
            name="trading_industry_name_em",
            signature=(
                "trading_industry_name_em(limit=200, offset=0, "
                "response_format='markdown'): return EM industry board name records."
            ),
            resource_description="EM industry board name records",
            resource_fields=["columns", "items"],
        ),
        ToolMeta(
            name="trading_board_change_em",
            signature=(
                "trading_board_change_em(limit=200, offset=0, "
                "response_format='markdown'): return Eastmoney board change detail "
                "records."
            ),
            resource_description="Eastmoney board change detail records",
            resource_fields=["columns", "items"],
        ),
        ToolMeta(
            name="trading_industry_spot_em",
            signature=(
                "trading_industry_spot_em(symbol, limit=200, offset=0, "
                "response_format='markdown'): return EM industry board spot records."
            ),
            resource_description="EM industry board spot records",
            resource_fields=["columns", "items", "symbol"],
        ),
        ToolMeta(
            name="trading_industry_cons_em",
            signature=(
                "trading_industry_cons_em(symbol, limit=200, offset=0, "
                "response_format='markdown'): return EM industry board constituent "
                "records."
            ),
            resource_description="EM industry board constituent records",
            resource_fields=["columns", "items", "symbol"],
        ),
    ]
