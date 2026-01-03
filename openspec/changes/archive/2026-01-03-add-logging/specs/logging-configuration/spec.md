## ADDED Requirements

### Requirement: Loguru Configuration
The system SHALL provide centralized loguru configuration for the library.

#### Scenario: Default configuration INFO level
- **WHEN** `configure_logging(debug=False)` is called
- **THEN** loguru is configured with INFO level
- **AND** output goes to stderr
- **AND** format includes timestamp, level, and message

#### Scenario: DEBUG level configuration
- **WHEN** `configure_logging(debug=True)` is called
- **THEN** loguru is configured with DEBUG level
- **AND** all debug messages are visible

#### Scenario: Verbose mode independent
- **WHEN** `configure_logging(debug=False, verbose=True)` is called
- **THEN** loguru level remains INFO
- **AND** verbose flag is stored for tqdm configuration

#### Scenario: Multiple configuration calls
- **GIVEN** loguru already configured
- **WHEN** `configure_logging()` is called again
- **THEN** existing handlers are removed
- **AND** new configuration is applied
- **AND** no duplicate handlers exist

### Requirement: Logging in Proxy Manager
The system SHALL log proxy-related events using loguru.

#### Scenario: Invalid proxy filtered
- **GIVEN** proxy list contains "invalid_proxy"
- **WHEN** ProxyManager validates proxies
- **THEN** DEBUG message logged: "Filtered invalid proxy format: invalid_proxy..."

#### Scenario: Proxies loaded successfully
- **GIVEN** proxy configuration with 10 valid proxies
- **WHEN** ProxyManager is initialized
- **THEN** INFO message logged: "Loaded 10 valid proxies, filtered 0 invalid proxies"

#### Scenario: Mixed proxy validation
- **GIVEN** proxy list with 5 valid, 2 invalid proxies
- **WHEN** ProxyManager is initialized
- **THEN** INFO message logged: "Loaded 5 valid proxies, filtered 2 invalid proxies"

### Requirement: Logging in Client API (Future)
The system SHALL log client lifecycle and request events using loguru.

#### Scenario: Backend selection logged
- **GIVEN** niquests backend selected
- **WHEN** ParallelRequests is initialized
- **THEN** INFO message logged: "Selected backend: niquests"

#### Scenario: Backend unavailable
- **GIVEN** niquests not installed, aiohttp selected
- **WHEN** ParallelRequests is initialized
- **THEN** INFO message logged: "Selected backend: aiohttp (niquests unavailable)"

#### Scenario: Request completed
- **WHEN** request successfully completes
- **THEN** DEBUG message logged with URL and status code

#### Scenario: Retry attempt
- **GIVEN** request failed with retry
- **WHEN** retry attempt is made
- **THEN** DEBUG message logged with attempt number and error

#### Scenario: Request failed after retries
- **GIVEN** max_retries=3, all attempts failed
- **WHEN** request raises RetryExhaustedError
- **THEN** ERROR message logged with URL and final error

### Requirement: Log Level Filtering
The system SHALL filter log messages based on configured level.

#### Scenario: DEBUG messages hidden in INFO mode
- **GIVEN** logging configured with debug=False
- **WHEN** `logger.debug("test")` is called
- **THEN** no output is produced

#### Scenario: DEBUG messages shown in DEBUG mode
- **GIVEN** logging configured with debug=True
- **WHEN** `logger.debug("test")` is called
- **THEN** "DEBUG" level message is output

#### Scenario: ERROR messages always shown
- **GIVEN** logging configured with any level
- **WHEN** `logger.error("test")` is called
- **THEN** "ERROR" level message is always output
