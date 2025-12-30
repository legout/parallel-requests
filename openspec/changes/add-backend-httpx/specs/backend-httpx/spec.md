## ADDED Requirements

### Requirement: Httpx Backend Implementation
The system SHALL provide httpx-based async HTTP backend.

#### Scenario: GET request
- **WHEN** `HttpxBackend().request(RequestConfig(url="https://httpbin.org/get", method="GET"))` is called
- **THEN** `NormalizedResponse` is returned with status_code 200
- **AND** `json_data` contains parsed JSON if response is JSON

#### Scenario: POST request with JSON
- **WHEN** httpx backend processes POST with json body
- **THEN** request is sent with Content-Type application/json
- **AND** body is serialized correctly

#### Scenario: HTTP/2 capability query
- **WHEN** `HttpxBackend().supports_http2()` is called
- **THEN** `True` is returned if httpx is configured with HTTP/2 support
- **AND** `False` is returned otherwise

#### Scenario: Streaming response
- **WHEN** `RequestConfig(url="https://example.com/large", stream=True)` is sent
- **THEN** response content can be consumed without eagerly loading the full response body

### Requirement: Httpx Context Manager
The system SHALL support async context manager for httpx backend.

#### Scenario: Context manager entry
- **WHEN** `async with HttpxBackend() as backend:` is used
- **THEN** `backend` is the HttpxBackend instance

#### Scenario: Context manager exit
- **WHEN** async context exits
- **THEN** `close()` is called automatically
- **AND** client resources are cleaned up

### Requirement: Httpx Response Normalization
The system SHALL convert httpx responses to NormalizedResponse format.

#### Scenario: Response fields populated
- **WHEN** httpx response is normalized
- **THEN** `status_code`, `headers`, `content`, `text`, `url` are populated
- **AND** `json_data` is parsed if is_json=True
