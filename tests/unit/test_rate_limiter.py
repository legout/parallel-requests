import asyncio
import time
import pytest

from parallel_requests.utils.rate_limiter import RateLimitConfig, TokenBucket, AsyncRateLimiter


@pytest.mark.asyncio
async def test_token_refill() -> None:
    bucket = TokenBucket(requests_per_second=10, burst=5)

    bucket._tokens = 2
    bucket._last_update = time.monotonic()

    await asyncio.sleep(0.2)

    available = bucket.available()
    assert 3 <= available <= 5


@pytest.mark.asyncio
async def test_token_acquisition() -> None:
    bucket = TokenBucket(requests_per_second=10, burst=5)
    bucket._tokens = 3

    available_before = bucket.available()
    assert available_before == 3

    await bucket.acquire(tokens=2)

    available_after = bucket.available()
    assert available_after == 1


@pytest.mark.asyncio
async def test_wait_for_tokens() -> None:
    bucket = TokenBucket(requests_per_second=10, burst=5)
    bucket._tokens = 0

    start_time = time.monotonic()
    await bucket.acquire(tokens=1)
    end_time = time.monotonic()

    elapsed = end_time - start_time
    assert 0.09 <= elapsed <= 0.15

    assert bucket.available() == 0


@pytest.mark.asyncio
async def test_semaphore_limits_concurrency() -> None:
    config = RateLimitConfig(requests_per_second=10, burst=5, max_concurrency=2)
    limiter = AsyncRateLimiter(config)

    concurrent_count = 0
    max_concurrent = 0

    async def worker() -> None:
        nonlocal concurrent_count, max_concurrent
        async with limiter._semaphore:
            concurrent_count += 1
            if concurrent_count > max_concurrent:
                max_concurrent = concurrent_count
            await asyncio.sleep(0.1)
            concurrent_count -= 1

    tasks = [worker() for _ in range(5)]
    await asyncio.gather(*tasks)

    assert max_concurrent == 2


@pytest.mark.asyncio
async def test_rate_and_concurrency_combined() -> None:
    config = RateLimitConfig(requests_per_second=5, burst=3, max_concurrency=3)
    limiter = AsyncRateLimiter(config)

    request_times: list[float] = []

    async def worker() -> None:
        async with limiter.acquire():
            request_times.append(time.monotonic())

    tasks = [worker() for _ in range(8)]
    await asyncio.gather(*tasks)

    assert len(request_times) == 8

    first_3_time = request_times[2]
    next_time = request_times[3]

    interval = next_time - first_3_time
    assert 0.18 <= interval <= 0.25


@pytest.mark.asyncio
async def test_query_available_tokens() -> None:
    bucket = TokenBucket(requests_per_second=10, burst=5)
    bucket._tokens = 3

    available = bucket.available()
    assert available == 3


@pytest.mark.asyncio
async def test_burst_capacity() -> None:
    bucket = TokenBucket(requests_per_second=10, burst=3)

    bucket._tokens = 3
    await asyncio.sleep(0.5)

    available = bucket.available()
    assert available == 3


@pytest.mark.asyncio
async def test_async_rate_limiter_acquire() -> None:
    config = RateLimitConfig(requests_per_second=10, burst=5, max_concurrency=10)
    limiter = AsyncRateLimiter(config)

    async with limiter.acquire():
        assert limiter.available() == 4

    async with limiter.acquire():
        assert limiter.available() == 3


@pytest.mark.asyncio
async def test_multiple_acquire_calls() -> None:
    bucket = TokenBucket(requests_per_second=10, burst=5)
    bucket._tokens = 5

    await bucket.acquire(tokens=2)
    assert bucket.available() == 3

    await bucket.acquire(tokens=1)
    assert bucket.available() == 2

    await bucket.acquire(tokens=2)
    assert bucket.available() == 0
