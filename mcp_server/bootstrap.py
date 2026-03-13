from __future__ import annotations

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations

from config import McpServerSettings
from data import AkshareMarketDataClient
from indicators import IndicatorEngine
from mcp_server.context import ServerContext
from mcp_server.metadata import ToolMeta, build_indicator_resource, build_tool_usage
from mcp_server.tools import (
    register_sector_fund_flow_tools,
    register_sector_overview_tools,
    register_sector_technical_tools,
    register_stock_fund_flow_tools,
    register_stock_fundamental_tools,
    register_stock_technical_tools,
)
from services.market_service import MarketService


def _register_prompt_and_resource(mcp: FastMCP, tool_metas: list[ToolMeta]) -> None:
    @mcp.prompt()
    def tool_usage() -> str:
        return build_tool_usage(tool_metas)

    @mcp.resource("trading://indicators")
    def indicator_resource() -> str:
        return build_indicator_resource(tool_metas)


def create_server() -> FastMCP:
    settings = McpServerSettings()
    mcp = FastMCP("trading_mcp", stateless_http=True, json_response=True)
    mcp.settings.host = settings.host
    mcp.settings.port = settings.port

    context = ServerContext(
        service=MarketService(AkshareMarketDataClient(), IndicatorEngine()),
        annotations=ToolAnnotations(
            readOnlyHint=True,
            destructiveHint=False,
            openWorldHint=True,
        ),
    )

    tool_metas: list[ToolMeta] = []
    tool_metas.extend(register_stock_technical_tools(mcp, context))
    tool_metas.extend(register_stock_fund_flow_tools(mcp, context))
    tool_metas.extend(register_sector_fund_flow_tools(mcp, context))
    tool_metas.extend(register_stock_fundamental_tools(mcp, context))
    tool_metas.extend(register_sector_overview_tools(mcp, context))
    tool_metas.extend(register_sector_technical_tools(mcp, context))
    _register_prompt_and_resource(mcp, tool_metas)
    return mcp
