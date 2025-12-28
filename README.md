# Fast Parallel HTTP Requests

A Python library for making fast, efficient parallel HTTP requests using asyncio.

## Installation

```bash
pip install git+https://github.com/legout/parallel-requests
```

## Quick Start

```python
from parallel_requests import parallel_requests

# Make multiple requests concurrently
results = parallel_requests(
    urls=[
        "https://httpbin.org/get/1",
        "https://httpbin.org/get/2",
        "https://httpbin.org/get/3",
    ],
    concurrency=10,
    verbose=True,
)

print(results)
```

## Features

- **Async-first design**: Built on `asyncio` for maximum performance
- **Multiple backends**: Support for `niquests`, `aiohttp`, and `requests`+`asyncer`
- **Automatic retries**: Exponential backoff retry strategy
- **Proxy rotation**: Built-in support for random proxy selection
- **User agent rotation**: Random user agents for each request
- **Progress tracking**: Built-in progress bars with tqdm
- **Flexible API**: Single requests, parallel batches, or class-based usage

## API Reference

### `parallel_requests(urls, ...)`

Make parallel HTTP requests with sensible defaults.

**Parameters**:
- `urls` (str | list): URL(s) to request
- `keys` (list | str | None, optional): Optional keys for response mapping
- `method` (str, default="GET"): HTTP method
- `params` (dict | list | None, optional): Query parameters
- `data` (dict | list | None, optional): Request body data
- `json` (dict | list | None, optional): JSON request body
- `headers` (dict | None, optional): Request headers
- `parse_func` (callable, optional): Custom function to parse responses
- `return_type` (str, default="json"): Response type ("json", "text", "content")
- `concurrency` (int, default=100): Maximum concurrent requests
- `max_retries` (int, default=5): Maximum retry attempts
- `random_delay_multiplier` (int | float, default=1): Random delay multiplier
- `random_proxy` (bool, default=False): Use random proxy from list
- `random_user_agent` (bool, default=True): Use random user agent
- `proxies` (list | None, optional): Custom proxy list
- `user_agents` (list | None, optional): Custom user agent list
- `cookies` (dict | None, optional): Request cookies
- `verbose` (bool, default=True): Show progress bar
- `debug` (bool, default=False): Enable debug logging
- `warnings` (bool, default=False): Show warning logs

**Returns**: dict | list | Response

### `parallel_requests_async(urls, ...)`

Async version of `parallel_requests()`. Returns a coroutine.

### `ParallelRequests` Class

For more control, use the class directly:

```python
from parallel_requests import ParallelRequests

async def main():
    async with ParallelRequests(
        concurrency=50,
        max_retries=3,
        random_user_agent=True,
    ) as pr:
        results = await pr.request(
            urls=["https://httpbin.org/get"] * 10,
            method="GET",
            return_type="json",
        )
        print(results)

import asyncio
asyncio.run(main())
```

## Examples

### With Custom Headers

```python
results = parallel_requests(
    urls=["https://api.example.com/data"],
    headers={"Authorization": "Bearer token123"},
)
```

### POST Requests with JSON Data

```python
results = parallel_requests(
    urls=["https://api.example.com/create"],
    method="POST",
    json={"name": "test", "value": 123},
)
```

### With Custom Parser

```python
def extract_id(response):
    return response.get("id", None)

results = parallel_requests(
    urls=["https://api.example.com/item/1"],
    parse_func=extract_id,
    keys=["item1"],
)
```

### With Keys for Response Mapping

```python
results = parallel_requests(
    urls=["https://api.example.com/user/1", "https://api.example.com/user/2"],
    keys=["user1", "user2"],
)

print(results["user1"])  # Response from first URL
print(results["user2"])  # Response from second URL
```

## Proxies

### Webshare.io Integration

For reliable proxies, use [webshare.io](https://www.webshare.io/):

1. Sign up for a plan
2. Get your proxy list export URL from Dashboard → Proxy → List → Download
3. Set environment variable:

**Linux/macOS:**
```bash
export WEBSHARE_PROXIES_URL="https://proxy.webshare.io/api/v2/proxy/list/download/YOUR_TOKEN/-/any/username/direct/-/"
```

**.env file:**
```env
WEBSHARE_PROXIES_URL="https://proxy.webshare.io/api/v2/proxy/list/download/YOUR_TOKEN/-/any/username/direct/-/"
```

### Free Proxies

Free proxies can be used by setting `random_proxy=True`:
- Note: Free proxies are unreliable and may be slow
- Some services block requests from known proxy IPs

```python
results = parallel_requests(
    urls=["https://httpbin.org/ip"],
    random_proxy=True,  # Uses free proxies from webshare or defaults
)
```

**Free proxy sources:**
- http://www.free-proxy-list.net
- https://free-proxy-list.net/anonymous-proxy.html
- https://free-proxy-list.net/uk-proxy.html

## Breaking Changes in v1.0.0

### Parameter Names Changed
- `url` → `urls`
- `key` → `keys`

**Before:**
```python
parallel_requests(
    url="https://example.com",
    key="result",
)
```

**After:**
```python
parallel_requests(
    urls="https://example.com",
    keys="result",
)
```

### Default Backend Changed
- The primary implementation is now `parallel_requests_asyncer` using `requests` + `asyncer`
- Previous implementations remain available but are not the default

### User Agents Loading
- USER_AGENTS now load lazily with default fallback
- Network calls at import time have been eliminated
- Call `update_user_agents()` to fetch fresh list from remote

## Advanced Usage

### Session Management

For multiple batches of requests, reuse a session:

```python
from parallel_requests import ParallelRequests

async def main():
    pr = ParallelRequests(concurrency=20)

    # First batch
    batch1 = await pr.request(urls=urls1)

    # Second batch (reuses session)
    batch2 = await pr.request(urls=urls2)

    # Cleanup
    await pr.close()

asyncio.run(main())
```

### Error Handling

```python
from parallel_requests import ParallelRequests

async with ParallelRequests(warnings=True) as pr:
    # Failed requests return None or {key: None}
    results = await pr.request(
        urls=["https://httpbin.org/status/500"],
        keys=["test"],
    )

    if results["test"] is None:
        print("Request failed!")
```

## Performance Tips

1. **Adjust concurrency**: Start with `concurrency=50`, tune based on server limits
2. **Use return_type="json"**: Faster than "text" or "content"
3. **Disable progress bar**: Set `verbose=False` for small batches
4. **Reuse sessions**: Use `ParallelRequests` class for multiple batches
5. **Consider proxies**: For rate-limited APIs, use proxies

## Contributing

Contributions are welcome! Please see the repository for guidelines.

## License

See LICENSE file for details.

---

**Support the project**: [Buy me a coffee](https://ko-fi.com/W7W0ACJPB)
