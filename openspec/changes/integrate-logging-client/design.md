## Context
The client API already accepts `debug` and `verbose` parameters but doesn't configure logging. We need to integrate the centralized logging module.

## Decisions
- **Decision**: Call `configure_logging()` in `ParallelRequests.__init__()`
  - Rationale: Ensures logging is configured when client is created
- **Decision**: Log at key lifecycle points
  - Backend selection: INFO - shows which backend was chosen
  - Request completion: INFO - shows URL and status
  - Retry attempts: DEBUG - detailed diagnostics
  - Rate limiting: DEBUG - shows token acquisition

## Implementation Notes
- Import `configure_logging` from `utils.logging`
- Call `configure_logging(self.debug, self.verbose)` in `__init__()`
- Use existing `from loguru import logger` pattern for inline logging
