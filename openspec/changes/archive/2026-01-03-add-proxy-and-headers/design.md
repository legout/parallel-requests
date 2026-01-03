## Context
Proxy and header management are orthogonal features used during HTTP requests. They don't depend on specific backends.

## Goals / Non-Goals
- Goals: Provide reliable proxy rotation and user agent rotation
- Non-Goals: No backend-specific proxy/header handling (backends receive normalized config)

## Decisions
- **Decision**: Free proxies are opt-in and disabled by default
  - Rationale: Avoid unreliability, explicit user control (PRD requirement)
- **Decision**: Proxy validation errors don't crash - invalid proxies are filtered
  - Rationale: Graceful degradation with logging (via loguru)
- **Decision**: User agent rotation enabled by default
  - Rationale: Anti-detection is standard practice

## Risks / Trade-offs
- **Risk**: Webshare.io may rate limit or change API
  - Mitigation: Use documented API format, catch exceptions gracefully
- **Risk**: User agent list becomes outdated
  - Mitigation: Support remote URL for user agent updates

## Open Questions
- None
