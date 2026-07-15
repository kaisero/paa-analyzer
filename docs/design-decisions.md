# PAA Analyzer — Design Decisions Log

This document captures key development and design decisions made during the build of the PAA Analyzer, including rationale and alternatives considered.

---

## 2026-04-06: Log Viewer — Initial Implementation

### Search: Simple substring over structured query language

**Decision:** Use a single plain-text search input that does case-insensitive substring matching across all 13 entry fields (level, source, message, host, pid, event_type, source_file, timestamp, destination, protocol, verdict, source_app, reason).

**Rationale:** An earlier iteration had a structured query language (`field = "value"`, `field contains "text"`) with autocomplete. This was replaced because:
- T3 engineers need fast, frictionless filtering — typing a keyword and seeing results instantly is faster than composing structured queries
- Substring search across all fields catches more relevant results (e.g. searching "tunnel" matches message, verdict, and reason fields simultaneously)
- 150ms debounce gives a "live" feel without excessive re-filtering

**Alternative rejected:** Structured query language with autocomplete — too much cognitive overhead for the primary use case of quickly narrowing down logs.

---

### Date filtering: Flatpickr range picker

**Decision:** Use Flatpickr (CDN) in range mode with 24h time support, dark-themed to match the app.

**Rationale:** Native `<input type="datetime-local">` has inconsistent UX across browsers and looks out of place in a dark-themed app. A text input for typing dates was tried but was not user-friendly for date selection. Flatpickr provides a modern calendar picker that also allows range selection in a single field. Auto-populates min/max from loaded data.

**Trade-off:** External CDN dependency, but Flatpickr is lightweight (~15KB) and widely adopted.

---

### Toolbar layout: Single row

**Decision:** Search, level filter buttons, date picker, clear button, and result count all in one flex row.

**Rationale:** Two-row toolbars wasted vertical space that's better used for log entries. A single row keeps all filter controls visible and accessible without scrolling. Level buttons are abbreviated (Warn instead of Warning) to save space.

---

### Message display: 3-line clamp with click-to-expand

**Decision:** Log messages display up to 3 lines with CSS `-webkit-line-clamp: 3`. Messages exceeding 3 lines show a subtle `...` indicator. Clicking a row expands it to show the full message.

**Rationale:** PAA log messages can be very long (multiline stack traces, JSON payloads). Showing full text for every entry would make the log view unusable. 3 lines balances readability with density. The `...` indicator is deliberately subtle — experienced users learn to click rows, and it doesn't add visual noise for short messages.

**Implementation detail:** Expand/collapse toggles the CSS class directly on the DOM element instead of re-rendering the entire page, keeping it performant even with large page sizes.

---

### Pagination over virtual scroll

**Decision:** Replace virtual scroll (fixed 26px row height) with paginated rendering. Default page size: 100, options for 250, 500, and All.

**Rationale:** Virtual scroll required fixed row heights, which conflicts with the 3-line message wrap requirement. Variable-height virtual scroll is complex and fragile. Pagination with 100 entries renders fast and gives clear navigation. The "All" option is available for filtered result sets where users want to see everything.

---

### Timestamp format: YYYY-MM-DD HH:mm:ss.mmm

**Decision:** Format timestamps as `2026-04-02 00:37:28.033` using a custom `fmtTs()` function.

**Rationale:** `Date.toLocaleString()` varies by browser/locale and is not precise enough for log analysis (missing milliseconds). The ISO-like format is universally readable, sortable, and includes millisecond precision which is critical for correlating rapid event sequences.

---

### Default sort: Newest first

**Decision:** Entries sort newest-first (descending timestamp) by default. Clickable "Timestamp" header toggles sort direction with an arrow indicator.

**Rationale:** In troubleshooting scenarios, the most recent events are typically the most relevant. Engineers usually start from the latest error and work backwards.

---

### Empty entries filtered out

**Decision:** Entries missing all three of `timestamp`, `message`, and `level` are excluded from display.

**Rationale:** Some parser outputs (e.g. `connection_history.json`) use a different schema with nested data structures that don't map to the log viewer's column model. Rather than showing empty rows, these are silently filtered.

---

### Log entry backgrounds: Uniform

**Decision:** All log entries have the same background color regardless of level. Level identification relies on the colored level badge only.

