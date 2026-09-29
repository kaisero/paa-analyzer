# harness-and-testing

Validated against eb5a7de on 2026-07-16 · Purpose: mechanism and rationale of the quality harness — nox sessions, pytest/coverage/mypy/ruff config, pre-commit, the Stop-hook offline gate, and the freshness mechanism for these docs.

## Purpose & responsibilities

One source of truth for the checks: `noxfile.py`. The same sessions run
locally, in pre-commit, in CI (`.github/workflows/ci.yml`), and on every agent
Stop via the hook — so "green" means the same thing everywhere. This doc
explains how the pieces fit; the commands themselves are in `CLAUDE.md`.

## How it works

### nox sessions (`noxfile.py`)

Default run (`uv run nox`) executes `lint`, `type_check`, `tests`, `docs`.
Each venv-backed session installs the project plus its dependency group via
`_sync` (`uv sync --no-default-groups --group <g>`; `--frozen` when `CI` is
set), so session deps always match `pyproject.toml` `[dependency-groups]`.

- `lint` — `ruff check .` + `ruff format --check .`.
- `type_check` — `mypy` (strict; see below).
- `tests` — `pytest --cov --cov-report=term-missing` on Python 3.14. The only
  session that enforces coverage (`fail_under = 85`).
- `audit` — `pip-audit` (also scheduled in CI, `audit.yml`).
- `docs` / `docs-serve` — `mkdocs build --strict` / live-reload serve. mkdocs
  reads only `docs/`, so `.agents/` never leaks into the published site.
- `context` — `venv_backend="none"`; runs `python tools/context_docs.py`
  (pass `-- --check` to verify instead of write). No venv because the
  generator is pure stdlib and never imports repo code.
- `gate` — `venv_backend="none"`; the fast offline gate: `ruff check`,
  `ruff format --check`, `mypy`, `pytest -q -m "not slow"`. Runs in the
  invoking environment (expects `uv run` with the dev group installed); no
  coverage, no venv creation — it must stay fast, it runs on every agent stop.

CI (`ci.yml`) runs `lint`, `type_check`, `tests-3.14`, and `docs` as separate
jobs, each preceded by `uv lock --check` so a stale `uv.lock` fails before any
`uv run` can silently refresh it. There is **no frontend job** — see
`frontend.md`.

### pytest layout and markers (`pyproject.toml`)

`testpaths = ["backend/tests", "tests"]` — the app suite plus the tooling
tests (`tests/` holds the context-docs generator tests; `pythonpath = ["."]`
exists so they can `from tools import context_docs`). Markers are strict:
`unit` (pure functions), `integration` (ZIP/SQLite), `api` (FastAPI
TestClient), `e2e` (real example bundles), `slow` (>1 s — what `gate`
deselects). Coverage measures `paa_analyzer` + `backend`, omits
`backend/tests/*` and `backend/main.py`, and fails under 85%.

### mypy and ruff

mypy is `strict = true` with the pydantic plugin over `files = ["paa_analyzer",
"backend"]`; `backend.tests.*` relaxes only the untyped-def/call rules (test
bodies are still checked for real type errors). ruff runs a broad ruleset
(`E,W,F,I,N,UP,B,C4,SIM,S,ASYNC,PTH,RUF`, line length 120) with documented
per-file ignores — notably `S608` in `backend/store.py` (f-string SQL with only
code-defined fragments; user values bind via `?`) and `S314` in
`paa_analyzer/parsers_win.py` (bundle XML is trusted operator input). Each
exemption carries its rationale as a comment in `pyproject.toml`; keep that
pattern when adding one. codespell checks the Python side only — its `skip`
excludes `frontend/`, lockfiles, build dirs, and `docs/plans`.

### pre-commit (`.pre-commit-config.yaml`)

gitleaks (repo-wide secrets scan), the generic hygiene hooks (excluding
`frontend/`, which has its own toolchain), `uv-lock` (keeps `uv.lock` in sync),
and the project tools — ruff, ruff-format, mypy, codespell — as **local hooks
shelling out to `uv run`**, so hook versions match nox/CI exactly and mypy
sees the real project environment (strict mode + the pydantic plugin need the
project deps, which an isolated pre-commit env cannot provide reliably).

### The Stop-hook offline gate (`.claude/`)

