# Change: Add async httpx backend

## Why
Some users prefer the `httpx` ecosystem for async HTTP. Adding an async httpx backend broadens compatibility and provides an additional high-quality backend option alongside niquests/aiohttp/requests.

## What Changes
- **ADDED** httpx backend implementation (`src/parallel_requests/backends/httpx.py`)
- **ADDED** optional dependency group for `httpx`
- **MODIFIED** backend auto-selection priority to include httpx (niquests → httpx → aiohttp → requests)
- **MODIFIED** docs/examples to include httpx in backend selection guidance
- **ADDED** tests to ensure `HttpxBackend` behavior matches existing backends (normalization, streaming, errors)

## Impact
- Affected specs: `backend-httpx`, `client-api`, `logging-integration`, `documentation`
- Affected code:
  - `src/parallel_requests/backends/httpx.py` (new)
  - `src/parallel_requests/client.py` (backend auto-detection order)
  - `pyproject.toml` (optional dependency)
  - Docs + examples for backend selection updates
  - Tests for httpx backend
- Dependencies: `httpx` (optional; installed via extras)