**Rationale:** Per-level background tinting (red for error, yellow for warning) created visual noise when scanning large log files. The colored level badge provides sufficient visual differentiation without the distraction.

---

## 2026-04-06: Sidebar Design

### Resizable sidebar

**Decision:** Sidebar is resizable via drag handle on the right edge (180px–500px range).

**Rationale:** Module/component names vary in length. "SecurityExtension" needs more space than "PAS". Fixed width forces truncation; resizable lets users optimize for their current view.

---

### Dot indicators instead of entry counts

**Decision:** Replace per-file error counts and entry totals with small red (error) and yellow (warning) dots. Hovering dots shows the exact count as a tooltip.

**Rationale:** Numeric counts consumed significant sidebar width, forcing file names to truncate. Dots provide at-a-glance severity indication while giving the name column maximum space. Exact counts are available on hover for when precision matters.

---

### Alphabetical sidebar ordering

**Decision:** Files within each module/component group are sorted alphabetically by name.

**Rationale:** Previous sort (by error count then entry count) was unpredictable — the order changed as data was loaded. Alphabetical ordering is stable and makes specific files easy to find.

---

### Auto-sizing columns on source switch

**Decision:** When selecting a log source in the sidebar, columns auto-resize based on actual content widths measured via canvas text metrics.

**Rationale:** The Source column varies widely ("PAS" vs "SecurityExtension"). Auto-sizing maximizes message column space for sources with short names. Manual resize via drag still works and overrides auto-sizing until the next source switch. Samples up to 200 entries for measurement.

---

## 2026-04-06: Column Visibility

### Right-click context menu on column headers

**Decision:** Right-clicking any column header shows a custom dark-themed context menu with checkboxes to toggle column visibility. At least one column must remain visible.

**Rationale:** Different analysis tasks need different columns. Traffic log analysis benefits from hiding Source (all entries have the same source). A right-click context menu is discoverable for power users without adding UI clutter. Styled to match the app's dark theme rather than using the browser's native context menu.

---

### Debug level badge styling

**Decision:** Debug level gets a subtle grey background (`rgba(139,148,158,0.12)` with `--text2` color), distinct from error (red), warning (yellow), info (blue), and the absence of styling.

**Rationale:** Without a background, debug entries looked like broken/unstyled entries. The grey tint gives them visual identity while remaining the least prominent level, matching the semantic hierarchy.

---

## 2026-04-06: Custom View

### Three-state Custom View flow

**Decision:** "Custom View" button at sidebar bottom cycles through three states:
1. **Off** → button says "Custom View" (neutral border)
2. **Selecting** → checkboxes appear on all sources, "Select all / Deselect all" toggle at top, button becomes blue "Apply (N selected)"
3. **Applied** → custom merged view active, green "Custom View (N)" label in sidebar, button becomes orange "Reset"

**Rationale:** Multi-select with Ctrl+Click would be less discoverable. Persistent checkboxes would add noise. The mode-configure-commit pattern is well-established UX (e.g. edit mode in iOS, column choosers in data grids). The three visual states (neutral/blue/orange) clearly communicate what action the button will take. Clicking any individual source or "All Logs" while in applied mode automatically exits custom view.

---

## 2026-04-06: Date Range Filter — Empty by Default

### No pre-filled date range on source switch

**Decision:** The date range picker is cleared (empty) every time the user switches log sources. The calendar's min/max bounds are still set to the data's range, but no dates are selected. Empty picker = no time filtering = all entries shown.

**Rationale:** The previous behavior auto-filled the picker with the selected source's min/max timestamps. This caused a critical bug: switching from a source with a narrow time range (e.g. a file spanning 1 hour) to one with a wider range left the narrow filter active, hiding most entries. Users had to manually clear the date filter after every switch. Making the picker empty by default ensures all entries are always visible on source switch, and users opt-in to time filtering only when they need it.

---

## 2026-04-06: Connection History — Flatten to Standard Schema

### Flatten hierarchical connection entries into per-step log entries

**Decision:** Changed the `connection_history` parser from producing hierarchical objects (`{id, steps[], outcome, gateway}`) to flat log entries (`{timestamp, level, message, source, source_file}`) — one entry per connection step.

**Rationale:** The viewer expects a flat `{timestamp, level, message, source}` schema for all log entries. The hierarchical format made connection_history completely invisible in the log viewer (entries had no timestamp, level, or message at the top level and were filtered out as empty).

