# PAA Analyzer

PAA Analyzer is a full-stack diagnostic tool for analyzing **Prisma Access
Agent** troubleshooting bundles. Upload a ZIP collected from a macOS or Windows
endpoint and explore parsed logs, agent state, and system details through an
interactive web UI. A FastAPI backend drives the `paa_analyzer` parser engine,
which routes each file in the bundle to a dedicated parser, and a React frontend
renders the results.

## Features

- **Multi-OS support** — macOS and Windows troubleshooting bundles are
  auto-detected from directory structure.
- **Log Viewer** — filterable by source, level, and date range, with search,
  resizable columns, and expandable rows showing raw or beautified JSON.
- **Agent Status** — overview cards, module status badges, and a forwarding
  profile with hitcount links.
- **System Details** — OS-adaptive tabs for macOS (System Extensions, autostart
  programs, routing table) and Windows (network config, firewall rules,
  installed drivers, netstat, and more).
- **PaCli terminal** — interactive command replay with autocomplete.
- **Upload with progress** — parse progress is streamed to the browser over SSE.
- **CLI tool** — `paa-parse` parses a bundle to JSON files with no server needed.

## Requirements

**Backend**

- **Python 3.14+**
- **[uv](https://docs.astral.sh/uv/)** — manages the virtual environment and dependencies
- Python packages (installed automatically by `uv sync`): FastAPI, uvicorn,
  Pydantic, pydantic-settings, python-multipart

**Frontend**

- **Node.js 20+** (a recent LTS) and **npm**
- JavaScript packages (installed by `npm install`): React 19, Vite, TypeScript,
  Tailwind CSS, TanStack Query

## Usage

The fastest way to run PAA Analyzer is with **Docker** — the from-source steps
below are mainly for development.

### Docker (recommended)

You only need Docker. This builds a single image containing both the frontend and
the backend and serves the whole app on one port:

```bash
docker compose up --build      # build the image and start the container
```

Then open **<http://localhost:8000>** in your browser. Stop it with
`docker compose down`.

The container builds the React UI and runs the FastAPI backend, which serves both
the API and the built UI on port 8000 — no separate frontend server needed.

### Backend (API + parser)

```bash
uv sync                 # create the virtual environment and install dependencies
uv run paa-server       # start the API on http://localhost:8000
```

`paa-server` serves the REST API and — when the frontend has been built into
`frontend/dist` — the web UI at the same address.

Parse a bundle from the command line without starting a server:

```bash
uv run paa-parse <bundle.zip> [output/]   # writes state/, logs/, manifest.json
```

### Frontend (dev server)

```bash
cd frontend
npm install             # install frontend dependencies
npm run dev             # Vite dev server (proxies /api to http://localhost:8000)
```

Run the backend (`uv run paa-server`) alongside it so the proxied `/api` requests
resolve. Vite prints the local URL to open (default http://localhost:5173).

### Production build

```bash
cd frontend && npm run build   # runs the frontend tests, type-checks, and builds to frontend/dist/
uv run paa-server              # now serves the API and the built UI on http://localhost:8000
```

## Architecture

ZIP bytes are parsed by the `paa_analyzer` package into **state** (key-value
snapshots) and **log** (time-series entries) categories. `taxonomy.py` maps each
filename to a `(data_type, module, component, parser)` tuple, and the backend
pipeline dispatches to parser functions in `parsers.py` (cross-platform) or
`parsers_win.py` (Windows-specific). State is held in Python dicts and logs in a
per-session in-memory SQLite database; the React frontend queries the REST API
via TanStack Query.

See the [Architecture](architecture.md) page for a full walkthrough of how a
bundle is processed, stored, and served to the browser.
