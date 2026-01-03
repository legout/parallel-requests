# Handling Errors

This tutorial covers error handling patterns and working with exceptions in fastreq.

**Estimated reading time: 15 minutes**

## Types of Errors

The library defines several exception types:

- **`FastRequestsError`**: Base exception class
- **`BackendError`**: Backend operation failures
- **`ProxyError`**: Proxy-related failures
- **`RetryExhaustedError`**: All retry attempts exhausted
- **`RateLimitExceededError`**: Rate limit triggered
- **`ValidationError`**: Invalid input parameters
- **`ConfigurationError`**: Invalid configuration
- **`PartialFailureError`**: Some requests succeeded, others failed

## Basic Exception Handling

Wrap your requests in try-except blocks:

```python
from fastreq import fastreq, FastRequestsError

try:
    results = fastreq(
        urls=["https://api.github.com/invalid"],
    )
except FastRequestsError as e:
    print(f"Request failed: {e}")
```

## Partial Failures

When making multiple requests, some may succeed while others fail. By default, the library raises `PartialFailureError`:

```python
from fastreq import fastreq, PartialFailureError

urls = [
    "https://api.github.com/repos/python/cpython",  # Valid
    "https://invalid-url-that-does-not-exist.com",  # Invalid
    "https://api.github.com/repos/python/pypy",     # Valid
]

try:
    results = fastreq(urls=urls)
except PartialFailureError as e:
    print(f"Partial failure: {e.successes}/{e.total} succeeded")
    print(f"Failed URLs: {e.get_failed_urls()}")

    # Access individual failures
    for url, details in e.failures.items():
        print(f"  {url}: {details.error}")
```

## Graceful Failure Handling

Use `return_none_on_failure` to return `None` for failed requests instead of raising exceptions:

```python
from fastreq import fastreq

results = fastreq(
    urls=[
        "https://api.github.com/repos/python/cpython",
        "https://invalid-url.com",
        "https://api.github.com/repos/python/pypy",
    ],
    return_none_on_failure=True,
)

for url, result in zip(urls, results):
    if result is None:
        print(f"Failed: {url}")
    else:
        print(f"Success: {url}")
```

## Retry Configuration

Control retry behavior with `max_retries`:

```python
from fastreq import fastreq

# Retry up to 3 times (default)
results = fastreq(
    urls=["https://api.example.com/unstable"],
    max_retries=3,
)

# Disable retries
results = fastreq(
    urls=["https://api.example.com/unstable"],
    max_retries=0,
)
```

### Catching Retry Exhaustion

```python
from fastreq import fastreq, RetryExhaustedError

try:
    results = fastreq(
        urls=["https://api.example.com/unreliable"],
        max_retries=3,
    )
except RetryExhaustedError as e:
    print(f"Retries exhausted after {e.attempts} attempts")
    print(f"Last error: {e.last_error}")
```

## Timeout Handling

Set timeouts to prevent hanging requests:

```python
from fastreq import fastreq
from concurrent.futures import TimeoutError

try:
    results = fastreq(
        urls=["https://httpbin.org/delay/10"],
        timeout=5,  # 5 second timeout
    )
except TimeoutError:
    print("Request timed out")
```

## Validation Errors

Catch validation errors for invalid inputs:

```python
from fastreq import fastreq, ValidationError

try:
    results = fastreq(
        urls=["ftp://invalid-protocol.com"],  # Invalid URL
    )
except ValidationError as e:
    print(f"Validation error: {e}")
    print(f"Field: {e.field_name}")
```

## Error Handling with Context Manager

Using a context manager gives you more control:

```python
import asyncio
from fastreq import FastRequests, PartialFailureError

async def fetch_with_retry():
    async with FastRequests(max_retries=3) as client:
        try:
            results = await client.request(
                urls=[
                    "https://api.github.com/repos/python/cpython",
                    "https://invalid-url.com",
                ],
            )
            return results
        except PartialFailureError as e:
            print(f"Partial failure: {e.successes}/{e.total}")
            # Handle partial results
            return None

results = asyncio.run(fetch_with_retry())
```

## Best Practices

### 1. Use Specific Exceptions

```python
# Good: Catch specific exceptions
from fastreq import RetryExhaustedError, PartialFailureError

try:
    results = fastreq(urls=urls)
except RetryExhaustedError as e:
    # Handle retry exhaustion
    pass
except PartialFailureError as e:
    # Handle partial failures
    pass
except FastRequestsError as e:
    # Catch-all for other errors
    pass
```

### 2. Log Errors

```python
from loguru import logger
from fastreq import fastreq, PartialFailureError

try:
    results = fastreq(urls=urls)
except PartialFailureError as e:
    logger.error(f"Partial failure: {e.successes}/{e.total}")
    for url, details in e.failures.items():
        logger.error(f"  {url}: {details.error}")
```

### 3. Implement Fallback Logic

```python
from fastreq import fastreq

def fetch_with_fallback(urls):
    try:
        return fastreq(urls=urls)
    except PartialFailureError:
        # Retry only failed URLs
        failed_urls = list(e.get_failed_urls())
        return fastreq(urls=failed_urls)
```

### 4. Use `return_none_on_failure` for Non-Critical Requests

```python
from fastreq import fastreq

# Fetch multiple resources, ignore failures
results = fastreq(
    urls=[
        "https://api1.example.com/data",
        "https://api2.example.com/data",
        "https://api3.example.com/data",
    ],
    return_none_on_failure=True,
)

valid_results = [r for r in results if r is not None]
print(f"Got {len(valid_results)} valid results")
```

## Summary

- Use try-except to handle exceptions
- `PartialFailureError` indicates mixed success/failure
- `return_none_on_failure` for graceful degradation
- Configure `max_retries` for automatic retries
- Set `timeout` to prevent hanging requests
- Use specific exception types for better error handling

## Next Steps

- Explore **[How-to Guides](../how-to-guides/index.md)** for more practical examples
- Check the **[API Reference](../reference/exceptions.md)** for complete exception documentation
