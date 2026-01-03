# Change: Add Core Utilities

## Why
The library needs retry logic, rate limiting, and input validation utilities before backends or client can be implemented. These are cross-cutting concerns used by all backends.

## What Changes
- **ADDED** retry strategy with exponential backoff and jitter (`utils/retry.py`)
- **ADDED** rate limiter with token bucket algorithm (`utils/rate_limiter.py`)
- **ADDED** input validators for URLs, proxies, and headers (`utils/validators.py`)
- **REMOVED** pandas dependency (no longer needed)

## Impact
- Affected specs: `retry-policy`, `rate-limiting`, `input-validation`
- Affected code:
  - `src/parallel_requests/utils/retry.py` (new)
  - `src/parallel_requests/utils/rate_limiter.py` (new)
  - `src/parallel_requests/utils/validators.py` (new)
- Dependencies: None (pure Python utilities)
