# input-validation Specification

## Purpose
TBD - created by archiving change add-core-utils. Update Purpose after archive.
## Requirements
### Requirement: URL Validation
The system SHALL validate URL format for requests.

#### Scenario: Valid HTTP URL
- **WHEN** `validate_url("https://example.com/path")` is called
- **THEN** `True` is returned

#### Scenario: Valid URL with query params
- **WHEN** `validate_url("https://example.com?key=value")` is called
- **THEN** `True` is returned

#### Scenario: Invalid URL (no scheme)
- **WHEN** `validate_url("example.com")` is called
- **THEN** `ValidationError` is raised

#### Scenario: Invalid URL (unsupported scheme)
- **WHEN** `validate_url("ftp://example.com")` is called
- **THEN** `ValidationError` is raised

### Requirement: Proxy Format Validation
The system SHALL validate proxy string formats.

#### Scenario: Valid proxy ip:port
- **WHEN** `validate_proxy("192.168.1.1:8080")` is called
- **THEN** `True` is returned

#### Scenario: Valid proxy with authentication
- **WHEN** `validate_proxy("192.168.1.1:8080:user:pass")` is called
- **THEN** `True` is returned

#### Scenario: Valid HTTP proxy URL
- **WHEN** `validate_proxy("http://user:pass@192.168.1.1:8080")` is called
- **THEN** `True` is returned

#### Scenario: Invalid proxy format
- **WHEN** `validate_proxy("invalid")` is called
- **THEN** `False` is returned (not ValidationError - for filtering)

### Requirement: Header Validation
The system SHALL validate header dictionaries.

#### Scenario: Valid headers
- **WHEN** `validate_headers({"User-Agent": "test", "Accept": "application/json"})` is called
- **THEN** `True` is returned

#### Scenario: Invalid header (non-string value)
- **WHEN** `validate_headers({"X-Count": 123})` is called
- **THEN** `ValidationError` is raised

#### Scenario: Invalid header (non-string key)
- **WHEN** `validate_headers({123: "value"})` is called
- **THEN** `ValidationError` is raised

### Requirement: Input Normalization
The system SHALL normalize inputs to consistent types.

#### Scenario: Single URL to list
- **WHEN** `normalize_urls("https://example.com")` is called with single string
- **THEN** `["https://example.com"]` is returned

#### Scenario: List of URLs unchanged
- **WHEN** `normalize_urls(["https://a.com", "https://b.com"])` is called
- **THEN** `["https://a.com", "https://b.com"]` is returned

#### Scenario: None stays None
- **WHEN** `normalize_urls(None)` is called
- **THEN** `None` is returned

