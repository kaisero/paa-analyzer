# backend

Validated against 0a0bba0 on 2026-07-26 · Purpose: the FastAPI app — ZIP upload → parse → in-memory store → REST/SSE API, plus static hosting of the built frontend.

## Purpose & responsibilities

`backend/` wraps the `paa_analyzer` parsing library in a web service: it
accepts a troubleshooting-bundle ZIP upload, runs the parse pipeline, holds the
results in an in-memory per-session store, and serves them to the React
frontend through a versioned REST API (`/api/v1`). It also serves the built
frontend (`frontend/dist`) as static files from the same process.

## How it works

### App assembly (`main.py`)

`create_app()` builds the `FastAPI` instance: permissive CORS middleware, then
the five routers from `backend/api/` (`sessions`, `logs`, `state`,
`dashboard`, `hip`) each mounted under `prefix="/api/v1"`, then — only if
`frontend/dist` exists — a `SpaStaticFiles(html=True)` mount at `/`. Router
registration order is what keeps `/api/*` ahead of the static catch-all.
Module-level `app = create_app()` is the uvicorn target; `run()` (the
`paa-server` script) starts uvicorn on `0.0.0.0:8000` with reload.

**`SpaStaticFiles`** (subclasses Starlette's `StaticFiles`, defined in
`main.py`) adds a single-page-app fallback. Plain `StaticFiles(html=True)`
maps only a *directory* to its `index.html`, so a client-side route the
frontend's router owns — `/s/<session>/hip`, `/logs`, `/dashboard`,
`/agent-status` — has no matching file on disk and 404s; the visible
symptom is a hard refresh or a shared session link failing while `/` works.
`SpaStaticFiles.get_response` catches a 404 from the base implementation and
retries against `index.html`, but only when the path looks like a client
route — two kinds of 404 must survive the fallback rather than becoming a
misleading 200:

- A request whose path has a file extension (`Path(path).suffix`) is asking
  for a real asset. Falling back to `index.html` for a missing
  `/assets/app.js` would make a broken build look like a working one — the
  browser would report a baffling JS syntax error instead of an honest 404.
- A request under `api/` is an API call. A typo'd endpoint must still return
  the API's own 404, not a page, or a client sees HTML where it expects
  JSON.

Covered by `backend/tests/test_spa_routing.py`, which mounts `SpaStaticFiles`
directly over a throwaway temp directory (not through `create_app()`, since
that only mounts anything when `frontend/dist` happens to exist).

### Settings (`config.py`)

`Settings(BaseSettings)` with `env_prefix="PAA_"`: `upload_dir`
(default `uploads`), `max_upload_bytes` (500 MB), `default_page_size` (100),
`max_page_size` (500). A module-level `settings` singleton is imported
everywhere; env vars like `PAA_MAX_UPLOAD_BYTES` override at process start.

### Parse pipeline (`pipeline.py`)

`parse_zip(data, on_progress=None)` takes the raw ZIP bytes and returns
`{"state": …, "logs": …, "manifest": …, "hip": …}`. Two passes over the
archive: pass 1 finds the timezone offset (`parsers.extract_tz_offset` on
`pacli_status.log`) and detects the platform (`Machine Info/` → windows;
`sw_vers.txt`/`launchctl_list.txt` → macos); pass 2 routes every entry through
`_parse_file`, which encodes the full routing-precedence chain over the
taxonomy dicts (see `parsers.md`). State entries key as
`{module}.{component}.{name}` with a `_meta` envelope; log entries accumulate
per source key and are sorted by timestamp at the end. `_run_parser` resolves
`FileMeta.parser` names via `getattr` on `parsers` then `parsers_win`.
`ProgressCallback = Callable[[str, int, str], None]` — `(stage, pct, detail)`
— drives the SSE upload progress stream.

Immediately after the sort — and before anything downstream can free the
parsed entries — `parse_zip` calls `paa_analyzer.hip.build_hip_data(all_logs,
all_state, platform, tz_offset)` and threads the result through as the `hip`
key; the manifest also gains `total_hip_cycles`. This is the only point in
the request lifecycle where the compliance log entries are guaranteed intact
(see the Gotchas below and `parsers.md`'s HIP section for what the model
contains).

### Store (`store.py`)

