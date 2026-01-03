## 1. Proxy Manager
- [x] 1.1 Create `src/parallel_requests/utils/proxies.py` with `ProxyConfig` dataclass
- [x] 1.2 Implement `ProxyManager` class with validation and rotation
- [x] 1.3 Add Webshare.io integration (load from URL, format conversion)
- [x] 1.4 Add free proxy fetching (opt-in only, returns empty by default)
- [x] 1.5 Add proxy failure tracking with temporary disable (retry_delay)
- [x] 1.6 Write unit tests for proxy manager (90%+ coverage)

## 2. Header Manager
- [x] 2.1 Create `src/parallel_requests/utils/headers.py` with `HeaderManager` class
- [x] 2.2 Implement user agent rotation with default list (from PRD Appendix B)
- [x] 2.3 Support custom user agent list via constructor
- [x] 2.4 Support environment variable for user agents
- [x] 2.5 Implement header merging (custom overrides default)
- [x] 2.6 Write unit tests for header manager (90%+ coverage)

## 3. Quality Gates
- [x] 3.1 Run `mypy src/parallel_requests/utils/proxies.py src/parallel_requests/utils/headers.py --strict`
- [x] 3.2 Run `ruff check src/parallel_requests/utils/proxies.py src/parallel_requests/utils/headers.py`
- [x] 3.3 Run `black --check src/parallel_requests/utils/proxies.py src/parallel_requests/utils/headers.py`
- [x] 3.4 Run `pytest tests/unit/test_proxies.py tests/unit/test_headers.py` (all pass, 90%+ coverage)
