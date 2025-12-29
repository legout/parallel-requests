## 1. Niquests Backend
- [x] 1.1 Create `src/parallel_requests/backends/niquests.py` with `NiquestsBackend` class
- [x] 1.2 Implement `request()` method handling all HTTP methods
- [x] 1.3 Add HTTP/2 support (enabled by default)
- [x] 1.4 Add streaming support (chunked responses)
- [x] 1.5 Implement context manager (`__aenter__`, `__aexit__`)
- [x] 1.6 Write integration tests (90%+ coverage)

## 2. Aiohttp Backend
- [x] 2.1 Create `src/parallel_requests/backends/aiohttp.py` with `AiohttpBackend` class
- [x] 2.2 Implement `request()` method handling all HTTP methods
- [x] 2.3 Add HTTP/2 support (via connector config, optional)
- [x] 2.4 Add streaming support (chunked responses)
- [x] 2.5 Implement context manager (`__aenter__`, `__aexit__`)
- [x] 2.6 Write integration tests (90%+ coverage)

## 3. Requests Backend
- [x] 3.1 Create `src/parallel_requests/backends/requests.py` with `RequestsBackend` class
- [x] 3.2 Implement sync `request()` method wrapped in `asyncio.to_thread()`
- [x] 3.3 Add streaming support (iter_content)
- [x] 3.4 Implement context manager (`__aenter__`, `__aexit__`)
- [x] 3.5 Write integration tests (90%+ coverage)

## 4. Quality Gates
- [x] 4.1 Run `mypy src/parallel_requests/backends/ --strict`
- [x] 4.2 Run `ruff check src/parallel_requests/backends/`
- [x] 4.3 Run `black --check src/parallel_requests/backends/`
- [x] 4.4 Run `pytest tests/backends/ tests/integration/` (all pass, 90%+ coverage)
