from __future__ import annotations

import asyncio
import json
from typing import cast

from mcp_server import create_server
from mcp.types import TextContent

EXPECTED_TOOL_NAMES = {
    "trading_board_change_em",
    "trading_fund_flow_individual_em",
    "trading_fund_flow_individual_rank_em",
    "trading_fund_flow_sector_rank_em",
    "trading_fund_flow_sector_summary_em",
    "trading_fundamental_cn_indicators",
    "trading_fundamental_us_indicators",
    "trading_fundamental_us_report",
    "trading_info_global_em",
    "trading_industry_cons_em",
    "trading_industry_hist_em",
    "trading_industry_hist_min_em",
    "trading_industry_index_ths",
    "trading_industry_name_em",
    "trading_industry_spot_em",
    "trading_industry_summary_ths",
    "trading_kline",
    "trading_ma",
    "trading_macd",
    "trading_rsi",
    "trading_volume",
}

EXPECTED_TOOL_SIGNATURES = [
    "trading_kline(symbol, limit=30, offset=0, period_type='1d', start_date=None, end_date=None, response_format='markdown'): return OHLCV bars.",
    "trading_macd(symbol, limit=30, fast_period=12, slow_period=26, signal_period=9, offset=0, period_type='1d', start_date=None, end_date=None, response_format='markdown'): return MACD, signal, histogram values.",
    "trading_volume(symbol, limit=30, offset=0, period_type='1d', start_date=None, end_date=None, response_format='markdown'): return volume, amount, turnover_rate values.",
    "trading_rsi(symbol, limit=30, period=14, offset=0, period_type='1d', start_date=None, end_date=None, response_format='markdown'): return RSI values.",
    "trading_ma(symbol, limit=30, period=20, ma_type='sma', offset=0, period_type='1d', start_date=None, end_date=None, response_format='markdown'): return moving average values.",
    "trading_fund_flow_individual_em(symbol, limit=30, offset=0, start_date=None, end_date=None, response_format='markdown'): return Eastmoney individual stock fund-flow records.",
    "trading_fund_flow_individual_rank_em(indicator='5日', limit=30, offset=0, response_format='markdown'): return Eastmoney individual stock fund-flow rankings.",
    "trading_fund_flow_sector_rank_em(indicator='今日', sector_type='行业资金流', sort_by='主力净流入', limit=30, offset=0, response_format='markdown'): return Eastmoney sector fund-flow rankings.",
    "trading_fund_flow_sector_summary_em(symbol, indicator='今日', limit=30, offset=0, response_format='markdown'): return board constituent fund-flow records.",
    "trading_fundamental_cn_indicators(symbol, indicator='按报告期', limit=30, offset=0, start_date=None, end_date=None, response_format='markdown'): return A-share fundamental indicators (raw records).",
    "trading_fundamental_us_report(stock, symbol='资产负债表', indicator='年报', limit=30, offset=0, start_date=None, end_date=None, response_format='markdown'): return US financial statements (raw records).",
    "trading_fundamental_us_indicators(symbol, indicator='年报', limit=30, offset=0, start_date=None, end_date=None, response_format='markdown'): return US fundamental indicators (raw records).",
    "trading_industry_summary_ths(limit=30, offset=0, response_format='markdown'): return THS industry board summary records.",
    "trading_industry_name_em(limit=30, offset=0, response_format='markdown'): return EM industry board name records.",
    "trading_board_change_em(limit=30, offset=0, response_format='markdown'): return Eastmoney board change detail records.",
    "trading_industry_spot_em(symbol, limit=30, offset=0, response_format='markdown'): return EM industry board spot records.",
    "trading_industry_cons_em(symbol, limit=30, offset=0, response_format='markdown'): return EM industry board constituent records.",
    "trading_industry_index_ths(symbol, limit=30, offset=0, start_date=None, end_date=None, response_format='markdown'): return THS industry index records.",
    "trading_industry_hist_em(symbol, period='日k', adjust='none', limit=30, offset=0, start_date=None, end_date=None, response_format='markdown'): return EM industry historical K-line records.",
    "trading_industry_hist_min_em(symbol, period='5', limit=30, offset=0, response_format='markdown'): return EM industry intraday history records.",
    "trading_info_global_em(limit=30, offset=0, response_format='markdown'): return Eastmoney global finance news records.",
]

EXPECTED_RESOURCE_FIELDS = {
    "trading_kline": ["timestamp", "open", "high", "low", "close", "volume"],
    "trading_macd": ["timestamp", "macd", "signal", "histogram"],
    "trading_volume": ["timestamp", "volume", "amount", "turnover_rate"],
    "trading_rsi": ["timestamp", "rsi"],
    "trading_ma": ["timestamp", "ma"],
    "trading_fund_flow_individual_em": [
        "columns",
        "items",
        "symbol",
        "start_date",
        "end_date",
    ],
    "trading_fund_flow_individual_rank_em": ["columns", "items", "indicator"],
    "trading_fund_flow_sector_rank_em": [
        "columns",
        "items",
        "indicator",
        "sector_type",
        "sort_by",
    ],
    "trading_fund_flow_sector_summary_em": [
        "columns",
        "items",
        "symbol",
        "indicator",
    ],
    "trading_fundamental_cn_indicators": [
        "columns",
        "items",
        "indicator",
        "symbol",
    ],
    "trading_fundamental_us_report": [
        "columns",
        "items",
        "stock",
        "symbol",
        "indicator",
    ],
    "trading_fundamental_us_indicators": [
        "columns",
        "items",
        "symbol",
        "indicator",
    ],
    "trading_industry_summary_ths": ["columns", "items"],
    "trading_industry_name_em": ["columns", "items"],
    "trading_board_change_em": ["columns", "items"],
    "trading_industry_spot_em": ["columns", "items", "symbol"],
    "trading_industry_cons_em": ["columns", "items", "symbol"],
    "trading_industry_index_ths": [
        "columns",
        "items",
        "symbol",
        "start_date",
        "end_date",
    ],
    "trading_industry_hist_em": [
        "columns",
        "items",
        "symbol",
        "period",
        "adjust",
        "start_date",
        "end_date",
    ],
    "trading_industry_hist_min_em": ["columns", "items", "symbol", "period"],
    "trading_info_global_em": ["columns", "items"],
}


def test_create_server_registers_all_tools() -> None:
    async def run() -> None:
        server = create_server()
        tools = await server.list_tools()
        assert {tool.name for tool in tools} == EXPECTED_TOOL_NAMES

    asyncio.run(run())


def test_create_server_registers_prompt_with_all_signatures() -> None:
    async def run() -> None:
        server = create_server()
        prompts = await server.list_prompts()
        assert [prompt.name for prompt in prompts] == ["tool_usage"]

        prompt = await server.get_prompt("tool_usage")
        assert len(prompt.messages) == 1
        text = cast(TextContent, prompt.messages[0].content).text
        assert text is not None
        for signature in EXPECTED_TOOL_SIGNATURES:
            assert signature in text

    asyncio.run(run())


def test_create_server_registers_indicator_resource_payload() -> None:
    async def run() -> None:
        server = create_server()
        resources = await server.list_resources()
        assert [str(resource.uri) for resource in resources] == ["trading://indicators"]

        contents = list(await server.read_resource("trading://indicators"))
        assert len(contents) == 1
        payload = json.loads(contents[0].content)

        assert set(payload) == EXPECTED_TOOL_NAMES
        for tool_name, fields in EXPECTED_RESOURCE_FIELDS.items():
            assert payload[tool_name]["fields"] == fields

    asyncio.run(run())
