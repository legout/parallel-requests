# Change: Add Backend Implementations

## Why
The library needs concrete HTTP backend implementations following the `Backend` interface contract. Three backends are required: niquests (primary, HTTP/2), aiohttp (secondary), and requests (fallback for sync users).

## What Changes
- **ADDED** niquests backend with HTTP/2 support (`backends/niquests.py`)
- **ADDED** aiohttp backend (`backends/aiohttp.py`)
- **ADDED** requests backend with asyncio.to_thread() (`backends/requests.py`)
- All backends implement the `Backend` interface and return `NormalizedResponse`

## Impact
- Affected specs: `backend-niquests`, `backend-aiohttp`, `backend-requests`
- Affected code:
  - `src/parallel_requests/backends/niquests.py` (new)
  - `src/parallel_requests/backends/aiohttp.py` (new)
  - `src/parallel_requests/backends/requests.py` (new)
- Dependencies: niquests, aiohttp, requests (optional, installed separately)
