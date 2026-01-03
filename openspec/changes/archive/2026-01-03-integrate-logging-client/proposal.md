# Change: Integrate Logging with Client API

## Why
The `add-logging` phase created a centralized logging module (`utils/logging.py`) with `configure_logging()`, but it's not yet integrated with the client API. The `ParallelRequests` class already has `debug` and `verbose` parameters that are stored but never used.

## What Changes
- **UPDATED** `ParallelRequests.__init__()` to call `configure_logging(debug, verbose)`
- **ADDED** logging at key lifecycle points:
  - Backend selection (INFO level)
  - Request completion (INFO level)
  - Retry attempts (DEBUG level)
  - Rate limiting (DEBUG level)

## Impact
- Affected code: `src/parallel_requests/client.py`
- Dependencies: `src/parallel_requests/utils/logging.py` (already exists)
