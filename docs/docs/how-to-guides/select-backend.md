# Select Backend

Learn how to choose and configure HTTP backends (niquests, aiohttp, requests).

## Backend Auto-Detection

The library automatically selects the best available backend:

```python
from parallel_requests import parallel_requests

# Auto-detection (default)
results = parallel_requests(
    urls=["https://httpbin.org/get"],
    backend="auto",  # Default behavior
)
```

**Detection Order:**
1. **niquests** - HTTP/2 support, streaming, async native
2. **aiohttp** - Streaming support, async native
3. **requests** - Sync-first, streaming via thread wrapper

## Explicit Backend Selection

Force a specific backend:

```python
from parallel_requests import parallel_requests

# Use niquests (recommended)
results = parallel_requests(
    urls=["https://httpbin.org/get"],
    backend="niquests",
)

# Use aiohttp
results = parallel_requests(
    urls=["https://httpbin.org/get"],
    backend="aiohttp",
)

# Use requests
results = parallel_requests(
    urls=["https://httpbin.org/get"],
    backend="requests",
)
```

## Backend Feature Comparison

| Feature              | niquests | aiohttp | requests |
|----------------------|---------|---------|----------|
| HTTP/2 Support       | ✅ Yes  | ❌ No   | ❌ No    |
| Streaming            | ✅ Yes  | ✅ Yes  | ✅ Yes   |
| Async Native         | ✅ Yes  | ✅ Yes  | ❌ No    |
| Sync Native          | ✅ Yes  | ❌ No   | ✅ Yes   |
| Connection Pooling   | ✅ Yes  | ✅ Yes  | ✅ Yes   |
| Cookies              | ✅ Yes  | ✅ Yes  | ✅ Yes   |
| Proxies              | ✅ Yes  | ✅ Yes  | ✅ Yes   |
| Session Reuse        | ✅ Yes  | ✅ Yes  | ✅ Yes   |

## When to Use Each Backend

### Use niquests When:

- You need HTTP/2 support
- You want the best performance
- You need both sync and async compatibility

```python
from parallel_requests import parallel_requests

# Best for modern APIs with HTTP/2
results = parallel_requests(
    urls=["https://api.example.com/data"] * 100,
    backend="niquests",
    concurrency=50,
)
```

### Use aiohttp When:

- You're building async/await applications
- You need efficient async I/O
- You're already using aiohttp

```python
import asyncio
from parallel_requests import parallel_requests_async

async def async_fetch():
    results = await parallel_requests_async(
        urls=["https://api.example.com/data"] * 100,
        backend="aiohttp",
        concurrency=50,
    )
    return results

results = asyncio.run(async_fetch())
```

### Use requests When:

- You need synchronous code
- You're working with existing requests-based code
- Compatibility is more important than performance

```python
from parallel_requests import parallel_requests

# Simple synchronous use
results = parallel_requests(
    urls=["https://api.example.com/data"] * 50,
    backend="requests",
)
```

## HTTP/2 Support Example

niquests supports HTTP/2 for better performance:

```python
from parallel_requests import parallel_requests

# HTTP/2 with niquests
results = parallel_requests(
    urls=["https://httpbin.org/get"] * 10,
    backend="niquests",
    debug=True,
)

# Other backends use HTTP/1.1
results = parallel_requests(
    urls=["https://httpbin.org/get"] * 10,
    backend="aiohttp",  # HTTP/1.1 only
)
```

**Benefits of HTTP/2:**
- Multiplexing: Multiple requests over single connection
- Header compression: Reduced bandwidth
- Server push: Optional optimization

## Backend Performance Comparison

Benchmark different backends:

```python
import time
from parallel_requests import parallel_requests

urls = ["https://httpbin.org/get"] * 100

for backend in ["niquests", "aiohttp", "requests"]:
    start = time.time()
    results = parallel_requests(
        urls=urls,
        backend=backend,
        concurrency=20,
    )
    elapsed = time.time() - start
    print(f"{backend}: {elapsed:.2f}s")
```

## Installing Backend-Specific Dependencies

