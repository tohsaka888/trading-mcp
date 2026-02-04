## ADDED Requirements

### Requirement: uv manages dependencies
The project SHALL define runtime and development dependencies in `pyproject.toml` and SHALL provide a lock file managed by uv for reproducible installs.

#### Scenario: Install uses uv lock
- **WHEN** a developer runs `uv sync`
- **THEN** the environment is resolved according to the lock file and installs successfully

### Requirement: Core module layout is stable
The project SHALL expose a stable package layout with importable modules for configuration, data access, indicators, and utilities under the `trading_mcp` package.

#### Scenario: Core modules are importable
- **WHEN** a developer imports `trading_mcp.config`, `trading_mcp.data`, `trading_mcp.indicators`, and `trading_mcp.utils`
- **THEN** each module is importable without errors
