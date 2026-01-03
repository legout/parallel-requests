# fastreq v2.0.2

[![PyPI Version](https://img.shields.io/pypi/v/fastreq)](https://pypi.org/project/fastreq/)
[![Python Version](https://img.shields.io/pypi/pyversions/fastreq)](https://pypi.org/project/fastreq/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Test Coverage](https://img.shields.io/badge/coverage-95%25-brightgreen)](https://github.com/legout/fastreq)
[![Tests](https://img.shields.io/badge/tests-250%2B-brightgreen)](https://github.com/legout/fastreq)

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
pip install fastreq

# With specific backend (recommended: niquests for HTTP/2 support)
pip install fastreq[niquests]  # Primary (recommended)
pip install fastreq[aiohttp]
pip install fastreq[httpx]
pip install fastreq[requests]

# All backends
pip install fastreq[all]
```

## Quick Start

### Sync Usage

```python
from fastreq import parallel_requests

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
from fastreq import parallel_requests_async

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
from fastreq import ParallelRequests

async def main():
    async with ParallelRequests(concurrency=5) as client:
        results = await client.request(urls=["https://httpbin.org/get"] * 10)
    return results
```

## Documentation

- **[Full Documentation](https://legout.github.io/fastreq/)** - Complete user guide
- **[API Reference](docs/reference/api/)** - Detailed API documentation
- **[How-To Guides](docs/how-to-guides/)** - Practical guides for specific tasks
- **[Tutorials](docs/tutorials/)** - Step-by-step learning guides

## Examples

Visit the [examples](https://github.com/legout/fastreq/tree/main/examples) folder for 17 executable code samples covering all library features, including:

- Basic requests and concurrency tuning
- Rate limiting and retry configuration
- Proxy and user-agent rotation
- POST data and streaming downloads
- Error handling and backend selection
- Cookie management and keyed responses

## Development

### Versioning and Publishing

This project uses [semantic versioning](https://semver.org/). To release a new version:

1. Update the version in `pyproject.toml`
2. Create a version tag:

```bash
# For patch release (e.g., v2.0.1)
git tag v2.0.1

# For minor release (e.g., v2.1.0)
git tag v2.1.0

# For major release (e.g., v3.0.0)
git tag v3.0.0
```

3. Push the tag to trigger the automated workflow:

```bash
git push origin v2.0.1
```

The workflow will:
- Run tests, linting, and type checking
- Create a version tag and update CHANGELOG.md
- Publish to PyPI

## Backend Selection

The library automatically detects and uses the best available backend in this priority order:

1. **niquests** - Recommended (HTTP/2 support, streaming, async native)
2. **aiohttp** - Streaming support, async native
3. **httpx** - Modern sync/async HTTP client
4. **requests** - Sync-first, widely used

To explicitly select a backend:

```python
from fastreq import parallel_requests

results = parallel_requests(
    urls=["https://httpbin.org/get"],
    backend="niquests",  # Explicit backend selection
)
```

## License

MIT License - see [LICENSE](https://github.com/legout/fastreq/blob/main/LICENSE) for details.
