# public-api Specification

## Purpose
TBD - created by archiving change add-client-api. Update Purpose after archive.
## Requirements
### Requirement: Public API Exports
The system SHALL export public API in `parallel_requests` package.

#### Scenario: ParallelRequests exported
- **WHEN** `from parallel_requests import ParallelRequests` is executed
- **THEN** `ParallelRequests` is available

#### Scenario: parallel_requests function exported
- **WHEN** `from parallel_requests import parallel_requests` is executed
- **THEN** `parallel_requests` function is available

#### Scenario: parallel_requests_async function exported
- **WHEN** `from parallel_requests import parallel_requests_async` is executed
- **THEN** `parallel_requests_async` function is available

#### Scenario: Exceptions exported
- **WHEN** `from parallel_requests import ParallelRequestsError, RetryExhaustedError` is executed
- **THEN** exception classes are available

### Requirement: Sync Wrapper Function
The system SHALL provide `parallel_requests()` synchronous convenience function.

#### Scenario: Sync call
- **WHEN** `parallel_requests(urls=["https://httpbin.org/get"])` is called
- **THEN** result is returned directly (not await)

#### Scenario: Uses asyncio.run
- **WHEN** `parallel_requests(...)` is called
- **THEN** `asyncio.run()` is used internally

#### Scenario: Parameters passed through
- **WHEN** `parallel_requests(urls=["https://example.com"], concurrency=10, max_retries=2)` is called
- **THEN** parameters are passed to ParallelRequests

### Requirement: Async Wrapper Function
The system SHALL provide `parallel_requests_async()` async convenience function.

#### Scenario: Async call returns coroutine
- **WHEN** `parallel_requests_async(urls=["https://httpbin.org/get"])` is called
- **THEN** coroutine is returned

#### Scenario: Awaited result
- **WHEN** `await parallel_requests_async(urls=["https://httpbin.org/get"])` is called
- **THEN** result is returned

#### Scenario: Context manager internally
- **WHEN** `parallel_requests_async(...)` is called
- **THEN** `ParallelRequests` is used with async context manager

### Requirement: Return Type Handling
The system SHALL return results based on specified return type.

#### Scenario: JSON return type
- **WHEN** `parallel_requests(urls=["https://httpbin.org/json"], return_type="json")` is called
- **THEN** parsed JSON (dict/list) is returned

#### Scenario: TEXT return type
- **WHEN** `parallel_requests(urls=["https://example.com"], return_type="text")` is called
- **THEN** response.text (str) is returned

#### Scenario: CONTENT return type
- **WHEN** `parallel_requests(urls=["https://example.com"], return_type="content")` is called
- **THEN** response.content (bytes) is returned

#### Scenario: RESPONSE return type
- **WHEN** `parallel_requests(urls=["https://example.com"], return_type="response")` is called
- **THEN** NormalizedResponse object is returned

### Requirement: Custom Parse Function
The system SHALL support custom parse function.

#### Scenario: Parse function applied
- **GIVEN** `parse_func=lambda r: r.get("id")`
- **WHEN** `parallel_requests(urls=["https://api.com/1"], parse_func=parse_func)` is called
- **THEN** result is the parsed value (not the full response)

#### Scenario: Parse function with keys
- **GIVEN** `parse_func=lambda r: r.get("id")`
- **WHEN** `parallel_requests(urls=["https://api.com/1", "https://api.com/2"], keys=["a", "b"], parse_func=fn)` is called
- **THEN** `{"a": parsed_a, "b": parsed_b}` is returned

### Requirement: Streaming Support
The system SHALL support streaming for large file downloads.

#### Scenario: Streaming enabled
- **WHEN** `parallel_requests(urls=["https://example.com/large.zip"], stream=True)` is called
- **THEN** response is streamed

#### Scenario: Stream callback
- **GIVEN** `def callback(key, chunk): pass`
- **WHEN** `parallel_requests(urls=["https://example.com"], stream=True, stream_callback=callback)` is called
- **THEN** callback is called for each chunk with key and chunk data

