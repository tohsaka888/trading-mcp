## ADDED Requirements

### Requirement: Tool usage prompt
The MCP server SHALL expose a prompt that explains how to use the `kline`, `macd`, `rsi`, and `ma` tools and their required inputs.

#### Scenario: Client requests prompts
- **WHEN** an MCP client requests available prompts
- **THEN** a tool-usage prompt is returned

### Requirement: Resources for discoverability
The MCP server SHALL expose at least one resource that documents tool metadata or indicator definitions.

#### Scenario: Client requests resources
- **WHEN** an MCP client requests available resources
- **THEN** at least one resource describing tools or indicators is returned
