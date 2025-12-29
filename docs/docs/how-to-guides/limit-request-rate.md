# Limit Request Rate

Learn how to control request rate to avoid API quotas and be a good citizen.

## Token Bucket Algorithm

The library uses a token bucket algorithm for rate limiting:

- **Tokens**: A bucket fills with tokens at a constant rate (`rate_limit`)
- **Requests**: Each request consumes one token from the bucket
- **Burst**: The bucket can hold a maximum of `rate_limit_burst` tokens
- **Wait**: If bucket is empty, requests wait until tokens are available

This allows for smooth rate limiting while accommodating short bursts of traffic.

## Basic Rate Limiting

Set `rate_limit` to control requests per second:

```python
from parallel_requests import parallel_requests

# Limit to 10 requests per second
results = parallel_requests(
    urls=["https://api.example.com/endpoint"] * 50,
    rate_limit=10,  # 10 requests/second
)
```

## Configuring Burst Capacity

Use `rate_limit_burst` to allow temporary spikes in traffic:

```python
from parallel_requests import parallel_requests

# Allow bursts of 20 requests, then sustain 10 requests/second
results = parallel_requests(
    urls=["https://api.example.com/endpoint"] * 100,
    rate_limit=10,           # 10 requests/second sustained
    rate_limit_burst=20,     # Allow bursts of 20
)
```

With this configuration:
- First 20 requests execute immediately
- Subsequent requests execute at ~10 requests/second
- Bucket refills at 10 tokens/second

## Example: GitHub API Rate Limiting

GitHub API has a limit of 5,000 requests per hour (~1.4 requests/second):

```python
from parallel_requests import parallel_requests

# Safe rate limiting for GitHub API
results = parallel_requests(
    urls=[f"https://api.github.com/repos/{repo}" for repo in my_repos],
    rate_limit=1,            # Conservative rate
    rate_limit_burst=5,      # Allow small bursts
    headers={
        "Accept": "application/vnd.github.v3+json",
    },
)
```

## Example: Peak Load Handling

Handle peak loads with burst capacity:

```python
from parallel_requests import parallel_requests

# Allow bursts during peak traffic, sustain rate otherwise
results = parallel_requests(
    urls=["https://api.example.com/data"] * 100,
    rate_limit=20,           # Sustain 20 req/s
    rate_limit_burst=50,     # Allow bursts of 50
    concurrency=30,           # Max 30 concurrent
)
```

## Burst Behavior Explained

### Without Burst (rate_limit_burst=1)

```python
results = parallel_requests(
    urls=["https://api.example.com/data"] * 10,
    rate_limit=5,              # 5 req/s
    rate_limit_burst=1,       # No burst capacity
)
```

**Timing:**
- Request 1: 0s
- Request 2: 0.2s
- Request 3: 0.4s
- ...smooth ~0.2s between requests

### With Burst (rate_limit_burst=5)

```python
results = parallel_requests(
    urls=["https://api.example.com/data"] * 10,
    rate_limit=5,              # 5 req/s
    rate_limit_burst=5,       # Allow burst of 5
)
```

**Timing:**
- Request 1-5: ~0s (burst)
- Request 6: ~0.2s (bucket refilling)
- Request 7: ~0.4s
- ...smooth after burst is exhausted

## Combining Rate Limiting with Concurrency

Rate limiting works together with concurrency limits:

```python
results = parallel_requests(
    urls=["https://api.example.com/data"] * 100,
    concurrency=20,           # Max 20 concurrent requests
    rate_limit=10,            # 10 requests/second
    rate_limit_burst=15,      # Burst of 15
)
```

In this example:
- Up to 20 requests can start immediately (limited by concurrency)
- Only 10 requests/second complete (limited by rate limit)
- Burst of 15 allows initial spike

## Rate Limiting vs Concurrency

Understanding the difference:

| Parameter      | Purpose                          | Example                     |
|----------------|----------------------------------|-----------------------------|
| `concurrency`  | Max requests running at once    | Don't overwhelm server      |
| `rate_limit`   | Requests per second             | Respect API quotas          |
| `rate_limit_burst` | Allow temporary spikes      | Handle peak loads           |

```python
# Example: High concurrency, low rate limit
results = parallel_requests(
    urls=["https://api.example.com/data"] * 100,
    concurrency=50,           # Many concurrent connections
    rate_limit=5,             # But only 5 complete per second
    rate_limit_burst=10,      # Allow initial burst
)
```

## Disabling Rate Limiting

Set `rate_limit=None` to disable rate limiting:

```python
results = parallel_requests(
    urls=["https://api.example.com/data"] * 50,
    rate_limit=None,  # No rate limiting (use with caution!)
)
```

**Warning**: Only disable rate limiting when you control the target server and can handle the load.

## Monitoring Rate Limiting

Enable debug logging to see rate limiting in action:

```python
results = parallel_requests(
    urls=["https://api.example.com/data"] * 20,
    rate_limit=5,
    rate_limit_burst=10,
    debug=True,  # See rate limiting logs
)
```

Example output:
```
[DEBUG] Rate limit: 5.0 req/s, burst: 10
[DEBUG] Request 1: immediate (bucket: 9/10)
[DEBUG] Request 2: immediate (bucket: 8/10)
...
[DEBUG] Request 11: waiting 0.2s for token
```

## Best Practices

1. **Know Your API Limits**: Check documentation for rate limits
   ```python
   # GitHub: 5000 requests/hour ~ 1.4 req/s
   rate_limit=1
   ```

2. **Use Burst for Initialization**: Allow burst when starting up
   ```python
   rate_limit=10
   rate_limit_burst=20  # Warm-up burst
   ```

3. **Stay Conservative**: Set rate limit slightly below documented limits
   ```python
   # API says 10 req/s, use 8 to be safe
   rate_limit=8
   ```

4. **Test Different Values**: Find optimal rate for your use case
   ```python
   # Start conservative, increase if needed
   rate_limit=5  # Test this first
   ```

## See Also

- **[Handle Retries](handle-retries.md)** - Automatic retry configuration
- **[Debug Issues](debug-issues.md)** - Enable debug logging
- **[API Reference](../reference/configuration.md)** - Configuration options
