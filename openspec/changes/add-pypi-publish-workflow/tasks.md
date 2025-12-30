## 1. Create Publish Workflow
- [x] 1.1 Create `.github/workflows/publish.yml` with Test PyPI publishing on tags
- [x] 1.2 Add pre-publish validation: run tests, lint, type check
- [x] 1.3 Configure build using `hatchling` (existing build system)
- [x] 1.4 Set up Test PyPI upload step

## 2. Configure Production Publishing
- [x] 2.1 Add production PyPI publishing step (conditional on Test PyPI success)
- [x] 2.2 Configure trusted publishing via OIDC in workflow
- [x] 2.3 Add permissions configuration for PyPI upload

## 3. Add Version Tag Trigger
- [x] 3.1 Configure workflow to trigger on version tags (v* pattern)
- [x] 3.2 Add concurrency controls to prevent concurrent publishes
- [x] 3.3 Document tagging convention in README or contributing guide

## 4. Testing and Validation
- [x] 4.1 Verify workflow syntax with act or GitHub Actions lint
- [ ] 4.2 Test publish workflow against a fork or test repository (requires OIDC setup)
- [x] 4.3 Validate workflow permissions are minimal and secure
