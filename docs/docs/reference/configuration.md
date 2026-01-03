# Configuration

Configure fastreq using client parameters, environment variables, or global config.

## FastRequests Parameters

Configure the `FastRequests` client with these parameters:

```python
from fastreq import FastRequests

client = FastRequests(
    backend="auto",
    concurrency=20,
    max_retries=3,
    rate_limit=10.0,
    rate_limit_burst=5,
    http2=True,
    follow_redirects=True,
    verify_ssl=True,
    timeout=30.0,
    cookies={"session": "abc123"},
    random_user_agent=True,
    random_proxy=False,
    debug=False,
    verbose=True,
    return_none_on_failure=False,
)
```

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `backend` | `str` | `"auto"` | Backend to use: `"auto"`, `"niquests"`, `"aiohttp"`, or `"requests"` |
| `concurrency` | `int` | `20` | Maximum concurrent requests |
| `max_retries` | `int` | `3` | Maximum retry attempts per request |
| `rate_limit` | `float \| None` | `None` | Requests per second (None = no limit) |
| `rate_limit_burst` | `int` | `5` | Burst size for rate limiter |
| `http2` | `bool` | `True` | Enable HTTP/2 (if supported by backend) |
| `follow_redirects` | `bool` | `True` | Follow HTTP redirects |
| `verify_ssl` | `bool` | `True` | Verify SSL certificates |
| `timeout` | `float \| None` | `None` | Default timeout per request (seconds) |
| `cookies` | `dict[str, str] \| None` | `None` | Initial session cookies |
| `random_user_agent` | `bool` | `True` | Rotate user agents |
| `random_proxy` | `bool` | `False` | Enable proxy rotation |
| `debug` | `bool` | `False` | Enable debug logging |
| `verbose` | `bool` | `True` | Enable verbose output |
| `return_none_on_failure` | `bool` | `False` | Return None on failure instead of raising |

---

## Request-Level Overrides

Override client settings per request:

```python
async with FastRequests(
    timeout=30,
    follow_redirects=True
) as client:
    # Override timeout for this request
    result1 = await client.request(
        "https://example.com/1",
        timeout=60
    )

    # Override follow_redirects for this request
    result2 = await client.request(
        "https://example.com/2",
        follow_redirects=False
    )
```

Overrideable parameters:
- `timeout`
- `follow_redirects`
- `verify_ssl`

---

## Environment Variables

Set defaults using environment variables:

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `PARALLEL_BACKEND` | `str` | `"auto"` | Default backend selection |
| `PARALLEL_CONCURRENCY` | `int` | `20` | Default concurrency limit |
| `PARALLEL_MAX_RETRIES` | `int` | `3` | Default max retries |
| `PARALLEL_RATE_LIMIT` | `float \| None` | `None` | Default rate limit (requests/sec) |
| `PARALLEL_RATE_LIMIT_BURST` | `int` | `5` | Rate limit burst size |
| `PARALLEL_HTTP2` | `bool` | `true` | Enable HTTP/2 |
| `PARALLEL_RANDOM_USER_AGENT` | `bool` | `true` | Rotate user agents |
| `PARALLEL_RANDOM_PROXY` | `bool` | `false` | Enable proxy rotation |
| `PARALLEL_PROXY_ENABLED` | `bool` | `false` | Enable proxy usage |
| `PARALLEL_FREE_PROXIES` | `bool` | `false` | Enable free proxy fetching |

### Using Environment Variables

Create a `.env` file:

```bash
# .env
PARALLEL_BACKEND=niquests
PARALLEL_CONCURRENCY=10
PARALLEL_RATE_LIMIT=5.0
PARALLEL_RATE_LIMIT_BURST=3
PARALLEL_DEBUG=false
```

Load in your application:

```python
from dotenv import load_dotenv
from fastreq.config import GlobalConfig

load_dotenv()
config = GlobalConfig.load_from_env()
```

---

## GlobalConfig

Use `GlobalConfig` for programmatic configuration:

```python
from fastreq.config import GlobalConfig

# Create config programmatically
config = GlobalConfig(
    backend="niquests",
    default_concurrency=10,
    rate_limit=5.0,
)

# Load from environment
config = GlobalConfig.load_from_env()

# Save to environment file
config.save_to_env(".env")

# Convert to dict
env_dict = config.to_env()
```

### GlobalConfig Attributes

| Attribute | Type | Default |
|-----------|------|---------|
| `backend` | `str` | `"auto"` |
| `default_concurrency` | `int` | `20` |
| `default_max_retries` | `int` | `3` |
| `rate_limit` | `float \| None` | `None` |
| `rate_limit_burst` | `int` | `5` |
| `http2_enabled` | `bool` | `True` |
| `random_user_agent` | `bool` | `True` |
| `random_proxy` | `bool` | `False` |
| `proxy_enabled` | `bool` | `False` |
| `free_proxies_enabled` | `bool` | `False` |

---

## Backend Selection

Choose a backend based on your needs:

### Auto (default)
Automatically selects the best available backend:
1. `niquests` (if installed) - Recommended
2. `aiohttp` (if installed)
3. `requests` (if installed)

```python
client = FastRequests(backend="auto")
```

### Niquests (Recommended)
Best performance with HTTP/2 support:
```python
client = FastRequests(backend="niquests")
```

Install: `pip install niquests`

### Aiohttp
Native async backend:
```python
client = FastRequests(backend="aiohttp")
```

Install: `pip install aiohttp`

### Requests
Synchronous backend (uses `asyncio` wrapper):
```python
client = FastRequests(backend="requests")
```

Install: `pip install requests`

---

## Cookie Management

Manage session cookies:

```python
async with FastRequests(cookies={"session": "abc123"}) as client:
    # Add cookies
    client.set_cookies({"user_id": "456"})

    # Make request (cookies sent automatically)
    result = await client.request("https://example.com/api")

    # Clear all cookies
    client.reset_cookies()
```

---

## See Also

- [API Reference: FastRequests](api/parallelrequests.md)
- [API Reference: GlobalConfig](api/globalconfig.md)
- [How-to: Select a Backend](../how-to-guides/select-backend.md)
