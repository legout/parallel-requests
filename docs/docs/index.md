# Parallel Requests

A high-performance Python library for executing parallel HTTP requests with built-in retry logic, proxy rotation, rate limiting, and support for multiple HTTP backends.

## Features

- **Parallel Execution**: Execute multiple HTTP requests concurrently with automatic async/sync handling
- **Multiple Backends**: Support for niquests, aiohttp, and requests with automatic backend detection
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
pip install fastreq

# Install with all backend support
pip install fastreq[all]

# Install with specific backend
pip install fastreq[niquests]  # For HTTP/2 support
pip install fastreq[aiohttp]
pip install fastreq[requests]
```

## Quick Start

```python
from fastreq import fastreq

# Make parallel requests
results = fastreq(
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

## Async Usage

```python
import asyncio
from fastreq import fastreq_async

async def main():
    results = await fastreq_async(
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

## Quick Links

### New Users
- [Getting Started Tutorial](tutorials/getting-started.md) - Installation and your first parallel requests
- [Basic Examples](https://github.com/legout/fastreq/tree/main/examples) - Runnable code samples

### Common Tasks
- [Make Parallel Requests](how-to-guides/make-fastreq.md)
- [Handle Rate Limits](how-to-guides/limit-request-rate.md)
- [Configure Retries](how-to-guides/handle-retries.md)
- [Use Proxies](how-to-guides/use-proxies.md)

### API Reference
- [API Overview](reference/index.md)
- [ParallelRequests Class](reference/api/parallelrequests.md)
- [Configuration Options](reference/configuration.md)

### Advanced Topics
- [Architecture](explanation/architecture.md)
- [Backend Comparison](explanation/backends.md)

## Examples

Visit the [examples](https://github.com/legout/fastreq/tree/main/examples) folder for executable code samples covering all library features.

## Backend Selection

The library automatically detects and uses the best available backend in this priority order:

1. **niquests** - Recommended (HTTP/2 support, streaming, async native)
2. **aiohttp** - Streaming support, async native
3. **requests** - Sync-first, streaming via thread wrapper

To explicitly select a backend:

```python
from fastreq import fastreq

results = fastreq(
    urls=["https://httpbin.org/get"],
    backend="niquests",  # Explicit backend selection
)
```

## License

MIT License - see [LICENSE](https://github.com/legout/fastreq/blob/main/LICENSE) for details.
