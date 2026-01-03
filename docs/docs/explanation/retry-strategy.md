# Retry Strategy

Retry strategies determine how the library handles failed requests. The fastreq library implements **exponential backoff with jitter** to balance resilience with efficiency.

## Exponential Backoff Algorithm

Exponential backoff is a standard technique for handling transient failures by increasing the wait time between retries.

### The Algorithm

The retry strategy calculates delay using this formula:

```
delay = backoff_multiplier × (2^attempt) ± jitter
```

Where:
- `attempt`: Retry attempt number (0-indexed)
- `backoff_multiplier`: Base delay in seconds (default: 1.0)
- `jitter`: Random variation as fraction of base delay (default: 10%)

### Delay Calculation

```python
def _calculate_delay(self, attempt: int) -> float:
    base_delay = self.config.backoff_multiplier * (2 ** attempt)
    jitter_amount = self.config.jitter * base_delay
    jittered_delay = base_delay + random.uniform(-jitter_amount, jitter_amount)
    return float(max(0, jittered_delay))
```

### Example Calculations

With `backoff_multiplier=1.0` and `jitter=0.1` (10%):

| Attempt | Base Delay | Jitter Range | Possible Delay |
|---------|-----------|--------------|----------------|
| 0 | 1.0s | ±0.10s | 0.90s - 1.10s |
| 1 | 2.0s | ±0.20s | 1.80s - 2.20s |
| 2 | 4.0s | ±0.40s | 3.60s - 4.40s |
| 3 | 8.0s | ±0.80s | 7.20s - 8.80s |

## Why Exponential Backoff?

### Benefits

**1. Reduces Server Load**
- Failed requests are retried with increasing delays
- Gives failing service time to recover
- Prevents immediate retry storms

**2. Transient Failure Handling**
- Network glitches often resolve quickly
- Temporary overload clears with time
- Database locks release

**3. Resource Efficiency**
- Fewer retries on persistent failures
- Faster failure detection
- Better use of limited resources

### Alternative Strategies

| Strategy | Advantages | Disadvantages |
|----------|-----------|---------------|
| **Exponential Backoff** | Balances speed and load | Can be slow for many retries |
| **Linear Backoff** | Predictable delay | Doesn't adapt quickly |
| **Fixed Delay** | Simple | Inefficient for many failures |
| **No Backoff** | Fastest | Overwhelms failing services |

### Comparison Example

Request that fails 3 times:

**Fixed 1-second delay:**
```
Attempt 0: Fail → Wait 1s → Retry
Attempt 1: Fail → Wait 1s → Retry
Attempt 2: Fail → Wait 1s → Retry
Total wait: 3 seconds
```

**Exponential backoff (1x, 10% jitter):**
```
Attempt 0: Fail → Wait ~1s → Retry
Attempt 1: Fail → Wait ~2s → Retry
Attempt 2: Fail → Wait ~4s → Retry
Total wait: ~7 seconds
```

Exponential backoff waits longer but is much gentler on failing services.

## Jitter (Random Variation)

Jitter adds randomness to retry delays to prevent synchronization issues.

### Why Jitter Is Needed

Without jitter, multiple clients might retry at the same time:

```
Without Jitter:
Client A: [Retry]────────────→[Retry]────────────→[Retry]
Client B: [Retry]────────────→[Retry]────────────→[Retry]
Client C: [Retry]────────────→[Retry]────────────→[Retry]
           ↑ All retry at same time

With Jitter:
Client A: [Retry]──────→[Retry]─────────→[Retry]
Client B: [Retry]────────→[Retry]───────→[Retry]
Client C: [Retry]─────→[Retry]──────────→[Retry]
           ↑ Distributed over time
```

### Jitter Formula

```python
jitter_amount = base_delay * jitter_fraction
random_delay = base_delay + random.uniform(-jitter_amount, +jitter_amount)
```

With `jitter=0.1` (10%), delays vary by ±10% around the base.

### Thundering Herd Problem

The thundering herd occurs when many clients retry a failing service simultaneously:

