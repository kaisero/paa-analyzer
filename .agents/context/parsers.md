# parsers

Validated against eb5a7de on 2026-07-16 · Purpose: the `paa_analyzer/` parsing library — taxonomy-driven routing of troubleshooting-bundle files to parser functions, plus the `paa-parse` CLI.

## Purpose & responsibilities

`paa_analyzer/` is the dependency-free core of the project: it turns the raw
text files inside a Prisma Access Agent troubleshooting bundle into structured
records. It owns three things:

- **The taxonomy** (`taxonomy.py`) — the routing table mapping every known
  bundle filename (or structured-log source name) to its data type
  (`state`/`log`), module (`Agent`/`System`), component, and parser name.
- **The parsers** (`parsers.py` cross-platform + macOS, `parsers_win.py`
  Windows-format) — pure functions `text -> Record | list[Record] |
  list[LogEntry] | str`.
- **The standalone CLI** (`cli.py`, entry point `paa-parse`) — parses a ZIP to
  JSON files on disk without the backend.
- **The HIP domain model** (`hip/`) — a layer on top of already-parsed
  `PACompliance*`/`PAComplianceMp*` log entries that turns them into a
  structured Host Information Profile model (cycles, reports, policy, OPSWAT
  errors, status). Not part of the taxonomy/parser/CLI triad above — it
  consumes their output rather than being dispatched by the taxonomy.

The backend (`backend/pipeline.py`, `backend/store.py`) imports this package
directly; it is the single implementation of parsing for both the CLI and the
web app.

## How it works

### Taxonomy routing (`taxonomy.py`)

`FileMeta` is a 4-field dataclass: `data_type` ("state" or "log"), `module`,
`component`, `parser` (the parser **function name**, resolved by string). The
module-level dicts are the routing tables (rendered below in the generated
taxonomy table):

- `PACLI_FILES` — files under `Pacli Output/`; all state snapshots except
  `pacli_connection_history.log` and `pacli_event.log`, which are logs.
- `SYSTEM_INFO_FILES` — macOS system-info text files AND Windows
  `Machine Info/` files (one dict for both platforms).
- `SPECIAL_FILES` — one-offs like `traffic_log_json.txt` and files marked
  `skip_large` (recognized but deliberately not ingested).
- `LOG_SOURCES` — structured-log source name → `(module, component)` tuple
  (NOT `FileMeta`), used for `Logs/**/*.log` routing.
- `PACLI_COMMAND_MAP` — state key (`Agent.Core.status`) → human-readable pacli
  command; consumed by `backend/store.py::get_state_keys` for display.
- `SKIP_EXTENSIONS` / `SKIP_PREFIXES` — Windows binary/installer artifacts to
  ignore (`.dmp`, `.etl`, `MSI*`, …).

### Parser dispatch is by name, not by reference

Consumers look the parser up with `getattr(parsers, name, None) or
getattr(parsers_win, name, None)` (`backend/pipeline.py::_run_parser`; `cli.py`
has the same logic). An unknown parser name silently degrades to returning the
raw text — see Gotchas.

### `parsers.py` (cross-platform + macOS)

- **Timestamp core:** `parse_ts` normalizes every known timestamp format to an
  epoch float (UTC seconds); `format_ts` renders it back to ISO;
  `extract_tz_offset` pulls the bundle's UTC offset out of `pacli_status.log`
  text (found once per bundle and threaded into parsers as `tz=`).
