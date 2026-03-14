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
from models.mcp_tools import InfoGlobalEmRequest, InfoGlobalEmResponse
from utils.mcp_formatting import format_info_global_em_response


def register_tools(mcp: FastMCP, context: ServerContext) -> list[ToolMeta]:
    service = context.service

    @mcp.tool(
        description="Return Eastmoney global finance news records with pagination metadata.",
        annotations=context.annotations,
    )
    def trading_info_global_em(
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
    ) -> Annotated[CallToolResult, InfoGlobalEmResponse]:
        request = InfoGlobalEmRequest(limit=limit, offset=offset)
        try:
            response = service.info_global_em(request)
        except MarketDataError as exc:
            return structured_error_result(
                f"Error: {exc}. Check the Eastmoney global news source and upstream connectivity.",
                empty_table_response(
                    InfoGlobalEmResponse,
                    limit=limit,
                    offset=offset,
                ),
            )
        return success_result(
            response, response_format, format_info_global_em_response
        )

    return [
        ToolMeta(
            name="trading_info_global_em",
            signature=(
                "trading_info_global_em(limit=200, offset=0, "
                "response_format='markdown'): return Eastmoney global finance news "
                "records."
            ),
            resource_description="Eastmoney global finance news records",
            resource_fields=["columns", "items"],
        )
    ]
