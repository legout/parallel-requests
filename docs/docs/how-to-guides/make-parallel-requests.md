# Make Parallel Requests

Learn how to create parallel HTTP requests with different configurations and return types.

## Basic Parallel Requests

Make multiple requests to the same or different URLs:

```python
from parallel_requests import parallel_requests

# Single URL repeated
results = parallel_requests(
    urls=["https://httpbin.org/get"] * 5,
    concurrency=3,
)

# Multiple different URLs
results = parallel_requests(
    urls=[
        "https://api.github.com/repos/python/cpython",
        "https://api.github.com/repos/python/pypy",
        "https://api.github.com/repos/legout/parallel-requests",
    ],
)
```

## Named Results with Keys

Use the `keys` parameter to return a dictionary mapping names to results:

```python
from parallel_requests import parallel_requests

results = parallel_requests(
    urls=[
        "https://api.github.com/repos/python/cpython",
        "https://api.github.com/repos/python/pypy",
    ],
    keys=["cpython", "pypy"],
)

# Access results by key
print(f"CPython: {results['cpython']['name']}")
print(f"PyPy: {results['pypy']['name']}")
```

The keys parameter is useful when you need to track which result corresponds to which request.

## Custom Response Transformation

Use `parse_func` to apply custom transformation to each response:

```python
from parallel_requests import parallel_requests

def extract_repo_info(response):
    """Extract only relevant fields from GitHub API response."""
    return {
        "name": response.get("name"),
        "stars": response.get("stargazers_count"),
        "language": response.get("language"),
    }

results = parallel_requests(
    urls=[
        "https://api.github.com/repos/python/cpython",
        "https://api.github.com/repos/legout/parallel-requests",
    ],
    parse_func=extract_repo_info,
)

for repo in results:
    print(f"{repo['name']}: {repo['stars']} stars, {repo['language']}")
```

## Different Return Types

Control how responses are parsed with `return_type`:

### JSON Response (Default)

```python
from parallel_requests import parallel_requests

results = parallel_requests(
    urls=["https://api.github.com/repos/python/cpython"],
    return_type="json",
)

print(results[0]["name"])  # Access JSON fields directly
```

### Text Response

```python
results = parallel_requests(
    urls=["https://httpbin.org/html"],
    return_type="text",
)

print(results[0])  # Raw HTML text
```

### Binary Content

```python
results = parallel_requests(
    urls=["https://httpbin.org/bytes/1024"],
    return_type="content",
)

print(len(results[0]))  # Length in bytes
```

### Full Response Object

```python
from parallel_requests import parallel_requests, ReturnType

results = parallel_requests(
    urls=["https://httpbin.org/get"],
    return_type=ReturnType.RESPONSE,
)

response = results[0]
print(f"Status: {response.status_code}")
print(f"Headers: {response.headers}")
print(f"Body: {response.json()}")
```

## Async Parallel Requests

For async applications, use the async version:

```python
import asyncio
from parallel_requests import parallel_requests_async

async def fetch_data():
    results = await parallel_requests_async(
        urls=[
            "https://api.github.com/repos/python/cpython",
            "https://api.github.com/repos/python/pypy",
        ],
        concurrency=5,
    )
    return results

results = asyncio.run(fetch_data())
```

## Using a Context Manager

Reuse sessions across multiple request batches:

```python
import asyncio
from parallel_requests import ParallelRequests

async def fetch_with_session():
    async with ParallelRequests(concurrency=5) as client:
        # First batch
        results1 = await client.request(
            urls=["https://api.github.com/repos/python/cpython"],
        )

        # Second batch (reuses session/cookies)
        results2 = await client.request(
            urls=["https://api.github.com/repos/python/pypy"],
        )

        return results1, results2

results1, results2 = asyncio.run(fetch_with_session())
```

## Mixing URL Parameters

Pass URL-specific parameters using dictionaries:

```python
from parallel_requests import parallel_requests

results = parallel_requests(
    urls=[
        "https://api.github.com/repos/python/cpython",
        "https://api.github.com/repos/python/pypy",
    ],
    params=[
        {"ref": "main"},  # First URL params
        {},               # Second URL params (empty)
    ],
)
```

## Combining with Other Options

Combine parallel requests with other features:

```python
from parallel_requests import parallel_requests

results = parallel_requests(
    urls=[
        "https://api.github.com/repos/python/cpython",
        "https://api.github.com/repos/python/pypy",
    ],
    keys=["cpython", "pypy"],
    concurrency=3,
    max_retries=2,
    timeout=10,
    rate_limit=10,
    headers={
        "User-Agent": "MyApp/1.0",
        "Accept": "application/vnd.github.v3+json",
    },
)
```

## See Also

- **[Limit Request Rate](limit-request-rate.md)** - Control request frequency
- **[Handle Retries](handle-retries.md)** - Configure retry logic
- **[API Reference](../reference/api/parallel_requests.md)** - Complete function documentation