`SessionStore` (module-level singleton `store`) keeps everything in memory:
session dicts, per-session **SQLite `:memory:` connections** for logs (one
`logs` table per session; standard columns `timestamp/level/message/host/pid`
plus an `extra` JSON column for the rest), and plain dicts for state.
`get_logs` builds a WHERE clause from source/level/search/date filters —
f-string SQL fragments are fixed code, every user value is a bound `?`
parameter (the documented S608 exemption) — and paginates with
LIMIT/OFFSET (`page_size=0` = all). Beautification is lazy: `beautify_message`
runs only on the returned page. `get_log_sources` aggregates counts/levels/
time-ranges in SQL; `get_state_keys` decorates each key with
`PACLI_COMMAND_MAP`. `delete_session` closes the session's SQLite connection
and pops the session's `_hip` entry.

A third store, `_hip: dict[sid, dict]`, mirrors `_state` (small, fetched
whole) rather than SQL: it holds one already-built `HipData` dict per session
(`paa_analyzer.hip.build_hip_data()`'s output), passed in by
`add_session(session, logs, state, hip)` — `hip` must arrive pre-built,
because `add_session` is also what frees `log_data["entries"]` to cut peak
memory. `get_hip(sid)` returns the model with its `_raw` key stripped (raw
XML is ~⅔ of the payload and only needed on toggle, see Decision 14 in
`decisions.md`); `get_hip_raw(sid, index)` returns one cycle's `{raw_xml,
raw_patches_xml}` by its `str`-keyed index into `_raw`.

### API routers (`backend/api/`)

All routes below are additionally prefixed with `/api/v1` by `create_app()`
(the generated route table shows only the router-level prefix):

- `sessions.py` — `POST /sessions/upload` is the SSE path: it validates the
  `.zip` upload and size cap, runs `parse_zip` in a thread
  (`loop.run_in_executor`), marshals progress callbacks onto an
  `asyncio.Queue` via `call_soon_threadsafe`, and streams
  `data: {stage, progress, detail}` events, ending with a `complete` event
  carrying the session (or an `error` event — parse failures still store an
  error session). `POST /sessions` is the synchronous variant; plus
  list/get/delete. Both the SSE and synchronous paths call
  `store.add_session(session, logs, state, hip)` with `parse_zip`'s `hip` key
  passed straight through.
- `logs.py` — `GET /logs/sources` (per-source aggregates as `LogSource`) and
  `GET /logs` (filterable, paginated; returns `PaginatedResponse`).
- `state.py` — `GET /state` (key listing), `GET /state/batch` (comma-separated
  keys), `GET /state/forwarding-profile` (rules from
  `Agent.Networking.traffic_show` enriched with hit counts regex-extracted
  from `Agent.Core.traffic_log_json` entries), and the catch-all
  `GET /state/{key:path}` — declared LAST so the specific routes win.
- `dashboard.py` — `GET /dashboard` summary stub (counts from the session).
- `hip.py` — `GET /hip` returns the session's `HipData` (structured model,
  `_raw` stripped by the store); `GET /hip/cycles/{index}/raw` returns that
  one cycle's verbatim `{raw_xml, raw_patches_xml}`. Both 404 on an unknown
  session; the raw route also 404s on an out-of-range cycle index. Splitting
  raw XML into its own endpoint keeps `GET /hip` cheap for a session with
  several cycles — the frontend only fetches raw XML when its XML toggle is
  selected (`frontend.md`).

### Models (`backend/models/`)

`session.py`: `Session` (id, filename, parse status/error/duration, platform,
totals) and `LogSource`. `responses.py`: the response envelopes — every
endpoint returns `DataResponse` (`{"data": …}`) or `PaginatedResponse`
(`{"data": [...], "meta": PaginationMeta}`).

## Build / run pointers

- Run the server: `uv run paa-server` (uvicorn, reload, port 8000).
- API tests: `uv run pytest -m api`; store/pipeline:
  `backend/tests/test_store.py`, `test_pipeline.py`; end-to-end: `-m e2e`.
- Full offline gate: `uv run nox -s gate`.
- Regenerate the blocks below after changing this package: `uv run nox -s context`.

## Module map

<!-- GENERATED:module-map -->
- `config.py` — Application settings.
- `main.py` — FastAPI application factory.
- `pipeline.py` — ZIP upload → parse → store pipeline. Reuses paa_analyzer parsers directly.
- `store.py` — In-memory session store — logs in SQLite :memory:, state in Python dicts.
<!-- /GENERATED:module-map -->

## Public API (`store.py`, `pipeline.py`, `config.py`)

<!-- GENERATED:api -->
- `config.py`
  - class `Settings`
- `pipeline.py`
  - `parse_zip(data, on_progress)` — Parse a troubleshooting ZIP from raw bytes. Returns {state: {}, logs: {}, manifest: {}}.
- `store.py`
  - class `SessionStore`
<!-- /GENERATED:api -->

## Route table (`backend/api/*.py`)

Router-level paths; prepend `/api/v1` for the real URL.

<!-- GENERATED:route-table -->
| Method | Path | Handler | Summary |
| --- | --- | --- | --- |
| GET | `/sessions` | `list_sessions` |  |
| POST | `/sessions` | `create_session` |  |
| POST | `/sessions/upload` | `create_session_stream` |  |
| DELETE | `/sessions/{session_id}` | `delete_session` |  |
| GET | `/sessions/{session_id}` | `get_session` |  |
| GET | `/sessions/{session_id}/dashboard` | `get_dashboard` |  |
| GET | `/sessions/{session_id}/hip` | `get_hip` |  |
| GET | `/sessions/{session_id}/hip/cycles/{index}/raw` | `get_hip_raw` |  |
| GET | `/sessions/{session_id}/logs` | `get_logs` |  |
| GET | `/sessions/{session_id}/logs/sources` | `get_log_sources` |  |
| GET | `/sessions/{session_id}/state` | `list_state` |  |
| GET | `/sessions/{session_id}/state/batch` | `get_state_batch` | Return multiple state entries in a single response. |
| GET | `/sessions/{session_id}/state/forwarding-profile` | `get_forwarding_profile` | Return forwarding rules enriched with hitcounts computed from traffic_log. |
| GET | `/sessions/{session_id}/state/{key:path}` | `get_state` |  |
<!-- /GENERATED:route-table -->

## Gotchas / invariants

- **Everything is in-memory.** Sessions, logs (SQLite `:memory:`), and state
  vanish on restart; there is no persistence layer. `store` is a module-level
  singleton shared by all routers.
- **Route order in `state.py` is load-bearing** — `/state/batch` and
  `/state/forwarding-profile` must stay declared before the catch-all
  `/state/{key:path}` or they become unreachable state-key lookups.
- **The SSE upload parses in a worker thread** — progress callbacks hop to the
  event loop via `call_soon_threadsafe`; don't touch the store from the
  callback. The sync `POST /sessions` blocks the event loop for the whole
  parse and stays only as the non-streaming fallback.
- **Failed parses still create a session** (`parse_status="error"` with
  `parse_error` set) so the UI can show the failure; don't assume a stored
  session parsed successfully.
- **`page_size=0` means "all"** in `store.get_logs`, and the API allows it
  (`ge=0`); the upper bound is `settings.max_page_size`.
- **S608 in `store.py` is a reviewed exemption** — SQL fragments are fixed
  code (whitelisted ASC/DESC, fixed columns); user values always bind via `?`.
  Keep it that way.
- **Static mount depends on a frontend build** — no `frontend/dist`, no UI;
  the API works regardless. API routers must be included before the mount.
- **The SPA fallback is deliberately narrow.** `SpaStaticFiles` only retries
  as `index.html` for a 404 on an extensionless, non-`api/` path. A missing
  asset (has a file extension) and an unknown `api/` route both keep their
  real 404 — don't widen the fallback's condition to "any 404" or a broken
  build and a typo'd endpoint both start returning HTML.
- **App-level `/api/v1` prefix lives in `create_app()`**, not in the routers —
  the generated route table above is router-relative by design.
- **`build_hip_data()` runs in `pipeline.py`, not lazily in the store.**
  `SessionStore.add_session()` frees `log_data["entries"]` for every log
  source to cut peak memory, so by the time a request reaches `store.py` the
  compliance log entries the HIP model needs no longer exist. `hip` must
  always arrive pre-built.
- **`get_hip` never leaks `_raw`.** The whole point of the raw/structured
  split is a small `GET /hip` payload; `_raw` only ever leaves the store via
  `get_hip_raw`. Don't add a code path that returns the store's `_hip[sid]`
  dict unfiltered.

## See also

- `parsers.md` — the parsing library this app drives; taxonomy + parser
  contracts live there.
- `frontend.md` — the React client consuming this API (added in a later task).
- `index.md` — entry point for all agent-context docs (added in a later task).
- `../../docs/architecture.md` — human-facing architecture narrative with the
  request-lifecycle walkthrough; cross-link only, content not duplicated here.
- `../../CLAUDE.md` — working agreement, including the read-before /
  regenerate-after contract for these docs.
