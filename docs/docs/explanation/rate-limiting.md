# Rate Limiting

Rate limiting controls the rate at which requests are sent to prevent overwhelming servers or hitting API rate limits. The fastreq library uses the **token bucket algorithm** for efficient and flexible rate limiting.

## Token Bucket Algorithm

The token bucket algorithm is a fundamental rate limiting technique that allows for both controlled request rates and burst capability.

### How It Works

Imagine a bucket that holds tokens:

```
┌─────────────────────────────┐
│      Token Bucket           │
│                             │
│  Token Token Token Token    │  ← burst size (max tokens)
│                             │
│  Refill: 10 tokens/second   │
└─────────────────────────────┘
         │
         ▼
   Make request?
   Consume 1 token
```

### Key Concepts

**Bucket Size (Burst)**: Maximum number of tokens the bucket can hold.

**Refill Rate**: How quickly tokens are added to the bucket (tokens per second).

**Token Consumption**: Each request consumes one token.

### Algorithm Details

```python
class TokenBucket:
    def __init__(self, requests_per_second: float, burst: int):
        self.requests_per_second = requests_per_second
        self.burst = burst
        self._tokens = float(burst)  # Start full
        self._last_update = time.monotonic()

    def _refill_tokens(self):
        now = time.monotonic()
        elapsed = now - self._last_update
        # Add tokens based on elapsed time
        self._tokens = min(
            self.burst,
            self._tokens + elapsed * self.requests_per_second
        )
        self._last_update = now
```

### Token Refill

Tokens are refilled based on elapsed time since the last request:

```
If requests_per_second = 10 and burst = 5:

Time 0s:  [█████] 5 tokens (full bucket)
Time 0.1s:[████▒▒] 4 tokens (0.1 * 10 = 1 token consumed)
Time 0.2s:[███▒▒▒] 3 tokens
Time 0.3s:[██▒▒▒▒] 2 tokens
Time 0.5s:[█▒▒▒▒▒] 1 token
Time 0.6s:[▒▒▒▒▒▒] 0 tokens (bucket empty)
Time 0.7s:[█▒▒▒▒▒] 1 token (refilled: 0.1 * 10 = 1)
```

### Acquiring Tokens

When a request needs to be made:

```python
async def acquire(self, tokens: int = 1):
    while True:
        self._refill_tokens()
        if self._tokens >= tokens:
            self._tokens -= tokens
            return  # Proceed with request

        # Not enough tokens, wait for refill
        wait_time = (tokens - self._tokens) / self.requests_per_second
        await asyncio.sleep(wait_time)
```

If tokens are available, they're consumed immediately. Otherwise, the request waits until enough tokens are refilled.

## Burst Handling

Burst capability is a key advantage of the token bucket algorithm. It allows temporary spikes in request rate as long as the average rate stays within limits.

### Burst Example

With `rate_limit=10` and `rate_limit_burst=5`:

```
Rate: 10 requests/second
Burst: 5 tokens

Time 0.00s: Request 1 → 4 tokens left (████)
Time 0.01s: Request 2 → 3 tokens left (███▒)
Time 0.02s: Request 3 → 2 tokens left (██▒▒)
Time 0.03s: Request 4 → 1 token left (█▒▒▒)
Time 0.04s: Request 5 → 0 tokens left (▒▒▒▒)  ← Burst exhausted

Time 0.10s: Request 6 → 0 tokens left (bucket refilled 1 token)
Time 0.11s: Request 7 → 0 tokens left
Time 0.20s: Request 8 → 0 tokens left
```

After the burst is exhausted, requests are throttled to the refill rate (10 requests/second).

### Why Burst Matters

**Without burst** (fixed rate): Maximum 10 requests/second, even if server can handle more
**With burst**: Send 5 requests instantly, then 10 requests/second thereafter

Burst is useful for:
- **Initial data fetching**: Get multiple pages quickly
- **Recovering from downtime**: Catch up on queued work
- **Flexible rate limits**: Some APIs allow short bursts

## Concurrency Control

The library uses a **semaphore** to control the maximum number of concurrent requests, separate from rate limiting.

### Semaphore Operation

```python
class AsyncRateLimiter:
    def __init__(self, config: RateLimitConfig):
        self._bucket = TokenBucket(
            config.requests_per_second,
            config.burst
        )
        self._semaphore = asyncio.Semaphore(
            config.max_concurrency
        )

    async def acquire(self):
        async with self._semaphore:      # Limit concurrency
            await self._bucket.acquire()  # Limit rate
            yield                         # Make request
```

### Combined Controls

The rate limiter uses both mechanisms:

```
┌─────────────────────────────────────────────────────┐
│              Rate Limiting Controls                   │
│                                                       │
│  ┌──────────────┐         ┌──────────────────┐       │
│  │  Semaphore   │         │   Token Bucket   │       │
│  │              │         │                  │       │
│  │  Max: 20     │────────▶│  Rate: 10/s      │       │
│  │  Concurrent  │         │  Burst: 5        │       │
│  │  Requests    │         │                  │       │
│  └──────────────┘         └──────────────────┘       │
│         │                          │                  │
│         ▼                          ▼                  │
│  Limits simultaneous    Controls request rate       │
│  connections             (with burst capability)    │
└─────────────────────────────────────────────────────┘
```

### Example: Rate Limit vs Concurrency

With `rate_limit=10`, `rate_limit_burst=5`, `concurrency=20`:

```
Scenario: Need to make 100 requests

Concurrency limit: 20 simultaneous connections
Rate limit: 10 requests/second average
Burst: Can send 5 immediately, then 10/second

Timeline:
0.0s:  5 requests (burst) ────┐
0.1s:  5 requests (burst)     │
0.2s:  5 requests (burst)     │   20 concurrent connections
0.3s:  5 requests (burst) ────┘
0.4s:  10 requests (sustained rate)
0.5s:  10 requests
...
9.5s:  Final request completed

Total time: ~10 seconds
```

