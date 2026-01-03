## Context
`parallel-requests` uses a strategy pattern to support multiple HTTP backends behind the shared async `Backend` interface. `httpx` provides an `AsyncClient`, which maps cleanly to this interface.

## Goals / Non-Goals
- Goals:
  - Add `HttpxBackend` implementing `Backend`
  - Ensure parity with existing backend behavior (headers/cookies/proxies, streaming, JSON detection)
  - Include httpx in `backend="auto"` selection priority
  - Keep changes minimal and consistent with existing backend modules
- Non-Goals:
  - Reworking retry/rate limiting/client orchestration
  - Adding new public API beyond allowing `backend="httpx"`

## Decisions
- **Decision**: Backend id is `"httpx"` and class name is `HttpxBackend` in `src/parallel_requests/backends/httpx.py`.
- **Decision**: Auto-detection order becomes: `niquests → httpx → aiohttp → requests`.
  - Rationale: user requested httpx to be selected before aiohttp.
- **Decision**: `supports_http2()` reports HTTP/2 capability based on whether httpx is configured to use HTTP/2.
  - Note: httpx HTTP/2 requires extra dependencies (commonly `h2`). The proposal keeps `httpx` as the required optional dependency and documents any additional requirement to enable HTTP/2.

## Risks / Trade-offs
- **Risk**: Adding httpx ahead of aiohttp changes runtime backend choice for users with both installed.
  - Mitigation: Explicit backend selection remains available (`backend="aiohttp"` or `backend="httpx"`).
- **Risk**: httpx proxy/streaming APIs differ across versions.
  - Mitigation: Pin a minimum httpx version and test the supported proxy + streaming paths.

## Migration Plan
1. Add `HttpxBackend` with normalization and streaming support
2. Add `httpx` optional dependency
3. Update backend auto-selection order and logging messages
4. Update docs/examples to reflect the new backend and order
5. Validate with `openspec validate add-backend-httpx --strict`

## Open Questions
- Should `all` extras include httpx (recommended), or should users opt in explicitly via `[httpx]`?
