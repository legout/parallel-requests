## ADDED Requirements

### Requirement: Niquests Backend Implementation
The system SHALL provide niquests-based HTTP backend with HTTP/2 support.

#### Scenario: GET request
- **WHEN** `NiquestsBackend().request(RequestConfig(url="https://httpbin.org/get", method="GET"))` is called
- **THEN** `NormalizedResponse` is returned with status_code 200
- **AND** `json_data` contains parsed JSON if response is JSON

#### Scenario: POST request with JSON
- **WHEN** niquests backend processes POST with json body
- **THEN** request is sent with Content-Type application/json
- **AND** body is serialized correctly

#### Scenario: HTTP/2 enabled by default
- **WHEN** `NiquestsBackend()` is created
- **AND** `request()` is called
- **THEN** HTTP/2 is attempted (niquests auto-negotiates)

#### Scenario: HTTP/2 capability query
- **WHEN** `NiquestsBackend().supports_http2()` is called
- **THEN** `True` is returned

#### Scenario: Streaming response
- **WHEN** `RequestConfig(url="https://example.com/large", stream=True)` is sent
- **THEN** response content can be consumed in chunks

### Requirement: Niquests Context Manager
The system SHALL support async context manager for niquests backend.

#### Scenario: Context manager entry
- **WHEN** `async with NiquestsBackend() as backend:` is used
- **THEN** `backend` is the NiquestsBackend instance

#### Scenario: Context manager exit
- **WHEN** async context exits
- **THEN** `close()` is called automatically
- **AND** session is cleaned up

### Requirement: Niquests Response Normalization
The system SHALL convert niquests responses to NormalizedResponse format.

#### Scenario: Response fields populated
- **WHEN** niquests response is normalized
- **THEN** `status_code`, `headers`, `content`, `text`, `url` are populated
- **AND** `json_data` is parsed if is_json=True