```
┌─────────────────────────────────────────────────┐
│              Failing Service                    │
│                                                │
│  Time 0s:  [████████████] 100 requests        │
│           Service crashes!                      │
│                                                │
│  Time 1s:  [████████████] 100 clients retry   │
│           Service still overwhelmed            │
│                                                │
│  Time 2s:  [████████████] 100 clients retry   │
│           Service never recovers               │
└─────────────────────────────────────────────────┘
```

With jitter, retries are distributed:

```
Time 1s:  [██] 10 clients retry
Time 1.1s:[██] 10 clients retry
Time 1.2s:[██] 10 clients retry
...
Time 2s:  [██] Remaining clients retry

Service has time to recover between retry waves
```

## Retry Logic Flow

### Decision Process

```
Request Failed
      │
      ▼
┌─────────────────────────────┐
│  Should retry?              │
│  - Check dont_retry_on      │
│  - Check retry_on           │
└─────────────────────────────┘
      │
      ├──► No → Raise error
      │
      ▼
┌─────────────────────────────┐
│  Attempts < max_retries?    │
└─────────────────────────────┘
      │
      ├──► No → Raise RetryExhaustedError
      │
      ▼
┌─────────────────────────────┐
│  Calculate delay             │
│  - Exponential backoff      │
│  - Add jitter                │
└─────────────────────────────┘
      │
      ▼
┌─────────────────────────────┐
│  Wait for delay              │
└─────────────────────────────┘
      │
      ▼
┌─────────────────────────────┐
│  Retry request               │
└─────────────────────────────┘
```

### Selective Retry Logic

The library supports selective retrying:

```python
@dataclass
class RetryConfig:
    max_retries: int = 3
    backoff_multiplier: float = 1.0
    jitter: float = 0.1
    retry_on: set[type[Exception]] | None = None
    dont_retry_on: set[type[Exception]] | None = None
```

**Retry on specific errors:**
```python
config = RetryConfig(
    retry_on={TimeoutError, ConnectionError},
    # Only retry timeout and connection errors
)
```

**Don't retry specific errors:**
```python
config = RetryConfig(
    dont_retry_on={AuthenticationError, PermissionError},
    # Don't retry auth/permission errors
)
```

### Retry Decision Logic

```python
def _should_retry(self, error: Exception) -> bool:
    # Never retry if error is in dont_retry_on
    if self.config.dont_retry_on and isinstance(
        error, tuple(self.config.dont_retry_on)
    ):
        return False

    # Only retry if error is in retry_on (if specified)
    if self.config.retry_on:
        return isinstance(error, tuple(self.config.retry_on))

    # Default: retry all errors
    return True
```

## Configuration Examples

### Default Configuration

```python
# Default: 3 retries, 1s base delay, 10% jitter
client = ParallelRequests(max_retries=3)
```

Retry delays (with 10% jitter):
- Attempt 0: ~1s wait
- Attempt 1: ~2s wait
- Attempt 2: ~4s wait
- After 3 failures: raise error

### Aggressive Retries

```python
# More retries, faster initial delay
client = ParallelRequests(
    max_retries=5,
    # Default backoff_multiplier=1.0
)
```

Retry delays:
- Attempt 0: ~1s
- Attempt 1: ~2s
- Attempt 2: ~4s
- Attempt 3: ~8s
- Attempt 4: ~16s

### Conservative Retries

```python
# Fewer retries, slower backoff, more jitter
client = ParallelRequests(
    max_retries=2,
    backoff_multiplier=2.0,  # Slower backoff
)
```

Note: Jitter is not configurable in current API (fixed at 10%).

Retry delays (with 10% jitter):
- Attempt 0: ~2s
- Attempt 1: ~4s

### No Jitter (Not Recommended)

Jitter is currently fixed at 10% in the implementation. If you need to disable jitter, you would need to modify the `RetryStrategy` class:

```python
# In RetryStrategy._calculate_delay():
# Original:
jittered_delay = base_delay + random.uniform(-jitter_amount, jitter_amount)

# Without jitter:
jittered_delay = base_delay
```

**Warning**: Disabling jitter can cause thundering herd problems.

