# Project Context

## Purpose

`parallel-requests` v2.0.0 is a Python library for making fast parallel HTTP requests with:
- Automatic retry logic with exponential backoff and jitter
- Proxy rotation (Webshare.io integration, opt-in free proxies)
- User agent rotation (enabled by default)
- Rate limiting using token bucket algorithm
- HTTP/2 support (via niquests backend)
- Streaming support for large file downloads
- Multiple backend support: niquests (primary), aiohttp (secondary), requests (fallback)

This is a complete rewrite from v0.2.x which was non-functional due to critical bugs.

## Tech Stack

- **Language**: Python 3.10 - 3.12
- **Async Framework**: asyncio (native Python)
- **HTTP Backends**: niquests (primary), aiohttp, requests
- **Core Dependencies**: tqdm, python-dotenv, loguru
- **Development Tools**:
  - Formatting: black, ruff, isort
  - Type Checking: mypy
  - Testing: pytest, pytest-asyncio, pytest-cov
  - Security: bandit

## Project Conventions

### Code Style

- **Line Length**: 100 characters
- **Type Hints**: Required, `disallow_untyped_defs` enabled in mypy
- **Formatting**: black with line-length 100
- **Import Sorting**: isort with black profile
- **Linting**: ruff
- **No Comments**: Unless explicitly requested

### Architecture Patterns

- **Strategy Pattern**: Backend implementations via abstract base class
- **Context Managers**: Always use async context managers for resource management
- **Explicit Parameters**: No `*args` or `**kwargs` without validation
- **Data Classes**: Use dataclasses for configuration and response types
- **Module Structure**:
  - `src/parallel_requests/` - Main package
  - `src/parallel_requests/backends/` - Backend strategy implementations
  - `src/parallel_requests/utils/` - Utility modules (retry, rate_limiter, headers, proxies)
  - `tests/` - Unit, integration, and benchmark tests

### Testing Strategy

- **Test Framework**: pytest with pytest-asyncio
- **Test Paths**: `tests/` directory
- **Naming**: `test_*.py` files, `test_*` functions
- **Coverage**: pytest-cov for coverage reporting
- **Test Types**:
  - Unit tests in `tests/unit/`
  - Integration tests in `tests/integration/`
  - Benchmarks in `tests/benchmarks/`

### Git Workflow

- **Branching**: Feature branches from main
- **Commits**: Conventional commits, descriptive messages
- **No Force Push**: Never force push to main/master
- **Hooks**: Pre-commit hooks via tools like bandit for security

### Logging

- **Library**: Loguru (>=0.7.0) - do NOT use Python's standard `logging` module
- **Import Pattern**: `from loguru import logger`
- **Log Levels**: Use appropriate levels (debug, info, warning, error, critical)
- **Usage Pattern**:
  ```python
  from loguru import logger

  logger.debug("Detailed diagnostic info")
  logger.info("General informational messages")
  logger.warning("Warning conditions")
  logger.error("Error conditions")
  logger.critical("Critical conditions")
  ```
- **Configuration**: Use centralized `configure_logging()` from `utils/logging.py`
- **Default Behavior**: INFO level logging, DEBUG only when explicitly enabled via `debug=True`
- **Parameters**:
  - `debug`: Controls loguru log level (INFO vs DEBUG)
  - `verbose`: Controls tqdm progress bar visibility (separate from logging)

## Domain Context

- HTTP request parallelism and concurrency
- Rate limiting (token bucket algorithm)
- Exponential backoff retry strategies
- Proxy rotation and management
- HTTP/2 multiplexing
- Response streaming for large files

## Important Constraints

- Python 3.10 minimum, 3.12 maximum
- No pandas or unnecessary dependencies
- Free proxies opt-in only (not enabled by default)
- Clean break v2.0.0 - no backward compatibility with v0.2.x
- No silent failures - exceptions must be raised by default

## External Dependencies

- **Webshare.io**: Proxy provider integration
- **HTTP Libraries**: niquests, aiohttp, requests (optional backends)
