# Change: Prevent import failures when optional deps are missing

## Why
Users should be able to install `parallel-requests` with only a subset of optional backend dependencies and still import the package successfully. Today, importing `parallel_requests.backends` eagerly imports all backend implementations, which can raise `ImportError` if (for example) `aiohttp` is not installed—even when `niquests` is installed and will be selected.

## What Changes
- **MODIFIED** `parallel_requests.backends` package to avoid importing optional backend dependencies at import time
- **ADDED** lazy exports for optional backend classes (import backend implementation only when accessed)
- **ADDED** tests/quality gates to ensure importing the package works with partial optional installs

## Impact
- Affected specs: `optional-dependency-imports`
- Affected code:
  - `src/parallel_requests/backends/__init__.py` (lazy imports; avoid importing `aiohttp`/`requests` unless used)
  - Potentially docs/tests that import backend symbols directly
- Dependencies: none (behavioral change only)
