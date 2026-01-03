# backend-requests Specification

## Purpose
TBD - created by archiving change add-backends. Update Purpose after archive.
## Requirements
### Requirement: Requests Backend Implementation
The system SHALL provide requests-based HTTP backend for sync users.

#### Scenario: GET request
- **WHEN** `RequestsBackend().request(RequestConfig(url="https://httpbin.org/get", method="GET"))` is called
- **THEN** `NormalizedResponse` is returned with status_code 200

#### Scenario: POST request with JSON
- **WHEN** requests backend processes POST with json body
- **THEN** request is sent with Content-Type application/json

#### Scenario: Async wrapper for sync library
- **WHEN** `RequestsBackend().request()` is called from async context
- **THEN** the blocking requests call is run in `asyncio.to_thread()`

#### Scenario: HTTP/2 not supported
- **WHEN** `RequestsBackend().supports_http2()` is called
- **THEN** `False` is returned

#### Scenario: Streaming response
- **WHEN** `RequestConfig(url="https://example.com/large", stream=True)` is sent
- **THEN** response content can be consumed in chunks via `iter_content()`

### Requirement: Requests Context Manager
The system SHALL support async context manager for requests backend.

#### Scenario: Context manager entry
- **WHEN** `async with RequestsBackend() as backend:` is used
- **THEN** `backend` is the RequestsBackend instance
- **AND** `requests.Session` is created

#### Scenario: Context manager exit
- **WHEN** async context exits
- **THEN** `requests.Session` is closed
- **AND** all connections are cleaned up

### Requirement: Requests Response Normalization
The system SHALL convert requests responses to NormalizedResponse format.

#### Scenario: Response fields populated
- **WHEN** requests response is normalized
- **THEN** `status_code`, `headers`, `content`, `text`, `url` are populated
- **AND** `json_data` is parsed if is_json=True

