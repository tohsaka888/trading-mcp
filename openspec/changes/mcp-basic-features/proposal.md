## Why

The project needs a minimal MCP server that can be deployed and used immediately for market/indicator queries. Enabling streamable HTTP on all interfaces and defining core tools with strict types makes the server usable in real environments now.

## What Changes

- Add an MCP server entrypoint that listens on 0.0.0.0 using streamable-http transport.
- Define tools for K-line data and indicator queries (MACD, RSI, MA) with typed inputs/outputs.
- Provide prompts/resources as needed for discoverability and tool guidance.
- Introduce Pydantic models to enforce request/response schemas used by tools.

## Capabilities

### New Capabilities
- `mcp-streamable-http-server`: MCP server configured for streamable-http transport on 0.0.0.0.
- `mcp-indicator-tools`: Tool set for K-line, MACD, RSI, and MA queries with typed schemas.
- `mcp-prompts-resources`: Prompt/resource definitions to document and support tool usage.

### Modified Capabilities
- (none)

## Impact

- `main.py` server startup/transport configuration.
- `models/` for new Pydantic schemas.
- Tool implementation modules (likely under `data/`, `indicators/`, or new `tools/`).
- `README.md` for usage and tool examples.
- `tests/` for schema/tool behavior coverage.
