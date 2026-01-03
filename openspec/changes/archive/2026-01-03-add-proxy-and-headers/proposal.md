# Change: Add Proxy and Header Management

## Why
The library needs proxy rotation (with Webshare.io integration) and user agent rotation for anti-detection and request distribution. Free proxies are opt-in only to avoid reliability issues.

## What Changes
- **ADDED** proxy manager with format validation, Webshare.io loading, and rotation (`utils/proxies.py`)
- **ADDED** header manager with user agent rotation and custom header merging (`utils/headers.py`)
- **ADDED** free proxies opt-in (disabled by default per PRD)
- **ADDED** proxy failure tracking with temporary disable

## Impact
- Affected specs: `proxy-rotation`, `header-management`
- Affected code:
  - `src/parallel_requests/utils/proxies.py` (new)
  - `src/parallel_requests/utils/headers.py` (new)
- Dependencies: None (uses requests for Webshare loading, can be swapped)