**Implementation details:**
- Each step becomes a flat entry with the connection context in the message: `Connection #98 [Austria] (connected) — Starting connection attempt...`
- Level is derived from outcome: connected → info, disconnected → warning, failed → error
- Gateway name and outcome are included in the message prefix so they're searchable
- Also fixed the CLI to pass `source` and `source_file` kwargs to all Pacli Output log parsers (previously only passed `filename` and `tz`)

**Alternative considered:** Transforming entries in the viewer JS. Rejected because the parser is the right place to normalize data — the viewer shouldn't need schema-specific transformation logic for each parser type.

---

## 2026-04-06: v2 Architecture — Full-Stack Migration

### FastAPI backend + React frontend replacing single-file viewer

**Decision:** Migrate from the single-file `viewer.html` (client-side only) to a full-stack architecture: FastAPI backend handles ZIP upload and parsing, React+TypeScript+Vite frontend provides the UI.

**Rationale:** The POC required users to manually run the CLI parser and load a folder. The new architecture lets users drag-and-drop a ZIP file, and the backend parses it in-memory and serves the data via REST API. This is the intended workflow for T3 engineers — upload a bundle and start analyzing.

### Reuse existing parsers directly

**Decision:** The backend imports `paa_analyzer.parsers` and `paa_analyzer.taxonomy` directly. The `pipeline.py` adapts the CLI's `parse_file()` routing logic for in-memory use (BytesIO instead of filesystem extraction).

**Rationale:** The 17 parser functions in `parsers.py` are stateless, tested against real data (3.5M entries parsed successfully), and have no external dependencies. Rewriting them as class-based parsers (as the main branch did) would add complexity without benefit.

### Server-side filtering and pagination

**Decision:** All log filtering (level, search, date range, sort) and pagination happens on the backend. The frontend sends query params and receives a page of results.

**Rationale:** The example dataset has 3.5M entries. Loading all entries into the browser (as the POC did) works for single sources (~190K for PAS) but not for "All Logs." Server-side processing keeps the frontend responsive regardless of dataset size.

### React + TypeScript + Vite + Tailwind frontend

**Decision:** Use React 19 with TypeScript, Vite for bundling, Tailwind CSS for utility styling, TanStack React Query for data fetching, and react-router-dom for routing.

**Rationale:** The POC's 770-line single-file vanilla JS reached its maintainability limit. React's component model maps naturally to the Log Viewer's 12+ distinct UI concerns (sidebar, toolbar, column headers, entries, pagination, context menu, custom view). TypeScript catches API contract mismatches at compile time. React Query handles caching, loading states, and cache invalidation.

**Alternative rejected:** Vanilla JS with Jinja templates — simpler stack but doesn't support "extensible, reusable software architecture" as the user required.

### Top-level navigation: Dashboard / Log Viewer / State Viewer

**Decision:** Three tabs in a top nav bar. Log Viewer is the default (index route). Dashboard and State Viewer are placeholder pages ("Coming Soon") for future development.

**Rationale:** The navigation structure establishes the app's three core analysis modes early, even before all are implemented. Users see the full scope of the tool from day one.

### In-memory SessionStore

**Decision:** All parsed data lives in Python dicts, keyed by session ID. No persistence layer (SQLite, files, etc.).

**Rationale:** This is a single-user diagnostic tool. Sessions are ephemeral — upload a bundle, analyze it, done. In-memory storage avoids I/O overhead and keeps the architecture simple. The 3.5M-entry example dataset uses ~2-4 GB RAM, acceptable for a diagnostic workstation.

### API response envelope pattern

**Decision:** Consistent response format: `{data: ...}` for single items, `{data: [...], meta: {total, page, page_size, has_next}}` for paginated lists. All under `/api/v1/`.

**Rationale:** Follows the pattern established in the main branch. Frontend code can rely on a consistent structure without per-endpoint parsing logic.

### Comma-separated source param for Custom View

**Decision:** The `GET /logs?source=PAS,SecurityExtension` endpoint accepts comma-separated source keys. The backend merges entries from all specified sources, sorts by timestamp, then applies filters and pagination.

**Rationale:** This maps directly to the Custom View feature where users select multiple sources. A single query param is simpler than a POST body or repeated params.

---

