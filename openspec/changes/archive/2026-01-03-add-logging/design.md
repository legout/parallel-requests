## Context
Logging is a cross-cutting concern needed across all library components. Loguru provides superior features compared to Python's standard logging module: better exception handling, structured logging, and simpler API.

## Goals / Non-Goals
- Goals: Provide consistent, configurable logging across library
- Non-Goals: No custom log handlers beyond basic stderr/stdout output, no external logging service integration

## Decisions
- **Decision**: Use loguru exclusively (not standard logging)
  - Rationale: Already a dependency, superior API, no standard logging exists in codebase
- **Decision**: Default log level is INFO
  - Rationale: Shows important events without overwhelming output
- **Decision**: `debug` parameter enables DEBUG level
  - Rationale: Allows detailed diagnostics when troubleshooting
- **Decision**: `verbose` controls tqdm progress bars, not log level
  - Rationale: Separates concerns - logging vs progress indication
- **Decision**: Graceful degradation for proxies with loguru
  - Rationale: Invalid proxies filtered, logged at DEBUG/INFO level (add-proxy-and-headers)

## Logging Levels and Usage
- **DEBUG**: Detailed diagnostic info (proxy filtering, retry attempts, rate limiting details)
- **INFO**: General informational messages (proxy loading summary, backend selection, request completion)
- **WARNING**: Warning conditions (proxy temporary failure, retry without success)
- **ERROR**: Error conditions (proxy load failure, request failure after retries)
- **CRITICAL**: Critical conditions (no backends available, configuration errors)

## Configuration Behavior
- `debug=False` (default): Loguru level INFO, tqdm hidden
- `debug=True`: Loguru level DEBUG, tqdm shown
- `verbose=True`: Override tqdm visibility (independent of debug)

## Risks / Trade-offs
- **Risk**: Too much debug output
  - Mitigation: DEBUG only enabled via explicit `debug=True` parameter
- **Risk**: Loguru overhead
  - Mitigation: Minimal overhead at INFO level, async-friendly

## Open Questions
- None
