# paa-analyzer

Validated against eb5a7de on 2026-07-16 · Purpose: entry point for the agent-context docs — the system model and where each subsystem is documented.

> Full-stack diagnostic tool for Prisma Access Agent troubleshooting bundles:
> upload a `.zip` collected from a macOS or Windows endpoint, the backend parses
> it into state snapshots and log entries held entirely in memory, and a React
> UI explores them. This is the read-first map for coding agents working
> in-repo. Load only the deep-dive you need.

## System technical design

The whole system is one pipeline: **upload a zip → parse it → keep the result in
memory → serve it over an API → show it in a React UI**. Three layers, one repo:

- **Parser package** — `paa_analyzer/`. Dependency-free core: the taxonomy
  routing table (`taxonomy.py`), ~40 parser functions (`parsers.py`
  cross-platform + macOS, `parsers_win.py` Windows), and the standalone
  `paa-parse` CLI (`cli.py`). The backend imports it directly.
- **Backend** — `backend/`. FastAPI app (`main.py::create_app`): the upload
  endpoint runs `pipeline.py::parse_zip` (two passes over the archive —
  timezone/platform detection, then taxonomy-routed parsing), results land in
  `store.py::SessionStore` (session/state dicts plus one SQLite `:memory:`
  database per session for logs), and four routers under `/api/v1`
  (`sessions`, `logs`, `state`, `dashboard`) serve them back. The built
  frontend (`frontend/dist`) is mounted as static files from the same process.
- **Frontend** — `frontend/`. React 19 + TypeScript + Vite + Ant Design 6 SPA;
  TanStack Query hooks read the API, an SSE stream drives upload progress.

The human-facing narrative — request lifecycle, sequence/flow diagrams, stored
shapes — lives in [`../../docs/architecture.md`](../../docs/architecture.md);
these docs cross-link to it rather than duplicating it.

Repo map:

- `paa_analyzer/` — parsing library + `paa-parse` CLI.
- `backend/` — FastAPI app (`paa-server`): pipeline, store, `api/`, `models/`.
- `backend/tests/` — the pytest suite (unit/integration/api/e2e).
- `frontend/` — the React SPA; its own npm toolchain, outside the Python one.
- `tools/context_docs.py` — the generator that fills these docs' generated blocks.
- `tests/` — tooling tests (the generator's unit tests + the freshness gate).
- `docs/` — the mkdocs-material site (human docs; never reads `.agents/`).

Hard invariants:

- **Nothing is persisted.** Sessions, state, and logs live in one in-process
  `SessionStore` (per-session SQLite `:memory:` + dicts); a server restart
  loses everything. There is no database on disk.
- **Routing is taxonomy-driven.** Files map to parsers via the declarative
  dicts in `taxonomy.py`; dispatch resolves parser *names* with `getattr` and
  degrades to raw text on a miss.
- **Route order is load-bearing.** API routers are registered before the
  static catch-all; the `/state/{key:path}` catch-all is declared last.
- **The frontend has its own toolchain** (npm/Vite/Vitest); the Python gates
  (`nox`, pre-commit, codespell) deliberately exclude `frontend/`.

## Subsystem deep-dives

- [parsers](parsers.md): the `paa_analyzer/` parsing library — taxonomy routing table, parser functions, timestamp handling, the `paa-parse` CLI.
- [backend](backend.md): the FastAPI app — SSE upload/parse pipeline, the in-memory `SessionStore`, the `/api/v1` routers and response envelopes.
- [frontend](frontend.md): the React 19 + Ant Design SPA — API client and TanStack Query hooks, component layout, routing, the Vitest/MSW test stack.

## Cross-cutting

- [harness-and-testing](harness-and-testing.md): the quality harness — nox sessions, pytest markers, coverage/mypy/ruff config, the Stop-hook offline gate, and the freshness mechanism keeping these docs current.
- [decisions](decisions.md): the design-decision log — what was chosen, why, and what was rejected.

## Rules

The binding rules (commands, releasing, the decision-logging mandate) live in
`CLAUDE.md` at the repo root — this set explains mechanism and rationale, not
rules.