## 2026-04-06: Upload Page Redesign + Real-Time Parsing Progress

### SSE streaming for upload progress

**Decision:** New `POST /api/v1/sessions/upload` endpoint returns a `StreamingResponse` with `text/event-stream` media type. The pipeline function accepts a progress callback that fires at each parsing stage. Events stream to the frontend in real-time via Server-Sent Events.

**Rationale:** The original upload blocked for ~16 seconds with no feedback. Polling adds latency and server load. WebSocket is overkill for one-way server→client updates. SSE via `StreamingResponse` is the simplest solution — the frontend reads the response body as a `ReadableStream` and parses SSE events manually (since `EventSource` only supports GET).

**Progress stages:** extracting (0-2%), parsing (5-88%, per-file granularity), sorting (90%), storing (95%), complete (100%).

**Threading:** The CPU-bound parser runs in `loop.run_in_executor` (thread pool). Progress callback uses `loop.call_soon_threadsafe(queue.put_nowait, ...)` to bridge the sync thread to the async event loop.

### Sidebar source name deduplication

**Decision:** Source names in the sidebar strip the `Module.Component.` prefix that's already shown in the group heading. E.g., under "Agent / ADEM", show "AccessExperience" instead of "Agent.ADEM.AccessExperience".

**Rationale:** The prefix was redundant — the group heading already provides the context. Removing it gives more horizontal space for the actual source name.

### Top navigation redesign

**Decision:** Replaced pill-button tabs with a full-height tab bar using bottom-border active indicators. Reordered to Dashboard / Log Viewer / State Viewer. Added app branding on the left and session ID on the right.

**Rationale:** The original tiny pill buttons were hard to spot and looked out of place. The underline-tab pattern is a well-established navigation paradigm (used by GitHub, VS Code, Chrome DevTools) that provides clear active state feedback. Dashboard first because it will be the entry point for analysis once implemented.

---

## 2026-04-07: State Viewer

### Overview-oriented complement to Log Viewer

**Decision:** State Viewer is a dedicated page that provides a high-level summary of agent state, organized into four sections: System/Agent overview cards, Feature status panel, Forwarding Profile table, and Pacli Terminal (CLI simulator).

**Rationale:** Support Engineers need a fast way to understand "what is this agent?" before diving into logs. The Log Viewer is detail-oriented (millions of entries, filtering, pagination). The State Viewer is summary-oriented — key facts at a glance, with links to drill deeper into logs.

### Batch state endpoint over N individual fetches

**Decision:** Added `GET /state/batch?keys=key1,key2,...` endpoint that returns multiple state entries in a single response. The State Viewer overview needs data from 10+ state keys simultaneously.

**Rationale:** Without a batch endpoint, the frontend would fire 10+ individual `GET /state/{key}` requests on page load. A batch endpoint reduces round trips to 1. A dedicated `/state/overview` aggregation endpoint was considered but rejected — it would embed domain knowledge (which fields to extract from which keys) in the API layer, whereas the batch approach is generic and reusable.

### Computed hitcounts from traffic_log over pacli-reported hits

**Decision:** Added `GET /state/forwarding-profile` endpoint that enriches forwarding rules with `traffic_log_hits` computed by counting traffic log entries whose `reason` field matches `Rule priority N matched`. The original pacli `hits` field is preserved as a secondary reference.

**Rationale:** The pacli `hits` counter reflects the agent's runtime counter at the time of bundle generation. The traffic log contains the actual logged entries in the bundle. Computing counts from the traffic log gives a number that directly corresponds to what the engineer can see in the Log Viewer — clicking the hitcount link takes them to exactly those entries.

### Raw text storage for Pacli CLI simulator

**Decision:** Modified the pipeline to store the original raw text alongside parsed JSON data for all pacli state files. Added a `raw_text` field to state entries in the session store. System info files (sw_vers, uname, etc.) do not get raw text.

**Rationale:** The Pacli Terminal feature simulates the experience of running pacli commands on the endpoint. Engineers expect to see the exact same output they would see in a real terminal. The raw text is small (~200KB total for 18 files) and enables a "Raw" vs "JSON" toggle in the terminal UI.

### Forwarding profile deep-linking to Log Viewer

