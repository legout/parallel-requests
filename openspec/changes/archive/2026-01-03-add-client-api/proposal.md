# Change: Add Main Client API

## Why
The library needs a main `ParallelRequests` class and public API exports. This is the user-facing layer that orchestrates backends, applies retry/rate limiting, and returns results.

## What Changes
- **ADDED** `ParallelRequests` class with all features (concurrency, retries, rate limiting, proxies, headers)
- **ADDED** `parallel_requests()` sync wrapper
- **ADDED** `parallel_requests_async()` async wrapper
- **ADDED** `ReturnType` enum and `RequestOptions` dataclass
- **ADDED** public API exports in `__init__.py`
- **ADDED** timeout per-attempt semantics, shared session cookies, redirect following, SSL verify by default

## Impact
- Affected specs: `client-api`, `public-api`
- Affected code:
  - `src/parallel_requests/client.py` (new)
  - `src/parallel_requests/__init__.py` (updated)
- Dependencies: All previous phases (foundation, utils, proxies, backends)
