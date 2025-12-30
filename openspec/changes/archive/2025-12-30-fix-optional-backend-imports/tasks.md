## 1. Lazy Import Fix
- [x] 1.1 Update `src/parallel_requests/backends/__init__.py` to stop importing optional backend modules at import time
- [x] 1.2 Add lazy exports for `NiquestsBackend`, `AiohttpBackend`, and `RequestsBackend` (import on attribute access)
- [x] 1.3 Ensure `parallel_requests.client.ParallelRequests(backend="auto")` does not import unselected backend modules

## 2. Tests
- [x] 2.1 Add a test that `import parallel_requests` succeeds with only one optional backend installed
- [x] 2.2 Add a test that `import parallel_requests.backends` succeeds with missing optional dependencies
- [x] 2.3 Add a test that selecting `backend="niquests"` does not import `aiohttp` when `aiohttp` is not installed

## 3. Quality Gates
- [x] 3.1 Run `openspec validate fix-optional-backend-imports --strict`
- [x] 3.2 Run `pytest`
