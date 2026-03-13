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
    FundamentalCnIndicatorsRequest,
    FundamentalCnIndicatorsResponse,
    FundamentalUsIndicatorsRequest,
    FundamentalUsIndicatorsResponse,
    FundamentalUsReportRequest,
    FundamentalUsReportResponse,
)
from utils.mcp_formatting import (
    format_fundamental_cn_indicators_response,
    format_fundamental_us_indicators_response,
    format_fundamental_us_report_response,
)


def register_tools(mcp: FastMCP, context: ServerContext) -> list[ToolMeta]:
    service = context.service

    @mcp.tool(
        description=(
            "Return A-share fundamental analysis indicators with pagination metadata. "
            "indicator enum: '按报告期' or '按单季度'."
        ),
        annotations=context.annotations,
    )
    def trading_fundamental_cn_indicators(
        symbol: Annotated[
            str,
            Field(
                ...,
                min_length=1,
                description="A-share symbol (e.g. 000001, 000001.SZ, 600519.SH)",
            ),
        ],
        indicator: Annotated[
            Literal["按报告期", "按单季度"],
            Field("按报告期", description="Indicator mode"),
        ] = "按报告期",
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
    ) -> Annotated[CallToolResult, FundamentalCnIndicatorsResponse]:
        request = FundamentalCnIndicatorsRequest(
            symbol=symbol,
            indicator=indicator,
            limit=limit,
            offset=offset,
            start_date=start_date,
            end_date=end_date,
        )
        try:
            response = service.fundamental_cn_indicators(request)
        except MarketDataError as exc:
            return error_result(f"Error: {exc}. Check the symbol and indicator.")
        return success_result(
            response, response_format, format_fundamental_cn_indicators_response
        )

    @mcp.tool(
        description=(
            "Return US financial statements (balance sheet, comprehensive income, "
            "cash flow) with pagination metadata."
        ),
        annotations=context.annotations,
    )
    def trading_fundamental_us_report(
        stock: Annotated[
            str,
            Field(
                ...,
                min_length=1,
                description="US stock symbol (e.g. TSLA, AAPL.US, 105.AAPL, BRK.B)",
            ),
        ],
        symbol: Annotated[
            Literal["资产负债表", "综合损益表", "现金流量表"],
            Field("资产负债表", description="Report type"),
        ] = "资产负债表",
        indicator: Annotated[
            Literal["年报", "单季报", "累计季报"],
            Field("年报", description="Report frequency type"),
        ] = "年报",
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
    ) -> Annotated[CallToolResult, FundamentalUsReportResponse]:
        request = FundamentalUsReportRequest(
            stock=stock,
            symbol=symbol,
            indicator=indicator,
            limit=limit,
            offset=offset,
            start_date=start_date,
            end_date=end_date,
        )
        try:
            response = service.fundamental_us_report(request)
        except MarketDataError as exc:
            return error_result(f"Error: {exc}. Check stock, symbol and indicator.")
        return success_result(
            response, response_format, format_fundamental_us_report_response
        )

    @mcp.tool(
        description=(
            "Return US fundamental analysis indicators with pagination metadata. "
            "indicator enum: '年报', '单季报', '累计季报'."
        ),
        annotations=context.annotations,
    )
    def trading_fundamental_us_indicators(
        symbol: Annotated[
            str,
            Field(
                ...,
                min_length=1,
                description="US stock symbol (e.g. TSLA, AAPL.US, 105.AAPL, BRK.B)",
            ),
        ],
        indicator: Annotated[
            Literal["年报", "单季报", "累计季报"],
            Field("年报", description="Report frequency type"),
        ] = "年报",
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
    ) -> Annotated[CallToolResult, FundamentalUsIndicatorsResponse]:
        request = FundamentalUsIndicatorsRequest(
            symbol=symbol,
            indicator=indicator,
            limit=limit,
            offset=offset,
            start_date=start_date,
            end_date=end_date,
        )
        try:
            response = service.fundamental_us_indicators(request)
        except MarketDataError as exc:
            return error_result(f"Error: {exc}. Check symbol and indicator.")
        return success_result(
            response, response_format, format_fundamental_us_indicators_response
        )

    return [
        ToolMeta(
            name="trading_fundamental_cn_indicators",
            signature=(
                "trading_fundamental_cn_indicators(symbol, indicator='按报告期', "
                "limit=200, offset=0, start_date=None, end_date=None, "
                "response_format='markdown'): return A-share fundamental indicators "
                "(raw records)."
            ),
            resource_description="A-share fundamental indicator records",
            resource_fields=["columns", "items", "indicator", "symbol"],
        ),
        ToolMeta(
            name="trading_fundamental_us_report",
            signature=(
                "trading_fundamental_us_report(stock, symbol='资产负债表', "
                "indicator='年报', limit=200, offset=0, start_date=None, "
                "end_date=None, response_format='markdown'): return US financial "
                "statements (raw records)."
            ),
            resource_description="US financial statement records",
            resource_fields=["columns", "items", "stock", "symbol", "indicator"],
        ),
        ToolMeta(
            name="trading_fundamental_us_indicators",
            signature=(
                "trading_fundamental_us_indicators(symbol, indicator='年报', "
                "limit=200, offset=0, start_date=None, end_date=None, "
                "response_format='markdown'): return US fundamental indicators "
                "(raw records)."
            ),
            resource_description="US fundamental indicator records",
            resource_fields=["columns", "items", "symbol", "indicator"],
        ),
    ]
