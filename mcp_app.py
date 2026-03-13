from __future__ import annotations

import json
from typing import Annotated, Any, Callable, Literal

from mcp.server.fastmcp import FastMCP
from mcp.types import CallToolResult, TextContent, ToolAnnotations
from pydantic import BaseModel, Field

from config import McpServerSettings
from data import AkshareMarketDataClient
from data.client import MarketDataError
from indicators import IndicatorEngine
from indicators.engine import IndicatorError
from models.mcp_tools import (
    FundamentalCnIndicatorsRequest,
    FundamentalCnIndicatorsResponse,
    FundamentalUsIndicatorsRequest,
    FundamentalUsIndicatorsResponse,
    FundamentalUsReportRequest,
    FundamentalUsReportResponse,
    IndustryConsEmRequest,
    IndustryConsEmResponse,
    IndustryHistEmRequest,
    IndustryHistEmResponse,
    IndustryHistMinEmRequest,
    IndustryHistMinEmResponse,
    IndustryIndexThsRequest,
    IndustryIndexThsResponse,
    IndustryNameEmRequest,
    IndustryNameEmResponse,
    IndustrySpotEmRequest,
    IndustrySpotEmResponse,
    IndustrySummaryThsRequest,
    IndustrySummaryThsResponse,
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
from services.market_service import MarketService
from utils.mcp_formatting import (
    format_fundamental_cn_indicators_response,
    format_fundamental_us_indicators_response,
    format_fundamental_us_report_response,
    format_industry_cons_em_response,
    format_industry_hist_em_response,
    format_industry_hist_min_em_response,
    format_industry_index_ths_response,
    format_industry_name_em_response,
    format_industry_spot_em_response,
    format_industry_summary_ths_response,
    format_kline_response,
    format_macd_response,
    format_ma_response,
    format_rsi_response,
    format_volume_response,
)

PeriodType = Literal["1d", "1w", "1m"]


def create_server() -> FastMCP:
    settings = McpServerSettings()
    mcp = FastMCP("trading_mcp", stateless_http=True, json_response=True)
    mcp.settings.host = settings.host
    mcp.settings.port = settings.port

    service = MarketService(AkshareMarketDataClient(), IndicatorEngine())
    annotations = ToolAnnotations(
        readOnlyHint=True,
        destructiveHint=False,
        openWorldHint=True,
    )

    def _error_result(message: str) -> CallToolResult:
        return CallToolResult(
            content=[TextContent(type="text", text=message)],
            isError=True,
        )

    def _success_result(
        response: BaseModel,
        response_format: Literal["markdown", "json"],
        formatter: Callable[[Any], str],
    ) -> CallToolResult:
        structured = response.model_dump(mode="json", by_alias=True)
        if response_format == "json":
            text = json.dumps(structured, indent=2, ensure_ascii=False)
        else:
            text = formatter(response)
        return CallToolResult(
            content=[TextContent(type="text", text=text)],
            structuredContent=structured,
        )

    @mcp.tool(
        description=(
            "Return OHLCV bars with pagination metadata. "
            "period_type enum: '1d' (daily), '1w' (weekly), '1m' (monthly)."
        ),
        annotations=annotations,
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
            Literal["markdown", "json"],
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
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text=f"Error: {exc}. Check the symbol and date range.",
                    )
                ],
                isError=True,
            )

        structured = response.model_dump(mode="json", by_alias=True)
        if response_format == "json":
            text = json.dumps(structured, indent=2, ensure_ascii=False)
        else:
            text = format_kline_response(response)
        return CallToolResult(
            content=[TextContent(type="text", text=text)],
            structuredContent=structured,
        )

    @mcp.tool(
        description=(
            "Return volume, amount, and turnover rate values with pagination metadata. "
            "period_type enum: '1d' (daily), '1w' (weekly), '1m' (monthly)."
        ),
        annotations=annotations,
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
            int, Field(..., ge=1, description="Number of recent data points to return")
        ],
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
            Literal["markdown", "json"],
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
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text=f"Error: {exc}. Check the symbol and date range.",
                    )
                ],
                isError=True,
            )

        structured = response.model_dump(mode="json", by_alias=True)
        if response_format == "json":
            text = json.dumps(structured, indent=2, ensure_ascii=False)
        else:
            text = format_volume_response(response)
        return CallToolResult(
            content=[TextContent(type="text", text=text)],
            structuredContent=structured,
        )

    @mcp.tool(
        description=(
            "Return RSI values with pagination metadata. "
            "period_type enum: '1d' (daily), '1w' (weekly), '1m' (monthly)."
        ),
        annotations=annotations,
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
            int, Field(..., ge=1, description="Number of recent data points to return")
        ],
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
            Literal["markdown", "json"],
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
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text=f"Error: {exc}. Check the symbol and date range.",
                    )
                ],
                isError=True,
            )

        structured = response.model_dump(mode="json", by_alias=True)
        if response_format == "json":
            text = json.dumps(structured, indent=2, ensure_ascii=False)
        else:
            text = format_rsi_response(response)
        return CallToolResult(
            content=[TextContent(type="text", text=text)],
            structuredContent=structured,
        )

    @mcp.tool(
        description=(
            "Return moving average values with pagination metadata. "
            "period_type enum: '1d' (daily), '1w' (weekly), '1m' (monthly)."
        ),
        annotations=annotations,
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
            int, Field(..., ge=1, description="Number of recent data points to return")
        ],
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
            Literal["markdown", "json"],
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
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text=f"Error: {exc}. Check the symbol and date range.",
                    )
                ],
                isError=True,
            )

        structured = response.model_dump(mode="json", by_alias=True)
        if response_format == "json":
            text = json.dumps(structured, indent=2, ensure_ascii=False)
        else:
            text = format_ma_response(response)
        return CallToolResult(
            content=[TextContent(type="text", text=text)],
            structuredContent=structured,
        )

    @mcp.tool(
        description=(
            "Return MACD values with pagination metadata. "
            "period_type enum: '1d' (daily), '1w' (weekly), '1m' (monthly)."
        ),
        annotations=annotations,
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
            int, Field(..., ge=1, description="Number of recent data points to return")
        ],
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
            Literal["markdown", "json"],
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
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text=f"Error: {exc}. Check the symbol and date range.",
                    )
                ],
                isError=True,
            )

        structured = response.model_dump(mode="json", by_alias=True)
        if response_format == "json":
            text = json.dumps(structured, indent=2, ensure_ascii=False)
        else:
            text = format_macd_response(response)
        return CallToolResult(
            content=[TextContent(type="text", text=text)],
            structuredContent=structured,
        )

    @mcp.tool(
        description=(
            "Return A-share fundamental analysis indicators with pagination metadata. "
            "indicator enum: '按报告期' or '按单季度'."
        ),
        annotations=annotations,
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
            Literal["markdown", "json"],
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
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text=f"Error: {exc}. Check the symbol and indicator.",
                    )
                ],
                isError=True,
            )

        structured = response.model_dump(mode="json", by_alias=True)
        if response_format == "json":
            text = json.dumps(structured, indent=2, ensure_ascii=False)
        else:
            text = format_fundamental_cn_indicators_response(response)
        return CallToolResult(
            content=[TextContent(type="text", text=text)],
            structuredContent=structured,
        )

    @mcp.tool(
        description=(
            "Return US financial statements (balance sheet, comprehensive income, "
            "cash flow) with pagination metadata."
        ),
        annotations=annotations,
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
            Literal["markdown", "json"],
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
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text=f"Error: {exc}. Check stock, symbol and indicator.",
                    )
                ],
                isError=True,
            )

        structured = response.model_dump(mode="json", by_alias=True)
        if response_format == "json":
            text = json.dumps(structured, indent=2, ensure_ascii=False)
        else:
            text = format_fundamental_us_report_response(response)
        return CallToolResult(
            content=[TextContent(type="text", text=text)],
            structuredContent=structured,
        )

    @mcp.tool(
        description=(
            "Return US fundamental analysis indicators with pagination metadata. "
            "indicator enum: '年报', '单季报', '累计季报'."
        ),
        annotations=annotations,
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
            Literal["markdown", "json"],
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
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text=f"Error: {exc}. Check symbol and indicator.",
                    )
                ],
                isError=True,
            )

        structured = response.model_dump(mode="json", by_alias=True)
        if response_format == "json":
            text = json.dumps(structured, indent=2, ensure_ascii=False)
        else:
            text = format_fundamental_us_indicators_response(response)
        return CallToolResult(
            content=[TextContent(type="text", text=text)],
            structuredContent=structured,
        )

    @mcp.tool(
        description="Return THS industry board summary records with pagination metadata.",
        annotations=annotations,
    )
    def trading_industry_summary_ths(
        limit: Annotated[
            int, Field(200, ge=1, description="Number of recent records to return")
        ] = 200,
        offset: Annotated[
            int, Field(0, ge=0, description="Number of most recent records to skip")
        ] = 0,
        response_format: Annotated[
            Literal["markdown", "json"],
            Field("markdown", description="Response format"),
        ] = "markdown",
    ) -> Annotated[CallToolResult, IndustrySummaryThsResponse]:
        request = IndustrySummaryThsRequest(limit=limit, offset=offset)
        try:
            response = service.industry_summary_ths(request)
        except MarketDataError as exc:
            return _error_result(f"Error: {exc}. Check the THS industry summary source.")
        return _success_result(
            response, response_format, format_industry_summary_ths_response
        )

    @mcp.tool(
        description=(
            "Return THS industry board index records with pagination metadata. "
            "Supports start_date and end_date in YYYY-MM-DD or YYYYMMDD format."
        ),
        annotations=annotations,
    )
    def trading_industry_index_ths(
        symbol: Annotated[
            str,
            Field(..., min_length=1, description="THS industry board symbol"),
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
            Literal["markdown", "json"],
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
            return _error_result(f"Error: {exc}. Check the board symbol and date range.")
        return _success_result(
            response, response_format, format_industry_index_ths_response
        )

    @mcp.tool(
        description="Return EM industry board name records with pagination metadata.",
        annotations=annotations,
    )
    def trading_industry_name_em(
        limit: Annotated[
            int, Field(200, ge=1, description="Number of recent records to return")
        ] = 200,
        offset: Annotated[
            int, Field(0, ge=0, description="Number of most recent records to skip")
        ] = 0,
        response_format: Annotated[
            Literal["markdown", "json"],
            Field("markdown", description="Response format"),
        ] = "markdown",
    ) -> Annotated[CallToolResult, IndustryNameEmResponse]:
        request = IndustryNameEmRequest(limit=limit, offset=offset)
        try:
            response = service.industry_name_em(request)
        except MarketDataError as exc:
            return _error_result(f"Error: {exc}. Check the EM industry board source.")
        return _success_result(response, response_format, format_industry_name_em_response)

    @mcp.tool(
        description="Return EM industry board spot records with pagination metadata.",
        annotations=annotations,
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
            Literal["markdown", "json"],
            Field("markdown", description="Response format"),
        ] = "markdown",
    ) -> Annotated[CallToolResult, IndustrySpotEmResponse]:
        request = IndustrySpotEmRequest(symbol=symbol, limit=limit, offset=offset)
        try:
            response = service.industry_spot_em(request)
        except MarketDataError as exc:
            return _error_result(f"Error: {exc}. Check the board symbol.")
        return _success_result(response, response_format, format_industry_spot_em_response)

    @mcp.tool(
        description="Return EM industry board constituent records with pagination metadata.",
        annotations=annotations,
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
            Literal["markdown", "json"],
            Field("markdown", description="Response format"),
        ] = "markdown",
    ) -> Annotated[CallToolResult, IndustryConsEmResponse]:
        request = IndustryConsEmRequest(symbol=symbol, limit=limit, offset=offset)
        try:
            response = service.industry_cons_em(request)
        except MarketDataError as exc:
            return _error_result(f"Error: {exc}. Check the board symbol.")
        return _success_result(response, response_format, format_industry_cons_em_response)

    @mcp.tool(
        description=(
            "Return EM industry board historical K-line records with pagination metadata. "
            "period enum: '日k', '周k', '月k'; adjust enum: 'none', 'qfq', 'hfq'. "
            "'none' means no price adjustment."
        ),
        annotations=annotations,
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
            Literal["markdown", "json"],
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
            return _error_result(
                f"Error: {exc}. Check the board symbol, date range and adjust option."
            )
        return _success_result(response, response_format, format_industry_hist_em_response)

    @mcp.tool(
        description=(
            "Return EM industry board intraday historical records with pagination metadata. "
            "period enum: '1', '5', '15', '30', '60'."
        ),
        annotations=annotations,
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
            int, Field(200, ge=1, description="Number of recent records to return")
        ] = 200,
        offset: Annotated[
            int, Field(0, ge=0, description="Number of most recent records to skip")
        ] = 0,
        response_format: Annotated[
            Literal["markdown", "json"],
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
            return _error_result(f"Error: {exc}. Check the board symbol and period.")
        return _success_result(
            response, response_format, format_industry_hist_min_em_response
        )

    @mcp.prompt()
    def tool_usage() -> str:
        return (
            "Available tools:\n"
            "- trading_kline(symbol, limit=30, offset=0, period_type='1d', start_date=None, "
            "end_date=None, response_format='markdown'): return OHLCV bars.\n"
            "- trading_macd(symbol, limit, fast_period=12, slow_period=26, signal_period=9, "
            "offset=0, period_type='1d', start_date=None, end_date=None, "
            "response_format='markdown'): "
            "return MACD, signal, histogram values.\n"
            "- trading_volume(symbol, limit, offset=0, period_type='1d', start_date=None, "
            "end_date=None, response_format='markdown'): "
            "return volume, amount, turnover_rate values.\n"
            "- trading_rsi(symbol, limit, period=14, offset=0, period_type='1d', start_date=None, "
            "end_date=None, response_format='markdown'): return RSI values.\n"
            "- trading_ma(symbol, limit, period=20, ma_type='sma', offset=0, period_type='1d', "
            "start_date=None, end_date=None, response_format='markdown'): "
            "return moving average values.\n"
            "- trading_fundamental_cn_indicators(symbol, indicator='按报告期', limit=200, "
            "offset=0, start_date=None, end_date=None, response_format='markdown'): "
            "return A-share fundamental indicators (raw records).\n"
            "- trading_fundamental_us_report(stock, symbol='资产负债表', indicator='年报', "
            "limit=200, offset=0, start_date=None, end_date=None, response_format='markdown'): "
            "return US financial statements (raw records).\n"
            "- trading_fundamental_us_indicators(symbol, indicator='年报', limit=200, "
            "offset=0, start_date=None, end_date=None, response_format='markdown'): "
            "return US fundamental indicators (raw records).\n"
            "- trading_industry_summary_ths(limit=200, offset=0, response_format='markdown'): "
            "return THS industry board summary records.\n"
            "- trading_industry_index_ths(symbol, limit=200, offset=0, start_date=None, "
            "end_date=None, response_format='markdown'): return THS industry index records.\n"
            "- trading_industry_name_em(limit=200, offset=0, response_format='markdown'): "
            "return EM industry board name records.\n"
            "- trading_industry_spot_em(symbol, limit=200, offset=0, response_format='markdown'): "
            "return EM industry board spot records.\n"
            "- trading_industry_cons_em(symbol, limit=200, offset=0, response_format='markdown'): "
            "return EM industry board constituent records.\n"
            "- trading_industry_hist_em(symbol, period='日k', adjust='none', limit=200, offset=0, "
            "start_date=None, end_date=None, response_format='markdown'): "
            "return EM industry historical K-line records.\n"
            "- trading_industry_hist_min_em(symbol, period='5', limit=200, offset=0, "
            "response_format='markdown'): return EM industry intraday history records.\n"
            "period_type allowed values: '1d' | '1w' | '1m'. "
            "Use exact enum value, not 'daily/weekly/monthly'.\n"
            "Industry hist period values: '日k' | '周k' | '月k'; "
            "adjust values: 'none' | 'qfq' | 'hfq'; minute period values: "
            "'1' | '5' | '15' | '30' | '60'.\n"
            "Inputs require a positive limit and a non-empty symbol. "
            "US symbols: AAPL.US, AAPL, 105.AAPL, BRK.B."
        )

    @mcp.resource("trading://indicators")
    def indicator_resource() -> str:
        payload = {
            "trading_kline": {
                "description": "K-line OHLCV bars",
                "fields": ["timestamp", "open", "high", "low", "close", "volume"],
            },
            "trading_macd": {
                "description": "MACD indicator values",
                "fields": ["timestamp", "macd", "signal", "histogram"],
            },
            "trading_volume": {
                "description": "Volume, amount, and turnover rate values",
                "fields": ["timestamp", "volume", "amount", "turnover_rate"],
            },
            "trading_rsi": {
                "description": "Relative Strength Index values",
                "fields": ["timestamp", "rsi"],
            },
            "trading_ma": {
                "description": "Moving average values",
                "fields": ["timestamp", "ma"],
            },
            "trading_fundamental_cn_indicators": {
                "description": "A-share fundamental indicator records",
                "fields": ["columns", "items", "indicator", "symbol"],
            },
            "trading_fundamental_us_report": {
                "description": "US financial statement records",
                "fields": ["columns", "items", "stock", "symbol", "indicator"],
            },
            "trading_fundamental_us_indicators": {
                "description": "US fundamental indicator records",
                "fields": ["columns", "items", "symbol", "indicator"],
            },
            "trading_industry_summary_ths": {
                "description": "THS industry board summary records",
                "fields": ["columns", "items"],
            },
            "trading_industry_index_ths": {
                "description": "THS industry board index records",
                "fields": ["columns", "items", "symbol", "start_date", "end_date"],
            },
            "trading_industry_name_em": {
                "description": "EM industry board name records",
                "fields": ["columns", "items"],
            },
            "trading_industry_spot_em": {
                "description": "EM industry board spot records",
                "fields": ["columns", "items", "symbol"],
            },
            "trading_industry_cons_em": {
                "description": "EM industry board constituent records",
                "fields": ["columns", "items", "symbol"],
            },
            "trading_industry_hist_em": {
                "description": "EM industry board historical K-line records",
                "fields": [
                    "columns",
                    "items",
                    "symbol",
                    "period",
                    "adjust",
                    "start_date",
                    "end_date",
                ],
            },
            "trading_industry_hist_min_em": {
                "description": "EM industry board intraday historical records",
                "fields": ["columns", "items", "symbol", "period"],
            },
        }
        return json.dumps(payload, ensure_ascii=False, indent=2)

    return mcp
