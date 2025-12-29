## ADDED Requirements

### Requirement: Global Configuration Dataclass
The system SHALL provide `GlobalConfig` dataclass with sensible defaults.

#### Scenario: Default values
- **WHEN** `GlobalConfig()` is instantiated with no arguments
- **THEN** `backend` equals `"auto"`
- **AND** `default_concurrency` equals `20`
- **AND** `default_max_retries` equals `3`
- **AND** `http2_enabled` is `True`
- **AND** `random_user_agent` is `True`
- **AND** `random_proxy` is `False`
- **AND** `free_proxies_enabled` is `False`

### Requirement: Environment Variable Loading
The system SHALL load configuration from environment variables.

#### Scenario: Load from environment
- **GIVEN** `PARALLEL_BACKEND=niquests` and `PARALLEL_CONCURRENCY=50` are set
- **WHEN** `GlobalConfig.load_from_env()` is called
- **THEN** `backend` equals `"niquests"`
- **AND** `default_concurrency` equals `50`

#### Scenario: Missing env vars use defaults
- **GIVEN** no parallel-requests env vars are set
- **WHEN** `GlobalConfig.load_from_env()` is called
- **THEN** all values use defaults

### Requirement: Environment Variable Serialization
The system SHALL export configuration to environment variables.

#### Scenario: Convert to environment format
- **WHEN** `config.to_env()` is called
- **THEN** a dict is returned with keys like `PARALLEL_BACKEND`, `PARALLEL_CONCURRENCY`

### Requirement: Configuration Persistence
The system SHALL save configuration to `.env` file.

#### Scenario: Save to file
- **WHEN** `config.save_to_env(Path("test.env"))` is called
- **THEN** `test.env` contains key=value pairs for all non-default settings