**Decision:** Traffic Log Hits in the forwarding table are clickable links that navigate to the Log Viewer with pre-set URL parameters: `?source=Agent.Core.traffic_log_json&search=Rule priority N matched`. The Log Viewer hook was updated to initialize `activeSource` and `search` from URL search params.

**Rationale:** The connection between a forwarding rule and its traffic is the key insight for troubleshooting. Making hitcounts clickable creates a direct bridge between the State Viewer's "what is configured" and the Log Viewer's "what actually happened." URL param initialization is one-time only — subsequent user interactions override the initial values.

### Pacli command name mapping in taxonomy

**Decision:** Added `PACLI_COMMAND_MAP` dictionary to `paa_analyzer/taxonomy.py` mapping state keys to human-readable pacli command names. Exposed via the `pacli_command` field in the state key listing API response.

**Rationale:** State keys use the internal `Module.Component.name` format (e.g., `Agent.Core.status`). Engineers think in terms of the actual CLI commands they run (`pacli status`). An explicit mapping is clearer than auto-deriving from filenames, and allows for exact command names.

### Test foundation

**Decision:** Created a comprehensive test suite alongside the State Viewer feature: shared conftest with fixtures (sample ZIP builder, TestClient, session factory), parser unit tests, pipeline integration tests, and state API endpoint tests. 51 tests total.

**Rationale:** The project had zero automated tests. Building the test infrastructure as part of the first major feature establishes patterns (fixture-based ZIP building, TestClient usage) that future features can reuse. Testing parsers with inline sample data keeps tests isolated and fast.

---

## 2026-04-07: Enriched Log Messages & Raw Entry View

### Multi-line message for complex log types

**Decision:** For log parsers that extract structured fields beyond `message` (traffic_json, event_table), the `message` field now contains a multi-line string with all key data. First line is the summary (visible in the 3-line clamp), subsequent lines contain full details (App path, Reason, etc.).

**Rationale:** The previous traffic_json message was a lossy one-liner (`"Tunnel TCP example.com:443 app=Chrome"`) that discarded the full app path, reason, and other fields. Engineers couldn't see this data without inspecting the raw JSON. The multi-line approach leverages the existing expand/collapse mechanism — the first line serves as a summary, clicking the row reveals everything.

**Alternative rejected:** A separate `full_message` field alongside `message` — this would require changes to the LogEntry type, dual rendering logic, and break the principle that `message` is the canonical display text.

### Missing source field fix

**Decision:** Fixed `traffic_json()` and `event_table()` parsers to accept and populate `source` and `source_file` parameters, matching all other log parsers. Also added `index` and `traffic_type` fields from the raw JSON.

**Rationale:** The missing `source` field caused the Source column to be empty in Log Viewer for traffic log entries. The `source` and `source_file` kwargs were already being passed by the pipeline but discarded via `**_`. Including `index` and `trafficType` preserves data that was silently dropped.

### Raw entry view button

**Decision:** Added a per-row `CodeOutlined` icon button in the Log Viewer message column that toggles a JSON view of the complete log entry. The button is invisible by default, appearing on row hover. State tracked via `rawViewRows: Set<number>` in `useLogViewer`, independent of expand/collapse.

**Rationale:** Engineers need to inspect the full entry data for any log type, not just complex ones. A universal raw view works for structured_log entries (showing host, pid), traffic entries (showing all fields), and any future log format. Separate from expand/collapse because the use cases are different — expand shows the full message text, raw view shows the complete data structure.

### Log message beautification

**Decision:** Added parser-side beautification as a pipeline post-processing step. After all entries are parsed, messages containing `{` are scanned for embedded JSON. Valid JSON objects with 2+ keys are pretty-printed inline. The beautified version is stored as a `beautified` field on the entry. The frontend shows a `FormatPainterOutlined` toggle button (visible on hover) when `beautified` exists.

**Rationale:** ~3% of log entries (~105K out of 3.5M) contain embedded JSON — DEM analytics measurements, compliance results, portal poll responses, agent events. Inline JSON is unreadable. Parser-side beautification was chosen over client-side because Python handles escaped JSON (`\"`) and Python dict literals (`{'key': 'value'}`) more robustly than JavaScript. The `beautified` field doubles as a detection signal — no client-side JSON scanning needed.

