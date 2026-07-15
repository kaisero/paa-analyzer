# PAA Analyzer — Claude Code Instructions

## Project
PAA Analyzer: full-stack diagnostic tool for Prisma Access Agent troubleshooting bundles.
Upload a .zip → backend parses it → React frontend displays logs, state, and dashboard.

## Stack
- **Backend**: Python 3.14, FastAPI, uvicorn, pydantic — in `backend/`
- **Parsers**: Standalone package in `paa_analyzer/` — imported by backend
- **Frontend**: React 19 + TypeScript + Vite + Tailwind + TanStack React Query — in `frontend/`

## Commands
- `uv run paa-server` — start backend (port 8000, serves API + built frontend)
- `uv run paa-parse <zip> [output/]` — CLI parser (standalone, no server needed)
- `cd frontend && npm run dev` — frontend dev server (proxies /api to :8000)
- `cd frontend && npm run build` — build frontend to frontend/dist/
- `uv run ruff check backend/ paa_analyzer/` — lint
- `uv run pytest` — run tests
- `uv run pytest --cov --cov-report=term-missing` — run tests with coverage
- `uv run pytest -m "not slow"` — skip slow/e2e tests
- `uv run pytest -m e2e` — run end-to-end tests only
- `cd frontend && npm test` — frontend tests (watch mode)
- `cd frontend && npm run test:run` — frontend tests (single run)
- `cd frontend && npm run test:coverage` — frontend tests with coverage

## Architecture
- Backend imports `paa_analyzer.parsers` and `paa_analyzer.taxonomy` directly
- All data in-memory (SessionStore) — no persistence
- API: `/api/v1/sessions` (upload), `/api/v1/sessions/{id}/logs` (query), `/api/v1/sessions/{id}/state`
- Frontend routes: `/` (upload), `/s/{id}` (log viewer), `/s/{id}/dashboard`, `/s/{id}/agent-status`

## Releasing
1. Bump version in `pyproject.toml` and `frontend/package.json`
2. Update `CHANGELOG.md` with new section
3. Commit: `"Release X.Y.Z"`
4. Merge to main: `git checkout main && git merge --no-ff <branch>`
5. Tag: `git tag -a vX.Y.Z -m "Release X.Y.Z"`

## Design Decisions Documentation
**Every dev or design decision must be documented in `docs/design-decisions.md`.**
When making changes to the viewer, parser, or architecture:
1. Add a dated section to `docs/design-decisions.md` with the decision, rationale, and alternatives considered
2. Keep entries concise but complete enough that a new developer can understand *why* a choice was made
3. Group related decisions under a shared date/heading
