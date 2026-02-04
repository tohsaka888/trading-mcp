## ADDED Requirements

### Requirement: Streamable HTTP transport
The MCP server SHALL use the MCP Python SDK streamable-http transport for all client connections.

#### Scenario: Server starts with streamable-http
- **WHEN** the server process starts
- **THEN** the MCP transport is streamable-http and accepts HTTP streaming requests

### Requirement: Bind to all interfaces
The MCP server SHALL bind to host `0.0.0.0` by default and SHALL allow the host and port to be configured.

#### Scenario: Default host binding
- **WHEN** the server starts without an explicit host override
- **THEN** it binds to `0.0.0.0`

#### Scenario: Configurable host and port
- **WHEN** a host or port is configured
- **THEN** the server binds to the configured host and port
