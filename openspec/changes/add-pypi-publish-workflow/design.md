## Context
The project uses `hatchling` as its build backend (defined in `pyproject.toml`). We need to automate the publishing process to PyPI using GitHub Actions. The publishing should be triggered by version tags and include proper validation before upload.

## Goals / Non-Goals
- Goals:
  - Automate PyPI publishing on version tags
  - Include pre-publish validation (tests, lint, type check)
  - Use trusted publishing (OIDC) for secure authentication
  - Publish to Test PyPI first for validation before production
- Non-Goals:
  - GitHub Releases creation (separate concern)
  - Docker/container publishing
  - Conditional publishing based on branch protection rules

## Decisions
- **Build Backend**: Use `hatchling` (already configured in pyproject.toml)
- **Publishing Strategy**: Test PyPI first, then production PyPI
- **Authentication**: Trusted publishing via OIDC (no API tokens in secrets)
- **Trigger**: Version tags matching `v*` pattern
- **Validation**: Run existing test suite, ruff lint, mypy type check before publish

## Workflow Structure
```yaml
jobs:
  validate:
    runs: tests, lint, type check
  publish-testpypi:
    needs: validate
    if: startsWith(github.ref, 'refs/tags/v')
    runs: hatch build, upload to Test PyPI
  publish-pypi:
    needs: publish-testpypi
    runs: upload to PyPI
```

## Alternatives Considered
- **Single PyPI publish**: Skipping Test PyPI increases risk of broken releases
- **API tokens**: OIDC trusted publishing is more secure (no long-lived tokens)
- **PyPI upload action**: Use `pypa/gh-action-pypi-publish` (mature, well-tested)

## Risks / Trade-offs
- **Risk**: Workflow might fail on first run due to OIDC configuration
  - **Mitigation**: Document OIDC setup steps; Test on fork first
- **Risk**: Version tag format inconsistency
  - **Mitigation**: Use clear tagging convention; validate in workflow
- **Trade-off**: Running full test suite before publish adds time
  - **Acceptable**: Better to catch issues before publication

## Open Questions
- Should we publish release notes automatically?
- Should we create GitHub Releases alongside PyPI publishing?
