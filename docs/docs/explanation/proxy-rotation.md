# Proxy Rotation

Proxy rotation distributes requests across multiple proxy servers to avoid IP-based rate limits, bypass geographical restrictions, and maintain anonymity.

## Why Proxy Rotation?

### IP-Based Rate Limits

Many services enforce rate limits based on IP address:

```
Without proxy rotation:
Your IP: 192.168.1.100
├─ Request 1  → API (count: 1/100)
├─ Request 2  → API (count: 2/100)
├─ Request 3  → API (count: 3/100)
...
└─ Request 100→ API (count: 100/100)
                  BLOCKED! ❌

With proxy rotation:
Request 1  → Proxy A (192.168.1.10)  → API (count: 1/100)
Request 2  → Proxy B (192.168.1.11)  → API (count: 1/100)
Request 3  → Proxy C (192.168.1.12)  → API (count: 1/100)
Request 4  → Proxy A (192.168.1.10)  → API (count: 2/100)
Request 5  → Proxy B (192.168.1.11)  → API (count: 2/100)
...
All requests succeed! ✓
```

### Use Cases

**1. Web Scraping**
- Avoid IP blocks when scraping at scale
- Distribute load across multiple IPs
- Maintain anonymity

**2. API Access**
- Bypass per-IP rate limits
- Access geo-restricted APIs
- Reduce risk of API key deactivation

**3. Testing**
- Simulate requests from different locations
- Test geo-specific functionality
- Verify load balancing

**4. Privacy**
- Hide your real IP address
- Prevent tracking
- Access region-locked content

## Proxy Formats Supported

The proxy manager supports multiple proxy formats for flexibility:

### Format 1: IP:PORT

```python
"192.168.1.10:8080"
"203.0.113.5:3128"
```

**Pattern**: `^(\d{1,3}\.){3}\d{1,3}:\d{1,5}$`

### Format 2: IP:PORT:USER:PASS

```python
"192.168.1.10:8080:admin:secret"
"203.0.113.5:3128:user:pass123"
```

**Pattern**: `^(\d{1,3}\.){3}\d{1,3}:\d{1,5}:[^:]+:[^:]+$`

### Format 3: Full URL with Credentials

```python
"http://admin:secret@192.168.1.10:8080"
"https://user:pass@proxy.example.com:3128"
```

**Patterns**:
- `^http://[^:]+:[^@]+@[^:]+:\d+$`
- `^https://[^:]+:[^@]+@[^:]+\d+$`

### Automatic Format Conversion

The proxy manager normalizes formats internally:

```python
# Input in IP:PORT:USER:PASS format
"192.168.1.10:8080:admin:secret"

# Internally converted to URL format
"http://admin:secret@192.168.1.10:8080"
```

## Proxy Validation

The proxy manager validates proxies to ensure they're properly formatted before use.

### Format Validation

```python
@classmethod
def validate(cls, proxy: str) -> bool:
    """Validate proxy format."""
    if not proxy or not isinstance(proxy, str):
        return False

    for pattern in cls.PROXY_PATTERNS:
        if re.match(pattern, proxy):
            # For IP-based formats, validate octets
            if pattern in cls.PROXY_PATTERNS[:2]:
                ip_part = proxy.split(":")[0]
                if not cls._validate_ip_octets(ip_part):
                    return False
            return True

    return False
```

### IP Octet Validation

IP addresses are validated to ensure each octet is in the valid range (0-255):

```python
@classmethod
def _validate_ip_octets(cls, ip: str) -> bool:
    """Validate IP octets are in range 0-255."""
    octets = ip.split(".")
    if len(octets) != 4:
        return False

    try:
        return all(0 <= int(octet) <= 255 for octet in octets)
    except ValueError:
        return False
```

### Validation Examples

```python
ProxyManager.validate("192.168.1.10:8080")              # ✓ Valid
ProxyManager.validate("192.168.1.10:8080:admin:pass")    # ✓ Valid
ProxyManager.validate("http://admin:pass@192.168.1.10:8080")  # ✓ Valid

ProxyManager.validate("256.1.1.1:8080")                  # ✗ Invalid octet
ProxyManager.validate("192.168.1:8080")                  # ✗ Invalid IP format
ProxyManager.validate("not-a-proxy")                     # ✗ Invalid format
```

### Loading and Filtering

When proxies are loaded, invalid ones are filtered out:

