## ADDED Requirements

### Requirement: Configuration is validated
The system SHALL validate configuration values using pydantic models and reject invalid types or missing required fields.

#### Scenario: Invalid configuration is rejected
- **WHEN** a required configuration field is missing or has the wrong type
- **THEN** a validation error is raised that includes the field name

### Requirement: Configuration supports environment overrides
The system SHALL allow configuration values to be provided via environment variables in addition to explicit instantiation.

#### Scenario: Environment overrides are applied
- **WHEN** an environment variable corresponding to a configuration field is set
- **THEN** the resolved configuration uses the environment value
