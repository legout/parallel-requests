# error-handling Specification

## Purpose
TBD - created by archiving change add-foundation-contracts. Update Purpose after archive.
## Requirements
### Requirement: Exception Hierarchy
The system SHALL provide a base exception class `ParallelRequestsError` with specific subclasses for different error categories.

#### Scenario: Base exception instantiation
- **WHEN** `ParallelRequestsError("connection failed")` is instantiated
- **THEN** `str(e)` returns `"connection failed"`
- **AND** `isinstance(e, Exception)` is `True`

#### Scenario: Specific exception categories
- **WHEN** `BackendError("niquests unavailable")` is instantiated
- **THEN** `isinstance(e, ParallelRequestsError)` is `True`
- **AND** `isinstance(e, BackendError)` is `True`

### Requirement: Retry Exhausted Error
The system SHALL provide `RetryExhaustedError` that captures attempt count, last error, and failed URL.

#### Scenario: RetryExhaustedError attributes
- **WHEN** `RetryExhaustedError("failed after 3 attempts", attempts=3, last_error=TimeoutError(), url="https://example.com")` is instantiated
- **THEN** `e.attempts` equals `3`
- **AND** `e.last_error` is the original `TimeoutError` instance
- **AND** `e.url` equals `"https://example.com"`

### Requirement: Partial Failure Tracking
The system SHALL provide `PartialFailureError` that tracks which requests failed while others succeeded.

#### Scenario: Partial failure aggregates failures
- **WHEN** `PartialFailureError("partial failure", failures={"a": FailureDetails(...), "b": FailureDetails(...)}, successes=8, total=10)` is instantiated
- **THEN** `e.successes` equals `8`
- **AND** `e.total` equals `10`
- **AND** `e.get_failed_urls()` returns list of failed URLs

### Requirement: Default Exception Behavior
The system SHALL raise exceptions by default, with opt-in `return_none_on_failure` mode for backward compatibility.

#### Scenario: Default raises exception
- **WHEN** a request fails and `return_none_on_failure` is `False` (default)
- **THEN** an appropriate exception is raised

#### Scenario: Opt-in returns None
- **WHEN** a request fails and `return_none_on_failure` is `True`
- **THEN** `None` is returned instead of raising

