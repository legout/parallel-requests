# Tasks: Add Logging Infrastructure

## Implementation Tasks

- [ ] 1.1 Create `src/parallel_requests/utils/logging.py` module
  - [ ] Add `configure_logging()` function with loguru setup
  - [ ] Support `debug` and `verbose` parameters
  - [ ] Configure stderr output with appropriate format
  - [ ] Add type hints and docstrings

- [ ] 1.2 Write unit tests for logging configuration
  - [ ] Test default INFO level logging
  - [ ] Test DEBUG level logging with `debug=True`
  - [ ] Test loguru handler removal and reconfiguration
  - [ ] Capture and assert log output

- [ ] 1.3 Update existing proxies.py to use centralized logging (optional)
  - [ ] Consider adding logging configuration call
  - [ ] Ensure backward compatibility with existing loguru usage

- [ ] 1.4 Add logging configuration to client.py (in add-client-api phase)
  - [ ] Call `configure_logging()` in `ParallelRequests.__init__()`
  - [ ] Pass `debug` and `verbose` parameters
  - [ ] Add logging at key points (backend selection, request lifecycle)

## Documentation Tasks

- [ ] 2.1 Update `openspec/project.md` with logging conventions section
- [ ] 2.2 Update `openspec/changes/add-proxy-and-headers/design.md` with loguru reference
- [ ] 2.3 Update `openspec/changes/add-client-api/design.md` with logging decisions
- [ ] 2.4 Create logging usage examples in project documentation

## Integration Tasks

- [ ] 3.1 Ensure loguru dependency is in pyproject.toml (already present)
- [ ] 3.2 Update test fixtures to support log output capture
- [ ] 3.3 Verify no conflicts with existing loguru usage in proxies.py

## Validation Tasks

- [ ] 4.1 Run existing tests to ensure no regressions
- [ ] 4.2 Test debug mode with verbose output
- [ ] 4.3 Test default mode with minimal output
- [ ] 4.4 Verify logging works across all components when client API is implemented