**Implementation details:**
- Bracket-matching algorithm with quote tracking finds JSON spans in messages
- Three-stage parsing: `json.loads()` → unescaped `json.loads()` → `ast.literal_eval()`
- Minimum 2-key threshold skips trivial objects like `{"a": 1}`
- Surrounding text (prefix/suffix) is preserved
- Beautify and raw view are mutually exclusive toggle states in the frontend

---

## 2026-04-07: Memory Optimization — ~1 GB Reduction

### String interning for high-frequency fields (~515 MB saved)

**Decision:** Apply `sys.intern()` to `level`, `host`, and `pid` fields in `structured_log()` and `dem_log()` parsers. Also intern `level` in `dlp_netfilter()` and `remote_shell()`.

**Rationale:** These fields have very few unique values (5 levels, 1-2 hosts, ~50 PIDs) but are stored as new string objects per entry because `re.group()` and `.lower()` create fresh strings. With 3.5M entries, this wastes ~515 MB on duplicate string objects. `sys.intern()` ensures all identical strings share the same object.

### Remove `source` and `source_file` from log entries (~354 MB saved)

**Decision:** Removed `source` and `source_file` fields from individual log entry dicts. The store injects `source` back into entries at query time using `_log_meta[sid][key]["name"]`. `source_file` is preserved in pipeline metadata but not on entries.

**Rationale:** `source` is fully redundant — it's the same as the dict key under which entries are stored. Every entry in `_logs[sid]["Agent.Core.PAS"]` had `"source": "PAS"`. `source_file` was never displayed in the frontend. Together they consumed 354 MB across 3.5M entries. The API contract is preserved — the response still contains `source` on every entry.

**Frontend impact:** None — `source` is injected in `get_logs()` before serving. Search also matches on source name.

### Compact timestamps: ISO string → epoch float (~164 MB saved)

**Decision:** Changed `parse_ts()` to return epoch floats instead of ISO-8601 strings. Timestamps are stored as Python float objects (24 bytes) instead of 32-char strings (73 bytes). The store formats them back to ISO-8601 strings in API responses. Date filtering uses float comparison (faster than string comparison). State parser timestamps (`hip_status`, `epm_commands`) use `format_ts()` to produce strings since they're served directly.

**Rationale:** With 3.5M entries × 49 bytes saved per entry = 164 MB. Float comparison is also faster than ISO string comparison for sorting and filtering.

**Frontend impact:** None — API responses contain ISO-8601 strings as before.

### SQLite :memory: for log storage

**Decision:** Replaced the Python dict-based log storage (`_logs: dict[str, dict[str, list[dict]]]`) with SQLite `:memory:` databases. Each session gets its own SQLite connection. Log entries are stored in a `logs` table with dedicated columns for standard fields (timestamp, level, message, host, pid) and a JSON `extra` column for parser-specific fields. Indexes on `(source_key, timestamp)` and `(source_key, level)` enable fast queries.

**Rationale:** Profiling revealed that 3.5M Python dict objects consumed 656 MB in container overhead alone, plus 746 MB in malloc fragmentation from millions of tiny allocations. SQLite stores the same data in ~857 MB total with zero Python object overhead and dramatically faster queries (1-2ms vs seconds for filtered queries, 300ms vs 10-15s for global search). SQLite is in the Python standard library — zero dependencies.

**Key implementation details:**
- Entries are inserted in batches of 50K with indexes created after bulk insert for speed
- `source` field is injected at query time from `_log_meta`, not stored per-row
- `beautified` field is computed lazily for each page of results (not pre-stored)
- Extra fields (destination, protocol, verdict, etc.) packed as JSON, unpacked on query
- `check_same_thread=False` for async FastAPI compatibility
- `get_log_sources()` uses SQL GROUP BY for aggregation instead of Python loops
- `get_log_entries()` unpacks extra JSON for forwarding-profile hitcount computation

**Frontend impact:** None — API response format is identical. All existing frontend functionality (source selection, level filtering, search, date range, pagination, sort, expand, raw view, beautify) works unchanged.

---

## 2026-04-07: Rename State Viewer → Agent Status + System Details

### Rename and nav reorder

**Decision:** Renamed "State Viewer" to "Agent Status" and moved it from 3rd to 2nd position in the top nav (Dashboard → Agent Status → Log Viewer). Route changed from `/s/{id}/state` to `/s/{id}/agent-status`.

