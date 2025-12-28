# parallel-requests v2.0.0

**Status**: 🚧 Rebuilding from scratch

Fast parallel HTTP requests with asyncio, retry logic, proxy rotation, and rate limiting.

## Quick Start

```python
from parallel_requests import parallel_requests

results = parallel_requests(
    urls=["https://httpbin.org/get"] * 10,
    concurrency=20,
    rate_limit=10,  # 10 requests/second
    verbose=True,
)
```

## Features

- 🔄 **Retry Logic**: Exponential backoff with jitter
- 🔒 **Proxy Rotation**: Webshare.io integration, free proxies (opt-in)
- 🌐 **User Agent Rotation**: Random rotation enabled by default
- ⚡ **Rate Limiting**: Token bucket algorithm, respects API limits
- 🚀 **HTTP/2 Support**: When using niquests backend
- 📡 **Streaming**: Support for large file downloads
- 🎯 **Multiple Backends**: niquests (primary), aiohttp (secondary), requests (fallback)

## Installation

```bash
# Core library only
pip install parallel-requests

# With specific backend (recommended: niquests)
pip install parallel-requests[niquests]  # Primary (recommended)
pip install parallel-requests[aiohttp]
pip install parallel-requests[requests]

# All backends
pip install parallel-requests[all]
```

## Documentation

- 📖 **PRD.md**: Complete product requirements and specifications
- 📋 **PROJECT.md**: Development progress tracking

## Development Status

See PROJECT.md for detailed progress.

### Phase 1: Foundation (Week 1) - NOT STARTED
### Phase 2: Core Utilities (Week 2) - NOT STARTED
### Phase 3: Proxy & Headers (Week 2-3) - NOT STARTED
### Phase 4: Niquests Backend (Week 3-4) - NOT STARTED
### Phase 5: Aiohttp Backend (Week 4) - NOT STARTED
### Phase 6: Requests Backend (Week 5) - NOT STARTED
### Phase 7: Main Client (Week 5-6) - NOT STARTED
### Phase 8: Advanced Features (Week 6) - NOT STARTED
### Phase 9: Testing & Documentation (Week 6-7) - NOT STARTED
### Phase 10: Release (Week 7) - NOT STARTED

## Migration from v0.2.x

**Note**: v0.2.x was broken and has been archived to `legacy/v0.2.x` branch.

v2.0.0 is a complete rewrite with breaking changes. See PRD.md for detailed migration guide.

## License

See LICENSE file.
