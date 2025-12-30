# Change: Add PyPI Publishing GitHub Workflow

## Why
Currently, the project lacks automated publishing to PyPI. Publishing requires manual steps which are error-prone and not reproducible. Automated CI/CD workflows ensure consistent, reliable package releases with proper validation before publishing.

## What Changes
- Add `.github/workflows/publish.yml` workflow for automated PyPI publishing
- Configure workflow to publish on version tags (v* pattern)
- Add pre-publish validation steps (tests, linting, type checking)
- Configure trusted publishing via OIDC for secure authentication
- Add workflow for publishing to Test PyPI first as a safety measure

## Impact
- Affected specs: `optional-dependency-imports`
- Affected code: `.github/workflows/` (new file), `pyproject.toml` (version management)
