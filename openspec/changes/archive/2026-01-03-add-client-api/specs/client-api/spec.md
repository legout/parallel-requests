## ADDED Requirements

### Requirement: ParallelRequests Initialization
The system SHALL provide `ParallelRequests` class with sensible defaults.

#### Scenario: Default initialization
- **WHEN** `ParallelRequests()` is instantiated with no arguments
- **THEN** `concurrency` defaults to 20
- **AND** `max_retries` defaults to 3
- **AND** `rate_limit` defaults to None (no limit)
- **AND** `random_user_agent` defaults to True
- **AND** `random_proxy` defaults to False
- **AND** `http2` defaults to True
- **AND** `backend` defaults to "auto"

#### Scenario: Custom initialization
- **WHEN** `ParallelRequests(concurrency=50, max_retries=5, rate_limit=10)` is called
- **THEN** respective attributes are set

#### Scenario: Backend auto-selection
- **WHEN** `ParallelRequests(backend="auto")` is called
- **AND** niquests is installed
- **THEN** niquests backend is selected
- **AND** `self._backend.name` equals "niquests"

#### Scenario: No backend available raises error
- **WHEN** `ParallelRequests(backend="niquests")` is called
- **AND** niquests is not installed
- **THEN** `ImportError` is raised

### Requirement: Backend Auto-Selection Priority
The system SHALL select backends in priority order.

#### Scenario: Niquests preferred
- **GIVEN** niquests, aiohttp, and requests are all installed
- **WHEN** `ParallelRequests(backend="auto")` is called
- **THEN** niquests backend is selected

#### Scenario: Aiohttp fallback
- **GIVEN** niquests is NOT installed, aiohttp and requests are installed
- **WHEN** `ParallelRequests(backend="auto")` is called
- **THEN** aiohttp backend is selected

#### Scenario: Requests last resort
- **GIVEN** only requests is installed
- **WHEN** `ParallelRequests(backend="auto")` is called
- **THEN** requests backend is selected

### Requirement: Request Method
The system SHALL make parallel HTTP requests via `request()` method.

#### Scenario: Single URL request
- **WHEN** `await pr.request(urls="https://httpbin.org/get")` is called
- **THEN** single result is returned (not dict)

#### Scenario: Multiple URL request
- **WHEN** `await pr.request(urls=["https://a.com", "https://b.com"])` is called
- **THEN** list of 2 results is returned

#### Scenario: Key mapping
- **WHEN** `await pr.request(urls=["https://a.com", "https://b.com"], keys=["first", "second"])` is called
- **THEN** dict with keys "first" and "second" is returned

### Requirement: Request Method Parameters
The system SHALL support all standard HTTP request parameters.

#### Scenario: POST with JSON
- **WHEN** `pr.request(urls=["https://api.com"], method="POST", json={"key": "value"})` is called
- **THEN** POST request is sent with JSON body

#### Scenario: Query parameters
- **WHEN** `pr.request(urls=["https://api.com"], params={"page": 1})` is called
- **THEN** request includes query string ?page=1

#### Scenario: Custom headers
- **WHEN** `pr.request(urls=["https://api.com"], headers={"Authorization": "Bearer token"})` is called
- **THEN** request includes Authorization header

### Requirement: Per-Attempt Timeout
The system SHALL apply timeout to each retry attempt separately.

#### Scenario: Timeout per attempt
- **GIVEN** `ParallelRequests(timeout=5, max_retries=3)`
- **WHEN** first request times out after 5s
- **AND** retry is attempted
- **THEN** second attempt also has 5s timeout

#### Scenario: Total time can exceed timeout
- **GIVEN** `timeout=5`, `max_retries=2`, server delays 8s each attempt
- **WHEN** request is made
- **THEN** total time is approximately 16s (not capped at 5s)

### Requirement: Shared Session Cookies
The system SHALL share cookies across requests in a session.

#### Scenario: Cookies set on client
- **WHEN** `ParallelRequests(cookies={"session": "abc123"})` is called
- **AND** `pr.request(urls=["https://a.com", "https://b.com"])` is called
- **THEN** both requests include session cookie

#### Scenario: Cookie reset
- **WHEN** `pr.reset_cookies()` is called
- **AND** `pr.request(urls=["https://a.com"])` is called
- **THEN** no cookies are sent

### Requirement: Redirect Following
The system SHALL follow redirects by default.

#### Scenario: Redirect followed
- **GIVEN** URL redirects from http to https
- **WHEN** `pr.request(urls=["http://example.com"])` is called
- **THEN** final response is from https://example.com
- **AND** status_code is 200 (not 301/302)

#### Scenario: Disable redirects
- **WHEN** `pr.request(urls=["http://example.com"], follow_redirects=False)` is called
- **THEN** response has status_code 301 or 302

### Requirement: SSL Verification
The system SHALL verify SSL certificates by default.

#### Scenario: SSL verify enabled by default
- **WHEN** `pr.request(urls=["https://example.com"])` is called
- **THEN** SSL certificate is verified

#### Scenario: Disable SSL verification
- **WHEN** `pr.request(urls=["https://example.com"], verify_ssl=False)` is called
- **THEN** SSL verification is skipped (insecure, but allowed)

### Requirement: Context Manager Support
The system SHALL support async context manager for session reuse.

#### Scenario: Context manager entry
- **WHEN** `async with ParallelRequests() as pr:` is used
- **THEN** `pr` is the ParallelRequests instance
- **AND** backend is initialized

#### Scenario: Context manager exit
- **WHEN** async context exits
- **THEN** `close()` is called
- **AND** all resources are cleaned up

#### Scenario: Reuse session in context
- **WHEN** `async with ParallelRequests() as pr:` is used
- **AND** multiple `pr.request()` calls are made
- **THEN** same backend session is reused
