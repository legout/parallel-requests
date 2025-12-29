## Context
This change establishes the foundational contracts for error handling, backend abstraction, and configuration. All other capabilities depend on these.

## Goals / Non-Goals
- Goals: Define clear error taxonomy, backend interface, and configuration system
- Non-Goals: Implement actual backend code, retry logic, or proxy management (future phases)

## Decisions
- **Decision**: Exception hierarchy with `return_none_on_failure` opt-in for backward compatibility
  - Rationale: Pythonic "raise by default" aligns with modern library expectations
- **Decision**: Backend interface uses dataclasses for request/response normalization
  - Rationale: Type safety, serialization support, and clear contract
- **Decision**: Configuration uses environment variables as primary config source
  - Rationale: 12-factor app compliance, container-friendly

## Risks / Trade-offs
- **Risk**: Backward incompatibility with v0.2.x silent failure behavior
  - Mitigation: `return_none_on_failure=True` opt-in for migration path

## Open Questions
- None (resolved in planning phase)
