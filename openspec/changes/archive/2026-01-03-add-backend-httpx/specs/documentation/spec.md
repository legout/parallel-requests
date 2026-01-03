## ADDED Requirements

### Requirement: Documentation Includes Httpx Backend
The documentation SHALL describe the httpx backend and how to select it.

#### Scenario: Backend selection guide mentions httpx
- **WHEN** user reads `how-to-guides/select-backend.md`
- **THEN** user understands when to use backend="httpx"
- **AND** user understands auto-detection order: niquests → httpx → aiohttp → requests

#### Scenario: Backends explanation includes httpx
- **WHEN** user reads `explanation/backends.md`
- **THEN** user can compare niquests/aiohttp/httpx/requests differences
- **AND** user understands HTTP/2 support expectations per backend
