## 1. Dependency Setup

- [x] 1.1 Add runtime dependencies to `pyproject.toml` (pydantic, pydantic-settings, akshare, ta-lib, pandas, numpy)
- [x] 1.2 Add any dev/test dependencies needed for basic validation
- [x] 1.3 Regenerate `uv.lock` to reflect new dependencies

## 2. Package Skeleton

- [x] 2.1 Create package modules `trading_mcp/config`, `trading_mcp/data`, `trading_mcp/indicators`, `trading_mcp/utils` with `__init__.py`
- [x] 2.2 Expose core symbols from `trading_mcp/__init__.py`

## 3. Config Validation

- [x] 3.1 Implement a pydantic settings model with required fields and env overrides
- [x] 3.2 Add a minimal validation example or test that shows invalid input raises an error with field name

## 4. Market Data Access

- [x] 4.1 Define a `MarketDataClient` interface with a fetch method (symbol, date range)
- [x] 4.2 Implement `AkshareMarketDataClient` that returns time-ordered data in a consistent structure
- [x] 4.3 Add basic error handling for akshare failures

## 5. Indicator Engine

- [x] 5.1 Implement an indicator engine wrapper with a supported-indicator registry
- [x] 5.2 Validate inputs and raise a clear error for unsupported indicators
- [x] 5.3 Ensure outputs align to input length and ordering

## 6. Documentation

- [x] 6.1 Document setup steps and TA-Lib system dependency notes
- [x] 6.2 Add a minimal usage example for config, data fetch, and indicator compute
