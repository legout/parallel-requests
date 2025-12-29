#!/usr/bin/env python3
"""
Backend selection example.

This example demonstrates:
- Auto-detecting best available backend
- Explicit backend selection
- Comparing backend features
"""

from parallel_requests import (
    parallel_requests,
    ParallelRequests,
)


def test_backend(backend_name: str) -> dict:
    """Test a specific backend and return results."""
    print(f"\nTesting backend: {backend_name}")
    print("-" * 50)

    urls = [f"https://httpbin.org/get?backend={backend_name}"] * 3

    try:
        results = parallel_requests(
            urls=urls,
            backend=backend_name,
            concurrency=3,
            verbose=False,
        )
        return {"success": True, "results": len(results)}
    except Exception as e:
        return {"success": False, "error": str(e)}


def main():
    print("=== Backend Selection Example ===\n")

    print("Scenario 1: Auto backend detection (recommended)")
    print("-" * 50)

    auto_result = test_backend("auto")
    if auto_result["success"]:
        print(f"✓ Auto-detection successful!")
        print(f"  Processed {auto_result['results']} requests")
    else:
        print(f"✗ Auto-detection failed: {auto_result.get('error')}")

    print("\n\nScenario 2: Explicit backend selection")
    print("-" * 50)

    backends = ["niquests", "aiohttp", "requests"]

    results = {}
    for backend in backends:
        result = test_backend(backend)
        results[backend] = result

        if result["success"]:
            print(f"  ✓ {backend}: {result['results']} requests")
        else:
            print(f"  ✗ {backend}: {result.get('error', 'Not available')}")

    print("\n\nScenario 3: Backend comparison")
    print("-" * 50)

    print("Backend features:")
    print()
    print("┌─────────────┬────────┬────────┬─────────┐")
    print("│ Backend     │ HTTP/2 │ Async  │ Stream  │")
    print("├─────────────┼────────┼────────┼─────────┤")
    print("│ niquests    │   ✓    │   ✓    │    ✓    │")
    print("│ aiohttp     │   ✗    │   ✓    │    ✓    │")
    print("│ requests    │   ✗    │   ✗*   │    ✓†   │")
    print("└─────────────┴────────┴────────┴─────────┘")
    print("* async via thread pool wrapper")
    print("† streaming via thread pool wrapper")

    print("\n\nScenario 4: Using ParallelRequests class")
    print("-" * 50)

    client = ParallelRequests(
        backend="auto",
        concurrency=5,
        verbose=False,
    )

    print(f"Initialized client with auto backend")
    print(f"Concurrency: {client.concurrency}")
    print(f"Random user agent: {client.random_user_agent}")

    print("\n--- Backend Selection Guide ---")
    print("• auto: Automatically select best available (recommended)")
    print("• niquests: Best choice - HTTP/2 support, native async")
    print("• aiohttp: Good async alternative, no HTTP/2")
    print("• requests: Pure synchronous, good for compatibility")

    print("\n✓ Choose backend based on your requirements")


if __name__ == "__main__":
    main()
