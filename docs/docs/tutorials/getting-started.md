# Getting Started

This tutorial will walk you through installing parallel-requests and making your first parallel HTTP requests.

## Installation

Install parallel-requests using pip:

```bash
pip install parallel-requests
```

### Installing with Backend Support

The library supports three HTTP backends. You can install with all backends or choose specific ones:

```bash
# Install with all backends (recommended)
pip install parallel-requests[all]

# Install with specific backend
pip install parallel-requests[niquests]  # HTTP/2 support
pip install parallel-requests[aiohttp]
pip install parallel-requests[requests]
```

### Backend Priority

The library automatically detects and uses the best available backend in this order:

1. **niquests** - Recommended (HTTP/2 support, streaming, async native)
2. **aiohttp** - Streaming support, async native
3. **requests** - Sync-first, streaming via thread wrapper

## Your First Parallel Request

Let's start with a simple example that makes multiple API calls in parallel:

```python
from parallel_requests import parallel_requests

# Make parallel requests
results = parallel_requests(
    urls=[
        "https://api.github.com/repos/python/cpython",
        "https://api.github.com/repos/python/cpython/issues",
        "https://api.github.com/repos/python/cpython/pulls",
    ],
    concurrency=3,
)

# Process results
for result in results:
    print(f"Name: {result.get('name', result.get('title', 'N/A'))}")
```

This code fetches information about the CPython repository, issues, and pull requests in parallel, significantly faster than making these requests sequentially.

## Async Usage

For async applications, use the async version:

```python
import asyncio
from parallel_requests import parallel_requests_async

async def main():
    results = await parallel_requests_async(
        urls=[
            "https://httpbin.org/delay/1",
            "https://httpbin.org/delay/2",
            "https://httpbin.org/delay/3",
        ],
        concurrency=5,
        timeout=10,
    )
    return results

results = asyncio.run(main())
print(f"Got {len(results)} results")
```

## Response Types

By default, responses are parsed as JSON. You can specify different return types:

```python
# Get response as JSON (default)
results = parallel_requests(
    urls=["https://api.github.com/repos/python/cpython"],
    return_type="json",
)

# Get response as text
results = parallel_requests(
    urls=["https://example.com"],
    return_type="text",
)

# Get raw bytes
results = parallel_requests(
    urls=["https://example.com"],
    return_type="content",
)

# Get full response object
from parallel_requests import parallel_requests, ReturnType

results = parallel_requests(
    urls=["https://httpbin.org/get"],
    return_type=ReturnType.RESPONSE,
)
print(results[0].status_code)  # 200
print(results[0].headers)      # Response headers
```

## Configuration Options

Configure the client with various options:

```python
from parallel_requests import parallel_requests

results = parallel_requests(
    urls=["https://httpbin.org/get"] * 5,
    concurrency=3,            # Max concurrent requests
    max_retries=2,            # Retry failed requests up to 2 times
    rate_limit=10,            # 10 requests per second
    timeout=5,                # 5 second timeout per request
    debug=True,               # Enable debug logging
    backend="niquests",       # Explicit backend selection
)
```

## POST Requests

Make POST requests with JSON data:

```python
results = parallel_requests(
    urls=["https://httpbin.org/post"] * 3,
    method="POST",
    json={"key": "value"},
    headers={"Content-Type": "application/json"},
)
```

## Using a Context Manager

For more control, use the ParallelRequests class with an async context manager:

```python
import asyncio
from parallel_requests import ParallelRequests

async def main():
    async with ParallelRequests(concurrency=5) as client:
        # First batch
        results1 = await client.request(
            urls=["https://api.github.com/repos/python/cpython"],
        )

        # Second batch (reuses the same session)
        results2 = await client.request(
            urls=["https://api.github.com/repos/volkerlorrmann/parallel-requests"],
        )

    return results1, results2

results1, results2 = asyncio.run(main())
```

## Next Steps

- Learn about **[Parallel Fundamentals](parallel-fundamentals.md)** to understand concurrency and async patterns
- Explore **[How-to Guides](../how-to-guides/index.md)** for practical solutions
- Check the **[API Reference](../reference/index.md)** for complete documentation
