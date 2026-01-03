# Proxy Rotation

Manage, validate, and rotate HTTP proxies with automatic health tracking.

## ProxyManager

Main proxy manager class for proxy rotation and validation.

```python
from fastreq.utils.proxies import ProxyManager, ProxyConfig

config = ProxyConfig(
    enabled=True,
    list=[
        "192.168.1.1:8080",
        "192.168.1.2:8080:user:pass",
    ],
    retry_delay=60.0,
    validation_timeout=5.0,
)

manager = ProxyManager(config)

# Get next available proxy
proxy = await manager.get_next()

# Mark proxy as failed
await manager.mark_failed(proxy)

# Mark proxy as successful
await manager.mark_success(proxy)
```

### ProxyManager Methods

| Method | Return Type | Description |
|--------|-------------|-------------|
| `get_next()` | `Optional[str]` | Get next available proxy |
| `mark_failed(proxy)` | `None` | Mark proxy as failed |
| `mark_success(proxy)` | `None` | Mark proxy as successful |
| `count()` | `int` | Get total proxy count |
| `count_available()` | `int` | Get available proxy count |
| `validate(proxy)` | `bool` | Validate proxy format (class method) |

---

## ProxyConfig

Configuration for proxy rotation.

```python
from fastreq.utils.proxies import ProxyConfig

config = ProxyConfig(
    enabled=True,                      # Enable proxy rotation
    list=["192.168.1.1:8080"],        # Proxy list
    webshare_url="https://...",       # Webshare proxy list URL
    free_proxies=False,               # Fetch free proxies
    retry_delay=60.0,                 # Seconds before retrying failed proxy
    validation_timeout=5.0,           # Proxy validation timeout
)
```

### ProxyConfig Attributes

| Attribute | Type | Default | Description |
|-----------|------|---------|-------------|
| `enabled` | `bool` | `False` | Enable proxy rotation |
| `list` | `List[str] \| None` | `None` | List of proxy URLs |
| `webshare_url` | `str \| None` | `None` | Webshare proxy list URL |
| `free_proxies` | `bool` | `False` | Enable free proxy fetching |
| `retry_delay` | `float` | `60.0` | Seconds before retrying failed proxy |
| `validation_timeout` | `float` | `5.0` | Timeout for proxy validation |

---

## Proxy Formats

### Supported Formats

1. **IP:PORT**
   ```python
   "192.168.1.1:8080"
   ```

2. **IP:PORT:USER:PASS**
   ```python
   "192.168.1.1:8080:admin:password"
   ```

3. **http://USER:PASS@HOST:PORT**
   ```python
   "http://user:pass@proxy.example.com:8080"
   ```

4. **https://USER:PASS@HOST:PORT**
   ```python
   "https://user:pass@proxy.example.com:8080"
   ```

### Proxy Validation

```python
from fastreq.utils.proxies import ProxyManager

# Validate proxy format
is_valid = ProxyManager.validate("192.168.1.1:8080")  # True
is_valid = ProxyManager.validate("invalid-proxy")     # False
```

### IP Validation

IP octets are validated to be in range 0-255:

```python
# Valid
"192.168.1.1:8080"    # True

# Invalid
"256.168.1.1:8080"    # False (256 > 255)
"192.168.1:8080"      # False (missing octet)
```

---

## Loading Proxies

### From Configuration

```python
config = ProxyConfig(
    enabled=True,
    list=[
        "192.168.1.1:8080",
        "192.168.1.2:8080:user:pass",
    ],
)
manager = ProxyManager(config)
```

### From Environment Variable

```bash
# .env or environment
PROXIES=192.168.1.1:8080,192.168.1.2:8080,http://user:pass@proxy:8080
```

```python
import os
from fastreq.utils.proxies import ProxyConfig

config = ProxyConfig(enabled=True)
manager = ProxyManager(config)  # Loads from PROXIES env var
```

### From Webshare

```python
config = ProxyConfig(
    enabled=True,
    webshare_url="https://proxy.webshare.io/api/v2/proxy/list",
)
manager = ProxyManager(config)
```

Webshare format: One per line, `IP:PORT:USER:PASS`

---

## Proxy Health Tracking

### Failed Proxies

Failed proxies are temporarily excluded from rotation:

```python
config = ProxyConfig(
    enabled=True,
    list=["proxy1:8080", "proxy2:8080", "proxy3:8080"],
    retry_delay=60.0,  # Retry failed proxies after 60s
)

manager = ProxyManager(config)

# Proxy fails
proxy = await manager.get_next()  # e.g., "proxy1:8080"
await manager.mark_failed(proxy)   # Excluded for 60s

# Next request gets different proxy
next_proxy = await manager.get_next()  # "proxy2:8080" (not proxy1)

# After 60s, proxy1 is available again
```

### Successful Proxies

Successful proxies are cleared from failed state:

```python
proxy = await manager.get_next()
# Make request
try:
    result = await make_request(proxy)
    await manager.mark_success(proxy)  # Clear failed status
except Exception:
    await manager.mark_failed(proxy)
```

### Monitoring

```python
# Total proxies
total = manager.count()

# Available proxies (not failed)
available = manager.count_available()

# Failed proxies
failed = total - available
```

---

## Using Proxy Rotation

### In ParallelRequests Client

```python
from fastreq import ParallelRequests

# Enable proxy rotation
client = ParallelRequests(
    random_proxy=True,
    proxy="http://proxy:8080",  # Base proxy
)
```

### Standalone Usage

```python
from fastreq.utils.proxies import ProxyManager, ProxyConfig

config = ProxyConfig(
    enabled=True,
    list=["proxy1:8080", "proxy2:8080"],
)
manager = ProxyManager(config)

async def make_request(url):
    proxy = await manager.get_next()
    if not proxy:
        raise Exception("No proxies available")

    try:
        response = await fetch(url, proxy=proxy)
        await manager.mark_success(proxy)
        return response
    except Exception as e:
        await manager.mark_failed(proxy)
        raise e

results = await asyncio.gather(*[make_request(url) for url in urls])
```

---

## Proxy Validation Patterns

Regex patterns for proxy validation:

```python
PROXY_PATTERNS = [
    r"^(\d{1,3}\.){3}\d{1,3}:\d{1,5}$",                    # IP:PORT
    r"^(\d{1,3}\.){3}\d{1,3}:\d{1,5}:[^:]+:[^:]+$",        # IP:PORT:USER:PASS
    r"^http://[^:]+:[^@]+@[^:]+:\d+$",                     # http://user:pass@host:port
    r"^https://[^:]+:[^@]+@[^:]+\d+$",                     # https://user:pass@host:port
]
```

---

## ProxyValidationError

Raised when proxy validation or loading fails:

```python
from fastreq.utils.proxies import ProxyValidationError

try:
    config = ProxyConfig(webshare_url="https://invalid-url")
    manager = ProxyManager(config)
except ProxyValidationError as e:
    print(f"Proxy validation error: {e}")
```

---

## See Also

- [How-to: Use Proxies](../how-to-guides/use-proxies.md)
- [Reference: Exceptions](exceptions.md)
