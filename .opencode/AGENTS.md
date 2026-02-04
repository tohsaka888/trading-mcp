# Agents Guide

## Project Goal
Build a stock trading quantitative MCP with:
- Markets: CN/US/HK/ETF
- K-line by symbol
- Indicators: MACD, RSI, MA5/10/30
- Output: JSON
- Timezone: Asia/Shanghai

## Architecture Summary
- MCP Server: tool interface layer
- Data Source: AKShare adapters per market
- Normalization: unified kline schema
- Indicators: TA-Lib wrappers
- Cache: optional (memory/disk)

## Data Schema (Normalized K-line)
{
  "ts": "YYYY-MM-DD HH:mm:ss",
  "open": float,
  "high": float,
  "low": float,
  "close": float,
  "volume": float
}

## Tool Interfaces
1) get_kline
- Inputs: market, symbol, interval, start, end
- Output: list[Kline]

2) calc_indicators
- Inputs: kline, indicators
- Output: list[IndicatorRow] (aligned with kline)

## Market Mapping (AKShare)
- CN: stock_zh_a_hist / stock_zh_a_hist_min_em
- US: stock_us_hist / stock_us_hist_min_em
- HK: stock_hk_hist
- ETF: fund_etf_hist_em

## Timezone Rule
- All timestamps normalized to Asia/Shanghai before output

## Output Rule
- Always JSON list, no DataFrame in tool outputs

## Error Handling
- Validate inputs
- Retry AKShare failures
- Return empty list on no data

## Suggested Next Steps for Agents
1) Create folder structure
2) Implement AKShare adapters
3) Implement normalization helpers (tz, schema)
4) Implement indicators (TA-Lib)
5) Wire MCP tools
6) Add tests for each market + indicator
