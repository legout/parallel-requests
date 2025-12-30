## 1. Create Publish Workflow
- [ ] 1.1 Create `.github/workflows/publish.yml` with Test PyPI publishing on tags
- [ ] 1.2 Add pre-publish validation: run tests, lint, type check
- [ ] 1.3 Configure build using `hatchling` (existing build system)
- [ ] 1.4 Set up Test PyPI upload step

## 2. Configure Production Publishing
- [ ] 2.1 Add production PyPI publishing step (conditional on Test PyPI success)
- [ ] 2.2 Configure trusted publishing via OIDC in workflow
- [ ] 2.3 Add permissions configuration for PyPI upload

## 3. Add Version Tag Trigger
- [ ] 3.1 Configure workflow to trigger on version tags (v* pattern)
- [ ] 3.2 Add concurrency controls to prevent concurrent publishes
- [ ] 3.3 Document tagging convention in README or contributing guide

## 4. Testing and Validation
- [ ] 4.1 Verify workflow syntax with act or GitHub Actions lint
- [ ] 4.2 Test publish workflow against a fork or test repository
- [ ] 4.3 Validate workflow permissions are minimal and secure
