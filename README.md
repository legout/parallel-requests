# parallel-requests v2.0.0

[![PyPI Version](https://img.shields.io/pypi/v/parallel-requests)](https://pypi.org/project/parallel-requests/)
[![Python Version](https://img.shields.io/pypi/pyversions/parallel-requests)](https://pypi.org/project/parallel-requests/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Test Coverage](https://img.shields.io/badge/coverage-95%25-brightgreen)](https://github.com/volkerlorrmann/parallel-requests)
[![Tests](https://img.shields.io/badge/tests-140%2B-brightgreen)](https://github.com/volkerlorrmann/parallel-requests)

Fast parallel HTTP requests with asyncio, retry logic, proxy rotation, and rate limiting.

## Features

- **Parallel Execution**: Execute multiple HTTP requests concurrently with automatic async/sync handling
- **Multiple Backends**: Support for niquests, aiohttp, httpx, and requests with automatic backend detection
- **Retry Logic**: Exponential backoff with jitter for resilient request handling
- **Proxy Rotation**: Automatic proxy management with support for authenticated proxies
- **Rate Limiting**: Token bucket algorithm for precise request rate control
- **User-Agent Rotation**: Built-in user agent string rotation
- **Cookie Management**: Session-based cookie handling with set/reset methods
- **Flexible Response Parsing**: Custom parse functions, keyed responses, and graceful failure handling
- **HTTP/2 Support**: Full HTTP/2 support when using the niquests backend
- **Streaming**: Efficient streaming of large responses

## Installation

```bash
# Core library only
pip install parallel-requests

# With specific backend (recommended: niquests for HTTP/2 support)
pip install parallel-requests[niquests]  # Primary (recommended)
pip install parallel-requests[aiohttp]
pip install parallel-requests[httpx]
pip install parallel-requests[requests]

# All backends
pip install parallel-requests[all]
```

## Quick Start

### Sync Usage

```python
from parallel_requests import parallel_requests

results = parallel_requests(
    urls=[
        "https://api.github.com/repos/python/cpython",
        "https://api.github.com/repos/python/cpython/issues",
        "https://api.github.com/repos/python/cpython/pulls",
    ],
    concurrency=3,
)

for result in results:
    print(result.json())
```

### Async Usage

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
```

### Context Manager

```python
from parallel_requests import ParallelRequests

async def main():
    async with ParallelRequests(concurrency=5) as client:
        results = await client.request(urls=["https://httpbin.org/get"] * 10)
    return results
```

## Documentation

- **[Full Documentation](https://volkerlorrmann.github.io/parallel-requests/)** - Complete user guide
- **[API Reference](docs/reference/api/)** - Detailed API documentation
- **[How-To Guides](docs/how-to-guides/)** - Practical guides for specific tasks
- **[Tutorials](docs/tutorials/)** - Step-by-step learning guides

## Examples

Visit the [examples](https://github.com/volkerlorrmann/parallel-requests/tree/main/examples) folder for 17 executable code samples covering all library features, including:

- Basic requests and concurrency tuning
- Rate limiting and retry configuration
- Proxy and user-agent rotation
- POST data and streaming downloads
- Error handling and backend selection
- Cookie management and keyed responses

## Backend Selection

The library automatically detects and uses the best available backend in this priority order:

1. **niquests** - Recommended (HTTP/2 support, streaming, async native)
2. **aiohttp** - Streaming support, async native
3. **httpx** - Modern sync/async HTTP client
4. **requests** - Sync-first, widely used

To explicitly select a backend:

```python
from parallel_requests import parallel_requests

results = parallel_requests(
    urls=["https://httpbin.org/get"],
    backend="niquests",  # Explicit backend selection
)
```

## License

MIT License - see [LICENSE](https://github.com/volkerlorrmann/parallel-requests/blob/main/LICENSE) for details.
