# proxy-rotation Specification

## Purpose
TBD - created by archiving change add-proxy-and-headers. Update Purpose after archive.
## Requirements
### Requirement: Proxy Format Validation
The system SHALL validate proxy formats without crashing on malformed input.

#### Scenario: Valid ip:port proxy
- **WHEN** `ProxyManager.validate("192.168.1.1:8080")` is called
- **THEN** `True` is returned

#### Scenario: Valid proxy with auth
- **WHEN** `ProxyManager.validate("192.168.1.1:8080:user:pass")` is called
- **THEN** `True` is returned

#### Scenario: Valid HTTP proxy URL
- **WHEN** `ProxyManager.validate("http://user:pass@192.168.1.1:8080")` is called
- **THEN** `True` is returned

#### Scenario: Invalid proxy filtered (not crash)
- **WHEN** `ProxyManager.validate("malformed")` is called
- **THEN** `False` is returned (no exception)

### Requirement: Proxy Rotation
The system SHALL provide random proxy rotation from configured list.

#### Scenario: Select random proxy
- **GIVEN** proxy list with 3 proxies
- **WHEN** `get_next()` is called
- **THEN** one of the 3 proxies is returned

#### Scenario: Empty proxy list
- **GIVEN** empty proxy list
- **WHEN** `get_next()` is called
- **THEN** `None` is returned

### Requirement: Webshare.io Integration
The system SHALL load proxies from Webshare.io URL.

#### Scenario: Load from Webshare URL
- **GIVEN** `ProxyConfig(webshare_url="https://proxy.webshare.io/api/proxy.txt")`
- **WHEN** `ProxyManager` is initialized
- **THEN** proxies are loaded from URL
- **AND** format is converted to `http://user:pass@ip:port`

#### Scenario: Webshare load failure doesn't crash
- **GIVEN** invalid Webshare URL
- **WHEN** `ProxyManager` is initialized
- **THEN** `ProxyValidationError` is raised during init (fail-fast)

### Requirement: Free Proxies Opt-In
The system SHALL fetch free proxies only when explicitly enabled.

#### Scenario: Free proxies disabled by default
- **GIVEN** `ProxyConfig(free_proxies=False)`
- **WHEN** `ProxyManager` is initialized
- **THEN** no free proxies are fetched

#### Scenario: Free proxies opt-in
- **GIVEN** `ProxyConfig(free_proxies=True)`
- **WHEN** `ProxyManager` is initialized
- **THEN** free proxies may be added to proxy list

### Requirement: Proxy Failure Tracking
The system SHALL temporarily disable failing proxies.

#### Scenario: Mark proxy as failed
- **WHEN** `mark_failed("192.168.1.1:8080")` is called
- **THEN** proxy is temporarily disabled for retry_delay seconds

#### Scenario: Failed proxy skipped
- **GIVEN** proxy A is marked as failed
- **WHEN** `get_next()` is called
- **THEN** proxy A is not returned

#### Scenario: Failed proxy re-enabled after delay
- **GIVEN** proxy A was marked failed 61 seconds ago with retry_delay=60
- **WHEN** `get_next()` is called
- **THEN** proxy A may be returned again

