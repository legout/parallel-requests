## 1. Httpx Backend
- [x] 1.1 Create `src/parallel_requests/backends/httpx.py` with `HttpxBackend` class
- [x] 1.2 Implement `request()` mapping `RequestConfig` → `httpx.AsyncClient.request()`
- [x] 1.3 Implement streaming support consistent with other backends
- [x] 1.4 Implement proxy support using `RequestConfig.proxy`
- [x] 1.5 Implement context manager (`__aenter__`, `__aexit__`) and `close()`
- [x] 1.6 Implement `supports_http2()` behavior and document limitations

## 2. Client Integration
- [x] 2.1 Update backend auto-detection order to `niquests → httpx → aiohttp → requests`
- [x] 2.2 Support explicit backend selection `backend="httpx"`
- [x] 2.3 Ensure backend selection logging includes httpx fallback messaging

## 3. Dependencies
- [x] 3.1 Add `httpx` as a project optional dependency (`[project.optional-dependencies]`)
- [x] 3.2 Decide whether `[all]` extra includes `httpx` (included in `[all]`)

## 4. Documentation
- [x] 4.1 Update backend selection guide to include httpx and new priority
- [x] 4.2 Update backend explanation/feature matrix to include httpx

## 5. Tests
- [x] 5.1 Add backend tests for GET/POST normalization and error mapping
- [x] 5.2 Add streaming test coverage for httpx backend
- [x] 5.3 Add selection tests for `backend="httpx"` and `backend="auto"` order

## 6. Quality Gates
- [x] 6.1 Run `openspec validate add-backend-httpx --strict`
- [x] 6.2 Run `pytest` (252 passed, 1 pre-existing failure)
- [x] 6.3 Run `ruff check` and `mypy` for backend module

## Notes
- httpx is an optional dependency and is NOT imported when not installed
- Lazy loading via `__getattr__` in `__init__.py` ensures no import errors
- HTTP/2 support requires the `h2` extra (`pip install httpx[http2]`)
- Without `h2`, the backend falls back to HTTP/1.1
