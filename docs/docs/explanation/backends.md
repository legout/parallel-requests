# Backends

The parallel-requests library supports three HTTP backends, each with different capabilities and trade-offs.

## Overview

| Backend | HTTP/2 | Streaming | Async Native | Notes |
|---------|--------|----------|--------------|-------|
| **niquests** | ✓ | ✓ | ✓ | Recommended default |
| **aiohttp** | ✗ | ✓ | ✓ | Mature, widely used |
| **requests** | ✗ | ✓ | ✗ | Familiar API, wrapped |

## Auto-Detection Order

When `backend="auto"` (default), the library checks backends in this order:

1. **niquests** - HTTP/2 support, streaming, async native
2. **aiohttp** - Streaming support, async native
3. **requests** - Streaming via thread wrapper, sync-first

The first available backend is used. This means if you have both niquests and aiohttp installed, niquests will be selected.

## Niquests Backend

### Capabilities

- **HTTP/2 Support**: Native HTTP/2 with multiplexing
- **Streaming**: Full streaming support for large files
- **Async Native**: Built on async I/O from the ground up
- **Connection Reuse**: Efficient connection pooling

### When to Use

- **Default choice** for most use cases
- **HTTP/2 APIs** (e.g., some modern web services)
- **High-throughput scenarios** where connection reuse matters
- **Large file downloads** with streaming

### Implementation Details

```python
class NiquestsBackend(Backend):
    async def __init__(self, http2_enabled: bool = True):
        self._session = niquests.AsyncSession(
            disable_http2=not http2_enabled
        )

    async def request(self, config: RequestConfig) -> NormalizedResponse:
        response = await self._session.request(**kwargs)
        # Handles streaming automatically
        if config.stream:
            content = await response.content
        else:
            content = response.content
```

### Performance Characteristics

- **HTTP/2 Multiplexing**: Multiple requests over single connection
- **Low Overhead**: Async native, minimal thread usage
- **Efficient Streaming**: Memory-efficient for large responses

## Aiohttp Backend

### Capabilities

- **No HTTP/2**: Only HTTP/1.1 (unless using external extensions)
- **Streaming**: Full streaming support
- **Async Native**: Pure async implementation
- **Mature Library**: Widely used and battle-tested

### When to Use

- **Already using aiohttp** in your project
- **Need aiohttp-specific features** not exposed by our abstraction
- **HTTP/1.1 environments** (most standard web services)
- **Familiar aiohttp API** (though we abstract it)

### Implementation Details

```python
class AiohttpBackend(Backend):
    async def __init__(self, http2_enabled: bool = True):
        self._session = aiohttp.ClientSession()
        # http2_enabled is ignored, warning is issued

    async def request(self, config: RequestConfig) -> NormalizedResponse:
        response = await self._session.request(**kwargs)
        content = await response.read()  # Always read full content
```

**Note**: When `http2=True` is set with aiohttp, a warning is issued because aiohttp doesn't natively support HTTP/2.

### Performance Characteristics

- **Connection Pooling**: Efficient connection reuse
- **Mature Stability**: Years of production use
- **HTTP/1.1 Only**: No multiplexing benefits
- **Low Overhead**: Async native, minimal thread usage

## Requests Backend

### Capabilities

- **No HTTP/2**: Only HTTP/1.1
- **Streaming**: Full streaming support (via thread wrapper)
- **Sync-First**: Synchronous library wrapped in async
- **Familiar API**: Most developers know requests

### When to Use

- **Already using requests** and don't want to add dependencies
- **Sync codebases** migrating to async gradually
- **Need requests-specific features** (session hooks, custom adapters)
- **Simple use cases** where HTTP/2 isn't needed

### Implementation Details

```python
class RequestsBackend(Backend):
    async def __init__(self, http2_enabled: bool = True):
        self._session = requests.Session()
        # http2_enabled is ignored, warning is issued

    async def request(self, config: RequestConfig) -> NormalizedResponse:
        def _make_request():
            return self._session.request(**kwargs)

        # Run synchronous request in thread pool
        response = await asyncio.to_thread(_make_request)
```

**Thread Wrapper**: The synchronous `requests.Session.request()` is executed in a thread pool using `asyncio.to_thread()`. This allows it to work in an async context but adds thread overhead.

### Performance Characteristics

- **Thread Pool Overhead**: Each request runs in a thread pool
- **Connection Pooling**: Standard requests connection reuse
- **Familiar Stability**: Proven in production
- **No HTTP/2 Benefits**: Misses multiplexing advantages

## Feature Comparison Table

| Feature | niquests | aiohttp | requests |
|---------|----------|---------|----------|
| **HTTP/2** | ✓ (native) | ✗ (extensions only) | ✗ |
| **HTTP/1.1** | ✓ | ✓ | ✓ |
| **Streaming** | ✓ | ✓ | ✓ (thread wrapper) |
| **Async Native** | ✓ | ✓ | ✗ (thread wrapper) |
| **Connection Pooling** | ✓ | ✓ | ✓ |
| **Session Cookies** | ✓ | ✓ | ✓ |
| **Thread Safe** | ✓ | ✓ | ✓ |
| **Maturity** | Medium | High | Very High |
| **Installation Size** | ~2MB | ~1MB | ~0.5MB |

