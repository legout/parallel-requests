## 1. Retry Policy
- [x] 1.1 Create `src/parallel_requests/utils/retry.py` with `RetryConfig` dataclass
- [x] 1.2 Implement `RetryStrategy` class with exponential backoff and jitter
- [x] 1.3 Add `RetryExhausted` exception
- [x] 1.4 Write unit tests for retry logic (90%+ coverage)
  - Test exponential calculation
  - Test jitter randomization
  - Test max retries enforcement
  - Test retry-on / dont-retry-on filtering

## 2. Rate Limiting
- [x] 2.1 Create `src/parallel_requests/utils/rate_limiter.py` with `RateLimitConfig` dataclass
- [x] 2.2 Implement `TokenBucket` class for token bucket algorithm
- [x] 2.3 Implement `AsyncRateLimiter` combining token bucket with semaphore
- [x] 2.4 Write unit tests for rate limiting (90%+ coverage)
  - Test token refill rate
  - Test burst capacity
  - Test wait time calculation
  - Test concurrent access

## 3. Input Validation
- [x] 3.1 Create `src/parallel_requests/utils/validators.py`
- [x] 3.2 Implement URL validation (must be valid http/https)
- [x] 3.3 Implement proxy format validation (ip:port:user:pw, http://, etc.)
- [x] 3.4 Implement header validation (dict with string keys/values)
- [x] 3.5 Write unit tests for validators (90%+ coverage)

## 4. Quality Gates
- [x] 4.1 Run `mypy src/parallel_requests/utils/ --strict`
- [x] 4.2 Run `ruff check src/parallel_requests/utils/`
- [x] 4.3 Run `black --check src/parallel_requests/utils/`
- [x] 4.4 Run `pytest tests/unit/test_retry.py tests/unit/test_rate_limiter.py tests/unit/test_validators.py` (all pass, 90%+ coverage)