Install with specific backend support:

```bash
# All backends (recommended)
pip install parallel-requests[all]

# niquests only (HTTP/2 support)
pip install parallel-requests[niquests]

# aiohttp only
pip install parallel-requests[aiohttp]

# requests only
pip install parallel-requests[requests]
```

## Checking Backend Availability

Check which backends are available:

```python
from parallel_requests.backends import get_available_backends

available = get_available_backends()
print(f"Available backends: {available}")
```

## Backend-Specific Configuration

Some backends support additional configuration:

```python
from parallel_requests import parallel_requests

# niquests-specific options
results = parallel_requests(
    urls=["https://httpbin.org/get"],
    backend="niquests",
    # Backend can expose additional options
)

# aiohttp-specific options
results = parallel_requests(
    urls=["https://httpbin.org/get"],
    backend="aiohttp",
    # Backend can expose additional options
)
```

## Connection Pooling by Backend

All backends support connection pooling:

```python
from parallel_requests import parallel_requests

# Connection pooling is automatic
results = parallel_requests(
    urls=["https://api.example.com/data"] * 100,
    concurrency=20,
    backend="niquests",
)

# Same request reuses connections (if using context manager)
```

## Session Reuse with Context Manager

Reuse sessions across multiple batches:

```python
import asyncio
from parallel_requests import ParallelRequests

async def reuse_session():
    async with ParallelRequests(backend="niquests") as client:
        # First batch
        results1 = await client.request(
            urls=["https://api.github.com/repos/python/cpython"],
        )

        # Second batch (reuses session)
        results2 = await client.request(
            urls=["https://api.github.com/repos/python/pypy"],
        )

        return results1, results2

results1, results2 = asyncio.run(reuse_session())
```

## Error Handling by Backend

Different backends handle errors differently:

```python
from parallel_requests import parallel_requests

try:
    results = parallel_requests(
        urls=["https://invalid-url.com"],
        backend="niquests",
    )
except Exception as e:
    print(f"niquests error: {e}")

try:
    results = parallel_requests(
        urls=["https://invalid-url.com"],
        backend="aiohttp",
    )
except Exception as e:
    print(f"aiohttp error: {e}")
```

## Backend-Specific Timeout Handling

Timeouts work consistently across backends:

```python
from parallel_requests import parallel_requests

# Timeout works the same for all backends
results = parallel_requests(
    urls=["https://httpbin.org/delay/5"],
    timeout=3,  # 3 second timeout
    backend="niquests",  # or aiohttp, requests
)
```

## Backend Selection Strategy

### Production Recommendation

```python
from parallel_requests import parallel_requests

# Use auto-detection for production
results = parallel_requests(
    urls=["https://api.example.com/data"] * 100,
    backend="auto",  # Will pick niquests if available
    concurrency=20,
)
```

### Development Strategy

```python
# During development, test with multiple backends
for backend in ["niquests", "aiohttp", "requests"]:
    try:
        results = parallel_requests(
            urls=test_urls,
            backend=backend,
        )
        print(f"{backend}: OK")
    except Exception as e:
        print(f"{backend}: FAILED - {e}")
```

## Best Practices

1. **Use Auto-Detection**: Let the library choose the best backend
   ```python
   backend="auto"  # Default
   ```

2. **Prefer niquests**: For HTTP/2 support and best performance
   ```python
   backend="niquests"
   ```

3. **Test All Backends**: Verify compatibility during development
   ```python
   for backend in ["niquests", "aiohttp", "requests"]:
       # Test code
   ```

4. **Handle Backend Errors**: Catch backend-specific errors
   ```python
   except Exception as e:
       print(f"Backend error: {e}")
   ```

5. **Use Context Managers**: Reuse sessions for better performance
   ```python
   async with ParallelRequests() as client:
       await client.request(urls=urls)
   ```

## See Also

- **[Make Parallel Requests](make-parallel-requests.md)** - Request configuration
- **[Stream Large Files](stream-large-files.md)** - Backend streaming differences
- **[API Reference](../reference/backend.md)** - Backend documentation