**Rationale:** "Agent Status" better describes the page's purpose — showing agent and system health at a glance. The nav order follows the natural analysis workflow: high-level overview (Dashboard) → status check (Agent Status) → deep-dive into logs (Log Viewer).

### Structured parsers for routing table and launchctl

**Decision:** Replaced the `raw_text` parser for `routing.txt` and `launchctl_list.txt` with new `routing_table()` and `launchctl_list()` parsers that produce structured records. Routing table returns `{ipv4: [...], ipv6: [...]}` with per-route fields (destination, gateway, flags, netif, expire). Launchctl returns `[{pid, status, label}]`.

**Rationale:** The data is inherently tabular. Structured records enable sortable Ant Design tables with column-level features (flag tooltips, status colors, label filtering) instead of plain `<pre>` blocks. The raw original text is preserved via `raw_text` for the Raw view toggle.

**Alternatives considered:** Displaying raw text in formatted `<pre>` blocks — simpler but no sorting, filtering, or visual indicators. Rejected since the data is clearly columnar and support engineers benefit from interactive tables.

### Raw text storage for system detail files

**Decision:** Modified `pipeline.py` to store `raw_text` alongside parsed `data` for three system files: `routing.txt`, `launchctl_list.txt`, `system_extension_list.txt`. Other system info files (sw_vers, uname, external_ip) remain without raw text.

**Rationale:** Enables the Raw view toggle on the new System Details component, matching the existing pattern from PACli Terminal. Only stored for files where users need to see original formatting. Minimal memory impact (~50KB per file).

### System Details tabbed component

**Decision:** Added a "System Details" section between Features Panel and Forwarding Table with three card-style tabs: System Extensions, Routing Table, Autostart Programs. Each tab has a shared Table/Raw/JSON view mode toggle.

**Rationale:** System-level data (extensions, routes, daemons) is a distinct troubleshooting concern from agent features. Tabs keep the page scannable — support engineers can jump to the relevant system view without scrolling past irrelevant data. The three-mode toggle (Table/Raw/JSON) extends the existing Raw/JSON pattern from PACli Terminal with a structured Table default.

---

## 2026-04-08: Repository Cleanup & Central App Name

### Remove prototype frontend directories

**Decision:** Deleted `frontend-mantine/`, `frontend-mui/`, `frontend-shadcn/`, and `frontend-bak/` from the repository. Only `frontend-antd/` (symlinked as `frontend/`) remains.

**Rationale:** The UI kit evaluation concluded with Ant Design selected. The three prototype frontends were stale (last updated Apr 6), contained broken imports to deleted components, and consumed ~687 MB of tracked files. Keeping them adds confusion and bloats the repo.

### Central APP_NAME constant

**Decision:** Created `frontend-antd/src/constants.ts` with `APP_NAME = 'PAA Analyzer'`. Updated `index.html` title, `TopNav`, and `UploadPage` to use this constant instead of hardcoded strings.

**Rationale:** The browser tab title was still "frontend-antd" (the Vite template default). The app name appeared as a hardcoded string in multiple components. A single constant ensures consistency and makes future rebranding a one-line change.

---

## 2026-04-08: Comprehensive Testing Strategy

### pytest + pytest-cov with tiered markers

**Decision:** Established a comprehensive test suite using pytest with pytest-cov for coverage measurement. Tests are organized with markers (`unit`, `integration`, `api`, `e2e`, `slow`) and `--strict-markers` enforced. Coverage threshold set to 70% with `fail_under`.

**Rationale:** The project had 108 tests covering ~40-50% of functional surface area, with critical gaps in timestamp parsing (called on every log entry), 6 of 8 log parsers untested, no CLI tests, and no end-to-end validation with real data. Markers enable fast iteration (`pytest -m "not slow"`) while still validating full system correctness with real troubleshooting bundles.

**Result:** 248 tests at 91% coverage. Key additions:
- Timestamp parsing: parametrized tests for all 7 formats (highest bug-catching ROI)
- Log parsers: structured_log, dem_log, dlp_log, dlp_netfilter, connection_history, event_table, remote_shell
- State parsers: epm_commands, traffic_rdns, system_extensions, app_list, raw_text
- Store: session lifecycle, log query edge cases (pagination, sorting, filtering), state queries
- API: session CRUD, upload validation, dashboard endpoint
- Pipeline: file routing, edge cases (empty ZIP, unknown files)
- CLI: paa-parse end-to-end with tmp_path
- E2E: real 37MB example ZIP through both parse_zip and API endpoints

