import asyncio
import pytest

from parallel_requests.exceptions import RetryExhaustedError
from parallel_requests.utils.retry import RetryConfig, RetryStrategy


@pytest.mark.asyncio
async def test_exponential_delay_calculation() -> None:
    strategy = RetryStrategy(RetryConfig(max_retries=3, backoff_multiplier=1.0, jitter=0.0))

    delay_attempt_0 = strategy._calculate_delay(0)
    assert delay_attempt_0 == 1.0

    delay_attempt_1 = strategy._calculate_delay(1)
    assert delay_attempt_1 == 2.0

    delay_attempt_2 = strategy._calculate_delay(2)
    assert delay_attempt_2 == 4.0


@pytest.mark.asyncio
async def test_jitter_randomization() -> None:
    strategy = RetryStrategy(RetryConfig(max_retries=3, backoff_multiplier=1.0, jitter=0.1))

    delays = [strategy._calculate_delay(0) for _ in range(100)]
    assert len(set(delays)) > 1

    for delay in delays:
        assert 0.9 <= delay <= 1.1


@pytest.mark.asyncio
async def test_max_retries_enforcement() -> None:
    call_count = 0

    async def failing_func() -> None:
        nonlocal call_count
        call_count += 1
        raise ValueError("Always fails")

    strategy = RetryStrategy(RetryConfig(max_retries=2))

    with pytest.raises(RetryExhaustedError):
        await strategy.execute(failing_func)

    assert call_count == 3


@pytest.mark.asyncio
async def test_retry_on_specific_exceptions() -> None:
    call_count = 0

    async def connection_error_func() -> None:
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise ConnectionError("Connection failed")
        return "success"

    strategy = RetryStrategy(RetryConfig(max_retries=3, retry_on={ConnectionError, TimeoutError}))

    result = await strategy.execute(connection_error_func)
    assert result == "success"
    assert call_count == 3


@pytest.mark.asyncio
async def test_dont_retry_on_specific_exceptions() -> None:
    call_count = 0

    async def value_error_func() -> None:
        nonlocal call_count
        call_count += 1
        raise ValueError("Invalid value")

    strategy = RetryStrategy(RetryConfig(max_retries=3, dont_retry_on={ValueError}))

    with pytest.raises(ValueError):
        await strategy.execute(value_error_func)

    assert call_count == 1


@pytest.mark.asyncio
async def test_successful_execution_without_retry() -> None:
    call_count = 0

    async def successful_func() -> str:
        nonlocal call_count
        call_count += 1
        return "success"

    strategy = RetryStrategy(RetryConfig(max_retries=3))

    result = await strategy.execute(successful_func)
    assert result == "success"
    assert call_count == 1


@pytest.mark.asyncio
async def test_default_retry_config() -> None:
    strategy = RetryStrategy()

    assert strategy.config.max_retries == 3
    assert strategy.config.backoff_multiplier == 1.0
    assert strategy.config.jitter == 0.1
    assert strategy.config.retry_on is None
    assert strategy.config.dont_retry_on is None


@pytest.mark.asyncio
async def test_delay_between_retries() -> None:
    call_times: list[float] = []

    async def recording_func() -> None:
        call_times.append(asyncio.get_event_loop().time())
        raise ConnectionError("Connection failed")

    strategy = RetryStrategy(RetryConfig(max_retries=2, backoff_multiplier=0.1, jitter=0.0))

    with pytest.raises(RetryExhaustedError):
        await strategy.execute(recording_func)

    assert len(call_times) == 3

    delay_1 = call_times[1] - call_times[0]
    delay_2 = call_times[2] - call_times[1]

    assert delay_1 == pytest.approx(0.1, abs=0.05)
    assert delay_2 == pytest.approx(0.2, abs=0.05)


@pytest.mark.asyncio
async def test_retry_exhausted_error_properties() -> None:
    async def failing_func() -> None:
        raise ValueError("Test error")

    strategy = RetryStrategy(RetryConfig(max_retries=2))

    with pytest.raises(RetryExhaustedError) as exc_info:
        await strategy.execute(failing_func)

    error = exc_info.value
    assert error.attempts == 2
    assert isinstance(error.last_error, ValueError)
    assert "Retry attempts exhausted" in str(error)
