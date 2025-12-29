## Context
Documentation follows the Diátaxis framework which organizes content into four types based on user need: tutorials (learning), how-to guides (problem-solving), reference (technical information), and explanation (conceptual understanding).

## Backend Selection
- **Niquests** (auto priority): Full HTTP/2 support, streaming, async native
- **Aiohttp**: No HTTP/2, streaming support, async native
- **Requests**: No HTTP/2, streaming via thread wrapper, sync-first

Auto-detection order: niquests → aiohttp → requests

## Goals / Non-Goals
- Goals: Complete, navigable documentation for all user skill levels
- Goals: Executable examples that work out of the box
- Goals: Auto-generated API reference from docstrings via mkdocstrings
- Goals: Document all utility classes (ProxyManager, HeaderManager, RetryStrategy, etc.)
- Non-Goals: No video tutorials or interactive tutorials (out of scope)
- Non-Goals: No translated documentation (English only for now)

## Decisions
- **Decision**: MkDocs + Material theme - Best balance of features, look-and-feel, and ease of maintenance for Python projects
- **Decision**: mkdocstrings for API reference - Auto-generates from docstrings, keeps docs in sync with code
- **Decision**: GitHub Pages via GitHub Actions - Free hosting, automatic deployment on push to main
- **Decision**: Diátaxis framework - Industry-standard documentation structure proven to work
- **Decision**: Real public APIs in examples (httpbin.org, jsonplaceholder.typicode.com) - Ensures examples work without setup

## Additional Features
- **Cookie Management**: Session cookies via `set_cookies()`/`reset_cookies()` methods on ParallelRequests
- **Custom Parsing**: `parse_func` parameter for response transformation
- **Keyed Responses**: `keys` parameter for named result mapping
- **Graceful Degradation**: `return_none_on_failure` option to return None instead of raising exceptions
- **Validation**: URL, proxy, and header validation utilities in utils/validators.py
- **Configuration Serialization**: `save_to_env()` and `to_env()` methods in GlobalConfig
- **Proxy Validation**: Format validation with regex patterns for IP:port and authenticated proxies

## Risks / Trade-offs
- **Risk**: Documentation becomes outdated as code evolves
  - Mitigation: mkdocstrings auto-generates API reference; cross-references in how-to guides link to source
- **Risk**: Examples fail if public APIs change
  - Mitigation: Use multiple backup APIs; examples include error handling for API failures
- **Risk**: Docstring enhancement is time-consuming (9 files need work)
  - Mitigation: Focus on high-impact docstrings first (ParallelRequests, utility classes)
- **Risk**: Backend HTTP/2 support differences confuse users
  - Mitigation: Clearly document which backends support HTTP/2; provide explicit backend selection examples

## Migration Plan
1. Create infrastructure (mkdocs.yml, workflow)
2. Enhance docstrings in source code (client.py, backends, utils)
3. Create documentation content (Diátaxis sections)
4. Create examples with .env setup
5. Add backend feature comparison to explanation
6. Document utility classes (ProxyManager, HeaderManager, etc.)
7. Test documentation build locally
8. Deploy to GitHub Pages

## Open Questions
- None
