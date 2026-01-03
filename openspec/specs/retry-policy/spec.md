# retry-policy Specification

## Purpose
TBD - created by archiving change add-core-utils. Update Purpose after archive.
## Requirements
### Requirement: Exponential Backoff with Jitter
The system SHALL provide retry logic with exponential backoff and configurable jitter.

#### Scenario: Exponential delay calculation
- **GIVEN** `RetryConfig(max_retries=3, backoff_multiplier=1.0, jitter=0.1)`
- **WHEN** retry attempt 2 is made
- **THEN** delay is approximately 2.0 seconds (±0.2s jitter)

#### Scenario: Jitter randomization
- **WHEN** retries are executed with jitter > 0
- **THEN** delays vary between attempts (not deterministic)

#### Scenario: Retry exhaustion
- **GIVEN** `max_retries=2`
- **WHEN** 3 attempts all fail
- **THEN** `RetryExhausted` exception is raised

### Requirement: Configurable Retry Conditions
The system SHALL support configurable retry-on / dont-retry-on exception sets.

#### Scenario: Retry on specific exceptions
- **GIVEN** `RetryConfig(retry_on={ConnectionError, TimeoutError})`
- **WHEN** `ConnectionError` occurs
- **THEN** retry is attempted

#### Scenario: Dont retry on specific exceptions
- **GIVEN** `RetryConfig(dont_retry_on={ValueError})`
- **WHEN** `ValueError` occurs
- **THEN** retry is NOT attempted, exception is raised immediately

### Requirement: Async Retry Execution
The system SHALL execute retry logic asynchronously.

#### Scenario: Async function retry
- **GIVEN** async function that fails twice then succeeds
- **WHEN** `RetryStrategy.execute(func, *args, **kwargs)` is called
- **THEN** function is awaited and result is returned after success