## Performance Considerations

### Throughput

For high-throughput scenarios, performance typically ranks:

1. **niquests** (HTTP/2): Fastest due to multiplexing
2. **aiohttp**: Fast, mature async implementation
3. **requests**: Slightly slower due to thread overhead

### Memory Usage

All backends have similar memory characteristics for the same workload, but:

- **niquests** with HTTP/2: Fewer connections → less memory for connections
- **requests**: Thread pool uses additional memory
- **aiohttp**: Standard async memory footprint

### Latency

For single-request latency, differences are minimal. For concurrent requests:

- **HTTP/2 (niquests)**: Lower latency due to connection reuse
- **HTTP/1.1 (aiohttp/requests)**: Higher latency under high concurrency

### CPU Usage

CPU usage generally follows async vs sync pattern:

- **niquests/aiohttp**: Lower CPU (async native)
- **requests**: Higher CPU (thread pool overhead)

## Backend Selection Guide

### Choose niquests if:
- ✓ You want HTTP/2 support
- ✓ You need maximum performance
- ✓ You're starting a new project
- ✓ You care about connection efficiency

### Choose aiohttp if:
- ✓ You're already using aiohttp
- ✓ You need aiohttp-specific features
- ✓ Your project uses aiohttp extensively
- ✓ HTTP/1.1 is sufficient

### Choose requests if:
- ✓ You're already using requests
- ✓ You want to minimize dependencies
- ✓ You're migrating a sync codebase
- ✓ HTTP/2 isn't needed
- ✓ You need requests-specific features (custom adapters, hooks)

## Example: Backend-Specific Behavior

### HTTP/2 Multiplexing (niquests only)

With HTTP/2, multiple requests share a single connection:

```python
# With niquests (HTTP/2 enabled)
client = ParallelRequests(backend="niquests", http2=True)
# All 100 requests share 1-2 connections due to multiplexing
results = await client.request(urls=[url] * 100)
```

### Connection Behavior (HTTP/1.1 backends)

With HTTP/1.1, each connection handles one request at a time:

```python
# With aiohttp or requests (HTTP/1.1 only)
client = ParallelRequests(backend="aiohttp")
# With concurrency=20, up to 20 connections are used
results = await client.request(urls=[url] * 100)
```

The `concurrency` parameter directly limits the number of concurrent connections.

## Installation and Dependencies

### Installing with Specific Backend

```bash
# Install only niquests
pip install parallel-requests[niquests]

# Install only aiohttp
pip install parallel-requests[aiohttp]

# Install only requests
pip install parallel-requests[requests]

# Install all backends (recommended)
pip install parallel-requests[all]
```

### Dependency Sizes

- **niquests**: ~2MB (includes urllib3 dependencies)
- **aiohttp**: ~1MB (includes yarl, multidict)
- **requests**: ~0.5MB (includes urllib3)

## Backend Internals

### Session Management

All backends implement async context managers:

```python
async with ParallelRequests(backend="niquests") as client:
    # Backend session is initialized here
    results = await client.request(urls=[...])
    # Backend session is closed here automatically
```

### Error Handling

Each backend catches its library-specific exceptions and wraps them in `BackendError`:

```python
# niquests
except niquests.RequestException as e:
    raise BackendError(f"Request failed: {e}", backend_name=self.name)

# aiohttp
except (aiohttp.ClientError, asyncio.TimeoutError) as e:
    raise BackendError(f"Request failed: {e}", backend_name=self.name)

# requests
except requests.RequestException as e:
    raise BackendError(f"Request failed: {e}", backend_name=self.name)
```

### Response Normalization

All backends return `NormalizedResponse` with consistent structure:

```python
# Regardless of backend, you get the same interface
response = await backend.request(config)
print(response.status_code)    # HTTP status code
print(response.headers)        # Headers (lowercase keys)
print(response.content)        # Raw bytes
print(response.text)           # Decoded string
print(response.json_data)      # Parsed JSON (if applicable)
print(response.url)            # Final URL (after redirects)
```

## Troubleshooting

### HTTP/2 Not Working

**Problem**: You set `http2=True` but requests are still HTTP/1.1

**Solution**: Ensure you're using the niquests backend:
```python
client = ParallelRequests(backend="niquests", http2=True)
```

### Backend Not Found

**Problem**: `ConfigurationError: No suitable backend found`

**Solution**: Install a backend:
```bash
pip install parallel-requests[all]  # or specific backend
```

### Thread Pool Exhaustion (requests backend)

**Problem**: High CPU usage with requests backend

**Solution**: Reduce concurrency or use aiohttp/niquests:
```python
client = ParallelRequests(
    backend="requests",  # or "aiohttp"
    concurrency=10,      # Lower concurrency for requests
)
```

## Related Documentation

- **[Architecture](architecture.md)** - Design philosophy and component interaction
- **[Rate Limiting](rate-limiting.md)** - How rate limiting works with different backends
- **[Retry Strategy](retry-strategy.md)** - Retry behavior across backends
