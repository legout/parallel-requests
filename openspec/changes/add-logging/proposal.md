# Change: Add Logging Infrastructure

## Why
The library needs consistent logging across all components for debugging, monitoring, and user feedback. Loguru is already a dependency and is used in proxies.py. We need to standardize logging patterns and provide user-configurable logging via `debug` and `verbose` parameters.

## What Changes
- **ADDED** centralized loguru configuration utilities (`utils/logging.py`)
- **ADDED** logging configuration to client API (add-client-api phase)
- **ADDED** `debug` parameter to enable DEBUG level logging
- **ADDED** `verbose` parameter for progress bar visibility (tqdm)
- **UPDATED** `project.md` with logging conventions
- **UPDATED** add-proxy-and-headers design to reference loguru
- **UPDATED** add-client-api design with logging decisions

## Impact
- Affected specs: `logging-configuration`
- Affected code:
  - `src/parallel_requests/utils/logging.py` (new)
  - `src/parallel_requests/client.py` (updated when add-client-api implemented)
- Dependencies: loguru (>=0.7.0, already in pyproject.toml)
