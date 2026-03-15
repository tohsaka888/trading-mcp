from __future__ import annotations

from typing import Annotated

from data.client import MarketDataError
from indicators.engine import IndicatorError
from mcp.server.fastmcp import FastMCP
from mcp.types import CallToolResult
from pydantic import Field

from mcp_server.context import ServerContext
from mcp_server.metadata import ToolMeta
from mcp_server.results import (
    empty_tool_response,
    structured_error_result,
    success_result,
)
from mcp_server.tools.common import PeriodType, ResponseFormat
from models.mcp_tools import (
    KlineRequest,
    KlineResponse,
    MacdRequest,
    MacdResponse,
    MaRequest,
    MaResponse,
    RsiRequest,
    RsiResponse,
    VolumeRequest,
    VolumeResponse,
)
from utils.mcp_formatting import (
    format_kline_response,
    format_macd_response,
    format_ma_response,
    format_rsi_response,
    format_volume_response,
)


def register_tools(mcp: FastMCP, context: ServerContext) -> list[ToolMeta]:
    service = context.service

    @mcp.tool(
        description=(
            "Return OHLCV bars with pagination metadata. "
            "period_type enum: '1d' (daily), '1w' (weekly), '1m' (monthly)."
        ),
        annotations=context.annotations,
    )
    def trading_kline(
        symbol: Annotated[
            str,
            Field(
                ...,
                min_length=1,
                description="Market symbol identifier (e.g. 000001, AAPL.US, AAPL)",
            ),
        ],
        limit: Annotated[
            int, Field(30, ge=1, description="Number of recent data points to return")
        ] = 30,
        offset: Annotated[
            int, Field(0, ge=0, description="Number of most recent points to skip")
        ] = 0,
        period_type: Annotated[
            PeriodType,
            Field(
                "1d",
                description="Data interval enum. Allowed values: '1d', '1w', '1m'.",
            ),
        ] = "1d",
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
    ) -> Annotated[CallToolResult, KlineResponse]:
        request = KlineRequest(
            symbol=symbol,
            limit=limit,
            offset=offset,
            period_type=period_type,
            start_date=start_date,
            end_date=end_date,
        )
        try:
            response = service.kline(request)
        except (MarketDataError, IndicatorError) as exc:
            return structured_error_result(
                f"Error: {exc}. Check the symbol, date range, and upstream connectivity.",
                empty_tool_response(
                    KlineResponse,
                    symbol=symbol,
                    limit=limit,
                    offset=offset,
                    period_type=period_type,
                    start_date=start_date,
                    end_date=end_date,
                ),
            )
        return success_result(response, response_format, format_kline_response)

    @mcp.tool(
        description=(
            "Return volume, amount, and turnover rate values with pagination metadata. "
            "period_type enum: '1d' (daily), '1w' (weekly), '1m' (monthly)."
        ),
        annotations=context.annotations,
    )
    def trading_volume(
        symbol: Annotated[
            str,
            Field(
                ...,
                min_length=1,
                description="Market symbol identifier (e.g. 000001, AAPL.US, AAPL)",
            ),
        ],
        limit: Annotated[
            int, Field(30, ge=1, description="Number of recent data points to return")
        ] = 30,
        offset: Annotated[
            int, Field(0, ge=0, description="Number of most recent points to skip")
        ] = 0,
        period_type: Annotated[
            PeriodType,
            Field(
                "1d",
                description="Data interval enum. Allowed values: '1d', '1w', '1m'.",
            ),
        ] = "1d",
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
    ) -> Annotated[CallToolResult, VolumeResponse]:
        request = VolumeRequest(
            symbol=symbol,
            limit=limit,
            offset=offset,
            period_type=period_type,
            start_date=start_date,
            end_date=end_date,
        )
        try:
            response = service.volume(request)
        except (MarketDataError, IndicatorError) as exc:
            return structured_error_result(
                f"Error: {exc}. Check the symbol, date range, and upstream connectivity.",
                empty_tool_response(
                    VolumeResponse,
                    symbol=symbol,
                    limit=limit,
                    offset=offset,
                    period_type=period_type,
                    start_date=start_date,
                    end_date=end_date,
                    volume_unit="lot",
                    amount_unit=None,
                    turnover_rate_unit="percent",
                ),
            )
        return success_result(response, response_format, format_volume_response)

    @mcp.tool(
        description=(
            "Return RSI values with pagination metadata. "
            "period_type enum: '1d' (daily), '1w' (weekly), '1m' (monthly)."
        ),
        annotations=context.annotations,
    )
    def trading_rsi(
        symbol: Annotated[
            str,
            Field(
                ...,
                min_length=1,
                description="Market symbol identifier (e.g. 000001, AAPL.US, AAPL)",
            ),
        ],
        limit: Annotated[
            int, Field(30, ge=1, description="Number of recent data points to return")
        ] = 30,
        period: Annotated[int, Field(14, ge=1, description="RSI lookback period")] = 14,
        offset: Annotated[
            int, Field(0, ge=0, description="Number of most recent points to skip")
        ] = 0,
        period_type: Annotated[
            PeriodType,
            Field(
                "1d",
                description="Data interval enum. Allowed values: '1d', '1w', '1m'.",
            ),
        ] = "1d",
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
    ) -> Annotated[CallToolResult, RsiResponse]:
        request = RsiRequest(
            symbol=symbol,
            limit=limit,
            period=period,
            offset=offset,
            period_type=period_type,
            start_date=start_date,
            end_date=end_date,
        )
        try:
            response = service.rsi(request)
        except (MarketDataError, IndicatorError) as exc:
            return structured_error_result(
                f"Error: {exc}. Check the symbol, date range, and upstream connectivity.",
                empty_tool_response(
                    RsiResponse,
                    symbol=symbol,
                    limit=limit,
                    offset=offset,
                    period_type=period_type,
                    start_date=start_date,
                    end_date=end_date,
                ),
            )
        return success_result(response, response_format, format_rsi_response)

    @mcp.tool(
        description=(
            "Return moving average values with pagination metadata. "
            "period_type enum: '1d' (daily), '1w' (weekly), '1m' (monthly)."
        ),
        annotations=context.annotations,
    )
    def trading_ma(
        symbol: Annotated[
            str,
            Field(
                ...,
                min_length=1,
                description="Market symbol identifier (e.g. 000001, AAPL.US, AAPL)",
            ),
        ],
        limit: Annotated[
            int, Field(30, ge=1, description="Number of recent data points to return")
        ] = 30,
        period: Annotated[int, Field(20, ge=1, description="MA lookback period")] = 20,
        ma_type: Annotated[
            str, Field("sma", description="Moving average type: sma or ema")
        ] = "sma",
        offset: Annotated[
            int, Field(0, ge=0, description="Number of most recent points to skip")
        ] = 0,
        period_type: Annotated[
            PeriodType,
            Field(
                "1d",
                description="Data interval enum. Allowed values: '1d', '1w', '1m'.",
            ),
        ] = "1d",
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
    ) -> Annotated[CallToolResult, MaResponse]:
        request = MaRequest(
            symbol=symbol,
            limit=limit,
            period=period,
            ma_type=ma_type,
            offset=offset,
            period_type=period_type,
            start_date=start_date,
            end_date=end_date,
        )
        try:
            response = service.ma(request)
        except (MarketDataError, IndicatorError) as exc:
            return structured_error_result(
                f"Error: {exc}. Check the symbol, date range, and upstream connectivity.",
                empty_tool_response(
                    MaResponse,
                    symbol=symbol,
                    limit=limit,
                    offset=offset,
                    period_type=period_type,
                    start_date=start_date,
                    end_date=end_date,
                ),
            )
        return success_result(response, response_format, format_ma_response)

    @mcp.tool(
        description=(
            "Return MACD values with pagination metadata. "
            "period_type enum: '1d' (daily), '1w' (weekly), '1m' (monthly)."
        ),
        annotations=context.annotations,
    )
    def trading_macd(
        symbol: Annotated[
            str,
            Field(
                ...,
                min_length=1,
                description="Market symbol identifier (e.g. 000001, AAPL.US, AAPL)",
            ),
        ],
        limit: Annotated[
            int, Field(30, ge=1, description="Number of recent data points to return")
        ] = 30,
        fast_period: Annotated[
            int, Field(12, ge=1, description="MACD fast EMA period")
        ] = 12,
        slow_period: Annotated[
            int, Field(26, ge=1, description="MACD slow EMA period")
        ] = 26,
        signal_period: Annotated[
            int, Field(9, ge=1, description="MACD signal period")
        ] = 9,
        offset: Annotated[
            int, Field(0, ge=0, description="Number of most recent points to skip")
        ] = 0,
        period_type: Annotated[
            PeriodType,
            Field(
                "1d",
                description="Data interval enum. Allowed values: '1d', '1w', '1m'.",
            ),
        ] = "1d",
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
    ) -> Annotated[CallToolResult, MacdResponse]:
        request = MacdRequest(
            symbol=symbol,
            limit=limit,
            fast_period=fast_period,
            slow_period=slow_period,
            signal_period=signal_period,
            offset=offset,
            period_type=period_type,
            start_date=start_date,
            end_date=end_date,
        )
        try:
            response = service.macd(request)
        except (MarketDataError, IndicatorError) as exc:
            return structured_error_result(
                f"Error: {exc}. Check the symbol, date range, and upstream connectivity.",
                empty_tool_response(
                    MacdResponse,
                    symbol=symbol,
                    limit=limit,
                    offset=offset,
                    period_type=period_type,
                    start_date=start_date,
                    end_date=end_date,
                ),
            )
        return success_result(response, response_format, format_macd_response)

    return [
        ToolMeta(
            name="trading_kline",
            signature=(
                "trading_kline(symbol, limit=30, offset=0, period_type='1d', "
                "start_date=None, end_date=None, response_format='markdown'): "
                "return OHLCV bars."
            ),
            resource_description="K-line OHLCV bars",
            resource_fields=["timestamp", "open", "high", "low", "close", "volume"],
        ),
        ToolMeta(
            name="trading_macd",
            signature=(
                "trading_macd(symbol, limit=30, fast_period=12, slow_period=26, "
                "signal_period=9, offset=0, period_type='1d', start_date=None, "
                "end_date=None, response_format='markdown'): return MACD, signal, "
                "histogram values."
            ),
            resource_description="MACD indicator values",
            resource_fields=["timestamp", "macd", "signal", "histogram"],
        ),
        ToolMeta(
            name="trading_volume",
            signature=(
                "trading_volume(symbol, limit=30, offset=0, period_type='1d', "
                "start_date=None, end_date=None, response_format='markdown'): "
                "return volume, amount, turnover_rate values."
            ),
            resource_description="Volume, amount, and turnover rate values",
            resource_fields=["timestamp", "volume", "amount", "turnover_rate"],
        ),
        ToolMeta(
            name="trading_rsi",
            signature=(
                "trading_rsi(symbol, limit=30, period=14, offset=0, period_type='1d', "
                "start_date=None, end_date=None, response_format='markdown'): "
                "return RSI values."
            ),
            resource_description="Relative Strength Index values",
            resource_fields=["timestamp", "rsi"],
        ),
        ToolMeta(
            name="trading_ma",
            signature=(
                "trading_ma(symbol, limit=30, period=20, ma_type='sma', offset=0, "
                "period_type='1d', start_date=None, end_date=None, "
                "response_format='markdown'): return moving average values."
            ),
            resource_description="Moving average values",
            resource_fields=["timestamp", "ma"],
        ),
    ]
