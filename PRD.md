# Product Requirements Document (PRD): parallel-requests v2.0.0

**Version:** 2.0.0  
**Status:** Draft  
**Last Updated:** December 28, 2025  
**Author:** Development Team

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Current State Analysis](#2-current-state-analysis)
3. [Architecture Problems Identified](#3-architecture-problems-identified)
4. [Root Causes](#4-root-causes)
5. [Design Principles](#5-design-principles)
6. [Proposed Architecture](#6-proposed-architecture)
7. [Detailed Specifications](#7-detailed-specifications)
8. [API Usage Examples](#8-api-usage-examples)
9. [Technical Decisions](#9-technical-decisions)
10. [Implementation Phases](#10-implementation-phases)
11. [Success Metrics](#11-success-metrics)
12. [Dependencies](#12-dependencies)
13. [Testing Strategy](#13-testing-strategy)
14. [Migration Guide](#14-migration-guide)
15. [Timeline](#15-timeline)
16. [Risks and Mitigations](#16-risks-and-mitigations)
17. [Open Questions](#17-open-questions)

---

## 1. Executive Summary

### 1.1 Purpose

This document defines the requirements for rebuilding the `parallel-requests` library from scratch as version 2.0.0. The current library is non-functional due to critical implementation bugs and architectural deficiencies.

### 1.2 Problem Statement

The `parallel-requests` library, intended to provide a simple, high-performance interface for parallel HTTP requests, is currently broken and cannot fulfill its purpose. Critical bugs prevent any HTTP requests from completing successfully.

### 1.3 Solution Overview

A complete rewrite following clean architecture principles with:
- Single unified interface across multiple backends
- Proper resource management and error handling
- Built-in retry logic, proxy rotation, and user agent rotation
- Rate limiting as a core feature
- HTTP/2 support (via niquests)
- Streaming support for large file downloads
- Zero unnecessary dependencies (no pandas)

### 1.4 Key Decisions Summary

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Backend Selection | Auto-select (niquests → aiohttp → requests) | Use best available, no user burden |
| Free Proxies | Opt-in only | Avoid unreliability, explicit user control |
| Error Handling | Raise exceptions by default | Better debugging |
| Pandas Dependency | Remove entirely | Unnecessary overhead |
| Backward Compatibility | Clean break (v2.0.0) | Avoid technical debt |
| HTTP/2 Support | Yes (niquests) | Future-proofing |
| WebSocket Support | No | Out of scope |
| Streaming Responses | Yes | Support large files |
| Default Concurrency | 20 | Balanced for general use |
| Rate Limiting | Yes, must-have | API politeness |
| User Agent Rotation | Yes, enabled by default | Anti-detection |
| Webshare Proxy Support | Yes, must-have | Reliable proxies |

---

## 2. Current State Analysis

### 2.1 Intended Functionality

Based on code analysis, the library was designed to:

1. **Make parallel HTTP requests** with a simple API
2. **Support multiple backends**: `niquests`, `aiohttp`, `requests`+`asyncer`
3. **Provide automatic retry logic** with exponential backoff
4. **Random proxy rotation** for avoiding rate limits
5. **Random user agent rotation** for avoiding detection
6. **Progress tracking** with tqdm integration
7. **Flexible response parsing** with custom `parse_func` callbacks
8. **Response mapping** with `keys` parameter
9. **Multiple return types**: JSON, text, raw content

### 2.2 Current Architecture

```
parallel-requests/
├── __init__.py              # Re-exports
├── parallel_requests_asyncer.py   # requests + asyncer (DEFAULT)
├── parallel_requests_aiohttp.py   # aiohttp backend
├── parallel_requests_niquests.py  # niquests backend
├── _parallel_requests.py          # Legacy sync version
├── utils.py                       # Helper functions
├── constants.py                   # Proxies, user agents
└── tests/                         # Minimal tests
```

### 2.3 Critical Bugs Found

#### 🔴 CRITICAL: Library is Completely Non-Functional

**Bug #1: Invalid parameter passing**

Location: `parallel_requests_asyncer.py:103`

```python
def single_request(self, ..., *args, **kwargs):
    response = self._session.request(
        method=method,
        url=url,
        params=params,
        data=data,
        json=json,
        proxies=proxies,
        headers=headers,
        cookies=self._cookies,
        *args,    # ❌ PASSES ALL PARAMS TO requests.Session.request()
        **kwargs, # ❌ INCLUDING 'verbose', 'return_type', 'parse_func'
    )
```

**Result:** `TypeError: Session.request() got an unexpected keyword argument 'verbose'`

The library catches this exception silently and returns `None`, so users see no error—only broken functionality.

**Bug #2: Multiple implementations with inconsistent APIs**

Each backend has different parameter support:
- `parallel_requests_asyncer.py`: Full support (but broken)
- `parallel_requests_aiohttp.py`: Missing `data`, `json`, `cookies` parameters
- `parallel_requests_niquests.py`: Returns Response objects instead of parsed data

**Bug #3: Resource Leaks**

1. **No session cleanup** in asyncer implementation
2. **TCPConnector lifecycle issues** in aiohttp implementation
3. **No context manager support** in asyncer

**Bug #4: Silent Failure**

```python
except Exception as e:
    if self._warnings:
        logger.warning(...)
    # Returns None silently without informing user!
return {key: None} if key else None
```

### 2.4 Current Limitations

| Issue | Impact | Workaround |
|-------|--------|------------|
| Silent failures | Cannot trust any results | None |
| No rate limiting | May get IP banned | Manual delays |
| Proxy crashes on malformed input | Library unusable | Validate proxies first |
| No HTTP/2 | Slower performance | Use niquests directly |
| No streaming | Cannot download large files | Use requests directly |
| Pandas dependency | Bloated install | Remove it |

---

## 3. Architecture Problems Identified

### 3.1 Three Conflicting Implementations

| File | Backend | Status | API Coverage |
|------|---------|--------|--------------|
| `parallel_requests_asyncer.py` | requests + asyncer | DEFAULT | Full (but broken) |
| `parallel_requests_aiohttp.py` | aiohttp | Active | Partial (no data/json/cookies) |
| `parallel_requests_niquests.py` | niquests | Active | Returns Response objects |

**Problems:**
- **Inconsistent APIs**: Each has different parameter support
- **No clear recommendation**: Which backend should users use?
- **Maintenance burden**: Three codebases to maintain for one feature
- **Different return types**: Users need different code for each backend

### 3.2 Over-Engineered Helper Functions

The `to_list()` and `extend_list()` functions try to handle too many cases:

```python
def to_list(x: list | str | int | float | pd.Series | None) -> list:
    # Handles 7 different types - overkill for a request library
    # pandas dependency pulled just for this one function
```

**Real need:** Just convert str/dict → list, keep lists as-is.

### 3.3 Resource Management Issues

**parallel_requests_asyncer.py:**
```python
class ParallelRequests:
    def __init__(self):
        self._session = requests.Session()  # Never closed!
    
    # No close() method
    # No async context manager
```

**parallel_requests_aiohttp.py:**
```python
async def request(self, ...):
    conn = aiohttp.TCPConnector(...)  # Created per request
    async with aiohttp.ClientSession(connector=conn) as session:
        # Connector not managed properly
```

### 3.4 Proxy Implementation Flaws

```python
# utils.py:60 - Will crash if proxy string is malformed
proxies = [
    dict(zip(["ip", "port", "user", "pw"], proxy.split(":")))
    for proxy in proxies
]
# Assumes format: ip:port:user:pw
# Will crash on other formats
```

### 3.5 Response Type Inconsistency

| Backend | Returns |
|---------|---------|
| asyncer | Parsed data (dict/list) |
| aiohttp | Parsed data (dict/list) |
| niquests | Response objects (not parsed!) |

### 3.6 Missing Critical Features

| Feature | Status | Impact |
|---------|--------|--------|
| Rate Limiting | ❌ Missing | Cannot respect API limits |
| HTTP/2 | ❌ Missing | Slower performance |
| Streaming | ❌ Missing | Cannot download large files |
| Proper Error Handling | ❌ Silent failures | Unreliable |

---

## 4. Root Causes

1. **Design by Copy-Paste**: Started with one implementation, then copied for others without proper adaptation
2. **Parameter Leakage**: Using `*args` and `**kwargs` without validation
3. **No Interface Definition**: No clear contract between implementations
4. **Over-Abstraction**: Helper functions handle cases that don't exist in practice
5. **Missing Integration Tests**: No end-to-end tests that would have caught the TypeError
6. **Silent Exception Handling**: Catching all exceptions without proper error reporting

---

## 5. Design Principles

### 5.1 Core Principles

1. **Single Unified Interface** - One class, multiple backends via strategy pattern
2. **Explicit Parameters** - No `*args` or `**kwargs` without validation
3. **Resource Safety** - Always use context managers
4. **Type Safety** - Use type hints and validation
5. **Minimal Dependencies** - Remove pandas, asyncer
6. **Clear Error Messages** - Never swallow exceptions without logging

### 5.2 Backward Compatibility Approach

**Clean break with v2.0.0:**
- No compatibility layer for v0.2.x
- Clear migration guide
- Breaking changes documented
- Deprecation warnings in any transitional code

### 5.3 User Experience Goals

1. **Simple API**: `parallel_requests(urls=...)` should just work
2. **Predictable behavior**: Errors raise exceptions, not return None
3. **Progressive disclosure**: Simple cases simple, complex cases possible
4. **Good defaults**: Sensible defaults for all parameters
5. **Clear documentation**: Examples for common use cases

---

## 6. Proposed Architecture

### 6.1 Module Structure

```
parallel-requests/
├── __init__.py                    # Public API exports only
├── client.py                      # Main ParallelRequests class
├── backends/                      # Backend strategy implementations
│   ├── __init__.py
│   ├── base.py                    # Abstract Backend interface
│   ├── niquests.py               # Primary: HTTP/2, async, built-in retry
│   ├── aiohttp.py                # Secondary: mature async client
│   └── requests.py               # Fallback: sync requests via asyncio
├── utils/                         # Utility modules
│   ├── __init__.py
│   ├── retry.py                  # Exponential backoff retry logic
│   ├── rate_limiter.py           # Token bucket rate limiting
│   ├── headers.py                # User agent rotation & header management
│   ├── proxies.py                # Proxy rotation & webshare integration
│   └── validators.py             # Input validation & normalization
├── config.py                     # Configuration management
└── exceptions.py                 # Custom exception hierarchy
```

### 6.2 Design Pattern: Strategy Pattern

```python
# client.py
class ParallelRequests:
    def __init__(self, backend: str = "auto"):
        self._backend = self._select_backend(backend)
    
    async def request(self, urls, ...):
        config = self._normalize_request(...)
        response = await self._backend.request(config)
        return self._process_response(response)
```

### 6.3 Data Flow

```
User Code
    ↓
ParallelRequests.request()
    ↓
Request Normalization (validators)
    ↓
Backend Selection (strategy pattern)
    ↓
Rate Limiter (token bucket)
    ↓
Backend Request (niquests/aiohttp/requests)
    ↓
Retry Logic (exponential backoff)
    ↓
Response Processing
    ↓
User Code
```

### 6.4 Key Components

#### Backend Interface (`backends/base.py`)

```python
class Backend(ABC):
    """Abstract interface for all HTTP backends"""
    
    @abstractmethod
    async def request(self, config: RequestConfig) -> NormalizedResponse:
        """Make single HTTP request"""
    
    @abstractmethod
    async def close(self):
        """Close session/connection"""
    
    @abstractmethod
    async def __aenter__(self):
        """Context manager support"""
    
    @abstractmethod
    async def __aexit__(self, *args):
        """Context manager support"""
```

#### Rate Limiter (`utils/rate_limiter.py`)

```python
class RateLimiter:
    """Token bucket algorithm for rate limiting"""
    
    async def acquire(self, tokens: int = 1) -> None:
        """Acquire tokens, wait if necessary"""
```

#### Proxy Manager (`utils/proxies.py`)

```python
class ProxyManager:
    """Manages proxy rotation with webshare integration"""
    
    async def get_next(self) -> Optional[str]:
        """Get next available proxy"""
    
    async def mark_failed(self, proxy: str) -> None:
        """Mark proxy as failed, temporarily disable"""
```

#### Header Manager (`utils/headers.py`)

```python
class HeaderManager:
    """Manages user agent rotation"""
    
    def get_headers(self, custom_headers: Optional[dict] = None) -> dict:
        """Get headers with user agent rotation"""
```

---

## 7. Detailed Specifications

### 7.1 Main Client (`client.py`)

#### Core Class Definition

```python
from dataclasses import dataclass
from typing import Callable, Any, Optional
from enum import Enum

class ReturnType(Enum):
    JSON = "json"
    TEXT = "text"
    CONTENT = "content"
    RESPONSE = "response"
    STREAM = "stream"

@dataclass
class RequestOptions:
    """Configuration for a single request"""
    url: str
    method: str = "GET"
    params: dict | None = None
    data: Any | None = None
    json: dict | None = None
    headers: dict | None = None
    timeout: int | None = None
    proxy: str | None = None
    stream: bool = False

class ParallelRequests:
    """
    Main class for parallel HTTP requests with:
    - Automatic retry with exponential backoff
    - Proxy rotation (webshare + custom)
    - User agent rotation
    - Rate limiting (requests/second)
    - HTTP/2 support (via niquests)
    - Streaming support
    - Progress tracking (optional)
    
    Example:
        >>> import asyncio
        >>> async def main():
        ...     async with ParallelRequests() as pr:
        ...         results = await pr.request(
        ...             urls=["https://httpbin.org/get"] * 10,
        ...             concurrency=20,
        ...         )
        >>> asyncio.run(main())
    """
    
    def __init__(
        # Concurrency control
        concurrency: int = 20,
        max_retries: int = 3,
        
        # Retry configuration
        retry_backoff: float = 1.0,
        retry_jitter: float = 0.1,
        
        # Rate limiting
        rate_limit: float | None = None,
        rate_limit_burst: int = 5,
        
        # Proxy & User Agent
        random_proxy: bool = False,
        random_user_agent: bool = True,
        proxies: list[str] | None = None,
        user_agents: list[str] | None = None,
        
        # Backend selection
        backend: str = "auto",
        
        # HTTP/2
        http2: bool = True,
        
        # Streaming
        stream: bool = False,
        
        # Other
        timeout: int = 30,
        cookies: dict | None = None,
        verbose: bool = False,
        debug: bool = False,
        return_none_on_failure: bool = False,
    ) -> None:
        """
        Initialize ParallelRequests.
        
        Backend auto-selection priority:
        1. niquests (if available) - HTTP/2, modern, best async support
        2. aiohttp (if available) - mature, widely used
        3. requests + asyncio (fallback) - for sync requests users
        
        Args:
            concurrency: Maximum concurrent requests (default: 20)
            max_retries: Total retry attempts per request (default: 3)
            retry_backoff: Exponential backoff multiplier (default: 1.0)
            retry_jitter: Randomization to avoid thundering herd (default: 0.1)
            rate_limit: Requests per second limit (default: None = no limit)
            rate_limit_burst: Burst allowance for token bucket (default: 5)
            random_proxy: Enable proxy rotation (default: False)
            random_user_agent: Enable user agent rotation (default: True)
            proxies: Custom proxy list (default: None)
            user_agents: Custom user agent list (default: None)
            backend: Backend selection ("auto" | "niquests" | "aiohttp" | "requests")
            http2: Enable HTTP/2 when using niquests (default: True)
            stream: Enable streaming mode for large files (default: False)
            timeout: Request timeout in seconds (default: 30)
            cookies: Session cookies to include (default: None)
            verbose: Show progress bar (default: False)
            debug: Enable debug logging (default: False)
            return_none_on_failure: Return None instead of raising exception (default: False)
        
        Raises:
            ImportError: If no HTTP backend is available
            ValueError: If invalid backend specified
        """
        self._concurrency = concurrency
        self._max_retries = max_retries
        self._retry_backoff = retry_backoff
        self._retry_jitter = retry_jitter
        self._rate_limit = rate_limit
        self._rate_limit_burst = rate_limit_burst
        self._random_proxy = random_proxy
        self._random_user_agent = random_user_agent
        self._http2 = http2
        self._stream = stream
        self._timeout = timeout
        self._cookies = cookies
        self._verbose = verbose
        self._debug = debug
        self._return_none_on_failure = return_none_on_failure
        
        # Initialize managers
        self._proxy_manager = self._init_proxy_manager(proxies)
        self._header_manager = self._init_header_manager(user_agents)
        self._rate_limiter = self._init_rate_limiter()
        
        # Select and initialize backend
        self._backend = self._select_backend(backend)
    
    async def request(
        self,
        urls: str | list[str],
        keys: list[str] | None = None,
        method: str = "GET",
        params: dict | list[dict] | None = None,
        data: Any | list[Any] | None = None,
        json: dict | list[dict] | None = None,
        headers: dict | list[dict] | None = None,
        parse_func: Callable[[Any], Any] | None = None,
        return_type: ReturnType = ReturnType.JSON,
        stream_callback: Callable[[str, Any], None] | None = None,
    ) -> dict[str, Any] | list[Any]:
        """
        Make parallel HTTP requests.
        
        Args:
            urls: URL or list of URLs to request (required)
            keys: Optional keys to map responses (default: None)
            method: HTTP method (default: "GET")
            params: Query parameters (default: None)
            data: Request body data (default: None)
            json: JSON request body (default: None)
            headers: Custom headers (default: None)
            parse_func: Custom function to parse responses (default: None)
            return_type: How to process responses (default: JSON)
            stream_callback: Callback for streaming mode (default: None)
        
        Returns:
            - If keys provided: dict mapping keys → responses
            - If single URL: single response
            - If multiple URLs: list of responses
        
        Raises:
            ParallelRequestsError: On request failure (unless return_none_on_failure=True)
        """
        # Implementation...
        pass
    
    async def __aenter__(self) -> "ParallelRequests":
        """Context manager entry for session reuse"""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - close session"""
        await self.close()
    
    async def close(self):
        """Explicit session cleanup"""
        if hasattr(self, '_backend'):
            await self._backend.close()
    
    def _init_proxy_manager(self, proxies: list[str] | None) -> "ProxyManager":
        """Initialize proxy manager"""
        # Implementation...
        pass
    
    def _init_header_manager(self, user_agents: list[str] | None) -> "HeaderManager":
        """Initialize header manager"""
        # Implementation...
        pass
    
    def _init_rate_limiter(self) -> "RateLimiter":
        """Initialize rate limiter"""
        # Implementation...
        pass
    
    def _select_backend(self, backend: str) -> "Backend":
        """Select and initialize backend"""
        # Implementation...
        pass
```

#### Standalone Functions

```python
async def parallel_requests_async(
    urls: str | list[str],
    keys: list[str] | None = None,
    method: str = "GET",
    params: dict | list[dict] | None = None,
    data: Any | list[Any] | None = None,
    json: dict | list[dict] | None = None,
    headers: dict | list[dict] | None = None,
    parse_func: Callable[[Any], Any] | None = None,
    return_type: str = "json",
    concurrency: int = 20,
    max_retries: int = 3,
    retry_backoff: float = 1.0,
    retry_jitter: float = 0.1,
    rate_limit: float | None = None,
    rate_limit_burst: int = 5,
    random_proxy: bool = False,
    random_user_agent: bool = True,
    proxies: list[str] | None = None,
    user_agents: list[str] | None = None,
    backend: str = "auto",
    http2: bool = True,
    stream: bool = False,
    timeout: int = 30,
    cookies: dict | None = None,
    verbose: bool = False,
    debug: bool = False,
    return_none_on_failure: bool = False,
    stream_callback: Callable[[str, Any], None] | None = None,
) -> dict[str, Any] | list[Any]:
    """
    Async version of parallel_requests.
    
    Returns a coroutine that can be awaited.
    """
    async with ParallelRequests(
        concurrency=concurrency,
        max_retries=max_retries,
        retry_backoff=retry_backoff,
        retry_jitter=retry_jitter,
        rate_limit=rate_limit,
        rate_limit_burst=rate_limit_burst,
        random_proxy=random_proxy,
        random_user_agent=random_user_agent,
        proxies=proxies,
        user_agents=user_agents,
        backend=backend,
        http2=http2,
        stream=stream,
        timeout=timeout,
        cookies=cookies,
        verbose=verbose,
        debug=debug,
        return_none_on_failure=return_none_on_failure,
    ) as pr:
        return await pr.request(
            urls=urls,
            keys=keys,
            method=method,
            params=params,
            data=data,
            json=json,
            headers=headers,
            parse_func=parse_func,
            return_type=ReturnType(return_type),
            stream_callback=stream_callback,
        )

def parallel_requests(
    urls: str | list[str],
    keys: list[str] | None = None,
    method: str = "GET",
    params: dict | list[dict] | None = None,
    data: Any | list[Any] | None = None,
    json: dict | list[dict] | None = None,
    headers: dict | list[dict] | None = None,
    parse_func: Callable[[Any], Any] | None = None,
    return_type: str = "json",
    concurrency: int = 20,
    max_retries: int = 3,
    retry_backoff: float = 1.0,
    retry_jitter: float = 0.1,
    rate_limit: float | None = None,
    rate_limit_burst: int = 5,
    random_proxy: bool = False,
    random_user_agent: bool = True,
    proxies: list[str] | None = None,
    user_agents: list[str] | None = None,
    backend: str = "auto",
    http2: bool = True,
    stream: bool = False,
    timeout: int = 30,
    cookies: dict | None = None,
    verbose: bool = False,
    debug: bool = False,
    return_none_on_failure: bool = False,
    stream_callback: Callable[[str, Any], None] | None = None,
) -> dict[str, Any] | list[Any]:
    """
    Make parallel HTTP requests synchronously.
    
    This is a convenience wrapper that runs parallel_requests_async()
    using asyncio.run().
    
    For better performance in async contexts, use parallel_requests_async()
    directly.
    """
    return asyncio.run(
        parallel_requests_async(
            urls=urls,
            keys=keys,
            method=method,
            params=params,
            data=data,
            json=json,
            headers=headers,
            parse_func=parse_func,
            return_type=return_type,
            concurrency=concurrency,
            max_retries=max_retries,
            retry_backoff=retry_backoff,
            retry_jitter=retry_jitter,
            rate_limit=rate_limit,
            rate_limit_burst=rate_limit_burst,
            random_proxy=random_proxy,
            random_user_agent=random_user_agent,
            proxies=proxies,
            user_agents=user_agents,
            backend=backend,
            http2=http2,
            stream=stream,
            timeout=timeout,
            cookies=cookies,
            verbose=verbose,
            debug=debug,
            return_none_on_failure=return_none_on_failure,
            stream_callback=stream_callback,
        )
    )
```

### 7.2 Backend Interface (`backends/base.py`)

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Optional
import enum

class HTTPMethod(enum.Enum):
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    PATCH = "PATCH"
    DELETE = "DELETE"
    HEAD = "HEAD"
    OPTIONS = "OPTIONS"

@dataclass
class NormalizedResponse:
    """Uniform response type across all backends"""
    status_code: int
    headers: dict[str, str]
    content: bytes
    text: str
    json_data: Optional[dict | list]
    url: str
    
    @classmethod
    def from_backend(cls, response: Any, is_json: bool = False) -> "NormalizedResponse":
        """
        Convert backend-specific response to normalized format.
        
        Args:
            response: Backend-specific response object
            is_json: Whether to parse JSON from content
        
        Returns:
            NormalizedResponse instance
        """
        # Extract common fields from backend response
        content = getattr(response, 'content', b'')
        text = content.decode('utf-8', errors='replace')
        
        json_data = None
        if is_json:
            try:
                import json
                json_data = json.loads(text)
            except (json.JSONDecodeError, UnicodeDecodeError):
                json_data = None
        
        return cls(
            status_code=getattr(response, 'status_code', 0),
            headers=dict(getattr(response, 'headers', {})),
            content=content,
            text=text,
            json_data=json_data,
            url=getattr(response, 'url', ''),
        )

@dataclass
class RequestConfig:
    """Normalized request configuration"""
    url: str
    method: str
    params: Optional[dict]
    data: Any
    json: Optional[dict]
    headers: dict
    cookies: Optional[dict]
    timeout: int
    proxy: Optional[str]
    http2: bool
    stream: bool

class Backend(ABC):
    """Abstract interface for all HTTP backends"""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Backend name (niquests, aiohttp, requests)"""
    
    @abstractmethod
    async def request(self, config: RequestConfig) -> NormalizedResponse:
        """
        Make single HTTP request.
        
        Args:
            config: Normalized request configuration
        
        Returns:
            NormalizedResponse instance
        
        Raises:
            BackendError: On request failure
        """
    
    @abstractmethod
    async def close(self):
        """Close session/connection"""
    
    @abstractmethod
    async def __aenter__(self) -> "Backend":
        """Context manager entry"""
    
    @abstractmethod
    async def __aexit__(self, *args):
        """Context manager exit"""
    
    @abstractmethod
    def supports_http2(self) -> bool:
        """Whether backend supports HTTP/2"""
```

### 7.3 Retry Strategy (`utils/retry.py`)

```python
import asyncio
import random
from dataclasses import dataclass
from typing import Callable, Type, Any, Optional, Set

@dataclass
class RetryConfig:
    """Retry configuration"""
    max_retries: int = 3
    backoff_multiplier: float = 1.0
    jitter: float = 0.1
    retry_on: Set[Type[Exception]] | None = None
    dont_retry_on: Set[Type[Exception]] | None = None

class RetryExhausted(Exception):
    """Raised when all retry attempts are exhausted"""
    pass

class RetryStrategy:
    """
    Exponential backoff with jitter for retries.
    
    Algorithm:
        delay = backoff_multiplier * (2 ** retry_attempt)
        jittered_delay = delay * (1 ± random(0, jitter))
    
    Example (max_retries=3, backoff=1.0, jitter=0.1):
        - Attempt 1: delay 0s (immediate)
        - Attempt 2: delay 1.0s ± 0.1s (0.9-1.1s)
        - Attempt 3: delay 2.0s ± 0.2s (1.8-2.2s)
        - Attempt 4: (if max_retries=4) 4.0s ± 0.4s (3.6-4.4s)
    
    Example:
        >>> strategy = RetryStrategy(RetryConfig(
        ...     max_retries=3,
        ...     backoff_multiplier=1.0,
        ...     jitter=0.1,
        ... ))
        >>> result = await strategy.execute(fetch_url, "https://example.com")
    """
    
    def __init__(self, config: RetryConfig):
        self._config = config
    
    async def execute(
        self,
        func: Callable[..., Any],
        *args,
        **kwargs,
    ) -> Any:
        """
        Execute function with retry logic.
        
        Args:
            func: Async callable to retry
            args, kwargs: Arguments to pass to func
        
        Returns:
            Result of func() on success
        
        Raises:
            RetryExhausted: After max_retries attempts
        """
        last_error = None
        
        for attempt in range(self._config.max_retries + 1):
            try:
                return await func(*args, **kwargs)
            
            except Exception as e:
                last_error = e
                
                # Check if we should retry
                if self._config.dont_retry_on:
                    if type(e) in self._config.dont_retry_on:
                        raise
                
                if self._config.retry_on:
                    if type(e) not in self._config.retry_on:
                        raise
                
                # Don't sleep on last attempt
                if attempt == self._config.max_retries:
                    raise RetryExhausted(
                        f"Failed after {attempt + 1} attempts: {e}"
                    ) from e
                
                # Calculate delay with exponential backoff and jitter
                delay = self._config.backoff_multiplier * (2 ** attempt)
                jitter_range = delay * self._config.jitter
                actual_delay = delay + random.uniform(-jitter_range, jitter_range)
                
                # Wait before retrying
                await asyncio.sleep(actual_delay)
        
        # Should not reach here
        raise RetryExhausted(f"Unexpected failure: {last_error}") from last_error
```

### 7.4 Rate Limiter (`utils/rate_limiter.py`)

```python
import asyncio
import time
from dataclasses import dataclass
from typing import Optional

@dataclass
class RateLimitConfig:
    """Rate limiting configuration"""
    requests_per_second: Optional[float] = None
    burst: int = 5

class TokenBucket:
    """
    Token bucket algorithm for rate limiting.
    
    The token bucket is a classic algorithm for rate limiting:
    - Tokens are added at a constant rate
    - Each request consumes one token
    - If no tokens available, request waits or fails
    
    Example:
        >>> bucket = TokenBucket(requests_per_second=10, burst=5)
        >>> await bucket.acquire()  # Takes a token
    """
    
    def __init__(
        self,
        requests_per_second: Optional[float],
        burst: int = 5,
    ):
        """
        Initialize token bucket.
        
        Args:
            requests_per_second: Rate at which tokens are added (None = infinite)
            burst: Maximum tokens in bucket (initial capacity)
        """
        self._rate = requests_per_second
        self._capacity = burst
        self._tokens = burst
        self._last_update = time.monotonic()
        self._lock = asyncio.Lock()
    
    async def acquire(self, tokens: int = 1) -> float:
        """
        Acquire tokens from the bucket.
        
        Args:
            tokens: Number of tokens to acquire
        
        Returns:
            Time waited in seconds
        
        Raises:
            ValueError: If tokens > capacity
        """
        if tokens > self._capacity:
            raise ValueError(
                f"Cannot acquire {tokens} tokens (capacity: {self._capacity})"
            )
        
        async with self._lock:
            # Calculate tokens to add since last update
            now = time.monotonic()
            elapsed = now - self._last_update
            
            if self._rate is not None and self._rate > 0:
                new_tokens = elapsed * self._rate
                self._tokens = min(
                    self._tokens + new_tokens,
                    self._capacity
                )
            
            self._last_update = now
            
            # Wait for tokens if needed
            wait_time = 0.0
            if self._tokens < tokens:
                if self._rate is None or self._rate == 0:
                    # No rate limiting, but not enough tokens
                    raise ValueError("Insufficient tokens")
                
                # Calculate wait time for tokens
                needed = tokens - self._tokens
                wait_time = needed / self._rate
                
                # Wait for tokens to be available
                await asyncio.sleep(wait_time)
                
                # Update tokens after waiting
                now = time.monotonic()
                elapsed = now - self._last_update
                new_tokens = elapsed * self._rate
                self._tokens = min(
                    self._tokens + new_tokens,
                    self._capacity
                )
            
            self._tokens -= tokens
            return wait_time
    
    def available(self) -> int:
        """Return number of available tokens"""
        return int(self._tokens)
    
    def reset(self) -> None:
        """Reset bucket to full capacity"""
        self._tokens = self._capacity
        self._last_update = time.monotonic()

class AsyncRateLimiter:
    """
    Async-compatible rate limiter for concurrent tasks.
    
    Combines token bucket with semaphore to ensure:
    1. Rate limit is respected (tokens)
    2. Concurrency is limited (semaphore)
    
    Example:
        >>> limiter = AsyncRateLimiter(requests_per_second=10, burst=5)
        >>> await limiter.acquire()  # Blocks if rate exceeded
    """
    
    def __init__(
        self,
        requests_per_second: Optional[float],
        burst: int = 5,
        max_concurrency: int = 100,
    ):
        """
        Initialize async rate limiter.
        
        Args:
            requests_per_second: RPS limit (None = no limit)
            burst: Burst allowance
            max_concurrency: Maximum concurrent operations
        """
        self._bucket = TokenBucket(requests_per_second, burst)
        self._semaphore = asyncio.Semaphore(max_concurrency)
    
    async def acquire(self, tokens: int = 1) -> float:
        """
        Acquire with both semaphore and rate limiting.
        
        Args:
            tokens: Number of tokens to acquire
        
        Returns:
            Time waited in seconds
        """
        async with self._semaphore:
            return await self._bucket.acquire(tokens)
    
    def available(self) -> int:
        """Return available tokens"""
        return self._bucket.available()
```

### 7.5 Proxy Manager (`utils/proxies.py`)

```python
import os
import asyncio
import time
from dataclasses import dataclass
from typing import Optional, List, Dict
import re

@dataclass
class ProxyConfig:
    """Proxy configuration"""
    enabled: bool = False
    list: Optional[List[str]] = None
    webshare_url: Optional[str] = None
    free_proxies: bool = False
    retry_delay: float = 60.0
    validation_timeout: float = 5.0

class ProxyValidationError(Exception):
    """Raised when proxy validation fails"""
    pass

class ProxyManager:
    """
    Manages proxy rotation with webshare integration.
    
    Features:
    - Load from list, env var, or webshare URL
    - Random rotation
    - Fail-fast: temporarily disable failing proxies
    - Format validation
    
    Example:
        >>> config = ProxyConfig(
        ...     enabled=True,
        ...     webshare_url=os.getenv("WEBSHARE_PROXIES_URL"),
        ... )
        >>> manager = ProxyManager(config)
        >>> proxy = await manager.get_next()
    """
    
    # Valid proxy formats
    PROXY_PATTERNS = [
        r'^(\d{1,3}\.){3}\d{1,3}:\d{1,5}$',  # ip:port
        r'^(\d{1,3}\.){3}\d{1,5}:[^:]+:[^:]+$',  # ip:port:user:pw
        r'^http://[^:]+:[^@]+@[^:]+:\d+$',  # http://user:pw@ip:port
        r'^https://[^:]+:[^@]+@[^:]+:\d+$',  # https://user:pw@ip:port
    ]
    
    def __init__(self, config: ProxyConfig):
        """
        Initialize proxy manager.
        
        Args:
            config: Proxy configuration
        
        Raises:
            ProxyValidationError: If initial validation fails
        """
        self._config = config
        self._proxies: List[str] = []
        self._failed_proxies: Dict[str, float] = {}  # proxy -> disable_until_timestamp
        self._lock = asyncio.Lock()
        
        # Load proxies
        self._load_proxies()
    
    def _load_proxies(self) -> None:
        """Load proxies from configured sources"""
        proxies = []
        
        # 1. Custom list
        if self._config.list:
            proxies.extend(self._config.list)
        
        # 2. Environment variable
        env_proxies = os.getenv("PROXIES", "")
        if env_proxies:
            proxies.extend(env_proxies.split(","))
        
        # 3. Webshare URL
        if self._config.webshare_url:
            webshare_proxies = self._load_webshare_proxies(self._config.webshare_url)
            proxies.extend(webshare_proxies)
        
        # 4. Free proxies (OPT-IN ONLY)
        if self._config.free_proxies:
            free_proxies = self._fetch_free_proxies()
            proxies.extend(free_proxies)
        
        # Validate and store
        self._proxies = []
        for proxy in proxies:
            if self.validate(proxy):
                self._proxies.append(proxy)
    
    def _load_webshare_proxies(self, url: str) -> List[str]:
        """
        Load proxies from webshare.io.
        
        Expected format: ip:port:user:password per line
        Converted to: http://user:password@ip:port
        """
        import requests
        
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            proxies = []
            for line in response.text.strip().split("\n"):
                line = line.strip()
                if not line:
                    continue
                
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
    
    def _fetch_free_proxies(self) -> List[str]:
        """
        Fetch free proxies (OPT-IN ONLY).
        
        Note: Free proxies are unreliable and may be slow.
        This should only be called if free_proxies=True in config.
        """
        # This is a placeholder - actual implementation would
        # scrape free proxy websites and validate them
        return []
    
    @classmethod
    def validate(cls, proxy: str) -> bool:
        """
        Validate proxy format.
        
        Args:
            proxy: Proxy string to validate
        
        Returns:
            True if valid, False otherwise
        """
        if not proxy or not isinstance(proxy, str):
            return False
        
        for pattern in cls.PROXY_PATTERNS:
            if re.match(pattern, proxy):
                return True
        
        return False
    
    async def get_next(self) -> Optional[str]:
        """
        Get next available proxy.
        
        Skips temporarily disabled (failed) proxies.
        Returns None if no proxies available.
        """
        async with self._lock:
            now = time.time()
            
            # Clean up expired failed proxies
            self._failed_proxies = {
                p: t for p, t in self._failed_proxies.items()
                if t > now
            }
            
            # Get enabled proxies
            available = [
                p for p in self._proxies
                if p not in self._failed_proxies
            ]
            
            if not available:
                return None
            
            # Random rotation
            import random
            return random.choice(available)
    
    async def mark_failed(self, proxy: str) -> None:
        """
        Mark proxy as failed.
        
        Temporarily disables the proxy for retry_delay seconds.
        
        Args:
            proxy: Proxy string that failed
        """
        async with self._lock:
            if proxy in self._proxies:
                self._failed_proxies[proxy] = time.time() + self._config.retry_delay
    
    async def mark_success(self, proxy: str) -> None:
        """
        Mark proxy as successful.
        
        Clears any temporary failure status.
        
        Args:
            proxy: Proxy string that succeeded
        """
        async with self._lock:
            self._failed_proxies.pop(proxy, None)
    
    def count(self) -> int:
        """Return number of configured proxies"""
        return len(self._proxies)
    
    def count_available(self) -> int:
        """Return number of available proxies"""
        now = time.time()
        return sum(
            1 for p in self._proxies
            if p not in self._failed_proxies or self._failed_proxies[p] <= now
        )
```

### 7.6 Header Manager (`utils/headers.py`)

```python
import os
import random
from typing import Optional, Callable, List, Dict

class HeaderManager:
    """
    Manages user agent rotation and header merging.
    
    Features:
    - Load user agents from list or remote source
    - Random rotation
    - Merge with custom headers (custom takes precedence)
    - Optional custom user-agent list
    
    Example:
        >>> manager = HeaderManager(random_user_agent=True)
        >>> headers = manager.get_headers({"Authorization": "Bearer token"})
        >>> headers["user-agent"]
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) ...'
    """
    
    DEFAULT_USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0",
        "Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1",
        "Mozilla/5.0 (iPad; CPU OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1",
    ]
    
    def __init__(
        self,
        random_user_agent: bool = True,
        user_agents: Optional[List[str]] = None,
        custom_user_agent: Optional[str] = None,
    ):
        """
        Initialize header manager.
        
        Args:
            random_user_agent: Enable random rotation (default: True)
            user_agents: Custom list of user agents (default: None)
            custom_user_agent: Single fixed user agent (default: None)
        """
        self._enabled = random_user_agent
        self._custom_ua = custom_user_agent
        self._agents = self._load_user_agents(user_agents)
    
    def _load_user_agents(self, provided: Optional[List[str]]) -> List[str]:
        """
        Load user agents with fallback chain.
        
        Priority:
        1. Provided list
        2. Environment variable USER_AGENTS (comma-separated)
        3. Remote URL (if USER_AGENTS_URL env var set)
        4. Default fallback list
        """
        # 1. Provided list
        if provided:
            return provided
        
        # 2. Environment variable
        env_agents = os.getenv("USER_AGENTS", "")
        if env_agents:
            return env_agents.split(",")
        
        # 3. Remote URL
        remote_url = os.getenv("USER_AGENTS_URL", "")
        if remote_url:
            try:
                import requests
                response = requests.get(remote_url, timeout=10)
                response.raise_for_status()
                agents = [line.strip() for line in response.text.split("\n") if line.strip()]
                if agents:
                    return agents
            except Exception:
                pass  # Fall through to defaults
        
        # 4. Default list
        return self.DEFAULT_USER_AGENTS.copy()
    
    def get_headers(
        self,
        custom_headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, str]:
        """
        Get headers with user agent.
        
        Args:
            custom_headers: User-provided headers that override defaults
        
        Returns:
            Merged headers with user-agent (if enabled)
        """
        headers = {}
        
        # Add user agent if enabled
        if self._enabled:
            if self._custom_ua:
                headers["user-agent"] = self._custom_ua
            else:
                headers["user-agent"] = random.choice(self._agents)
        
        # Merge custom headers (custom overrides default)
        if custom_headers:
            headers.update(custom_headers)
        
        return headers
    
    async def update_agents_from_remote(self, url: str) -> None:
        """
        Fetch fresh user agents from remote source.
        
        Expected format: one user agent per line.
        
        Args:
            url: URL to fetch user agents from
        """
        import requests
        
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            agents = [line.strip() for line in response.text.split("\n") if line.strip()]
            if agents:
                self._agents = agents
        except Exception as e:
            raise ValueError(f"Failed to update user agents: {e}") from e
    
    def set_custom_user_agent(self, user_agent: str) -> None:
        """
        Set a fixed custom user agent.
        
        Args:
            user_agent: User agent string to use
        """
        self._custom_ua = user_agent
    
    def get_user_agents(self) -> List[str]:
        """Return list of configured user agents"""
        return self._agents.copy()
```

### 7.7 Exceptions (`exceptions.py`)

```python
from dataclasses import dataclass, field
from typing import Optional, Any, Dict, Type
import sys

class ParallelRequestsError(Exception):
    """Base exception for all parallel-requests errors"""
    
    def __init__(self, message: str):
        self.message = message
        super().__init__(message)
    
    def __str__(self):
        return self.message

class BackendError(ParallelRequestsError):
    """Backend-specific error"""
    pass

class ProxyError(ParallelRequestsError):
    """Proxy connection or authentication failure"""
    pass

class RetryExhaustedError(ParallelRequestsError):
    """
    All retry attempts failed.
    
    Attributes:
        attempts: Number of retry attempts made
        last_error: The final error that occurred
        url: URL that failed
    """
    
    def __init__(
        self,
        message: str,
        attempts: int,
        last_error: Optional[Exception] = None,
        url: Optional[str] = None,
    ):
        self.attempts = attempts
        self.last_error = last_error
        self.url = url
        super().__init__(message)

class RateLimitExceededError(ParallelRequestsError):
    """Rate limit exceeded"""
    pass

class ValidationError(ParallelRequestsError):
    """Input validation failed"""
    pass

class ConfigurationError(ParallelRequestsError):
    """Invalid configuration"""
    pass

@dataclass
class FailureDetails:
    """Details about a single request failure"""
    key: Optional[str]
    url: str
    error: Exception
    attempts: int

class PartialFailureError(ParallelRequestsError):
    """
    Some requests failed, others succeeded.
    
    Attributes:
        failures: dict[key → FailureDetails] of failed requests
        successes: count of successful requests
        total: total requests attempted
    """
    
    def __init__(
        self,
        message: str,
        failures: Dict[str, FailureDetails],
        successes: int,
        total: int,
    ):
        self.failures = failures
        self.successes = successes
        self.total = total
        super().__init__(message)
    
    def get_failed_urls(self) -> list[str]:
        """Return list of failed URLs"""
        return [f.url for f in self.failures.values()]

# Exception mapping for backend-specific errors
EXCEPTION_MAPPING: Dict[Type[Exception], Type[ParallelRequestsError]] = {
    ConnectionError: BackendError,
    TimeoutError: BackendError,
    asyncio.TimeoutError: BackendError,
    ProxyError: ProxyError,
    RetryExhaustedError: RetryExhaustedError,
}

def map_exception(error: Exception) -> ParallelRequestsError:
    """
    Map backend-specific exception to parallel-requests exception.
    
    Args:
        error: The original exception
    
    Returns:
        Mapped parallel-requests exception
    """
    for exc_type, mapped_type in EXCEPTION_MAPPING.items():
        if isinstance(error, exc_type):
            return mapped_type(str(error))
    
    # Default to BackendError
    return BackendError(str(error))

def exc_info() -> tuple:
    """Get exception info for logging (compatible with Python 3.8-)"""
    return sys.exc_info()
```

### 7.8 Configuration (`config.py`)

```python
from dataclasses import dataclass, field
from typing import Optional, Literal, Dict
import os
from pathlib import Path

@dataclass
class GlobalConfig:
    """Global configuration for parallel-requests"""
    
    # Backend selection
    backend: Literal["auto", "niquests", "aiohttp", "requests"] = "auto"
    
    # Defaults
    default_concurrency: int = 20
    default_max_retries: int = 3
    default_timeout: int = 30
    default_retry_backoff: float = 1.0
    default_retry_jitter: float = 0.1
    
    # Features
    http2_enabled: bool = True
    random_user_agent: bool = True
    random_proxy: bool = False
    
    # Rate limiting
    rate_limit: Optional[float] = None
    rate_limit_burst: int = 5
    
    # Proxies
    proxy_enabled: bool = False
    proxy_retry_delay: float = 60.0
    free_proxies_enabled: bool = False  # MUST BE FALSE BY DEFAULT
    
    # User agents
    user_agents_url: Optional[str] = None
    
    # Logging
    verbose: bool = False
    debug: bool = False
    
    @classmethod
    def load_from_env(cls) -> "GlobalConfig":
        """
        Load config from environment variables.
        
        Supported env vars:
        - PARALLEL_BACKEND
        - PARALLEL_CONCURRENCY
        - PARALLEL_RATE_LIMIT
        - PARALLEL_RATE_LIMIT_BURST
        - PARALLEL_HTTP2
        - PARALLEL_RANDOM_USER_AGENT
        - PARALLEL_RANDOM_PROXY
        - PARALLEL_PROXY_ENABLED
        - PROXIES
        - WEBSHARE_PROXIES_URL
        - PARALLEL_FREE_PROXIES
        - USER_AGENTS
        - USER_AGENTS_URL
        
        Returns:
            GlobalConfig instance with values from environment
        """
        return cls(
            backend=os.getenv("PARALLEL_BACKEND", "auto"),
            default_concurrency=int(os.getenv("PARALLEL_CONCURRENCY", "20")),
            rate_limit=float(os.getenv("PARALLEL_RATE_LIMIT", "0") or None),
            rate_limit_burst=int(os.getenv("PARALLEL_RATE_LIMIT_BURST", "5")),
            http2_enabled=os.getenv("PARALLEL_HTTP2", "true").lower() == "true",
            random_user_agent=os.getenv("PARALLEL_RANDOM_USER_AGENT", "true").lower() == "true",
            random_proxy=os.getenv("PARALLEL_RANDOM_PROXY", "false").lower() == "true",
            proxy_enabled=os.getenv("PARALLEL_PROXY_ENABLED", "false").lower() == "true",
            free_proxies_enabled=os.getenv("PARALLEL_FREE_PROXIES", "false").lower() == "true",
            user_agents_url=os.getenv("USER_AGENTS_URL"),
        )
    
    def to_env(self) -> Dict[str, str]:
        """
        Convert config to environment variables.
        
        Returns:
            Dict of environment variable names to values
        """
        return {
            "PARALLEL_BACKEND": self.backend,
            "PARALLEL_CONCURRENCY": str(self.default_concurrency),
            "PARALLEL_RATE_LIMIT": str(self.rate_limit) if self.rate_limit else "",
            "PARALLEL_RATE_LIMIT_BURST": str(self.rate_limit_burst),
            "PARALLEL_HTTP2": str(self.http2_enabled).lower(),
            "PARALLEL_RANDOM_USER_AGENT": str(self.random_user_agent).lower(),
            "PARALLEL_RANDOM_PROXY": str(self.random_proxy).lower(),
            "PARALLEL_PROXY_ENABLED": str(self.proxy_enabled).lower(),
            "PARALLEL_FREE_PROXIES": str(self.free_proxies_enabled).lower(),
            "USER_AGENTS_URL": self.user_agents_url or "",
        }
    
    def save_to_env(self, path: Path | None = None) -> None:
        """
        Save config to .env file.
        
        Args:
            path: Path to .env file (default: current directory)
        """
        env_path = path or Path(".env")
        
        lines = ["# parallel-requests configuration"]
        for key, value in self.to_env().items():
            if value:
                lines.append(f"{key}={value}")
        
        env_path.write_text("\n".join(lines))

# Global config instance
config = GlobalConfig()
```

---

## 8. API Usage Examples

### 8.1 Basic Parallel Requests

```python
from parallel_requests import parallel_requests

results = parallel_requests(
    urls=[
        "https://api.example.com/users/1",
        "https://api.example.com/users/2",
        "https://api.example.com/users/3",
    ],
    keys=["user1", "user2", "user3"],
    concurrency=20,
)

print(results["user1"])  # Response from first URL
print(results["user2"])  # Response from second URL
print(results["user3"])  # Response from third URL
```

### 8.2 Async Usage with Context Manager

```python
from parallel_requests import ParallelRequests
import asyncio

async def main():
    async with ParallelRequests(
        concurrency=50,
        max_retries=3,
        random_user_agent=True,
    ) as pr:
        results = await pr.request(
            urls=["https://httpbin.org/get"] * 10,
            method="GET",
            return_type="json",
        )
        print(results)

asyncio.run(main())
```

### 8.3 Rate Limited Requests

```python
# 10 requests/second, burst of 5
results = parallel_requests(
    urls=["https://api.example.com/data"] * 100,
    concurrency=50,        # Can launch 50 concurrent
    rate_limit=10,        # But limited to 10 RPS
    rate_limit_burst=5,   # With burst allowance
    verbose=True,
)
# Result: ~10 requests/second, respectful to API
```

### 8.4 Webshare Proxies

```python
from parallel_requests import ParallelRequests
import os

# Set webshare URL once
os.environ["WEBSHARE_PROXIES_URL"] = "https://proxy.webshare.io/api/..."

async def main():
    async with ParallelRequests(
        random_proxy=True,
        max_retries=3,
    ) as pr:
        results = await pr.request(
            urls=["https://httpbin.org/ip"] * 50,
            concurrency=20,
        )

asyncio.run(main())
```

### 8.5 POST with JSON

```python
results = parallel_requests(
    urls=["https://api.example.com/create"] * 10,
    method="POST",
    json={"name": "test", "value": 123},
    concurrency=5,
    max_retries=3,
)
```

### 8.6 Streaming Large File

```python
async def download_chunk(key: str, chunk: bytes):
    """Process each chunk as it arrives"""
    with open(f"download_{key}", "ab") as f:
        f.write(chunk)

async with ParallelRequests(
    concurrency=5,
    stream=True,
) as pr:
    await pr.request(
        urls=["https://example.com/large-file.zip"],
        return_type="stream",
        stream_callback=download_chunk,
        keys=["file1"],
    )
```

### 8.7 HTTP/2 Requests

```python
from parallel_requests import ParallelRequests

# HTTP/2 enabled by default when using niquests
async with ParallelRequests(
    backend="niquests",  # Explicit backend selection
    http2=True,          # Enable HTTP/2 (default for niquests)
) as pr:
    results = await pr.request(
        urls=["https://api.example.com/data"] * 10,
    )
# Uses HTTP/2 for multiplexed requests on same domain
```

### 8.8 Custom User Agents

```python
from parallel_requests import ParallelRequests

custom_agents = [
    "MyCustomApp/1.0",
    "AnotherApp/2.0",
]

async with ParallelRequests(
    random_user_agent=True,
    user_agents=custom_agents,  # Override default list
) as pr:
    results = await pr.request(urls=urls)
```

### 8.9 Custom Parser

```python
def extract_user_id(response):
    """Extract user ID from response"""
    return response.get("id", None)

results = parallel_requests(
    urls=["https://api.example.com/user/1",
          "https://api.example.com/user/2"],
    parse_func=extract_user_id,
    keys=["user1", "user2"],
)

print(results["user1"])  # Just the ID, e.g., 42
print(results["user2"])  # Just the ID, e.g., 43
```

### 8.10 Error Handling

```python
from parallel_requests import (
    ParallelRequests,
    RetryExhaustedError,
    PartialFailureError,
)

try:
    async with ParallelRequests(
        max_retries=3,
        return_none_on_failure=False,  # Raise exceptions (default)
    ) as pr:
        results = await pr.request(urls=urls)
        
except RetryExhaustedError as e:
    print(f"Failed after {e.attempts} retries: {e.last_error}")
    
except PartialFailureError as e:
    print(f"Partial failure: {e.successes}/{e.total} succeeded")
    for key, error in e.failures.items():
        print(f"  {key}: {error}")
```

---

## 9. Technical Decisions

### 9.1 Default Concurrency: 20

**Rationale:**
- Too low: Wastes async capabilities (10 is conservative)
- Too high: May overwhelm APIs (100 is aggressive)
- **20 is balanced** for general web APIs
- Users can easily tune for their use case

**Use case guidance in docs:**
- Web APIs: 10-20 (respect rate limits)
- Scraping: 50-100 (aggressive)
- Local APIs: 100+ (no network bottleneck)

### 9.2 Rate Limiting: Token Bucket

**Algorithm:**
```
tokens = burst_size
last_refill_time = now()

def acquire():
    now = now()
    elapsed = now - last_refill_time
    tokens += elapsed * requests_per_second
    tokens = min(tokens, burst_size)  # Cap at burst size
    last_refill_time = now
    
    if tokens >= 1:
        tokens -= 1
        return  # Acquired
    else:
        wait_for(1 / requests_per_second)  # Wait for next token
        acquire()
```

**Benefits:**
- Allows burst traffic up to `burst_size`
- Long-term respects `requests_per_second`
- Prevents overwhelming APIs

### 9.3 HTTP/2 Implementation

**Niquests:** Native support (default enabled)
**Aiohttp:** Requires `http2=True` in connector config
**Requests:** No HTTP/2 (sync only)

**Implementation:**
```python
# backends/niquests.py
session = niquests.AsyncSession(http2=True)

# backends/aiohttp.py
import aiohttp
connector = aiohttp.TCPConnector(tls=True)  # HTTP/2 with TLS
```

### 9.4 Streaming Implementation

**Return types:**
- `"json"`: Parse to dict
- `"text"`: Decode to str
- `"content"`: Raw bytes
- `"response"`: Normalized response object
- `"stream"`: Yield chunks via callback (NEW)

**Implementation:**
```python
if return_type == "stream" and stream_callback:
    async for chunk in response.content.iter_chunked(8192):
        await asyncio.to_thread(stream_callback, key, chunk)
    return None  # Don't return large data
```

### 9.5 Backend Auto-Selection Logic

```python
async def _select_backend(backend: str) -> type[Backend]:
    if backend != "auto":
        return get_backend(backend)
    
    # Priority: niquests → aiohttp → requests
    for backend_name in ["niquests", "aiohttp", "requests"]:
        try:
            backend_class = get_backend(backend_name)
            # Quick validation: try importing
            await backend_class.__aenter__(None)  # Test initialization
            return backend_class
        except ImportError:
            continue
        except Exception:
            continue
    
    raise ImportError("No HTTP backend available")
```

### 9.6 Retry Logic

**Exponential backoff with jitter:**
```python
delay = backoff_multiplier * (2 ** attempt)
jitter_range = delay * jitter
actual_delay = delay + random.uniform(-jitter_range, jitter_range)
await asyncio.sleep(actual_delay)
```

### 9.7 Error Handling Strategy

**Options:**
1. Raise exceptions by default (Pythonic, explicit)
2. Return None on failure (legacy behavior)
3. Return both results and errors (complex)

**Decision:** Raise exceptions by default, with `return_none_on_failure=True` for legacy compatibility.

---

## 10. Implementation Phases

### Phase 1: Foundation (Week 1)

**Priority: 🔴 Critical**

| Task | Description | Deliverable |
|------|-------------|-------------|
| Create module structure | Set up directories and `__init__.py` | Working module structure |
| Implement exceptions | Full exception hierarchy | `exceptions.py` |
| Implement backend interface | Abstract interface | `backends/base.py` |
| Implement config | Environment loading | `config.py` |
| Add type hints | mypy strict mode | Type-safe foundation |

**Deliverables:**
- Working interface contracts
- Type-safe foundation
- Configuration system

---

### Phase 2: Core Utilities (Week 2)

**Priority: 🔴 Critical**

| Task | Description | Deliverable |
|------|-------------|-------------|
| Implement retry logic | Exponential backoff with jitter | `utils/retry.py` |
| Implement rate limiter | Token bucket algorithm | `utils/rate_limiter.py` |
| Implement validators | Input validation | `utils/validators.py` |
| Remove pandas dependency | Replace list helpers | Zero pandas |
| Unit tests for utils | 90%+ coverage | `tests/utils/` |

**Deliverables:**
- Working retry logic
- Rate limiting with RPS control
- Input validation
- Zero pandas dependency

---

### Phase 3: Proxy & Header Management (Week 2-3)

**Priority: 🟠 High**

| Task | Description | Deliverable |
|------|-------------|-------------|
| Implement proxy manager | Load, validate, rotate proxies | `utils/proxies.py` |
| Implement header manager | User agent rotation | `utils/headers.py` |
| Webshare integration | Load from webshare.io | Proxy manager feature |
| Free proxies (opt-in) | Fetch free proxies | Proxy manager feature |
| Unit tests for managers | 90%+ coverage | `tests/utils/` |

**Deliverables:**
- Complete proxy management with webshare integration
- User agent rotation
- All requirements met

---

### Phase 4: Niquests Backend (Week 3-4)

**Priority: 🔴 Critical**

| Task | Description | Deliverable |
|------|-------------|-------------|
| Implement niquests backend | HTTP/2, async, retry | `backends/niquests.py` |
| HTTP/2 support | Enable by default | Backend feature |
| Response normalization | Unified response format | Backend feature |
| Streaming support | Chunked downloads | Backend feature |
| Integration tests | Real endpoints | `tests/integration/` |

**Deliverables:**
- Primary backend fully functional
- HTTP/2 working
- All features supported

---

### Phase 5: Aiohttp Backend (Week 4)

**Priority: 🟠 High**

| Task | Description | Deliverable |
|------|-------------|-------------|
| Implement aiohttp backend | Mature async client | `backends/aiohttp.py` |
| HTTP/2 support | Via connector config | Backend feature |
| Streaming support | Chunked downloads | Backend feature |
| Response normalization | Unified response format | Backend feature |
| Integration tests | Real endpoints | `tests/integration/` |

**Deliverables:**
- Secondary backend fully functional
- Fallback option ready

---

### Phase 6: Requests Backend (Week 5)

**Priority: 🟡 Medium**

| Task | Description | Deliverable |
|------|-------------|-------------|
| Implement requests backend | Sync via asyncio | `backends/requests.py` |
| Response normalization | Unified response format | Backend feature |
| Integration tests | Real endpoints | `tests/integration/` |
| Benchmark | Compare with async | `tests/benchmarks/` |

**Deliverables:**
- Fallback backend for sync users
- Complete backend coverage

---

### Phase 7: Main Client (Week 5-6)

**Priority: 🔴 Critical**

| Task | Description | Deliverable |
|------|-------------|-------------|
| Implement ParallelRequests | Main class | `client.py` |
| Backend auto-selection | niquests → aiohttp → requests | Client feature |
| Request orchestration | Normalize and dispatch | Client feature |
| Error aggregation | Collect failures | Client feature |
| Context managers | `__aenter__`, `__aexit__` | Client feature |
| Standalone functions | `parallel_requests()`, etc. | `__init__.py` exports |

**Deliverables:**
- Working main API
- All features integrated
- End-to-end tests passing

---

### Phase 8: Advanced Features (Week 6)

**Priority: 🟡 Medium**

| Task | Description | Deliverable |
|------|-------------|-------------|
| Streaming support | `return_type="stream"` | Client feature |
| Rate limiting integration | Combine with concurrency | Client feature |
| Progress bars | tqdm integration | Client feature |
| Streaming examples | Large file examples | Documentation |

**Deliverables:**
- Complete feature set
- Streaming examples

---

### Phase 9: Testing & Documentation (Week 6-7)

**Priority: 🟠 High**

| Task | Description | Deliverable |
|------|-------------|-------------|
| Unit tests | 95%+ coverage | `tests/` |
| Integration tests | Real endpoints | `tests/integration/` |
| Performance tests | Benchmarks | `tests/benchmarks/` |
| README | Complete documentation | `README.md` |
| API reference | All public functions | `docs/` |
| Examples | 10+ use cases | `examples/` |

**Deliverables:**
- Production-ready library
- Complete documentation
- Comprehensive test suite

---

### Phase 10: Release Preparation (Week 7)

**Priority: 🟢 Low**

| Task | Description | Deliverable |
|------|-------------|-------------|
| Code quality | ruff, black, isort clean | Quality gate |
| CI/CD setup | GitHub Actions | `.github/workflows/` |
| CHANGELOG.md | Version history | `CHANGELOG.md` |
| Release notes | v2.0.0 announcement | Release assets |

**Deliverables:**
- Release v2.0.0
- CI/CD pipeline
- Complete documentation

---

## 11. Success Metrics

### 11.1 Functional Requirements (Must-Have)

- [ ] All three backends work identically
- [ ] Retry logic with exponential backoff + jitter works
- [ ] Rate limiting with token bucket works
- [ ] Proxy rotation works without crashing
- [ ] **MUST**: Webshare proxy support
- [ ] **MUST**: User agent rotation
- [ ] **MUST**: No pandas dependency
- [ ] HTTP/2 support (niquests default, aiohttp optional)
- [ ] Streaming support with callbacks
- [ ] All parameter combinations work
- [ ] Session cleanup works properly (context managers)
- [ ] No resource leaks
- [ ] Progress bars display correctly
- [ ] Free proxies opt-in only (disabled by default)

### 11.2 Quality Requirements

| Metric | Target | Tool |
|--------|--------|------|
| Type coverage | 100% | mypy --strict |
| Test coverage | 95%+ | pytest-cov |
| Linting errors | 0 | ruff |
| Formatting issues | 0 | black, isort |
| Docstring coverage | 100% | pydocstyle |
| Security vulnerabilities | 0 | bandit |

### 11.3 Performance Requirements

- [ ] No blocking calls in async code
- [ ] Efficient connection pooling
- [ ] Minimal memory overhead (< 1MB per 100 requests)
- [ ] Benchmark at 100+ concurrent requests
- [ ] Rate limiting respects RPS accurately (±10%)

### 11.4 Documentation Requirements

- [ ] Complete README (all features documented)
- [ ] API reference (all public functions/classes)
- [ ] Examples (10+ use cases)
- [ ] Streaming guide
- [ ] Rate limiting guide
- [ ] Proxy setup guide
- [ ] Migration guide from v0.2.x

---

## 12. Dependencies

### 12.1 Core (Required)

```
python>=3.10
```

### 12.2 Backends (At least one required)

```
# Choose one or install multiple:
niquests>=3.6.0      # Primary: HTTP/2, async, modern
aiohttp>=3.9.0       # Secondary: mature async
requests>=2.31.0      # Fallback: sync support
```

### 12.3 Features

```
tqdm>=4.66.0         # Progress bars
python-dotenv>=1.0.0  # Environment variable support
```

### 12.4 Optional (Development)

```
loguru>=0.7.0        # Enhanced logging (optional)
pytest>=7.4.0        # Testing
pytest-asyncio>=0.21 # Async tests
pytest-cov>=4.1.0    # Coverage
mypy>=1.7.0          # Type checking
ruff>=0.3.0          # Linting
black>=24.0.0        # Formatting
```

### 12.5 Removed

```
pandas>=2.0.0         # ❌ Remove (unnecessary)
numpy>=1.24.2          # ❌ Remove (unnecessary)
asyncer>=0.0.2         # ❌ Remove (use asyncio.to_thread())
```

---

## 13. Testing Strategy

### 13.1 Test Structure

```
tests/
├── unit/
│   ├── test_retry.py
│   ├── test_rate_limiter.py
│   ├── test_proxies.py
│   ├── test_headers.py
│   └── test_validators.py
├── integration/
│   ├── test_basic_requests.py
│   ├── test_rate_limiting.py
│   ├── test_proxy_rotation.py
│   ├── test_retry_logic.py
│   ├── test_streaming.py
│   └── test_all_backends.py
├── backends/
│   ├── test_niquests.py
│   ├── test_aiohttp.py
│   └── test_requests.py
├── conftest.py
└── fixtures/
    ├── sample_responses.json
    └── proxy_list.txt
```

### 13.2 Unit Tests

```bash
# Utils
pytest tests/unit/test_retry.py -v --cov
pytest tests/unit/test_rate_limiter.py -v --cov
pytest tests/unit/test_proxies.py -v --cov
pytest tests/unit/test_headers.py -v --cov

# Backends
pytest tests/backends/ -v --cov
```

### 13.3 Integration Tests

```bash
# End-to-end
pytest tests/integration/test_basic_requests.py -v
pytest tests/integration/test_rate_limiting.py -v
pytest tests/integration/test_proxy_rotation.py -v
pytest tests/integration/test_retry_logic.py -v
pytest tests/integration/test_streaming.py -v
```

### 13.4 Performance Tests

```bash
# Benchmarks
pytest tests/benchmarks/test_concurrent_requests.py -v
pytest tests/benchmarks/test_rate_limiting.py -v
pytest tests/benchmarks/test_backends.py -v
```

### 13.5 Test Coverage Goal

| Area | Target |
|------|--------|
| Total | 95%+ |
| Critical paths | 100% |
| Backends | 100% each |
| Utils | 90%+ |

---

## 14. Migration Guide

### 14.1 Breaking Changes

| Area | v0.2.x | v2.0.0 | Migration |
|------|---------|----------|-----------|
| Error handling | Silent None returns | Raises exceptions | Wrap in try/except |
| Proxies | Auto-fetch on import | Load on init | Call ParallelRequests() |
| Backends | 3 different APIs | 1 unified API | No changes needed |
| Pandas | Required for list ops | Removed | Convert Series beforehand |
| Rate limiting | ❌ Not available | ✅ RateLimiter class | Use `rate_limit` param |

### 14.2 Migration Example

```python
# v0.2.x (broken)
from parallel_requests import parallel_requests
result = parallel_requests(urls=bad_url)
if result is None:  # Check for failure
    print("Failed")

# v2.0.0 (fixed)
from parallel_requests import ParallelRequests, RetryExhaustedError

try:
    async with ParallelRequests() as pr:
        result = await pr.request(urls=bad_url)
except RetryExhaustedError as e:
    print(f"Failed after {e.attempts} retries: {e.last_error}")
```

### 14.3 API Comparison

| Feature | v0.2.x | v2.0.0 |
|---------|---------|----------|
| Basic request | `parallel_requests(url=...)` | `parallel_requests(urls=...)` |
| Async | `parallel_requests_async(...)` | `parallel_requests_async(...)` |
| Class | `ParallelRequests(...)` | `ParallelRequests(...)` |
| Proxy rotation | `random_proxy=True` | `random_proxy=True` |
| User agent | `random_user_agent=True` | `random_user_agent=True` |
| Rate limiting | ❌ Not available | `rate_limit=10` |
| Streaming | ❌ Not available | `return_type="stream"` |
| HTTP/2 | ❌ Not available | `http2=True` |
| Error handling | Returns None | Raises exceptions |

---

## 15. Timeline

| Week | Phase | Deliverables |
|------|-------|-------------|
| 1 | Foundation | Interfaces, config, exceptions |
| 2 | Core Utils | Retry, rate limiter, validation |
| 2-3 | Proxies/Headers | Proxy rotation, user agents |
| 3-4 | Niquests Backend | Primary backend, HTTP/2 |
| 4 | Aiohttp Backend | Secondary backend |
| 5 | Requests Backend | Fallback backend |
| 5-6 | Main Client | ParallelRequests class |
| 6 | Advanced | Streaming, rate limiting integration |
| 6-7 | Testing | 95% coverage, docs |
| 7 | Release | v2.0.0 ready |

**Total: 7 weeks to production-ready v2.0.0**  
**Estimated effort: 350-450 hours**

---

## 16. Risks and Mitigations

| Risk | Impact | Probability | Mitigation |
|------|--------|--------------|------------|
| HTTP/2 complexity | High | Medium | Well-tested in niquests, fallback to HTTP/1.1 |
| Rate limiting bugs | High | Low | Unit tests, integration tests |
| Backend incompatibility | Medium | Low | Abstract interface, each tested independently |
| Performance regression | Medium | Low | Benchmarks, optimization phase |
| Scope creep | Medium | High | Strict PRD, phase gates |
| Dependency changes | Medium | Low | Pin versions in pyproject.toml |

---

## 17. Open Questions

### 17.1 Implementation Questions

1. **CI/CD**: Should I set up GitHub Actions workflow for automated testing?
2. **Benchmarking**: Should I include automated benchmarks in CI?
3. **Documentation tool**: Sphinx, mkdocs, or just README.md?
4. **Example data**: Should I include example proxy lists and user agents in repo?
5. **Web partnership**: Any affiliate or partnership with webshare for proxy integration?

### 17.2 Technical Questions

1. **Timeout handling**: Should timeout be per-request or total (including retries)?
2. **Cookie management**: Should cookies be shared across requests or per-request?
3. **Redirect handling**: Should redirects be followed automatically?
4. **SSL verification**: Should SSL verification be enabled by default?

---

## Appendix A: Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `PARALLEL_BACKEND` | Backend selection | "auto" |
| `PARALLEL_CONCURRENCY` | Default concurrency | 20 |
| `PARALLEL_RATE_LIMIT` | Default RPS limit | None |
| `PARALLEL_RATE_LIMIT_BURST` | Default burst size | 5 |
| `PARALLEL_HTTP2` | Enable HTTP/2 | "true" |
| `PARALLEL_RANDOM_USER_AGENT` | Enable UA rotation | "true" |
| `PARALLEL_RANDOM_PROXY` | Enable proxy rotation | "false" |
| `PARALLEL_PROXY_ENABLED` | Enable proxy support | "false" |
| `PROXIES` | Comma-separated proxy list | None |
| `WEBSHARE_PROXIES_URL` | Webshare proxy URL | None |
| `PARALLEL_FREE_PROXIES` | Enable free proxies | "false" |
| `USER_AGENTS` | Comma-separated UA list | None |
| `USER_AGENTS_URL` | Remote UA list URL | None |

---

## Appendix B: Default User Agents

```python
DEFAULT_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (iPad; CPU OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1",
]
```

---

## Appendix C: Exception Hierarchy

```
ParallelRequestsError (base)
├── BackendError
├── ProxyError
├── RetryExhaustedError
├── RateLimitExceededError
├── ValidationError
├── ConfigurationError
└── PartialFailureError
```

---

## Appendix D: Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-12-28 | Development Team | Initial PRD draft |

---

**Document Status:** Ready for Review  
**Next Steps:** Approve PRD, begin Phase 1 implementation
