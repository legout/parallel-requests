# backend-aiohttp Specification

## Purpose
TBD - created by archiving change add-backends. Update Purpose after archive.
## Requirements
### Requirement: Aiohttp Backend Implementation
The system SHALL provide aiohttp-based HTTP backend.

#### Scenario: GET request
- **WHEN** `AiohttpBackend().request(RequestConfig(url="https://httpbin.org/get", method="GET"))` is called
- **THEN** `NormalizedResponse` is returned with status_code 200

#### Scenario: POST request with data
- **WHEN** aiohttp backend processes POST with data body
- **THEN** request is sent with correct body

#### Scenario: HTTP/2 support via connector
- **WHEN** `AiohttpBackend()` is configured for HTTP/2
- **AND** server supports HTTP/2
- **THEN** HTTP/2 connection is used

#### Scenario: HTTP/2 capability query
- **WHEN** `AiohttpBackend().supports_http2()` is called
- **THEN** `True` is returned (if configured) or `False` (if not)

#### Scenario: Streaming response
- **WHEN** `RequestConfig(url="https://example.com/large", stream=True)` is sent
- **THEN** response content can be consumed in chunks

### Requirement: Aiohttp Context Manager
The system SHALL support async context manager for aiohttp backend.

#### Scenario: Context manager entry
- **WHEN** `async with AiohttpBackend() as backend:` is used
- **THEN** `backend` is the AiohttpBackend instance
- **AND** `ClientSession` is created

#### Scenario: Context manager exit
- **WHEN** async context exits
- **THEN** `ClientSession` is closed properly
- **AND** `TCPConnector` is closed

### Requirement: Aiohttp Response Normalization
The system SHALL convert aiohttp responses to NormalizedResponse format.

#### Scenario: Response fields populated
- **WHEN** aiohttp response is normalized
- **THEN** `status_code`, `headers`, `content`, `text`, `url` are populated
- **AND** `json_data` is parsed if is_json=True

