## Context
Backend implementations depend on optional third-party libraries (`aiohttp`, `requests`, `niquests`, etc.). Importing `parallel_requests.backends` currently imports all backend modules unconditionally, which defeats the purpose of optional dependencies.

## Goals / Non-Goals
- Goals:
  - Importing `parallel_requests` MUST NOT require optional backend dependencies.
  - Importing `parallel_requests.backends` MUST NOT import optional backend dependencies unless the corresponding backend symbol is actually accessed.
  - Backend auto-selection MUST NOT import backend modules that are not selected.
- Non-Goals:
  - Changing request semantics, retry/rate-limit behavior, or backend priority.
  - Adding new backends.

## Decisions
- **Decision**: Implement PEP 562-style lazy imports in `src/parallel_requests/backends/__init__.py` using module-level `__getattr__`.
- **Decision**: Keep type-checker support via `typing.TYPE_CHECKING` guarded imports.

## Risks / Trade-offs
- Risk: Some tooling that introspects `parallel_requests.backends` may expect eager imports.
  - Mitigation: Preserve `__all__` and provide explicit error messages when a backend dependency is missing.

## Migration Plan
1. Update `parallel_requests/backends/__init__.py` to remove eager imports and add lazy attribute resolution.
2. Add tests ensuring `import parallel_requests` and `import parallel_requests.backends` succeed without optional deps.
3. Validate with OpenSpec and run test suite in a minimal install environment.

## Open Questions
- Should `parallel_requests.backends` export only `Backend`, `RequestConfig`, `NormalizedResponse` by default, and expose backend implementations only via lazy attributes? (proposed: yes)
