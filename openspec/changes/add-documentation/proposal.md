# Change: Add Comprehensive Documentation

## Why
The library lacks comprehensive user-facing documentation, which prevents users from discovering and effectively using its features. A well-structured documentation system following the Diátaxis framework will improve user onboarding, reduce support burden, and establish the library as a professional-grade project.

## What Changes
- **ADDED** MkDocs + Material theme documentation infrastructure
- **ADDED** Diátaxis-organized documentation (tutorials, how-to, reference, explanation)
- **ADDED** 3 tutorial documents (getting-started, parallel-fundamentals, handling-errors)
- **ADDED** 8 how-to guide documents (requests, rate-limiting, proxies, retries, streaming, POST, backends, debugging)
- **ADDED** 7 reference documents (API via mkdocstrings, return-types, configuration, exceptions)
- **ADDED** 5 explanation documents (architecture, backends, rate-limiting, retry-strategy, proxy-rotation)
- **ADDED** 14 executable examples in `examples/` folder with .env setup
- **ADDED** GitHub Pages deployment workflow
- **ENHANCED** All source code docstrings with examples for mkdocstrings

## Impact
- Affected specs: `documentation`
- Affected code:
  - `docs/mkdocs.yml` (new)
  - `docs/docs/**/*.md` (new)
  - `.github/workflows/docs.yml` (new)
  - `examples/**/*.py` (new)
  - `src/parallel_requests/*.py` (enhanced docstrings)
- Dependencies added: mkdocs, mkdocs-material, mkdocstrings (optional, docs extra)
- Hosting: GitHub Pages via GitHub Actions
