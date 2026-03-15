from __future__ import annotations

import asyncio
from typing import Any, cast

from mcp.server.fastmcp import FastMCP
from mcp.types import CallToolResult, TextContent, ToolAnnotations

from data.client import MarketDataError
from mcp_server.context import ServerContext
from mcp_server.tools import (
    register_sector_fund_flow_tools,
    register_stock_technical_tools,
)
from models.mcp_tools import FundFlowSectorRankEmResponse, KlineResponse


class ErrorSectorFundFlowService:
    def fund_flow_sector_rank_em(self, request: Any) -> Any:
        raise MarketDataError(
            "Eastmoney sector fund-flow ranking fetch failed "
            f"for indicator={request.indicator}, sector_type={request.sector_type}"
        )


class ErrorStockTechnicalService:
    def kline(self, request: Any) -> Any:
        raise MarketDataError(
            f"K-line fetch failed for symbol={request.symbol}, period_type={request.period_type}"
        )


def _make_server(service: Any, register_tools: Any) -> FastMCP:
    server = FastMCP("test_server", stateless_http=True, json_response=True)
    context = ServerContext(
        service=service,
        annotations=ToolAnnotations(
            readOnlyHint=True,
            destructiveHint=False,
            openWorldHint=True,
        ),
    )
    register_tools(server, context)
    return server


def test_sector_fund_flow_rank_error_returns_schema_safe_result() -> None:
    async def run() -> None:
        server = _make_server(
            ErrorSectorFundFlowService(),
            register_sector_fund_flow_tools,
        )

        result = cast(
            CallToolResult,
            await server.call_tool(
            "trading_fund_flow_sector_rank_em",
            {
                "indicator": "今日",
                "sector_type": "行业资金流",
                "sort_by": "涨跌幅",
                "limit": 5,
                "offset": 0,
                "response_format": "markdown",
            },
            ),
        )

        assert result.isError is True
        assert result.structuredContent is not None

        structured = FundFlowSectorRankEmResponse.model_validate(
            result.structuredContent
        )
        assert structured.indicator == "今日"
        assert structured.sector_type == "行业资金流"
        assert structured.sort_by == "涨跌幅"
        assert structured.items == []
        assert structured.columns == []

        text = cast(TextContent, result.content[0]).text
        assert text is not None
        assert "Eastmoney sector fund-flow ranking fetch failed" in text
        assert "indicator=今日" in text
        assert "sector_type=行业资金流" in text
        assert "FundFlowSectorRankEmResponse" not in text

    asyncio.run(run())


def test_kline_error_returns_schema_safe_result() -> None:
    async def run() -> None:
        server = _make_server(
            ErrorStockTechnicalService(),
            register_stock_technical_tools,
        )

        result = cast(
            CallToolResult,
            await server.call_tool(
            "trading_kline",
            {
                "symbol": "000001",
                "limit": 3,
                "offset": 0,
                "period_type": "1d",
                "response_format": "markdown",
            },
            ),
        )

        assert result.isError is True
        assert result.structuredContent is not None

        structured = KlineResponse.model_validate(result.structuredContent)
        assert structured.symbol == "000001"
        assert structured.items == []
        assert structured.count == 0
        assert structured.period_type == "1d"

        text = cast(TextContent, result.content[0]).text
        assert text is not None
        assert "K-line fetch failed for symbol=000001" in text
        assert "KlineResponse" not in text

    asyncio.run(run())
