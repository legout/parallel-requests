#!/usr/bin/env python3
"""
Basic parallel GET requests example.

This example demonstrates:
- Using parallel_requests() for simple parallel HTTP calls
- Making multiple requests to httpbin.org
- Printing response data
"""

from parallel_requests import parallel_requests
import json


def main():
    print("=== Basic Parallel Requests Example ===\n")

    urls = [
        "https://httpbin.org/get",
        "https://httpbin.org/uuid",
        "https://httpbin.org/ip",
        "https://httpbin.org/headers",
        "https://httpbin.org/user-agent",
    ]

    print(f"Making {len(urls)} parallel requests...")
    print("URLs:")
    for url in urls:
        print(f"  - {url}")
    print()

    results = parallel_requests(
        urls=urls,
        concurrency=3,
    )

    print("\nResults:")
    for i, result in enumerate(results):
        print(f"\n--- Request {i + 1} ---")
        print(json.dumps(result, indent=2))

    print("\n✓ All requests completed successfully")


if __name__ == "__main__":
    main()
