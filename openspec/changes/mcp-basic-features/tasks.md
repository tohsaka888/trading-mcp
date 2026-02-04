## 1. Discovery & Setup

- [x] 1.1 Review MCP Python SDK docs for streamable-http server setup and tool registration
- [x] 1.2 Identify existing Akshare and indicator utilities to reuse (data client, indicator engine)

## 2. Schemas & Models

- [x] 2.1 Add Pydantic input models for `kline`, `macd`, `rsi`, and `ma` tools (symbol, limit, optional params)
- [x] 2.2 Add Pydantic output models for kline bars and indicator series values
- [x] 2.3 Add validation rules for positive `limit` and any defaults

## 3. Data & Indicator Logic

- [x] 3.1 Extend indicator engine to support MACD and MA computation
- [x] 3.2 Implement kline fetcher that normalizes Akshare frames into ordered OHLCV bars
- [x] 3.3 Implement indicator computation helpers that align outputs to timestamps and respect `limit`

## 4. MCP Server & Tools

- [x] 4.1 Implement MCP server entrypoint with streamable-http transport and default host `0.0.0.0`
- [x] 4.2 Register `kline`, `macd`, `rsi`, and `ma` tools with typed schemas
- [x] 4.3 Add prompts/resources describing tools and indicator metadata

## 5. Documentation & Tests

- [x] 5.1 Update README with server start instructions and tool examples
- [x] 5.2 Add tests for model validation and tool outputs (mock Akshare client)
