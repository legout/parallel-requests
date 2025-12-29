## ADDED Requirements

### Requirement: Backend Interface Contract
The system SHALL provide an abstract `Backend` base class that all HTTP backend implementations MUST follow.

#### Scenario: Abstract request method
- **WHEN** a class implements `Backend`
- **THEN** it MUST define `async def request(self, config: RequestConfig) -> NormalizedResponse`

#### Scenario: Context manager support
- **WHEN** a class implements `Backend`
- **THEN** it MUST define `async def __aenter__(self)` returning `Backend`
- **AND** `async def __aexit__(self, *args)`

#### Scenario: Close method
- **WHEN** a class implements `Backend`
- **THEN** it MUST define `async def close(self)` for resource cleanup

### Requirement: HTTP/2 Capability Query
The system SHALL provide `supports_http2()` method to query backend HTTP/2 capability.

#### Scenario: Niquests supports HTTP/2
- **WHEN** `niquests.Backend().supports_http2()` is called
- **THEN** `True` is returned

#### Scenario: Requests does not support HTTP/2
- **WHEN** `requests.Backend().supports_http2()` is called
- **THEN** `False` is returned

### Requirement: Normalized Response Contract
The system SHALL normalize backend-specific responses into a consistent `NormalizedResponse` format.

#### Scenario: NormalizedResponse fields
- **WHEN** `NormalizedResponse` is instantiated
- **THEN** it has fields: `status_code`, `headers`, `content`, `text`, `json_data`, `url`

#### Scenario: JSON parsing on normalization
- **WHEN** `NormalizedResponse.from_backend(response, is_json=True)` is called with JSON response
- **THEN** `json_data` contains parsed JSON
- **AND** `text` contains raw text
- **AND** `content` contains raw bytes

### Requirement: Request Config Contract
The system SHALL use `RequestConfig` dataclass for normalized request parameters.

#### Scenario: RequestConfig fields
- **WHEN** `RequestConfig` is instantiated
- **THEN** it has fields: `url`, `method`, `params`, `data`, `json`, `headers`, `cookies`, `timeout`, `proxy`, `http2`, `stream`
