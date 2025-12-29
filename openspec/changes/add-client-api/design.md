## Context
The client API is the main user-facing layer. It orchestrates all previous phases into a cohesive, easy-to-use interface.

## Goals / Non-Goals
- Goals: Simple API, powerful features, excellent defaults
- Non-Goals: No backend-specific code (delegated to backends), no utility logic (delegated to utils)

## Decisions (From Planning Phase)
- **Timeout**: Per-attempt (each retry gets its own timeout)
- **Cookies**: Shared session-wide, with reset method
- **Redirects**: Follow by default, with disable option
- **SSL**: Verify enabled by default, with disable option
- **Logging**: Loguru for all logging, tqdm for progress bars
  - `debug`: Controls loguru log level (DEBUG vs INFO)
  - `verbose`: Controls tqdm progress bar visibility

## Backend Auto-Selection Priority
1. niquests (if available) - HTTP/2, best async
2. aiohttp (if available) - mature async
3. requests + asyncio.to_thread() (fallback) - sync users
4. ImportError if none available

## Return Type Behavior
- JSON: Parse response as JSON, return dict/list
- TEXT: Return response.text
- CONTENT: Return response.content (bytes)
- RESPONSE: Return NormalizedResponse object
- STREAM: Call stream_callback with chunks

## Error Handling
- Default: Raise exceptions (RetryExhaustedError, PartialFailureError, etc.)
- Opt-in: `return_none_on_failure=True` returns None on failure

## Risks / Trade-offs
- **Risk**: Complex initialization with many options
  - Mitigation: Sensible defaults, progressive disclosure
- **Risk**: Partial failures in parallel requests
  - Mitigation: `PartialFailureError` with failed URLs list

## Open Questions
- None (resolved in planning phase)
