## 1. RateLimiter Changes
- [x] 1.1 Remove `max_concurrency` field from `RateLimitConfig` dataclass in `src/fastreq/utils/rate_limiter.py`
- [x] 1.2 Remove `_semaphore` from `AsyncRateLimiter` class (rate limiter only manages rate, not concurrency)
- [x] 1.3 Simplify `AsyncRateLimiter.acquire()` to only acquire rate tokens, not semaphore
- [x] 1.4 Update tests in `tests/unit/test_rate_limiter.py` to remove concurrency-related assertions

## 2. Backend Base Class Changes
- [x] 2.1 Add optional `concurrency` parameter to `Backend.__init__()` signature in `src/fastreq/backends/base.py`
- [x] 2.2 Store concurrency in `Backend` instance as `self._concurrency`

## 3. Backend Implementation Changes
- [x] 3.1 Modify `AiohttpBackend.__aenter__()` to create `TCPConnector(limit=concurrency)` in `src/fastreq/backends/aiohttp.py`
- [x] 3.2 Modify `HttpxBackend.__aenter__()` to use `Limits(max_connections=concurrency)` in `src/fastreq/backends/httpx.py`
- [x] 3.3 Modify `NiquestsBackend.__aenter__()` to accept concurrency parameter in `src/fastreq/backends/niquests.py`
- [x] 3.4 Modify `RequestsBackend.__aenter__()` to accept concurrency parameter (no-op, handled by client semaphore) in `src/fastreq/backends/requests.py`

## 4. Client Changes
- [x] 4.1 Add `self._concurrency_semaphore = asyncio.Semaphore(concurrency)` in `ParallelRequests.__init__()` in `src/fastreq/client.py`
- [x] 4.2 Modify `ParallelRequests._select_backend()` to pass `concurrency` to backend constructor
- [x] 4.3 Wrap `_execute_request()` inner `make_request()` with `async with self._concurrency_semaphore:`
- [x] 4.4 Add debug log when concurrency semaphore blocks (e.g., "Concurrency slot acquired, making request to...")

## 5. Tests
- [x] 5.1 Create `tests/unit/test_concurrency.py` with tests for:
  - [x] Concurrency semaphore initialization
  - [x] Default concurrency value
  - [x] Custom concurrency values
  - [x] Semaphore type verification
- [x] 5.2 Update `tests/unit/test_rate_limiter.py` to remove concurrency-related tests
- [x] 5.3 Update `tests/unit/test_client.py` mock backends to accept concurrency parameter

## 6. Quality Gates
- [x] 6.1 Run `mypy src/fastreq/client.py src/fastreq/utils/rate_limiter.py src/fastreq/backends/*.py --strict`
- [x] 6.2 Run `ruff check src/fastreq/client.py src/fastreq/utils/rate_limiter.py src/fastreq/backends/*.py`
- [x] 6.3 Run `pytest tests/unit/test_concurrency.py tests/unit/test_rate_limiter.py -v` (all pass)
- [x] 6.4 Verify expected behavior:
  - [x] All unit tests pass (180 tests)
  - [x] Concurrency parameter now respected
  - [x] Rate limiting independent of concurrency