## Integration with Other Features

### Retry and Rate Limiting

Retries respect rate limiting:

```python
client = ParallelRequests(
    max_retries=3,
    rate_limit=10,
    rate_limit_burst=5,
)
```

Flow:
1. Request fails
2. Calculate retry delay (e.g., 1s)
3. Wait 1s
4. Acquire rate limit token
5. Retry request

### Retry and Concurrency

Retries don't increase concurrency:

```python
client = ParallelRequests(
    max_retries=3,
    concurrency=10,
)
```

If request fails, retry doesn't use additional concurrency slot. The original slot is held during retry.

### Retry and Timeouts

Retries are separate from timeouts:

```python
client = ParallelRequests(
    max_retries=3,
    timeout=5,  # Per-request timeout
)
```

- Each retry attempt has a 5-second timeout
- Total max time: 3 retries × (5s timeout + backoff delay)

## Best Practices

### Choosing Retry Settings

**For API calls:**
```python
# API calls: moderate retries
ParallelRequests(
    max_retries=3,
    backoff_multiplier=1.0,
)
```

**For long-running downloads:**
```python
# Downloads: fewer retries, longer timeout
ParallelRequests(
    max_retries=2,
    backoff_multiplier=2.0,
    timeout=30,
)
```

**For unreliable networks:**
```python
# Unstable network: more retries
ParallelRequests(
    max_retries=5,
    backoff_multiplier=1.0,
)
```

### Handling Specific Errors

**Never retry authorization errors:**
```python
# Auth errors won't be fixed by retrying
# The library handles common non-retryable errors automatically
```

**Always retry timeout errors:**
```python
# Timeouts are often transient
# Retried by default unless configured otherwise
```

### Monitoring Retries

Enable debug logging to see retry behavior:

```python
client = ParallelRequests(
    max_retries=3,
    debug=True,
)
```

Output:
```
Retry attempt 1/3, waiting 1.05s
Retry attempt 2/3, waiting 2.12s
Retry attempt 3/3, waiting 4.08s
```

## Performance Considerations

### Total Wait Time

With `max_retries=3` and `backoff_multiplier=1.0`:

```
Maximum total wait time on failure:
= 1s + 2s + 4s = 7 seconds
```

With `max_retries=5`:
```
Maximum total wait time:
= 1s + 2s + 4s + 8s + 16s = 31 seconds
```

### Resource Usage

Retries hold resources during backoff:

- **Semaphore slot**: Held during retry wait
- **Memory**: Retry state is minimal (~32 bytes)
- **CPU**: Minimal during sleep

### Timeout vs Retry Timeout

```
Per-request timeout: How long to wait for response
Retry delay: How long to wait between retries

Example with timeout=5, max_retries=3:
┌──────┐ 5s   ┌──────┐ 1s   ┌──────┐ 2s   ┌──────┐ 4s
│ Req  │──────▶│Wait  │──────▶│Retry │──────▶│Wait  │─────▶...
└──────┘       └──────┘       └──────┘       └──────┘

Max time per URL: 3 × (5s timeout + avg 2.33s delay) = ~22s
```

## Troubleshooting

### Too Many Retries

**Problem**: Application hanging due to excessive retries

**Solution**: Reduce `max_retries`:
```python
ParallelRequests(max_retries=1)  # Only retry once
```

### Retries Too Slow

**Problem**: Recoverable errors taking too long to retry

**Solution**: Reduce `backoff_multiplier` (not currently configurable via main API):
```python
# Would require custom RetryConfig
# Or accept current default of 1.0
```

### Retries Not Working

**Problem**: Errors not being retried

**Cause**: Error might be non-retryable (e.g., authentication)

**Solution**: Check error type or configure `retry_on`:
```python
# Current API doesn't expose retry_on configuration
# Future enhancement may allow this
```

## Related Documentation

- **[Architecture](architecture.md)** - How retry integrates with other components
- **[Rate Limiting](rate-limiting.md)** - How retries interact with rate limiting
- **[How-to: Handle Retries](../how-to-guides/handle-retries.md)** - Practical usage guide
