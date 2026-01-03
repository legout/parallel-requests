## MODIFIED Requirements
### Requirement: Concurrency Control
The system SHALL limit concurrent HTTP requests to the configured `concurrency` value.

#### Scenario: Sequential execution with concurrency of 1
- **GIVEN** `ParallelRequests(concurrency=1)` is configured
- **AND** 3 URLs are requested with delays of 1s, 2s, and 3s
- **WHEN** the requests are executed
- **THEN** the total execution time is approximately 6 seconds (1+2+3)
- **AND** requests are executed one at a time

#### Scenario: Parallel execution with concurrency of 3
- **GIVEN** `ParallelRequests(concurrency=3)` is configured
- **AND** 3 URLs are requested with delays of 1s, 2s, and 3s
- **WHEN** the requests are executed
- **THEN** the total execution time is approximately 3 seconds (max of delays)
- **AND** all 3 requests run concurrently

#### Scenario: High concurrency exceeds individual request times
- **GIVEN** `ParallelRequests(concurrency=100)` is configured
- **AND** 20 URLs are requested, each with a 1-second delay
- **WHEN** the requests are executed
- **THEN** the total execution time is approximately 1-2 seconds (limited by network overhead)
- **AND** requests are not rate-limited by the concurrency setting

### Requirement: Concurrency is Independent of Rate Limiting
The `concurrency` parameter SHALL control concurrent request limits regardless of whether `rate_limit` is configured.

#### Scenario: Concurrency works without rate limit
- **GIVEN** `ParallelRequests(concurrency=2, rate_limit=None)` is configured
- **AND** 4 URLs are requested
- **WHEN** the requests are executed
- **THEN** no more than 2 requests run concurrently at any time
- **AND** the behavior matches when `rate_limit` is explicitly set

#### Scenario: Concurrency and rate limit both active
- **GIVEN** `ParallelRequests(concurrency=2, rate_limit=5)` is configured
- **AND** 4 URLs are requested
- **WHEN** the requests are executed
- **THEN** no more than 2 requests run concurrently (concurrency limit)
- **AND** requests are also rate-limited to 5 per second