```python
def _load_proxies(self) -> None:
    proxies = []

    # Load from various sources
    if self._config.list:
        proxies.extend(self._config.list)

    # Filter invalid proxies
    self._proxies = []
    for proxy in proxies:
        if self.validate(proxy):
            self._proxies.append(proxy)
        else:
            logger.debug(f"Filtered invalid proxy format: {proxy}")
```

## Failed Proxy Tracking

The proxy manager tracks failed proxies to avoid repeatedly using problematic ones.

### Failed Proxy State

```python
class ProxyManager:
    def __init__(self, config: ProxyConfig):
        self._proxies: List[str] = []
        self._failed_proxies: Dict[str, float] = {}
        self._lock = asyncio.Lock()
```

- `_proxies`: All valid proxies
- `_failed_proxies`: Failed proxies with retry timestamps
- `_lock`: Async lock for thread-safe operations

### Marking Failed Proxies

```python
async def mark_failed(self, proxy: str) -> None:
    """Mark proxy as failed (unavailable for retry_delay)."""
    async with self._lock:
        if proxy in self._proxies:
            self._failed_proxies[proxy] = (
                time.time() + self._config.retry_delay
            )
```

When a proxy fails, it's marked with a timestamp indicating when it should be retried.

### Marking Successful Proxies

```python
async def mark_success(self, proxy: str) -> None:
    """Mark proxy as successful (clear failed status)."""
    async with self._lock:
        self._failed_proxies.pop(proxy, None)
```

If a proxy succeeds again, its failed status is cleared.

### Getting Next Proxy

```python
async def get_next(self) -> Optional[str]:
    """Get next available proxy."""
    async with self._lock:
        now = time.time()

        # Remove expired failed entries
        self._failed_proxies = {
            p: t for p, t in self._failed_proxies.items() if t > now
        }

        # Get available proxies (not in failed state)
        available = [
            p for p in self._proxies
            if p not in self._failed_proxies
        ]

        if not available:
            return None

        return random.choice(available)
```

### Failed Proxy Lifecycle

```
Time 0s: Proxy fails → mark_failed() → _failed_proxies[proxy] = 60s
Time 10s: get_next() → Proxy excluded from selection
Time 30s: get_next() → Proxy excluded from selection
Time 60s: get_next() → Expired, removed from _failed_proxies
Time 60s: Proxy available for selection again
```

### Retry Delay Configuration

```python
@dataclass
class ProxyConfig:
    retry_delay: float = 60.0  # Seconds before retrying failed proxy
```

Default retry delay is 60 seconds. Adjust based on your needs:

```python
# Short retry delay for quick testing
ProxyConfig(retry_delay=10.0)

# Long retry delay for production scraping
ProxyConfig(retry_delay=300.0)  # 5 minutes
```

## WebShare.io Integration

The proxy manager integrates with WebShare.io for easy proxy management.

### Loading from WebShare

```python
def _load_webshare_proxies(self, url: str) -> List[str]:
    """Load proxies from WebShare.io URL."""
    import requests

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()

        proxies = []
        for line in response.text.strip().split("\n"):
            line = line.strip()
            if not line:
                continue

            # WebShare format: IP:PORT:USER:PASS
            parts = line.split(":")
            if len(parts) >= 4:
                ip, port, user, pw = parts[:4]
                proxy = f"http://{user}:{pw}@{ip}:{port}"
                proxies.append(proxy)

        return proxies

    except Exception as e:
        raise ProxyValidationError(
            f"Failed to load webshare proxies: {e}"
        ) from e
```

### Using WebShare Proxies

```python
from parallel_requests.utils.proxies import ProxyManager, ProxyConfig

config = ProxyConfig(
    enabled=True,
    webshare_url="https://your-webshare-proxy-list-url",
    retry_delay=60.0,
)

manager = ProxyManager(config)
proxy = await manager.get_next()
```

### Environment Variable Loading

Proxies can also be loaded from the `PROXIES` environment variable:

```python
# Set environment variable
export PROXIES="192.168.1.10:8080,192.168.1.11:8080"

# Automatically loaded
manager = ProxyManager(config)
```

## Proxy Manager Internals

### Thread Safety

All proxy operations are protected by an async lock:

```python
async def get_next(self) -> Optional[str]:
    async with self._lock:  # Thread-safe
        # Modify shared state
```

This ensures multiple concurrent tasks can safely access the proxy manager.

### Proxy Statistics

The proxy manager provides statistics:

