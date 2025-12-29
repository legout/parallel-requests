# Use Proxies

Learn how to configure proxy rotation and integrate with proxy providers.

## Setting Up Proxies

Proxies can be configured via environment variable or code:

### Using Environment Variables

Set the `PARALLEL_REQUESTS_PROXIES` environment variable:

```bash
export PARALLEL_REQUESTS_PROXIES="http://proxy1:8080,http://proxy2:8080,socks5://proxy3:1080"
```

### Using .env File

Create a `.env` file:

```env
# .env
PARALLEL_REQUESTS_PROXIES=http://proxy1:8080,http://proxy2:8080,socks5://proxy3:1080
```

Load with python-dotenv:

```python
from dotenv import load_dotenv
from parallel_requests import parallel_requests

load_dotenv()

results = parallel_requests(
    urls=["https://httpbin.org/ip"] * 5,
)
```

### Using Code Configuration

Pass `proxies` directly:

```python
from parallel_requests import parallel_requests

proxies = [
    "http://proxy1.example.com:8080",
    "http://proxy2.example.com:8080",
    "socks5://proxy3.example.com:1080",
]

results = parallel_requests(
    urls=["https://httpbin.org/ip"] * 10,
    proxies=proxies,
)
```

## Proxy Rotation

The library automatically rotates through the proxy list:

```python
from parallel_requests import parallel_requests

proxies = [
    "http://proxy1:8080",
    "http://proxy2:8080",
    "http://proxy3:8080",
]

results = parallel_requests(
    urls=["https://httpbin.org/ip"] * 9,
    proxies=proxies,
)

# Requests are distributed across proxies
# proxy1: requests 1, 4, 7
# proxy2: requests 2, 5, 8
# proxy3: requests 3, 6, 9
```

## WebShare.io Integration

Use WebShare.io rotating proxies:

```python
import os
from parallel_requests import parallel_requests

# Set WebShare.io proxy (or use environment variable)
webshare_proxy = f"http://{os.getenv('WEBSHARE_USERNAME')}:{os.getenv('WEBSHARE_PASSWORD')}@p.webshare.io:80"

results = parallel_requests(
    urls=["https://httpbin.org/ip"] * 10,
    proxies=[webshare_proxy],
)
```

### WebShare.io in .env File

```env
# .env
WEBSHARE_USERNAME=your_username
WEBSHARE_PASSWORD=your_password
PARALLEL_REQUESTS_PROXIES=http://${WEBSHARE_USERNAME}:${WEBSHARE_PASSWORD}@p.webshare.io:80
```

## Verifying Proxy Usage

Use httpbin.org to verify which proxy was used:

```python
from parallel_requests import parallel_requests

proxies = [
    "http://proxy1.example.com:8080",
    "http://proxy2.example.com:8080",
]

results = parallel_requests(
    urls=["https://httpbin.org/ip"] * 6,
    proxies=proxies,
)

for result in results:
    print(f"IP: {result['origin']}")
```

## Proxy Authentication

Use authenticated proxies:

```python
from parallel_requests import parallel_requests

proxies = [
    "http://user:pass@proxy1.example.com:8080",
    "http://user:pass@proxy2.example.com:8080",
]

results = parallel_requests(
    urls=["https://httpbin.org/ip"] * 5,
    proxies=proxies,
)
```

**Security Note**: Avoid hardcoding credentials. Use environment variables instead:

```python
import os
from parallel_requests import parallel_requests

proxies = [
    f"http://{os.getenv('PROXY_USER')}:{os.getenv('PROXY_PASS')}@proxy1:8080",
]

results = parallel_requests(
    urls=["https://httpbin.org/ip"] * 5,
    proxies=proxies,
)
```

## Different Proxy Types

The library supports HTTP, HTTPS, and SOCKS5 proxies:

```python
from parallel_requests import parallel_requests

proxies = [
    "http://proxy.example.com:8080",      # HTTP proxy
    "https://secure-proxy.com:443",        # HTTPS proxy
    "socks5://socks-proxy.com:1080",      # SOCKS5 proxy
]

results = parallel_requests(
    urls=["https://httpbin.org/ip"] * 6,
    proxies=proxies,
)
```

