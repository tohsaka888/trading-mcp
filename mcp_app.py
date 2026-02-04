from __future__ import annotations

import json

from mcp.server.fastmcp import FastMCP

from config import McpServerSettings
from data import AkshareMarketDataClient
from indicators import IndicatorEngine
from models.mcp_tools import (
    KlineBar,
    KlineRequest,
    MacdPoint,
    MacdRequest,
    MaPoint,
    MaRequest,
    RsiPoint,
    RsiRequest,
)
from services.market_service import MarketService


def create_server() -> FastMCP:
    settings = McpServerSettings()
    mcp = FastMCP("Trading MCP", stateless_http=True, json_response=True)
    mcp.settings.host = settings.host
    mcp.settings.port = settings.port

    service = MarketService(AkshareMarketDataClient(), IndicatorEngine())

    @mcp.tool()
    def kline(symbol: str, limit: int) -> list[KlineBar]:
        request = KlineRequest(symbol=symbol, limit=limit)
        return service.kline(request)

    @mcp.tool()
    def rsi(symbol: str, limit: int, period: int = 14) -> list[RsiPoint]:
        request = RsiRequest(symbol=symbol, limit=limit, period=period)
        return service.rsi(request)

    @mcp.tool()
    def ma(
        symbol: str,
        limit: int,
        period: int = 20,
        ma_type: str = "sma",
    ) -> list[MaPoint]:
        request = MaRequest(
            symbol=symbol,
            limit=limit,
            period=period,
            ma_type=ma_type,
        )
        return service.ma(request)

    @mcp.tool()
    def macd(
        symbol: str,
        limit: int,
        fast_period: int = 12,
        slow_period: int = 26,
        signal_period: int = 9,
    ) -> list[MacdPoint]:
        request = MacdRequest(
            symbol=symbol,
            limit=limit,
            fast_period=fast_period,
            slow_period=slow_period,
            signal_period=signal_period,
        )
        return service.macd(request)

    @mcp.prompt()
    def tool_usage() -> str:
        return (
            "Available tools:\n"
            "- kline(symbol, limit): return OHLCV bars.\n"
            "- macd(symbol, limit, fast_period=12, slow_period=26, signal_period=9): "
            "return MACD, signal, histogram values.\n"
            "- rsi(symbol, limit, period=14): return RSI values.\n"
            "- ma(symbol, limit, period=20, ma_type='sma'): return moving average values.\n"
            "Inputs require a positive limit and a non-empty symbol."
        )

    @mcp.resource("trading://indicators")
    def indicator_resource() -> str:
        payload = {
            "kline": {
                "description": "K-line OHLCV bars",
                "fields": ["timestamp", "open", "high", "low", "close", "volume"],
            },
            "macd": {
                "description": "MACD indicator values",
                "fields": ["timestamp", "macd", "signal", "histogram"],
            },
            "rsi": {
                "description": "Relative Strength Index values",
                "fields": ["timestamp", "rsi"],
            },
            "ma": {
                "description": "Moving average values",
                "fields": ["timestamp", "ma"],
            },
        }
        return json.dumps(payload, ensure_ascii=False, indent=2)

    return mcp