## Why Token Bucket vs Other Algorithms?

### Comparison with Other Algorithms

| Algorithm | Burst Support | Complexity | Use Case |
|-----------|--------------|------------|----------|
| **Token Bucket** | ✓ | Low | General purpose, flexible |
| **Leaky Bucket** | ✗ | Medium | Network traffic shaping |
| **Fixed Window** | ✗ | Very Low | Simple rate limits |
| **Sliding Window** | Limited | High | Precise rate limiting |

### Advantages of Token Bucket

**1. Burst Capability**
- Allows temporary spikes
- Suitable for real-world usage patterns
- More flexible than fixed limits

**2. Smooth Request Distribution**
- Unlike leaky bucket (which regulates outflow)
- Token bucket regulates requests directly

**3. Simplicity**
- Easy to understand and implement
- Minimal state tracking (tokens, last refill time)
- Low computational overhead

**4. Predictable Behavior**
- Maximum burst size is known
- Average rate is guaranteed
- Easy to tune for specific requirements

### When Token Bucket Is Not Ideal

- **Precise per-second limits**: Sliding window is more accurate
- **Network traffic shaping**: Leaky bucket is designed for this
- **Distributed systems**: Requires distributed coordination

## Rate Limiting Use Cases

### API Rate Limits

Many APIs enforce rate limits (e.g., GitHub: 5000 requests/hour):

```python
# GitHub API: 5,000 requests/hour ≈ 1.4 requests/second
client = ParallelRequests(
    rate_limit=1.4,
    rate_limit_burst=5,  # Allow bursts
    concurrency=10,
)
```

### Preventing Server Overload

Protect your own servers from excessive requests:

```python
# Self-imposed limit: 100 requests/second
client = ParallelRequests(
    rate_limit=100,
    rate_limit_burst=20,
    concurrency=50,
)
```

### Avoiding IP Blocking

When scraping, stay under radar:

```python
# Conservative scraping: 1 request/second
client = ParallelRequests(
    rate_limit=1,
    rate_limit_burst=3,  # Small burst
    concurrency=5,
)
```

### Cost Management

Some APIs charge per request:

```python
# Stay within budget: 10,000 requests/day ≈ 0.12 requests/second
client = ParallelRequests(
    rate_limit=0.12,
    rate_limit_burst=10,
)
```

## Practical Examples

### Example 1: Basic Rate Limiting

```python
from fastreq import fastreq

# Limit to 5 requests/second, burst of 2
results = fastreq(
    urls=[url] * 50,
    rate_limit=5,
    rate_limit_burst=2,
    concurrency=10,
)
```

**Behavior**:
- First 2 requests execute immediately (burst)
- Remaining requests at ~5/second
- Up to 10 concurrent connections

### Example 2: High-Burst Scenario

```python
# Large burst for initial fetch
results = fastreq(
    urls=[url] * 100,
    rate_limit=10,
    rate_limit_burst=50,  # Can send 50 immediately
    concurrency=50,
)
```

**Behavior**:
- First 50 requests execute immediately
- Remaining 50 at ~10/second
- All 100 complete in ~10 seconds

### Example 3: Tight Rate Limiting

```python
# Strict API limit: 1 request/second
results = fastreq(
    urls=[url] * 10,
    rate_limit=1,
    rate_limit_burst=1,  # No real burst
    concurrency=3,
)
```

**Behavior**:
- 1 request per second
- Up to 3 requests queued/concurrent
- All 10 complete in ~10 seconds

## Performance Considerations

### Overhead

Rate limiting adds minimal overhead:

```python
# Token bucket operations
_refill_tokens(): O(1)  # Simple arithmetic
available(): O(1)      # Simple arithmetic
acquire(): O(1)        # May wait, but constant time check
```

### Wait Time Calculation

When tokens are insufficient, wait time is calculated:

```python
wait_time = (tokens_needed - tokens_available) / refill_rate
```

For example, with 0 tokens and 10 tokens/second:
- Need 1 token: wait 0.1 seconds
- Need 5 tokens: wait 0.5 seconds

### Memory Usage

Rate limiting state is minimal:
- `_tokens`: One float
- `_last_update`: One float (timestamp)
- Per limiter: ~16 bytes

## Troubleshooting

### Requests Slower Than Expected

**Problem**: Requests taking longer than `rate_limit` suggests

**Possible Causes**:
1. **Network latency**: Rate limiting doesn't account for network time
2. **Backend limitations**: Some backends have inherent overhead
3. **Server processing time**: Server may take time to process requests

**Solution**: Measure actual throughput and adjust accordingly.

### Burst Not Working

**Problem**: Requests not being sent in bursts

**Cause**: `rate_limit_burst` too low or already exhausted

**Solution**: Increase `rate_limit_burst` or wait for refill:
```python
client = ParallelRequests(
    rate_limit=10,
    rate_limit_burst=20,  # Larger burst
)
```

### Concurrency Exceeded

**Problem**: More concurrent requests than `concurrency` setting

**Cause**: Rate limiting and concurrency are separate controls

**Solution**: Remember that both limits apply:
- `concurrency`: Max simultaneous connections
- `rate_limit`: Max requests per second

## Related Documentation

- **[Architecture](architecture.md)** - How rate limiting integrates with other components
- **[Retry Strategy](retry-strategy.md)** - How retries interact with rate limiting
- **[How-to: Limit Request Rate](../how-to-guides/limit-request-rate.md)** - Practical usage guide
