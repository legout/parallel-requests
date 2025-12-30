## MODIFIED Requirements

### Requirement: Backend Selection Logging
The system SHALL log backend selection at INFO level.

#### Scenario: Backend selected
- **GIVEN** niquests backend is available
- **WHEN** `ParallelRequests()` is instantiated
- **THEN** INFO message logged: "Selected backend: niquests"

#### Scenario: Fallback backend selected (httpx)
- **GIVEN** niquests is not available, httpx is available
- **WHEN** `ParallelRequests()` is instantiated
- **THEN** INFO message logged: "Selected backend: httpx (niquests unavailable)"

#### Scenario: Fallback backend selected (aiohttp)
- **GIVEN** niquests and httpx are not available, aiohttp is available
- **WHEN** `ParallelRequests()` is instantiated
- **THEN** INFO message logged: "Selected backend: aiohttp (niquests/httpx unavailable)"
