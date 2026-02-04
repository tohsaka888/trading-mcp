## Context

The project currently has a minimal `main.py`, an Akshare-backed market data client, and a small indicator engine using TA-Lib. There is no MCP server or tool definitions yet. The change introduces an MCP Python SDK server that exposes market/indicator tools with strict request/response schemas and optional prompts/resources.

Constraints:
- Must use MCP Python SDK streamable-http transport and bind to `0.0.0.0`.
- Tools must expose K-line data and indicators (MACD, RSI, MA).
- Requests/responses should be defined with Pydantic models.

## Goals / Non-Goals

**Goals:**
- Stand up an MCP server entrypoint that runs on streamable-http and listens on all interfaces.
- Expose four tools with Pydantic-validated inputs/outputs: K-line, MACD, RSI, MA.
- Reuse existing data and indicator modules where possible.
- Provide prompts/resources that document tool usage where helpful.

**Non-Goals:**
- Full trading workflows, order execution, or portfolio management.
- Advanced indicator customization beyond required parameters.
- UI or client implementation beyond MCP server basics.

## Decisions

- **Server architecture:** Implement an MCP server in `main.py` (or a new module imported by it) using MCP Python SDK streamable-http transport. Host should be configurable but default to `0.0.0.0` to satisfy deployment needs. The implementation will follow the official MCP Python SDK docs for streamable HTTP server setup.
  - Alternatives: stdio transport or local-only bind. Rejected because streamable HTTP and external access are explicit requirements.

- **Tool structure:** Define tools as discrete functions registered with the MCP server. Each tool uses Pydantic input/output models, making validation explicit and simplifying JSON schema generation for MCP.
  - Alternatives: ad-hoc dict validation. Rejected due to weaker typing and inconsistent error messages.

- **Market data source:** Use the existing `AkshareMarketDataClient` for K-line data. Convert its DataFrame output into a normalized list of bars for tool responses.
  - Alternatives: new data provider. Rejected to reduce integration effort and keep dependencies unchanged.

- **Indicator calculations:** Extend `IndicatorEngine` to support MACD and MA (e.g., `talib.MACD`, `talib.SMA`/`EMA` depending on MA type). Indicator tools will fetch K-line data, compute indicator values aligned to the series, and return the latest `limit` or full series as required.
  - Alternatives: implement indicators manually. Rejected due to increased risk and duplication of TA-Lib.

- **Prompts/resources:** Provide lightweight prompt(s) and resource(s) that describe the tool set, inputs, and example usage. These will be static and served by the MCP server when clients request them.
  - Alternatives: no prompts/resources. Rejected because the change explicitly asks to create them if needed.

## Risks / Trade-offs

- **External dependency stability:** Akshare data retrieval can fail or change. → Mitigation: wrap errors with clear messages and add tests that mock client behavior.
- **Indicator library availability:** TA-Lib must be installed and functional. → Mitigation: document dependency and add runtime checks with actionable error messages.
- **Large responses:** K-line and indicator series can be large. → Mitigation: enforce `limit` and cap maximum values at the model level.
- **Transport/security:** Binding to `0.0.0.0` exposes the service. → Mitigation: document that it should run behind a trusted network or reverse proxy.

## Migration Plan

1. Add MCP server entrypoint and tool registration.
2. Add/extend Pydantic models and indicator engine support.
3. Add prompts/resources and update README with usage examples.
4. Add tests for model validation and tool behavior.

Rollback: revert the new server entrypoint and tool modules; no data migrations required.

## Open Questions

- What is the expected symbol format (e.g., Akshare stock symbols) and should we validate it?
- Should `limit` represent number of bars returned or number of recent values per indicator tool?
- Should MA default to SMA or allow MA type selection?