```python
def count(self) -> int:
    """Get total number of proxies."""
    return len(self._proxies)

def count_available(self) -> int:
    """Get number of available proxies."""
    now = time.time()
    return sum(
        1 for p in self._proxies
        if p not in self._failed_proxies
        or self._failed_proxies[p] <= now
    )
```

### Random Selection

Proxies are selected randomly to distribute load:

```python
return random.choice(available)
```

Random selection helps avoid:
- Predictable patterns
- Uneven proxy usage
- Hotspots on specific proxies

## Example Usage

### Basic Proxy Rotation

```python
from parallel_requests import ParallelRequests
from parallel_requests.utils.proxies import ProxyManager, ProxyConfig

# Configure proxy rotation
proxy_config = ProxyConfig(
    enabled=True,
    list=[
        "192.168.1.10:8080",
        "192.168.1.11:8080:admin:pass",
        "http://user:pass@192.168.1.12:8080",
    ],
    retry_delay=60.0,
)

# Create client with proxy rotation
client = ParallelRequests(
    random_proxy=True,  # Enable proxy rotation
    concurrency=10,
)
```

### WebShare Integration

```python
proxy_config = ProxyConfig(
    enabled=True,
    webshare_url="https://your-api.webshare.io/api/v2/proxy",
    retry_delay=120.0,  # 2 minutes
)

manager = ProxyManager(proxy_config)
print(f"Loaded {manager.count()} proxies")
```

### Monitoring Proxy Health

```python
manager = ProxyManager(proxy_config)

# Check proxy status
print(f"Total proxies: {manager.count()}")
print(f"Available proxies: {manager.count_available()}")

# Get next available proxy
proxy = await manager.get_next()
if proxy:
    print(f"Using proxy: {proxy}")
else:
    print("No proxies available!")
```

## Best Practices

### 1. Use Multiple Proxies

Don't rely on a single proxy:

```python
# Good: Multiple proxies for rotation
ProxyConfig(list=[
    "192.168.1.10:8080",
    "192.168.1.11:8080",
    "192.168.1.12:8080",
])

# Bad: Single proxy (no rotation benefit)
ProxyConfig(list=["192.168.1.10:8080"])
```

### 2. Handle Proxy Exhaustion

When all proxies fail, the request will fail without a proxy:

```python
proxy = await manager.get_next()
if not proxy:
    logger.error("All proxies failed!")
    # Handle gracefully: wait, alert, etc.
```

### 3. Monitor Failed Proxies

Track proxy health and rotation:

```python
logger.info(f"Proxies: {manager.count_available()}/{manager.count()}")

if manager.count_available() < manager.count() * 0.5:
    logger.warning("More than 50% of proxies failed!")
```

### 4. Use Appropriate Retry Delays

Adjust retry delay based on proxy quality:

```python
# High-quality proxies: Short retry delay
ProxyConfig(retry_delay=30.0)

# Low-quality proxies: Long retry delay
ProxyConfig(retry_delay=300.0)
```

### 5. Validate Proxies Before Use

The manager validates format, but consider testing connectivity:

```python
# Format validation is automatic
# You might want to add connectivity tests
```

## Troubleshooting

### All Proxies Failing

**Problem**: `count_available()` returns 0

**Possible Causes**:
1. All proxies marked as failed
2. Retry delay too long
3. Proxies genuinely offline

**Solutions**:
```python
# Reduce retry delay
ProxyConfig(retry_delay=30.0)  # Instead of 60.0

# Check proxy connectivity manually
# Consider using a proxy health check service
```

### Invalid Proxy Format

**Problem**: Proxies being filtered out

**Solution**: Check format:
```python
from parallel_requests.utils.proxies import ProxyManager

ProxyManager.validate("192.168.1.10:8080")  # Should return True
ProxyManager.validate("invalid")             # Should return False
```

### Proxy Not Working

**Problem**: Requests still failing with proxy

**Possible Causes**:
1. Proxy is offline
2. Credentials incorrect
3. Proxy blocked by target

**Solution**: Test proxy manually:
```python
import requests

proxy = "http://user:pass@192.168.1.10:8080"
try:
    response = requests.get(
        "https://httpbin.org/ip",
        proxies={"http": proxy, "https": proxy},
        timeout=10
    )
    print(response.json())  # Should show proxy IP
except Exception as e:
    print(f"Proxy failed: {e}")
```

## Related Documentation

- **[How-to: Use Proxies](../how-to-guides/use-proxies.md)** - Practical proxy usage guide
- **[Architecture](architecture.md)** - How proxy rotation integrates with other components
