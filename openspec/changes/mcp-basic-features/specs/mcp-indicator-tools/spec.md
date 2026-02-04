## ADDED Requirements

### Requirement: Tool registration
The MCP server SHALL register four tools: `kline`, `macd`, `rsi`, and `ma`.

#### Scenario: Tools appear in tool list
- **WHEN** an MCP client requests the tool list
- **THEN** the response includes `kline`, `macd`, `rsi`, and `ma`

### Requirement: K-line tool input
The `kline` tool SHALL accept input with `symbol` (string) and `limit` (positive integer) and SHALL reject non-positive limits.

#### Scenario: Valid kline request
- **WHEN** a client calls `kline` with a symbol and a positive limit
- **THEN** the server accepts the request

#### Scenario: Invalid kline limit
- **WHEN** a client calls `kline` with a limit less than 1
- **THEN** the server responds with a validation error

### Requirement: K-line tool output
The `kline` tool SHALL return an ordered list of bars where each bar includes date/time plus OHLCV fields.

#### Scenario: Kline response shape
- **WHEN** `kline` returns data
- **THEN** each bar includes `timestamp`, `open`, `high`, `low`, `close`, and `volume`

### Requirement: Indicator tool input
The `macd`, `rsi`, and `ma` tools SHALL accept input with `symbol` (string) and `limit` (positive integer) and SHALL reject non-positive limits.

#### Scenario: Valid indicator request
- **WHEN** a client calls an indicator tool with a symbol and positive limit
- **THEN** the server accepts the request

#### Scenario: Invalid indicator limit
- **WHEN** a client calls an indicator tool with a limit less than 1
- **THEN** the server responds with a validation error

### Requirement: RSI tool output
The `rsi` tool SHALL return an ordered list of values aligned to the symbol's time series.

#### Scenario: RSI response shape
- **WHEN** `rsi` returns data
- **THEN** each item includes `timestamp` and `rsi`

### Requirement: MA tool output
The `ma` tool SHALL return an ordered list of values aligned to the symbol's time series.

#### Scenario: MA response shape
- **WHEN** `ma` returns data
- **THEN** each item includes `timestamp` and `ma`

### Requirement: MACD tool output
The `macd` tool SHALL return an ordered list of values aligned to the symbol's time series, including MACD line, signal line, and histogram.

#### Scenario: MACD response shape
- **WHEN** `macd` returns data
- **THEN** each item includes `timestamp`, `macd`, `signal`, and `histogram`
