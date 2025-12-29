## ADDED Requirements

### Requirement: User Agent Rotation
The system SHALL provide random user agent rotation.

#### Scenario: Default user agents available
- **WHEN** `HeaderManager()` is instantiated with defaults
- **THEN** at least 8 user agents are available

#### Scenario: Random selection
- **GIVEN** multiple user agents configured
- **WHEN** `get_headers()` is called multiple times
- **THEN** different user agents are selected (not deterministic)

#### Scenario: User agent in headers
- **WHEN** `get_headers()` is called
- **THEN** `"user-agent"` key exists in returned headers

### Requirement: Custom User Agent List
The system SHALL support custom user agent list.

#### Scenario: Custom list provided
- **GIVEN** `HeaderManager(user_agents=["Custom/1.0"])`
- **WHEN** `get_headers()` is called
- **THEN** `"Custom/1.0"` is the user agent

### Requirement: Environment Variable Support
The system SHALL load user agents from environment variable.

#### Scenario: Load from USER_AGENTS
- **GIVEN** `USER_AGENTS="Agent1,Agent2,Agent3"` in environment
- **WHEN** `HeaderManager()` is instantiated
- **THEN** 3 user agents are loaded

### Requirement: Header Merging
The system SHALL merge custom headers with default headers.

#### Scenario: Custom headers override defaults
- **WHEN** `get_headers({"Authorization": "Bearer token"})` is called
- **THEN** returned headers contain `"Authorization": "Bearer token"`
- **AND** `"user-agent"` is also present

#### Scenario: Custom user-agent overrides rotation
- **GIVEN** `HeaderManager(custom_user_agent="MyApp/1.0")`
- **WHEN** `get_headers()` is called
- **THEN** `"user-agent"` equals `"MyApp/1.0"`
- **AND** rotation is disabled for user-agent

### Requirement: Remote User Agent Updates
The system SHALL support fetching user agents from remote URL.

#### Scenario: Update from remote URL
- **GIVEN** `HeaderManager` with default agents
- **WHEN** `update_agents_from_remote("https://example.com/ua.txt")` is called
- **THEN** agents are replaced with those from URL

#### Scenario: Remote update failure doesn't crash
- **GIVEN** invalid remote URL
- **WHEN** `update_agents_from_remote(...)` is called
- **THEN** `ValueError` is raised (original agents unchanged)
