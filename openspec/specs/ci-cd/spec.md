# ci-cd Specification

## Purpose
TBD - created by archiving change add-pypi-publish-workflow. Update Purpose after archive.
## Requirements
### Requirement: Automated PyPI Publishing
The system SHALL provide a GitHub Actions workflow that automatically publishes the package to PyPI when a version tag is pushed.

#### Scenario: Publish on version tag push
- **WHEN** a git tag matching the pattern `v*` is pushed to the repository
- **THEN** the publish workflow SHALL run pre-publish validation
- **AND** the validated package SHALL be built and uploaded to PyPI

#### Scenario: Skip on validation failure
- **WHEN** pre-publish validation (tests, lint, type check) fails
- **THEN** the workflow SHALL NOT publish to PyPI
- **AND** the workflow SHALL report the validation failure

### Requirement: Test PyPI Pre-validation
The system SHALL publish to Test PyPI before production PyPI to catch potential issues early.

#### Scenario: Two-stage publish workflow
- **WHEN** a version tag is pushed
- **THEN** the package SHALL first be published to Test PyPI
- **AND** only after successful Test PyPI upload SHALL the package be published to PyPI

#### Scenario: Test PyPI validation
- **WHEN** the package is published to Test PyPI
- **THEN** the maintainer can verify the package integrity
- **AND** production PyPI publishing requires manual confirmation or automatic continuation

### Requirement: Pre-publish Validation
The system SHALL run validation steps before attempting to publish to PyPI.

#### Scenario: Run test suite
- **WHEN** the publish workflow is triggered
- **THEN** the test suite SHALL run to verify package functionality
- **AND** all tests SHALL pass before publishing

#### Scenario: Run linting
- **WHEN** the publish workflow is triggered
- **THEN** ruff linting SHALL run to verify code quality
- **AND** no lint errors SHALL be present before publishing

#### Scenario: Run type checking
- **WHEN** the publish workflow is triggered
- **THEN** mypy type checking SHALL run to verify type correctness
- **AND** no type errors SHALL be present before publishing

### Requirement: Secure Authentication
The system SHALL use trusted publishing (OIDC) for PyPI authentication instead of long-lived API tokens.

#### Scenario: OIDC token exchange
- **WHEN** the workflow uploads to PyPI
- **THEN** the authentication SHALL use OIDC trusted publishing
- **AND** no PyPI API token SHALL be stored in repository secrets

### Requirement: Build Package
The system SHALL build the package using the configured build backend before publishing.

#### Scenario: Build wheel and source distribution
- **WHEN** the publish workflow runs
- **THEN** the package SHALL be built as a wheel (`.whl`) and source distribution (`.tar.gz`)
- **AND** the build SHALL use `hatchling` as specified in `pyproject.toml`