`.claude/settings.json` registers `.claude/hooks/fast_gate.py` on every
main-loop `Stop`. Its config is `.claude/harness.toml`:
`fast_gate_command = ["uv", "run", "nox", "-s", "gate"]`, `fast_gate_enabled`,
and `max_consecutive_blocks = 3`. The hook runs the gate and, on failure,
blocks the stop with the last 50 lines of output as the reason. Two deliberate
safety properties:

- **Fail-open.** Any internal error allows the stop (CI re-runs the same
  checks); a buggy hook must never wedge an unattended session.
- **Loop guard.** After 3 consecutive blocked stops it allows the stop with a
  loud stderr warning instead of blocking forever.

The hook defaults `UV_PROJECT_ENVIRONMENT` to a stable per-checkout path under
the temp dir so the gate reuses one venv across stops. `PAA_HARNESS_CONFIG`
overrides the config path (used by tests). That is the whole harness — there
is no write-blocking/protected-path hook in this repo.

### Context-docs freshness (the mechanism keeping THESE docs current)

`tools/context_docs.py` renders the `<!-- GENERATED:kind -->` blocks in
`parsers.md` and `backend.md` from the live code via `ast` (module maps,
public APIs, the taxonomy table, the route table) — pure stdlib, no imports of
repo code. Enforcement is two-layered:

- `tests/test_context_docs_current.py` asserts `context_docs.main(["--check"])
  == 0`. It rides the normal suite, so a code change that stales a generated
  block fails `pytest` → fails `nox -s gate` → **blocks the agent's stop** and
  fails CI. Fix with `uv run nox -s context`, which rewrites the blocks
  in place; `--check` names the stale `doc:kind` pairs.
- Narrative freshness is procedural: the `CLAUDE.md` "Agent context docs"
  contract (read the deep-dive before working in a subsystem; update its
  narrative and regenerate after changing one) plus each doc's line-3
  provenance stamp.

`tests/test_context_docs.py` unit-tests the generator itself (renderers,
marker injection, `--check` semantics). The hand-written docs (`index.md`,
`frontend.md`, this file, `decisions.md`) have no generated blocks and are
untouched by the generator.

### Frontend test toolchain

Vitest 4 (jsdom) + MSW 2 + Testing Library, colocated `*.test.{ts,tsx}` files;
`npm run build` runs `vitest run` before `tsc -b`/`vite build`, so a red suite
blocks the build. None of it is wired into nox or CI — details and gotchas in
`frontend.md`.

## Build / run pointers

- Everything: `uv run nox` (lint + type_check + tests + docs).
- Fast offline gate (what the Stop hook runs): `uv run nox -s gate`.
- Tests with coverage: `uv run nox -s tests` (or `uv run pytest --cov`).
- One marker: `uv run pytest -m api` / `-m "not slow"` / `-m e2e`.
- Regenerate these docs' blocks: `uv run nox -s context`; verify:
  `uv run nox -s context -- --check`.
- Pre-commit over everything: `uv run pre-commit run --all-files`.

## Gotchas / invariants

- **`gate` runs in the invoking environment** (`venv_backend="none"`) — it
  needs the dev group present, i.e. run it through `uv run`. It deliberately
  skips coverage and `slow`-marked tests; full enforcement is the `tests`
  session/CI.
- **Coverage `fail_under = 85` is enforced only where `--cov` runs** (`tests`
  session, CI) — a green `gate` says nothing about coverage.
- **The Stop hook fails open by design.** Don't "harden" it to fail-closed;
  a hook crash blocking every stop wedges unattended sessions. CI is the
  backstop.
- **`fast_gate_enabled = false` in `harness.toml`** turns the Stop gate off
  for interactive debugging without unwiring it.
- **A stale generated block is a test failure, not a warning** — if `gate`
  goes red right after a `paa_analyzer/` or `backend/` change, run
  `uv run nox -s context` before debugging anything else.
- **Ruff security exemptions are per-file and documented** — never widen one
  globally; add a new per-file ignore with a rationale comment instead.

## See also

- `index.md` — entry point for all agent-context docs.
- `frontend.md` — the npm-side toolchain the Python harness excludes.
- `decisions.md` — why the harness is shaped this way.
- `../../CLAUDE.md` — the binding commands and the context-docs contract.
