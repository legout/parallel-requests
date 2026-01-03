# Change: Fix Concurrency Parameter

## Why
The `concurrency` parameter is effectively ignored when `rate_limit=None`. All requests are launched immediately via `asyncio.gather()` without any concurrency gating, causing:
- `concurrency=1` not executing requests sequentially
- `concurrency=100` no faster than `concurrency=1` for small request sets

## What Changes
- **MODIFIED** `ParallelRequests` to always use a concurrency semaphore, not just when `rate_limit` is set
- **REMOVED** `max_concurrency` from `RateLimitConfig` - rate limiter only handles rate (tokens/sec)
- **ADDED** concurrency parameter passing to backend connection pools (aiohttp TCPConnector, httpx Limits)
- **ADDED** debug logging for concurrency semaphore operations

## Impact
- Affected specs: `client-api`
- Affected code:
  - `src/fastreq/client.py` - concurrency semaphore in ParallelRequests
  - `src/fastreq/utils/rate_limiter.py` - remove max_concurrency from RateLimitConfig
  - `src/fastreq/backends/aiohttp.py` - TCPConnector limit
  - `src/fastreq/backends/httpx.py` - max_connections limit
  - `src/fastreq/backends/base.py` - add concurrency parameter to Backend
  - `tests/unit/test_concurrency.py` - new tests for concurrency behavior
