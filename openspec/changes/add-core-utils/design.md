## Context
Core utilities are prerequisites for backend and client implementation. They provide reusable retry, rate limiting, and validation logic.

## Goals / Non-Goals
- Goals: Provide battle-tested retry, rate limiting, and validation primitives
- Non-Goals: No backend-specific logic, no proxy/header management (separate phases)

## Decisions
- **Decision**: Retry uses exponential backoff with random jitter
  - Formula: `delay = backoff * (2 ** attempt)` with `±jitter * delay`
- **Decision**: Rate limiting uses token bucket algorithm
  - Allows burst traffic up to capacity, then smooths to refill rate
- **Decision**: Validators return `ValidationError` with descriptive messages

## Risks / Trade-offs
- **Risk**: Retry delays may be too long for some use cases
  - Mitigation: Configurable backoff multiplier and jitter
- **Risk**: Rate limiting may cause requests to wait indefinitely
  - Mitigation: Timeout integration in client layer

## Open Questions
- None
