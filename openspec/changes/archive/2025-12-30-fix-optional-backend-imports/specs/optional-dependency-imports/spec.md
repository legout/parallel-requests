## ADDED Requirements

### Requirement: Importing Package Without Optional Dependencies
The system SHALL allow importing `parallel_requests` without requiring any optional backend dependencies.

#### Scenario: Import core package without aiohttp
- **GIVEN** `aiohttp` is not installed
- **WHEN** `import parallel_requests` is executed
- **THEN** the import succeeds

#### Scenario: Import backends package without aiohttp
- **GIVEN** `aiohttp` is not installed
- **WHEN** `import parallel_requests.backends` is executed
- **THEN** the import succeeds

### Requirement: Lazy Backend Implementation Imports
The system SHALL NOT import optional backend implementation modules unless the corresponding backend is selected or referenced.

#### Scenario: Auto-select niquests does not import aiohttp
- **GIVEN** `niquests` is installed
- **AND** `aiohttp` is not installed
- **WHEN** `ParallelRequests(backend="auto")` is instantiated
- **THEN** the selected backend is `niquests`
- **AND** no import of `aiohttp` occurs

#### Scenario: Explicit niquests does not import aiohttp
- **GIVEN** `niquests` is installed
- **AND** `aiohttp` is not installed
- **WHEN** `ParallelRequests(backend="niquests")` is instantiated
- **THEN** no import of `aiohttp` occurs

#### Scenario: Importing missing backend raises only on access
- **GIVEN** `aiohttp` is not installed
- **WHEN** `from parallel_requests.backends import AiohttpBackend` is executed
- **THEN** `ImportError` is raised
- **AND** the error message indicates `aiohttp` must be installed to use the aiohttp backend
