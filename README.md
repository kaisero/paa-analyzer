# PAA Analyzer

A full-stack diagnostic tool for analyzing **Prisma Access Agent** troubleshooting bundles. Upload a ZIP collected from a macOS or Windows endpoint, and instantly explore parsed logs, agent state, and system details through an interactive web UI.

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Backend** | Python 3.14, FastAPI, uvicorn, Pydantic |
| **Parser Engine** | `paa_analyzer/` package with 46 parsers (27 cross-platform + 19 Windows) |
| **Data Store** | SQLite in-memory (per session, no persistence) |
| **Frontend** | React 19, TypeScript, Vite, Ant Design, TanStack Query |
| **Testing** | pytest (403 tests, 92% coverage), Vitest + React Testing Library + MSW (65 tests) |

## Features

- **Multi-OS support** -- macOS and Windows troubleshooting bundles auto-detected
- **Log Viewer** -- filterable by source, level, date range, and search; resizable columns; expandable rows with raw/beautified JSON
- **Agent Status** -- overview cards, module status badges, forwarding profile with hitcount links
- **System Details** -- OS-adaptive tabs (macOS: System Extensions, Launchctl; Windows: Firewall Rules, Installed Drivers, Network Config, Netstat)
- **PaCli Terminal** -- interactive command replay with autocomplete
- **Upload with progress** -- SSE streaming of parse progress to the browser
- **CLI tool** -- `paa-parse` for offline parsing to JSON files

## Architecture

```
troubleshooting.zip
        |
        v
  +------------------+     +------------------+
  |  paa_analyzer/    |     |   backend/       |
  |  parsers.py       |---->|   pipeline.py    |
  |  parsers_win.py   |     |   store.py       |
  |  taxonomy.py      |     |   api/           |
  +------------------+     +------------------+
                                    |
                              REST API
                             /api/v1/*
                                    |
                                    v
                           +------------------+
                           |   frontend/      |
                           |   React + Antd   |
                           |   TanStack Query |
                           +------------------+
```

**Data flow:** ZIP bytes are parsed by `paa_analyzer` into state (key-value snapshots) and log (time-series entries) categories. The backend stores state in Python dicts and logs in per-session SQLite `:memory:` databases with indexes for fast filtering. The frontend queries via TanStack Query hooks.

**Parser architecture:** Files are routed by `taxonomy.py` which maps filenames to `(data_type, module, component, parser)` tuples. The pipeline dispatches to parser functions in `parsers.py` (cross-platform) or `parsers_win.py` (Windows-specific). New file types are added by extending the taxonomy and writing a parser function.

## Getting Started

### Run with Docker (recommended)

The quickest way to run PAA Analyzer — you only need Docker. This builds a single
image containing both the frontend and backend and serves the whole app on one port:

```bash
docker compose up --build   # build the image and start the container
```

Then open <http://localhost:8000> in your browser. Stop it with `docker compose down`.

The container builds the React UI and runs the FastAPI backend, which serves both the
API and the built UI on port 8000 — no separate frontend server or second container
needed. The sections below run the app from source, mainly for development.

### Prerequisites

- Python 3.11+ with [uv](https://docs.astral.sh/uv/)
- Node.js 18+

### Setup

```bash
# Clone and install backend
git clone <repo-url>
cd analyzer
uv sync --group dev

# Install frontend dependencies
cd frontend
npm install
cd ..

# Enable pre-commit hooks (lint + test gate)
git config core.hooksPath .githooks
```

### Development

```bash
# Start backend (port 8000, serves API + built frontend)
uv run paa-server

# In another terminal: start frontend dev server (hot reload, proxies /api to :8000)
cd frontend && npm run dev
```

Open http://localhost:5173 (dev server) or http://localhost:8000 (built frontend).

### CLI Usage

```bash
# Parse a troubleshooting ZIP to JSON files
uv run paa-parse examples/troubleshooting.zip output/

# Output structure:
# output/state/*.json   -- one file per state key
# output/logs/*.json    -- one file per log source
# output/manifest.json  -- parse summary
```

### Testing

```bash
# Backend tests (403 tests)
uv run pytest
uv run pytest --cov --cov-report=term-missing  # with coverage
uv run pytest -m "not slow"                     # skip e2e tests

# Frontend tests (65 tests)
cd frontend
npm test         # watch mode
npm run test:run # single run
```

### Building

```bash
cd frontend
npm run build  # runs tests, then tsc, then vite build -> dist/
```

The backend serves `frontend/dist/` as static files at `/`.

### Releasing

1. Bump version in `pyproject.toml` and `frontend/package.json`
2. Update `CHANGELOG.md`
3. Commit: `Release X.Y.Z`
4. Merge to main
5. Tag: `git tag -a vX.Y.Z -m "Release X.Y.Z"`

## Project Structure

```
analyzer/
  backend/
    api/             # FastAPI routers (sessions, logs, state, dashboard)
    models/          # Pydantic models
    pipeline.py      # ZIP -> parse -> store orchestration
    store.py         # In-memory session store with SQLite for logs
    tests/           # pytest test suite
  paa_analyzer/
    parsers.py       # Cross-platform parsers (27 functions)
    parsers_win.py   # Windows-specific parsers (19 functions)
    taxonomy.py      # File -> parser routing table
    cli.py           # paa-parse CLI tool
  frontend/
    src/
      api/           # Fetch client, TanStack Query hooks, TypeScript types
      components/    # React components (layout, log-viewer, agent-status, upload)
      hooks/         # useLogViewer, useUploadWithProgress
      pages/         # AgentStatusPage, DashboardPage
      test/          # Vitest setup, MSW handlers, test wrapper
  docs/
    design-decisions.md  # Architectural decisions log
    REVISIT.md           # Deferred features
  CHANGELOG.md
  CLAUDE.md              # Claude Code instructions
```

## License

[MIT](LICENSE)
