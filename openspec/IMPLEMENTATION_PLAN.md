# Implementation Order Plan

This document defines the execution order and dependencies for all OpenSpec proposals.

## Overview

| Phase | Change ID | Capabilities | Week |
|-------|-----------|--------------|------|
| 1 | `add-foundation-contracts` | `error-handling`, `backend-contract`, `configuration` | 1 |
| 2 | `add-core-utils` | `retry-policy`, `rate-limiting`, `input-validation` | 2 |
| 3 | `add-proxy-and-headers` | `proxy-rotation`, `header-management` | 2-3 |
| 4 | `add-backends` | `backend-niquests`, `backend-aiohttp`, `backend-requests` | 3-4 |
| 5 | `add-client-api` | `client-api`, `public-api` | 5-6 |

## Dependency Graph

```
add-foundation-contracts (MUST BE FIRST)
    │
    ├── add-core-utils
    │       └── retry-policy, rate-limiting, input-validation
    │
    ├── add-proxy-and-headers
    │       └── proxy-rotation, header-management
    │
    ├── add-backends
    │       └── backend-niquests, backend-aiohttp, backend-requests
    │
    └── add-client-api (NEEDS ALL PREVIOUS)
            └── client-api, public-api
```

## Dependency Details

| Change | Depends On | Dependency Reason |
|--------|-----------|-------------------|
| `add-foundation-contracts` | None | Foundation layer - no dependencies |
| `add-core-utils` | `add-foundation-contracts` | Uses `ValidationError` exception, `GlobalConfig` |
| `add-proxy-and-headers` | `add-foundation-contracts` | Uses `ValidationError`, `ProxyError` |
| `add-backends` | `add-foundation-contracts` | Implements `Backend` abstract interface |
| `add-client-api` | All previous | Uses exceptions, config, utils, proxy manager, header manager, backends |

## Execution Strategies

### Strategy A: Sequential (Recommended for Safety)

Complete each change fully before starting the next:

```
Week 1:  add-foundation-contracts
    → openspec archive add-foundation-contracts --yes
Week 2:  add-core-utils
    → openspec archive add-core-utils --yes
Week 2-3: add-proxy-and-headers
    → openspec archive add-proxy-and-headers --yes
Week 3-4: add-backends
    → openspec archive add-backends --yes
Week 5-6: add-client-api
    → openspec archive add-client-api --yes
```

**Pros:**
- No merge conflicts
- Clean archive history
- Each phase builds on tested previous work

**Cons:**
- Longer total time

### Strategy B: Parallel (Faster, More Complex)

Run parallel where dependencies allow:

```
Week 1:  add-foundation-contracts
    → archive immediately

Week 2:
    ├─ add-core-utils
    └─ add-proxy-and-headers
        (orthogonal - no cross-dependencies)

Week 3-4:
    ├─ add-backends (needs foundation only)
    └─ continue core-utils or proxy if not done

Week 5-6: add-client-api (needs everything else)
```

**Pros:**
- Faster total time
- Better CPU utilization (if implementing tests in parallel)

**Cons:**
- Potential merge conflicts
- Requires careful coordination

## Recommended Approach

**Use Strategy A (Sequential)** for this project because:
1. Clear phase boundaries defined in PRD
2. Each phase's tasks list dependencies explicitly
3. Fewer merge conflicts to resolve
4. Easier to track progress against PROJECT.md timeline

## Per-Change Implementation Order

Within each change, tasks should be implemented in the order listed in `tasks.md` to respect internal dependencies.

### add-foundation-contracts Order
1. Exceptions hierarchy (`exceptions.py`)
2. Backend interface (`backends/base.py`)
3. Configuration system (`config.py`)
4. Quality gates (mypy, ruff, black, pytest)

### add-core-utils Order
1. Retry policy (`utils/retry.py`)
2. Rate limiting (`utils/rate_limiter.py`)
3. Input validation (`utils/validators.py`)
4. Quality gates

### add-proxy-and-headers Order
1. Proxy manager (`utils/proxies.py`)
2. Header manager (`utils/headers.py`)
3. Quality gates

### add-backends Order
1. Niquests backend (primary)
2. Aiohttp backend (secondary)
3. Requests backend (fallback)
4. Integration tests for all

### add-client-api Order
1. ParallelRequests class core
2. Return types and options
3. Retry/rate-limit integration
4. Public API functions
5. Quality gates and e2e tests

## Archive Strategy

**Archive each change immediately after completion:**
- Run `openspec archive <change-id> --yes` after all tasks complete
- This moves the change to `openspec/changes/archive/YYYY-MM-DD-<change-id>/`
- Updates `openspec/specs/` with the new capability specs
- Keeps the active changes list clean

## Progress Tracking

After each phase:
1. Update `PROJECT.md` with completed tasks
2. Run `openspec archive <id> --yes`
3. Run full test suite: `pytest tests/ -v --cov`
4. Run full lint suite: `ruff check src/parallel_requests/ && black --check src/parallel_requests/ && mypy src/parallel_requests/ --strict`

## Key Decisions (Baked Into Specs)

| Decision | Value | Location |
|----------|-------|----------|
| Timeout | Per-attempt (each retry gets its own timeout) | `add-client-api/design.md` |
| Cookies | Shared session-wide, with reset method | `add-client-api/specs/client-api/spec.md` |
| Redirects | Follow by default, disableable | `add-client-api/specs/client-api/spec.md` |
| SSL Verify | Enabled by default, disableable | `add-client-api/specs/client-api/spec.md` |
| Free Proxies | Opt-in only (disabled by default) | `add-proxy-and-headers/specs/proxy-rotation/spec.md` |

## Total Effort

| Change | Tasks | Estimated Effort |
|--------|-------|------------------|
| `add-foundation-contracts` | 16 | Foundation |
| `add-core-utils` | 17 | Core utilities |
| `add-proxy-and-headers` | 16 | Proxy/header management |
| `add-backends` | 21 | Three backend implementations |
| `add-client-api` | 24 | Main client API |
| **Total** | **94** | **~7 weeks** |

## Next Steps

1. Review this plan
2. Confirm execution strategy (sequential recommended)
3. Begin with `add-foundation-contracts`
4. Run `openspec show add-foundation-contracts` to see all tasks
