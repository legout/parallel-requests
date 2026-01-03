# Change: Add Foundation Contracts

## Why
The library currently lacks a defined exception taxonomy, configuration system, and backend interface contract. This leads to silent failures, inconsistent error handling, and no clear abstraction for multiple HTTP backends.

## What Changes
- **ADDED** exception hierarchy (`ParallelRequestsError` base class + specific subclasses)
- **ADDED** backend interface contract (`Backend` abstract base class)
- **ADDED** configuration system (`GlobalConfig` with env var support)
- **ADDED** default behavior: exceptions raised by default, free proxies disabled by default, HTTP/2 enabled by default, user agent rotation enabled by default

## Impact
- Affected specs: `error-handling`, `backend-contract`, `configuration`
- Affected code:
  - `src/parallel_requests/exceptions.py` (new)
  - `src/parallel_requests/backends/base.py` (new)
  - `src/parallel_requests/config.py` (new)
- Dependencies: None (pure Python)
