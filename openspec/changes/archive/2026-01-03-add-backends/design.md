## Context
Backends implement the `Backend` interface defined in add-foundation-contracts. They handle HTTP specifics while client handles orchestration.

## Goals / Non-Goals
- Goals: All backends behave identically from client perspective
- Non-Goals: No client orchestration logic (handled in add-client-api)

## Decisions
- **Decision**: Niquests is primary backend (HTTP/2, modern async)
- **Decision**: Aiohttp is secondary backend (mature, widely used)
- **Decision**: Requests is fallback (sync users, uses asyncio.to_thread())
- **Decision**: Response normalization happens in backend, not client

## Risks / Trade-offs
- **Risk**: Backend-specific behavior differences
  - Mitigation: Shared interface contract, integration tests verify behavior parity
- **Risk**: HTTP/2 not supported by all servers
  - Mitigation: Niquests falls back to HTTP/1.1 automatically

## Open Questions
- None