## Proxy-Specific URLs

Route specific URLs through different proxies:

```python
from parallel_requests import parallel_requests

results = parallel_requests(
    urls=[
        "https://api.github.com/repos/python/cpython",
        "https://api.github.com/repos/python/pypy",
    ],
    proxies=[
        "http://proxy-github:8080",  # First URL
        "http://proxy-github:8080",  # Second URL
    ],
)
```

## No Proxy Configuration

To bypass proxy for specific domains:

```python
import os
os.environ['NO_PROXY'] = 'localhost,127.0.0.1,.local'

from parallel_requests import parallel_requests

results = parallel_requests(
    urls=["https://httpbin.org/ip"],
)
```

## Troubleshooting Proxy Issues

### Test Proxy Connectivity

Test if a proxy works:

```python
import requests

try:
    response = requests.get(
        "https://httpbin.org/ip",
        proxies={"http": "http://proxy.example.com:8080"},
        timeout=10,
    )
    print(f"Proxy working: {response.json()['origin']}")
except Exception as e:
    print(f"Proxy failed: {e}")
```

### Enable Debug Logging

See which proxy is being used:

```python
from parallel_requests import parallel_requests

results = parallel_requests(
    urls=["https://httpbin.org/ip"] * 3,
    proxies=["http://proxy1:8080", "http://proxy2:8080"],
    debug=True,
)
```

### Common Proxy Errors

```python
from parallel_requests import parallel_requests, ProxyError

try:
    results = parallel_requests(
        urls=["https://httpbin.org/ip"],
        proxies=["http://invalid-proxy:8080"],
    )
except ProxyError as e:
    print(f"Proxy error: {e}")
    # Check proxy address, port, and authentication
```

## Free Proxies (Experimental)

The library has experimental support for fetching free proxies, but this feature is not fully implemented yet.

```python
from parallel_requests import parallel_requests

# This is experimental and may not work
results = parallel_requests(
    urls=["https://httpbin.org/ip"] * 5,
    use_free_proxies=True,  # Experimental
)
```

**Warning**: Free proxies are unreliable and slow. Use a paid proxy service like WebShare.io for production use.

## Best Practices

1. **Use Environment Variables**: Store proxy URLs in `.env` files
2. **Monitor Proxy Health**: Check proxy status before large batches
3. **Handle Failures**: Use `return_none_on_failure` for unreliable proxies
4. **Rotate Properly**: Use enough proxies to distribute load
5. **Use Paid Services**: Free proxies are unreliable for production

## Example: Robust Proxy Configuration

```python
import os
from dotenv import load_dotenv
from parallel_requests import parallel_requests

load_dotenv()

# Load proxies from environment
proxies_str = os.getenv("PARALLEL_REQUESTS_PROXIES", "")
proxies = [p.strip() for p in proxies_str.split(",") if p.strip()]

# Add authenticated proxy if configured
webshare_user = os.getenv("WEBSHARE_USERNAME")
webshare_pass = os.getenv("WEBSHARE_PASSWORD")
if webshare_user and webshare_pass:
    webshare_proxy = f"http://{webshare_user}:{webshare_pass}@p.webshare.io:80"
    proxies.append(webshare_proxy)

# Make requests with fallback
results = parallel_requests(
    urls=["https://httpbin.org/ip"] * 10,
    proxies=proxies if proxies else None,
    max_retries=2,
    return_none_on_failure=True,
    debug=True,
)

# Filter successful results
successful = [r for r in results if r is not None]
print(f"Successful requests: {len(successful)}/{len(results)}")
```

## See Also

- **[Debug Issues](debug-issues.md)** - Troubleshoot proxy problems
- **[Handle Retries](handle-retries.md)** - Configure retry logic for unreliable proxies
- **[API Reference](../reference/configuration.md)** - Configuration options
