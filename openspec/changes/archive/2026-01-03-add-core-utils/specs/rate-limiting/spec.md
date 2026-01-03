## ADDED Requirements

### Requirement: Token Bucket Algorithm
The system SHALL implement token bucket rate limiting algorithm.

#### Scenario: Token refill
- **GIVEN** `TokenBucket(requests_per_second=10, burst=5)`
- **WHEN** 1 second elapses with no acquisitions
- **THEN** approximately 10 tokens are added (capped at burst=5)

#### Scenario: Token acquisition
- **GIVEN** bucket with 3 tokens available
- **WHEN** `acquire(tokens=2)` is called
- **THEN** 1 token remains
- **AND** returned wait time is 0

#### Scenario: Wait for tokens
- **GIVEN** bucket with 0 tokens and rate=10 RPS
- **WHEN** `acquire(tokens=1)` is called
- **THEN** asyncio.sleep is awaited for approximately 0.1 seconds
- **AND** token count becomes 0 after acquisition

### Requirement: Async Rate Limiter with Semaphore
The system SHALL combine token bucket with semaphore for concurrent access control.

#### Scenario: Semaphore limits concurrency
- **GIVEN** `AsyncRateLimiter(max_concurrency=5)`
- **WHEN** 10 coroutines try to acquire simultaneously
- **THEN** only 5 proceed at a time

#### Scenario: Rate and concurrency combined
- **GIVEN** `AsyncRateLimiter(requests_per_second=10, burst=5, max_concurrency=20)`
- **WHEN** many concurrent requests are made
- **THEN** rate limit is respected
- **AND** concurrency limit is respected

### Requirement: Available Tokens Query
The system SHALL provide way to check available tokens.

#### Scenario: Query available tokens
- **GIVEN** bucket with 3 tokens
- **WHEN** `available()` is called
- **THEN** `3` is returned