**Coverage target:** 70% initial (met at 91%), 85% aspirational. Module-scoped fixtures for e2e tests to avoid re-parsing the 37MB ZIP per test.

### Frontend testing: Vitest + React Testing Library + MSW

**Decision:** Added frontend test infrastructure with Vitest (Vite-native), React Testing Library, and MSW (Mock Service Worker). Tests run as part of the build (`vitest run && tsc -b && vite build`) to gate broken code.

**Rationale:** The frontend had zero test infrastructure. Rather than pursuing coverage metrics, tests target the code most likely to break during refactors:
- `api/client.ts` — error parsing, FormData Content-Type handling (breaks file upload if wrong)
- `useLogViewer` — raw/beautify mutual exclusion, "can't hide last column" guard, sourceParam derivation
- `useUploadWithProgress` — SSE stream chunk parsing, state machine transitions
- `useLogs` — query parameter construction (silent bugs cause wrong data)
- `fmtTs` — timestamp formatting called on every visible row
- `getField` — null-safe state traversal (breaks when backend response shape changes)

**What we skip:** Pure display components (FeaturesPanel, RoutingTableTab, etc.), Ant Design component behavior, CSS/styling, React Router config. These are either library responsibility or immediately caught by manual testing.

**Alternative rejected:** Jest — requires separate transform config, slower, not aligned with Vite pipeline. Cypress/Playwright e2e — high maintenance cost for a diagnostics tool with fast-changing UI; unit/hook tests provide better ROI.

---

## 2026-04-08: Windows Troubleshooting Bundle Support

### Multi-OS architecture with unified taxonomy

**Decision:** Extended the existing taxonomy and pipeline to handle Windows troubleshooting bundles alongside macOS. Windows entries added to `SYSTEM_INFO_FILES` (no separate dict), Windows parsers in new `paa_analyzer/parsers_win.py`, platform auto-detected from bundle structure.

**Rationale:** Analysis of `examples/pa_windows_example.zip` revealed that all 20 Pacli Output files and all structured logs (PAS, Adns, etc.) use identical formats across OS. Only system info files and some log formats differ. The architecture decision was to:
1. Merge Windows file mappings into the existing `SYSTEM_INFO_FILES` dict (filenames don't collide)
2. Keep Windows parsers in a separate `parsers_win.py` (prevents `parsers.py` from exceeding 1000 lines)
3. Route `Machine Info/` files through the same lookup, preserving raw_text for terminal view
4. Auto-detect platform from directory presence (`Machine Info/` = Windows, `sw_vers.txt` = macOS)
5. Make SystemDetails tabs data-driven (render available state keys, not hardcoded OS tab lists)
6. Keep Windows PAUI US date format (`MM/DD/YYYY`) isolated in `win_paui_log` (not added to global `parse_ts`)

**Key findings:** 19 new Windows parsers covering systeminfo, ipconfig, route print, installed drivers, firewall rules, netstat, DNS cache, power config, user groups/sessions, event viewer, plus 3 new log parsers (win_paui_log, win_dem_log, chromium_log). Binary files (.dmp, .etl) and installer logs (MSI, setupapi) are skipped and counted in manifest.

**Alternative rejected:** Separate `MACHINE_INFO_FILES` dict + OS-conditional pipeline logic — adds unnecessary complexity when filenames don't collide.

---

## 2026-04-08: Versioning Strategy

### pyproject.toml as single source of truth

**Decision:** `pyproject.toml` is the canonical version. Backend reads it at runtime via `importlib.metadata.version("paa-analyzer")`. Frontend reads `package.json` version at build time via Vite `define`. Both files are kept in sync manually.

**Rationale:** Two files to sync is manageable for a single-developer project. Adding `bump2version` or `python-semantic-release` would be over-engineering. The `importlib.metadata` approach is the Python standard (PEP 621) and requires no extra VERSION file. Frontend uses Vite's `define` for zero-runtime-cost injection.

**CHANGELOG:** Uses [Keep a Changelog](https://keepachangelog.com/) format with categories: Added, Changed, Fixed, Removed. Tracked in `CHANGELOG.md` at repo root.

**Release process:** Bump both files, update CHANGELOG, commit, merge to main, annotated git tag.