- **State parsers:** `key_value` (the generic `Key: Value` pacli format),
  `forwarding_profile`, `gateway_list`, `hip_status`, `protection`,
  `epm_commands`, `traffic_rdns`, `system_info`, `system_extensions`,
  `routing_table`, `launchctl_list`, `app_list`, `raw_text`.
  `hip_status` (`pacli_hip_status.log`) was rewritten to stop dropping the
  gateway status column: it used to flip into table mode on a
  `"Last HIP Report"` header string that the current agent format doesn't
  emit, so it silently returned zero gateways for every real bundle. It now
  anchors on the dashed separator line under the header — present in both
  the legacy 2-column (Gateway / Last HIP Report) and current 3-column
  (Name / Time / Status) layouts — and uses the dash runs in that line as
  column boundaries, which also survives gateway names of varying length
  better than a fixed-width split. Each gateway dict grew `status` (verbatim,
  possibly truncated by the agent's own display-width cutoff) and
  `status_kind` (`success`/`failed`/`not-needed`/`unknown`).
- **Log parsers** (return `list[LogEntry]`): `structured_log` (the standard
  agent log line format), `dem_log`, `dlp_log`, `dlp_netfilter`,
  `connection_history`, `event_table`, `traffic_json`, `remote_shell`.
- **Beautification:** `beautify_message` extracts and pretty-prints embedded
  JSON from a log message (helpers `_find_json_spans`, `_try_parse_json`);
  called lazily per page by `backend/store.py::get_logs`.

### `parsers_win.py` (Windows formats)

Parsers for `Machine Info/` files (`systeminfo`, `ipconfig`,
`win_routing_table`, `win_firewall_rules`, `win_netstat`, `win_dns_cache`,
power/session/group listings, `win_event_viewer` XML) and Windows log formats
(`win_paui_log` US-date PAUI logs, `win_dem_log`, `chromium_log` for
`PABrowser.log`).

### `cli.py` (`paa-parse`)

`main()` mirrors the backend pipeline standalone: two ZIP passes (first
extracts `tz_offset` from `pacli_status.log`, second routes each entry through
the taxonomy), then writes `state/*.json`, `logs/*.json`, `hip.json`, and a
manifest under the output directory. Kept in sync with
`backend/pipeline.py::_parse_file` by hand — the routing precedence rules live
in both files. `hip.json` is the one output that isn't a 1:1 mirror of the
backend: it holds the *full* `build_hip_data()` model including the `_raw` key
(raw XML), since the CLI has no separate raw-XML endpoint to defer it to —
`backend/store.py::get_hip` strips `_raw` for the same data over the API.

### HIP domain model (`hip/`)

A package layered on top of `structured_log()`'s output, not part of the
taxonomy-dispatched parser set: `build_hip_data(logs, state, platform,
tz_offset)` is the one entry point, called from `backend/pipeline.py` (and
`cli.py`) after the compliance logs are parsed and sorted, before anything
downstream can free them. It reads two structured-log sources —
`Agent.Compliance.PACompliance` and `Agent.Compliance.PAComplianceMp` — plus
the `Agent.Compliance.hip_status` state entry, and returns one `HipData` dict:
`platform`, `collection`, `next_check`, `gateways`, `cycles` (newest first),
plus a `_raw` key (raw XML, string-indexed by cycle) that callers strip before
serving the structured model. Full shape and the status heuristics are
recorded in `docs/plans/hip-analytics-foundation.md`'s "Data model" section.

Each submodule owns one concern, composed by `__init__.py`:

- `cycles.py` — `split_cycles()` cuts a chronological entry stream into HIP
  cycles on the `Try to parse hip policy` line (entries before the first such
  line form a `partial=True` leading cycle); `pair_cycles()` matches each
  `PAComplianceMp` cycle to the nearest `PACompliance` cycle by start
  timestamp within a 5 s tolerance, never silently dropping an unmatched Mp
  cycle.
- `report.py` — `parse_hip_report()` turns the `<hip-report>` XML embedded in
  a log message (located by string search, then parsed with
  `xml.etree.ElementTree`) into host_info / categories / products /
  custom_checks. `host_id_kind` (`mac-address` / `machine-guid` / `unknown`)
  is derived from the host-id *value's shape*, never from the `platform`
  argument — the two platforms share one XML schema.
- `patches.py` — `parse_missing_patches()` parses the separate
  `<missing-patches>` fragment from a `PAComplianceMp` message. The
  `<missing-patches>` element embedded in the *report* XML itself is always
  empty — the Mp worker computes real patches ~7 s later and this is the only
  place that sees them.
- `policy.py` — `parse_policy()` decodes the JSON after `Try to parse hip
  policy: `; malformed JSON returns `None`, never raises.
- `opswat.py` — `parse_detected_products()` builds a signature → product map
  from the `DETECT_PRODUCTS` JSON blobs (one per category, merged);
  `parse_opswat_errors()` parses `Opswat Error(-N): ...` lines and resolves
  each to a product via that map. The error's own function-name log prefix
  (e.g. `CollectComplianceDataForDLP`) is not trusted for category — only the
  line's `Category:` field is authoritative, since a Time Machine failure
  logs under the DLP-named function.
- `status.py` — `product_status()` / `category_status()` return `(status,
  reason)` over the vocabulary `ok` / `warn` / `unknown` / `not-detected`.
  Deliberately no "fail": the bundle carries no gateway match criteria, so no
  HIP pass/fail verdict can be truthfully asserted from it alone.
- `cycle_scalars.py` — log-line scraping for one cycle: category timings,
  creation duration, dispatch outcome, the policy blob, and `generate-time`
  (the report's endpoint-local timestamp, resolved to UTC via the bundle's
  `tz_offset` when supplied, else inferred from the enclosing log entry's own
  timestamp).
- `codes.py` — the OESIS error/method/category catalog
  (`error_explanation`, `method_query`, `method_attribute`, `category_name`);
  every lookup returns `None` for an uncatalogued id rather than raising, and
  is built only from codes actually observed in the fixtures.
- `_xml.py` — the one shared helper (`text_or_none`) used by `report.py` and
  `patches.py`.

Known gaps, both because no available bundle exercises them: the
`custom-checks/registry` branch in `report.py` (Windows equivalent of the
macOS `<plist>` shape) is implemented defensively from the plist shape's
symmetry but is untested; a cycle whose `report` is `None` (report XML never
landed in the log, e.g. rotation truncation) is likewise unexercised end to
end.

## Build / run pointers

- Tests: `uv run pytest backend/tests/test_parsers.py backend/tests/test_parsers_win.py backend/tests/test_cli.py`
  plus `backend/tests/test_hip_*.py` for the `hip/` package (the whole suite
  lives under `backend/tests/`; HIP fixtures are redacted real bundle logs
  under `backend/tests/fixtures/hip/`).
- CLI: `uv run paa-parse <troubleshooting.zip> [output_dir]`.
- Full offline gate: `uv run nox -s gate`.
- Regenerate the blocks below after changing this package: `uv run nox -s context`.

## Module map

<!-- GENERATED:module-map -->
- `cli.py` — CLI: parse a troubleshooting ZIP into structured JSON files.
- `parsers.py` — Parsers: each function takes file text and returns structured data.
- `parsers_win.py` — Windows-specific parsers for Machine Info files and Windows log formats.
- `taxonomy.py` — Taxonomy: maps every known file in the troubleshooting bundle to its type, module, and component.
<!-- /GENERATED:module-map -->

## Public API (`parsers.py` + `parsers_win.py`)

<!-- GENERATED:api -->
- `parsers.py`
  - `parse_ts(raw, default_offset)` — Parse any known timestamp format → epoch float (UTC seconds).
  - `format_ts(epoch)` — Format epoch float → ISO-8601 UTC string for API responses.
  - `extract_tz_offset(text)`
  - `key_value(text)` — Parse Key: Value lines into a dict.
  - `forwarding_profile(text)`
  - `gateway_list(text)`
  - `hip_status(text, tz)` — Parse `pacli_hip_status.log`.
  - `protection(text)`
  - `epm_commands(text, tz)`
  - `traffic_rdns(text)`
  - `system_info(text, filename)`
  - `system_extensions(text)`
  - `routing_table(text)` — Parse netstat -rn style routing table into structured records.
  - `launchctl_list(text)` — Parse launchctl list output into structured records.
  - `app_list(text)`
  - `raw_text(text)`
  - `structured_log(text, source, source_file)` — Parse ISO-8601 structured log files (PAS, SecurityExtension, etc.).
  - `dem_log(text, source, source_file)`
  - `dlp_log(text, source, source_file, tz)`
  - `dlp_netfilter(text, source, source_file, tz)`
  - `connection_history(text, tz, source, source_file)` — Parse connection history into flat log entries (one per step).
  - `event_table(text, tz, source, source_file)`
  - `traffic_json(text, tz, source, source_file)`
  - `remote_shell(text, source_file)`
  - `beautify_message(message)` — Extract embedded JSON from a log message and pretty-print it.
- `parsers_win.py`
  - `systeminfo(text)` — Parse Windows `systeminfo` output into key-value dict.
  - `ipconfig(text)` — Parse Windows `ipconfig /all` output into structured sections.
  - `win_routing_table(text)` — Parse Windows `route print` output.
  - `win_firewall_rules(text)` — Parse Windows firewall rules JSON export.
  - `win_installed_apps(text)` — Parse PowerShell Get-Package table output.
  - `win_installed_drivers(text)` — Parse `driverquery /v` fixed-width output using separator line for column positions.
  - `win_netstat(text)` — Parse Windows `netstat -ab` output with process names.
  - `win_dns_cache(text)` — Parse `ipconfig /displaydns` output into DNS record entries.
  - `win_user_groups(text)` — Parse `whoami /groups` table output.
  - `win_user_sessions(text)` — Parse `query session` output.
  - `win_powercfg(text)` — Parse `powercfg /availablesleepstates` output.
  - `win_powercfg_query(text)` — Parse `powercfg /query` power scheme output.
  - `win_power_history(text)` — Parse PowerShell event log export (Get-WinEvent style).
  - `win_nslookup(text)` — Parse nslookup output.
  - `win_ping(text)` — Parse Windows ping output.
  - `win_event_viewer(text)` — Parse PowerShell XML event log export (CLIXML Objects format).
  - `win_paui_log(text, tz, source, source_file)` — Parse Windows PAUI log format: 'PAUI Level: N : MM/DD/YYYY HH:MM:SS message'.
  - `win_dem_log(text, source, source_file)` — Parse Windows DEM log: '[YYYY-MM-DD HH:MM:SS.mmm] [source] [level] message'.
  - `chromium_log(text, source, source_file)` — Parse Chromium log: '[pid:tid:MMDD/HHMMSS.ms:LEVEL:file.cc(line)] message'.
<!-- /GENERATED:api -->

## Taxonomy routing table (`taxonomy.py`)

Only the `FileMeta`-valued dicts are rendered; `LOG_SOURCES`,
`PACLI_COMMAND_MAP`, and the skip sets are narrative-only (see above).

<!-- GENERATED:taxonomy-table -->
**`PACLI_FILES`**

| File | data_type | module | component | parser |
| --- | --- | --- | --- | --- |
| `pacli_status.log` | state | Agent | Core | key_value |
| `pacli_epm_status.log` | state | Agent | Core | key_value |
| `pacli_version.log` | state | Agent | Core | key_value |
| `pacli_proxy_status.log` | state | Agent | Core | key_value |
| `pacli_tunnel.log` | state | Agent | Networking | key_value |
| `pacli_ep.log` | state | Agent | Explicit Proxy | key_value |
| `pacli_browser_status.log` | state | Agent | Core | key_value |
| `pacli_captive_portal.log` | state | Agent | Core | key_value |
| `pacli_adns.log` | state | Agent | ADNS Resolver | key_value |
| `pacli_dpa_project_list.log` | state | Agent | Dynamic Privileged Access | key_value |
| `pacli_adem_status.log` | state | Agent | ADEM | key_value |
| `pacli_dlp_status.log` | state | Agent | DLP | key_value |
| `pacli_traffic_show.log` | state | Agent | Networking | forwarding_profile |
| `pacli_gateways_list.log` | state | Agent | Core | gateway_list |
| `pacli_hip_status.log` | state | Agent | Compliance | hip_status |
| `pacli_protect.log` | state | Agent | Security | protection |
| `pacli_epm_commands.log` | state | Agent | Core | epm_commands |
| `pacli_traffic_rdns.log` | state | Agent | Networking | traffic_rdns |
| `pacli_connection_history.log` | log | Agent | Core | connection_history |
| `pacli_event.log` | log | Agent | Core | event_table |

**`SYSTEM_INFO_FILES`**

| File | data_type | module | component | parser |
| --- | --- | --- | --- | --- |
| `sw_vers.txt` | state | Agent | Core | system_info |
| `uname.txt` | state | System | Core | system_info |
| `external_ip.txt` | state | System | Networking | system_info |
| `date_generated.txt` | state | Agent | Core | system_info |
| `ifconfig.txt` | state | System | Networking | raw_text |
| `routing.txt` | state | System | Networking | routing_table |
| `system_extension_list.txt` | state | System | Core | system_extensions |
| `installed_applications.txt` | state | System | Core | app_list |
| `launchctl_list.txt` | state | System | Core | launchctl_list |
| `ui_sample.txt` | state | System | Core | raw_text |
| `PrismaAccessAgent_agent_version.log` | state | Agent | Core | system_info |
| `systeminfo.log` | state | System | Core | systeminfo |
| `ipconfig.log` | state | System | Networking | ipconfig |
| `route.log` | state | System | Networking | win_routing_table |
| `installed_applications.log` | state | System | Core | win_installed_apps |
| `installed_drivers.log` | state | System | Core | win_installed_drivers |
| `netstat.log` | state | System | Networking | win_netstat |
| `dns_cache.log` | state | System | Networking | win_dns_cache |
| `WindowsFirewallrules.json` | state | System | Security | win_firewall_rules |
| `current_user_groups.log` | state | System | Core | win_user_groups |
| `user_sessions.log` | state | System | Core | win_user_sessions |
| `powercfg_all.log` | state | System | Power | win_powercfg |
| `powercfg_query.log` | state | System | Power | win_powercfg_query |
| `power_history_24h.log` | state | System | Power | win_power_history |
| `nslookup_google_com.log` | state | System | Networking | win_nslookup |
| `ping_8_8_8_8.log` | state | System | Networking | win_ping |
| `windows_event_viewer_logs.xml` | state | System | Core | win_event_viewer |

**`SPECIAL_FILES`**

| File | data_type | module | component | parser |
| --- | --- | --- | --- | --- |
| `traffic_log_json.txt` | log | Agent | Core | traffic_json |
| `networkextensions.txt` | log | System | Networking | skip_large |
| `unified_log_last_60minutes.txt` | log | System | Core | skip_large |
| `remote-shell.log` | log | Agent | Core | remote_shell |
| `fips_self_test.log` | state | Agent | Core | raw_text |
<!-- /GENERATED:taxonomy-table -->

## Gotchas / invariants

- **Adding a new bundle file type** = add a `FileMeta` row to the right
  taxonomy dict + a parser function whose NAME equals `FileMeta.parser` in
  `parsers.py` or `parsers_win.py`. Dispatch is `getattr`-based, so a typo'd
  parser name does not raise — the file is stored as raw text.
- **Routing precedence matters** (`backend/pipeline.py::_parse_file`): `Pacli
  Output/` → Windows `Machine Info/` → macOS `SYSTEM_INFO_FILES` →
  `SPECIAL_FILES` → skip patterns → PAUI/PABrowser/DLP/DEM special cases →
  `LOG_SOURCES` structured logs. `Machine Info/` must be checked before the
  filename-only `SYSTEM_INFO_FILES` lookup so Windows raw text is preserved.
- **`skip_large` is a sentinel parser name** meaning "recognized, deliberately
  not ingested" (`networkextensions.txt`, `unified_log_last_60minutes.txt`).
- **Timestamps normalize to epoch floats (UTC)**; the bundle-local `tz_offset`
  comes from `pacli_status.log` once per bundle and is passed as `tz=` to
  parsers that need it. `parse_ts` returns `None` for unparseable input.
- **Every parser accepts `**_: Any` extras** — callers pass `filename=`,
  `tz=`, `source=`, `source_file=` uniformly; parsers ignore what they don't
  need. Keep that contract when adding parsers.
- **`backend/` depends on this package's names**: `store.py` imports
  `beautify_message`, `format_ts`, `PACLI_COMMAND_MAP`; `pipeline.py` imports
  the taxonomy dicts. Renames here break the backend.
- **`parsers_win.py` has a documented lint exemption** — S314 (untrusted XML)
  is ignored in `pyproject.toml` because bundle XML is trusted operator input.
- **`hip/` must run before the store frees log entries.** `build_hip_data()`
  is called from `backend/pipeline.py` on the just-sorted `all_logs` dict,
  before `SessionStore.add_session()` clears each source's `entries` list to
  reduce peak memory. Extraction cannot be made lazy on the backend without
  keeping entries around for it.
- **`hip/` is dependency-free like the rest of `paa_analyzer/`** — stdlib
  `xml.etree.ElementTree`/`json`/`re` only, plain dicts/lists out, ISO-8601
  UTC strings via `parsers.format_ts()` for every timestamp, matching how the
  rest of this package returns data.
- **HIP test fixtures are never hand-authored.** Python fixtures
  (`backend/tests/fixtures/hip/`) are redacted copies of real
  `PACompliance*`/`PAComplianceMp*.log` files; the frontend's `hip.json`
  fixture is *generated* by running `build_hip_data()` over those same Python
  fixtures (`frontend/src/test/fixtures/generate-hip-fixture.py`) — see
  `frontend.md`.

## See also

- `backend.md` — the FastAPI app that drives these parsers via
  `backend/pipeline.py`.
- `index.md` — entry point for all agent-context docs (added in a later task).
- `../../docs/architecture.md` — the human-facing architecture narrative
  (request lifecycle, diagrams); cross-link only, content not duplicated here.
- `../../CLAUDE.md` — working agreement, including the read-before /
  regenerate-after contract for these docs.
