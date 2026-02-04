## ADDED Requirements

### Requirement: Indicator engine validates inputs
The system SHALL validate indicator inputs and reject unsupported indicator names.

#### Scenario: Unsupported indicator is rejected
- **WHEN** a caller requests an indicator that is not supported
- **THEN** the system raises a clear error indicating the indicator is unsupported

### Requirement: Indicator computation produces aligned output
The system SHALL compute indicators using TA-Lib and return outputs aligned to the input series length.

#### Scenario: Output aligns to input
- **WHEN** the engine computes an indicator for an input series of length N
- **THEN** the output has length N and preserves input ordering
