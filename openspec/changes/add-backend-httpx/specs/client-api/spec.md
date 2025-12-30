## MODIFIED Requirements

### Requirement: Backend Auto-Selection Priority
The system SHALL select backends in priority order.

#### Scenario: Niquests preferred
- **GIVEN** niquests, httpx, aiohttp, and requests are all installed
- **WHEN** `ParallelRequests(backend="auto")` is called
- **THEN** niquests backend is selected

#### Scenario: Httpx second
- **GIVEN** niquests is NOT installed, httpx, aiohttp, and requests are installed
- **WHEN** `ParallelRequests(backend="auto")` is called
- **THEN** httpx backend is selected

#### Scenario: Aiohttp fallback
- **GIVEN** niquests and httpx are NOT installed, aiohttp and requests are installed
- **WHEN** `ParallelRequests(backend="auto")` is called
- **THEN** aiohttp backend is selected

#### Scenario: Requests last resort
- **GIVEN** only requests is installed
- **WHEN** `ParallelRequests(backend="auto")` is called
- **THEN** requests backend is selected
