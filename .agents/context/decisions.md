# decisions

Validated against cc3f0cc on 2026-07-26 · Purpose: the load-bearing design decisions behind paa-analyzer — what was chosen, why, and what was rejected.

This is a decision log, not a how-to. Each entry records a choice that shaped
the system, terse: decision · date · why. `CLAUDE.md` mandates logging every
dev/design decision here — add a new numbered entry (append-only; newest last)
when you make one. The **binding rules** live in `CLAUDE.md`; this file
explains *why*, not *what you must do*.

Dates reflect when the decision landed in this repo's history (the codebase was
imported 2026-07-15, so the founding architecture decisions share that date).

---

## 1. Nothing is persisted — per-session in-memory SQLite plus dicts · 2026-07-15

Sessions, state, and logs live in one in-process `SessionStore`
(`backend/store.py`): plain dicts for session metadata and state, one SQLite
`:memory:` database per session for logs. No database on disk, no persistence
layer. The tool analyzes one uploaded bundle at a time; durability would add
schema/migration/cleanup machinery for data that is trivially re-created by
re-uploading the ZIP. Rejected: a shared on-disk DB. Cost (accepted): a server
restart drops every session.

## 2. Hybrid store: SQL for logs, dicts for state · 2026-07-15

Logs can be hundreds of thousands of rows and need filter/search/aggregate/
paginate — SQLite (with post-bulk-insert indexes) is the cheapest way to get
that. State is small and fetched whole — dicts suffice. Rejected: one
mechanism for both (SQL for state is overkill; Python filtering of logs is
too slow). See `backend.md`.

## 3. Taxonomy routing table over per-file conditionals · 2026-07-15

Every known bundle file maps to `FileMeta(data_type, module, component,
parser)` in declarative dicts (`paa_analyzer/taxonomy.py`); the pipeline is an
ordered dispatch cascade over those tables. Adding a file type = one dict row
+ one parser function, not another branch in a parsing if-tree. The table is
also machine-readable — the generated taxonomy table in `parsers.md` renders
straight from it. See `parsers.md`.

## 4. Parser dispatch by name, degrading to raw text · 2026-07-15

`FileMeta.parser` holds a function *name*, resolved with `getattr` on
`parsers` then `parsers_win` (`backend/pipeline.py::_run_parser`). An unknown
name stores the file as raw text instead of crashing — a partially understood
bundle still yields a usable session. Cost (accepted): a typo'd parser name
fails silently; the taxonomy table + tests are the guard.

## 5. Standalone parser package, imported by the backend · 2026-07-15

`paa_analyzer/` is dependency-free and owns all parsing; `backend/` and the
`paa-parse` CLI are two consumers of the same implementation. Parsing is
testable and usable (CLI → JSON files) without a server. Rejected: parsers
living inside the backend app.

## 6. Ant Design over Tailwind/other UI kits · 2026-07-15

The frontend is built on antd 6 (`frontend/package.json`, name
`frontend-antd`) — heavy data-display needs (tables with resizable columns,
tabs, cards, dark theme via `ConfigProvider` tokens) come out of the box
instead of being hand-built on utility CSS. Stale references to "Tailwind" in
older docs were corrected 2026-07-16; there is no tailwind dependency.

## 7. SSE upload progress from a worker thread · 2026-07-15

`POST /sessions/upload` streams parse progress as SSE: `parse_zip` runs in a
thread via `run_in_executor`, progress callbacks hop to the event loop through
an `asyncio.Queue` + `call_soon_threadsafe`. Big bundles parse for many
seconds; a silent request looks hung. The synchronous `POST /sessions` stays
as the non-streaming fallback. See `backend.md`.

## 8. One noxfile as the single source of checks · 2026-07-16

Local runs, pre-commit, CI jobs, and the Stop hook all invoke the same nox
sessions; pre-commit's project tools run via `uv run` so versions can't drift
from CI. Rejected: per-surface tool config (the usual way lint versions
diverge). See `harness-and-testing.md`.

## 9. Stop-hook offline gate — fail-open, loop-guarded · 2026-07-16

Every agent stop runs `uv run nox -s gate` via `.claude/hooks/fast_gate.py`; a
red gate blocks the stop. The hook fails **open** on internal errors and
allows the stop (with a loud warning) after 3 consecutive blocks — an
unattended session must never wedge on harness bugs or an unfixable red state;
CI is the backstop. See `harness-and-testing.md`.

## 10. Documented per-file lint exemptions over rule removal · 2026-07-15

Security-lint false positives (`S608` in `store.py`, `S314` in
`parsers_win.py`, `S603/S607` in the hook) are silenced per-file in
`pyproject.toml`, each with a rationale comment — the rules stay live
everywhere else. Rejected: dropping the rules from the ruleset.

## 12. Enterprise design system via antd ConfigProvider — no framework swap · 2026-07-25

The frontend visual design was overhauled to match a Palo Alto brand aesthetic
(PA orange `#FA582D` accent, rectangular borders, dark `#0C0F14` base). The
decision was to keep antd and achieve the look through `ConfigProvider` tokens +
CSS custom properties rather than replacing antd with bare CSS or Tailwind. Key
levers: `borderRadius: 0` propagates through every component; `colorPrimary`
carries the orange into focus rings, active states, and ink bars; a `data-theme`
attribute on `<html>` flips a CSS variable layer for dark/light mode.

Rejected: removing antd (would have required rebuilding tables, date pickers,
tabs, and form controls from scratch). Cost (accepted): antd's token system
doesn't cover every detail — five global CSS overrides are needed (active menu
bar side, tag text-transform, expand-icon column suppression).

## 13. Dark/light mode via CSS custom properties + React context · 2026-07-25

Theme state is owned by `ThemeContext` (`src/contexts/ThemeContext.tsx`):
`isDark`/`toggle()` backed by `localStorage("theme")`, with the active mode
written as `data-theme` on `document.documentElement`. All component styles read
from CSS custom properties declared in `global.css`; the antd `ConfigProvider`
token objects (`darkTokens`/`lightTokens` in `main.tsx`) are the bridge between
the CSS layer and antd's internal theming. An inline `<script>` in `index.html`
sets `data-theme` from `localStorage` before React hydrates to prevent a
light-flash on initial load.

Rejected: antd's built-in `theme.darkAlgorithm` toggle alone (it doesn't expose
the surface/border/text hierarchy as CSS variables, so non-antd elements would
need a separate mechanism anyway).

## 11. Agent-context docs with generated blocks + freshness gate · 2026-07-16

This `.agents/context/` system: hand-written narrative deep-dives carrying
machine-generated inventory blocks (`tools/context_docs.py`, pure stdlib AST),
kept honest by `tests/test_context_docs_current.py` riding the normal suite,
and a read-before/update-after contract in `CLAUDE.md`. It replaces the dead
`docs/design-decisions.md` mandate (the file never existed in this repo) —
this log is its successor. The generator is Python-only by design, so
`frontend.md` stays hand-written. Plan:
`../../docs/plans/2026-07-16-agents-context-docs-replication.md`.

## 14. HIP domain model: parse-time extraction, in-memory dict store, one data-driven UI grid · 2026-07-26

Added `paa_analyzer/hip/` — a structured Host Information Profile model
layered over already-parsed `PACompliance*`/`PAComplianceMp*` log entries —
plus a `GET /hip` + `GET /hip/cycles/{index}/raw` API and a HIP tab in the
frontend. Full design and the numbered decision table (17 entries) this
summarizes: `docs/plans/hip-analytics-foundation.md`.

**Extraction runs at parse time, not lazily.** `build_hip_data()` is called
from `backend/pipeline.py::parse_zip`, before `SessionStore.add_session()`
frees each log source's parsed `entries` list to cut peak memory. A lazy,
on-request extraction would need those entries to still exist, which they
don't past ingest. Cost (accepted): every upload pays for ~6 XML parses
whether or not the HIP tab is ever opened.

**Stored as a plain dict (`SessionStore._hip[sid]`), mirroring `_state`**,
not SQL like the logs table — the data is under 1 MB and always fetched
whole; SQLite's query power would be wasted on a handful of nested-dict rows
and would force an unnecessary JSON round-trip.

**Missing patches are merged into the structured model with a provenance
marker (`patches_source`), but the stored raw XML stays verbatim and
separate.** The `<missing-patches>` element inside the logged `hip-report`
XML is always empty — the `PAComplianceMp` worker computes real patches
~7 s later and splices them into what's actually sent to the gateway. The
structured view reflects what the gateway received; the raw view stays
ground truth for what was logged; neither is synthesized to match the other.

**Hybrid product model:** a uniform product shape (`name`/`version`/`vendor`/
`def_version`/`def_date`) plus a passthrough `attributes` dict holding every
other `Prod`/`ProductInfo` field verbatim. Nothing is dropped when Palo Alto
adds a field to the OESIS payload, and an unrecognized category or attribute
still renders instead of vanishing.

**OPSWAT errors are resolved to products server-side**, via the
`DETECT_PRODUCTS` signature→name map built from the same cycle's log
entries — the error lines identify a product only by OPSWAT signature
number, and the error line's own function-name prefix
(`CollectComplianceDataForDLP`) is actively misleading (a Time Machine
failure logs under it); only the line's `Category:` field is authoritative.
Doing this once in Python, where the OESIS category numbers are already
known, avoids re-deriving it in the UI.

**Status vocabulary is `ok` / `warn` / `unknown` / `not-detected` —
deliberately no `fail`.** The bundle contains no gateway match-criteria
policy, so no HIP pass/fail verdict can ever be truthfully asserted from it
alone; the UI must not imply one exists.

**Status colour tracks `_SEVERITY` ordering (`ok` 0 < `unknown` 1 <
`warn` 2), not visual alarm.** An earlier pass painted `unknown` red (fixed
in `78872b4`), which made an ordinary collection gap look louder than an
actual bad finding and inverted the feature's point. `unknown` now renders
with `--info`; `warn` outranks it because a known-bad value is a firmer,
more actionable finding than one that simply couldn't be queried.

**One data-driven category grid, not per-OS React components.** The
hip-report XML schema is identical on macOS and Windows; the few things that
differ (`host_id` shape, `custom-checks` subtree, product set) are resolved
server-side into explicit fields (`host_id_kind`, `custom_checks.kind`,
`platform`) so the grid component hardcodes no platform assumptions. Two
components would also mean maintaining Windows-specific UI against exactly
one available Windows sample.

**Every HIP test input, Python and frontend, is a redacted real bundle —
never hand-authored.** Frontend fixtures go one step further: they are
*generated* (`frontend/src/test/fixtures/generate-hip-fixture.py`) by running
the real parser over the redacted Python fixtures, not hand-written JSON
imitating parser output. Structural fidelity to Palo Alto's actual output is
the whole value of a HIP fixture; a hand-authored one would just encode this
author's assumptions instead.

**Known, accepted gaps** (both because no available bundle exercises them):
the `custom-checks/registry` branch in `hip/report.py` (Windows analogue of
the macOS `<plist>` shape) is implemented defensively from the plist shape's
symmetry but is untested; a cycle whose `report` is `None` (report XML never
made it into the log, e.g. truncated by rotation) is likewise unexercised
end to end. Both are called out in code comments rather than silently
assumed correct.

## 15. HIP layout v2: folded checklist replaces the 4-column category grid · 2026-07-26

Replaced `CategoryGrid`/`CategoryCard`/`NotDetectedStrip`/`CycleHeader` with
`HipReportHeader`, `SystemCard`, `GatewayCard`, `ComplianceChecklist`
(`ChecklistRow` rows) and `MissingPatchesPanel`. `HipReportPanel` itself is
now thin: it owns only the selected cycle index, no raw-document state.
Full design: `docs/plans/` (layout-v2 task series); this entry records what
changed and why, not the plan.

**Rows fold by default, one uniform row per category regardless of
content.** The old grid rendered every category's full product list at
once, so a 7-category macOS report was a wall of detail on load even when
6 categories were fine. `ChecklistRow` shows only a status dot, name,
one-line verdict, and product/error/patch-count stats until clicked; only
categories the analyst opens grow past a fixed collapsed height.
Empty/not-detected categories recede (dimmed) in place rather than being
pulled into a separate `NotDetectedStrip` — one list, not two, with
opacity carrying the "nothing here" signal.

**Each module owns its own `Grid | XML | JSON` toggle instead of one
page-level toggle.** The old `CycleHeader` toggle switched the *entire*
page between the category grid and two raw-XML blocks, so checking one
module's raw XML hid every other module's data. `ModuleToggle` is now a
prop of `SystemCard`, `GatewayCard`, `ComplianceChecklist`, and
`MissingPatchesPanel` individually — switching one to XML/JSON leaves the
others in Grid. `ComplianceChecklist` and `MissingPatchesPanel` both call
`useHipRaw` with the identical `queryKey: ['hipRaw', sessionId,
cycle.index]`; TanStack Query dedupes that into one request even when both
are in XML mode at once, so the split cost nothing extra over the shared
fetch the old single toggle made.

**Category-level error count is now correct, fixing an invisible-errors
bug.** `hipErrors.ts`'s `categoryErrors`/`unattachedErrors` derive counts
from the cycle's flat `opswat_errors` list, filtered by `category`, not
summed from each product's own `errors` field. The two
`GetMissingPatchesForThisProduct` OPSWAT errors carry no `Signature`, so
they resolve to no product and no `ProductRow` ever rendered them under the
old per-product-sum approach — Patch Management showed 0 errors on a
bundle that actually logged 2. The checklist's `{n} errors` stat is correct
from the start, and the two unattached errors now render explicitly as an
"Other OPSWAT errors" list inside the expanded row instead of vanishing.

**`alignItems: 'start'` on the two-card header grid is necessary but was not
sufficient — `HipCard` must also declare no height of its own.**
`SystemCard` and `GatewayCard` sit in a CSS grid; `alignItems: 'start'`
keeps a card's height content-driven instead of stretching to the row's
`1fr`. The first pass stopped there and the stretch persisted: `HipCard`
declared `height: '100%'` on its antd `Card`, which was inert under the old
grid-item wrapper (`height: auto` on the intervening `<div>`) but, once
`HipReportPanel` made the `.ant-card` itself the direct grid item, resolved
against the row's actual block size — the taller of the two cards — and
filled the shorter one with dead space *inside its own border*, regardless
of `alignItems`. A declared height overrides `align-self`; it doesn't
default to it. The plan's own verification test initially pinned only
`alignItems: 'start'` being present in the source and stayed green while
the header cards visibly stretched — jsdom doesn't compute layout, so the
test asserted a necessary condition and mistook it for a sufficient one.
Fixed in `a6f194e` (drop the height) and `c4feafd` (rewrite the test to
assert `HipCard`'s own inline style has no `height`, the actual mechanism).
Worth remembering for any future card placed directly in a grid.

## 17. Unify HIP and agent-status chrome: one `Panel`, one `ViewToggle` · 2026-07-26

Three defects reported against the HIP and agent-status pages traced to one
root cause: card chrome and view-mode controls were styled inline at each
call site instead of owned by a component, so the same idea drifted every
time it was copied.

**Four card-header treatments existed** — `OverviewCards` (×2),
`IpconfigTab` (×2, one with a mono header font), and HIP's `HipCard` — all
slightly different in size, weight, tracking, and colour. Replaced with one
`Panel` (`frontend/src/components/common/Panel.tsx`), using the treatment
that already shipped in `OverviewCards` as canonical (11px, weight 700,
0.12em tracking, uppercase, `--text-sec`, antd's default header
background/padding, body padding `8px 16px`) — chosen because it was already
live in production, not because it was closest to the `prototype/hip-kit`
mockup (it isn't; that mockup's `.panel-hdr` has its own background, border
and padding that `OverviewCards` never carried). `Panel` renders no wrapper
element of its own: the `.ant-card` it produces must be the direct child of
whatever the call site lays out, which matters concretely for HIP —
`HipReportPanel` places `SystemCard`/`GatewayCard` directly in a CSS grid,
and `HipReportPanel.test.tsx` asserts the `.ant-card` is the grid's direct
child (see decision 15's `HipCard`-height gotcha, which a reintroduced
wrapper would silently revive).

**Two view-mode vocabularies existed** — `Grid | XML | JSON` in HIP's
`ModuleToggle`, `Table | Raw | JSON` in agent-status's `SystemDetails` and
eight other components that had each redeclared the same prop-type union
by hand (plus `RawJsonView`'s own `'Raw' | 'JSON'`). Replaced with one
`ViewToggle` and one exported `ViewMode = 'View' | 'Raw' | 'JSON'`
(`frontend/src/components/common/ViewToggle.tsx`), imported everywhere
instead of redeclared. `View` rather than `Table`/`Grid` because most of
these views aren't tables (a key-value list, a row list, a folded
checklist); `Raw` rather than `XML` because it names "the original
document", and the compliance checklist has two of those (`hip-report` and
`missing-patches`, logged seconds apart by different sources).
`RoutingTableTab`'s `IPv4 | IPv6` control was deliberately left alone — it
filters which rows are shown, it isn't a view mode.

**Three components duplicated their page's section heading** —
`SystemDetails`, `ForwardingTable`, and `PacliTerminal` (the last spelling
it "PACli") each rendered the same title `AgentStatusPage` had already put
above them via `SectionTitle`. `SectionTitle` gained a right-hand slot, the
inner headings were removed, and `AgentStatusPage` took ownership of the
two view-mode states (`detailsView`, `terminalView`) that used to live in
`SystemDetails`/`PacliTerminal`, so the toggle has somewhere to sit on the
now-single heading line. The alternative — moving `SectionTitle` into each
component instead of lifting state to the page — was rejected because it
just relocates the same inconsistency: two sections would still be titled
by the page and three by themselves.

**Two consequences were accepted rather than fixed:**

- `SystemDetails` now returns `null` when a bundle has no `System.*` keys,
  which leaves the page's `SectionTitle` and a live `ViewToggle` rendered
  above empty space. No gating logic was added; the repo owner confirmed
  this can't happen in practice ("system details should always be
  populated, edge case cannot happen").
- HIP's cards lost their header rule, mono header font, and 34px
  min-height, and gained looser `8px 16px` body padding, to match
  `OverviewCards`. This is an intentional visual change to HIP, not a
  regression — the whole point of the unification was that one of the two
  pages' treatment had to give way to the other.

**The platform toggle was removed, not the platform fact.** Requirement 4
of the rework dropped the old page-level Windows/macOS switch — platform is
resolved once at parse time from the bundle contents, so a user-facing
toggle implied a choice that doesn't exist. But the platform is still a
fact worth surfacing: it now renders in `HipReportHeader`'s meta line
(`hip.platform.toUpperCase()`) alongside cycle count, collection and next
check, in the same spot `HipPage`'s old banner used to show it.

**Known, accepted test gaps in the v2 rework** (neither fixture slice
exercises them): `hipVerdict.ts`'s `attrPhrase` falls back to "first
scalar" only when no yes/no attribute is present, but every product in
both fixtures that lacks one has status `unknown`, which short-circuits
`productClause` before `attrPhrase` runs at all — the fallback branch is
implemented but untested. `custom_checks.kind === 'registry'` (the Windows
analogue of the macOS `plist` shape) remains untested in the frontend for
the same reason the backend's `hip/report.py` registry branch is (Decision
14): no available bundle contains one.

**`HostInfoCard`, `CustomChecksCard`, and `MissingPatchesTable` lost their
own `HipCard` chrome.** All three used to wrap themselves in a `HipCard`
with a hardcoded lowercase title. The new layout needs that chrome to carry
a per-module toggle (`SystemCard`/`ComplianceChecklist`/
`MissingPatchesPanel` own it now), and `CustomChecksCard` needed to render
*inside* a `ChecklistRow` where a nested card would be wrong. Rejected:
keeping the inner `HipCard` and hiding it with CSS — that leaves a card
nested inside a card in the DOM for no reason.

## 16. SPA fallback narrowed to extensionless, non-API 404s · 2026-07-26

Added `SpaStaticFiles` (`backend/main.py`), a `StaticFiles` subclass mounted
in place of plain `StaticFiles(html=True)` whenever `frontend/dist` exists.
Discovered while manually verifying the HIP layout v2 rework (`docs/plans/`
Task 9, Step 8): `html=True` maps only a *directory* to its `index.html`, so
a hard refresh or a shared link on any client-side route — `/s/<id>/hip`,
`/logs`, `/dashboard`, `/agent-status` — 404'd, because those paths have no
file on disk and React Router only ever sees them in the browser.

`SpaStaticFiles.get_response` catches the base implementation's 404 and
retries against `index.html`, but only when the path is extensionless and
does not start with `api/`. Both exclusions are load-bearing: a path with a
file extension is asking for a real asset, so a missing bundle file must
stay a 404 rather than return HTML and turn a broken build into a
bewildering JavaScript syntax error; a path under `api/` is an API call, so
a typo'd endpoint must keep the API's own 404 rather than hand a JSON-only
client a page. Rejected: falling back on *any* 404, which would swallow
both of those cases. Covered by `backend/tests/test_spa_routing.py`,
mounting `SpaStaticFiles` over a throwaway temp directory rather than
through `create_app()` (which only mounts anything when a build is
present).

## 17. Dev Compose override ships as a tracked template, not as `docker-compose.override.yml` · 2026-08-06

`docker compose up` builds only when no image with the configured tag exists.
`docker-compose.yml` pins `image: paa-analyzer:latest` alongside `build: .`, so
once that tag exists locally every subsequent `up` reuses it and never re-reads
the source — edits appeared to vanish until someone remembered `--build`.

`docker-compose.dev.yml` fixes the inner loop instead of the symptom: it
bind-mounts `backend/` and `paa_analyzer/` over the copies the Dockerfile
`COPY`s in, and replaces the production CMD with uvicorn `--reload`. This works
because `uv sync` installs the project **editable** — site-packages holds only
`_editable_impl_paa_analyzer.pth` pointing at `/app`, so `backend` and
`paa_analyzer` resolve to `/app/backend` and `/app/paa_analyzer`, exactly the
mount targets. Verified end-to-end: a host-side edit to an existing endpoint was
served by the container ~1s later, with no rebuild. `watchfiles` is present in
the runtime image despite `uv sync --no-dev`, because it arrives via the
`uvicorn[standard]` extra, which is a *main* dependency.

**Why a tracked `docker-compose.dev.yml` plus a gitignored copy, rather than
committing `docker-compose.override.yml` itself.** `docker-compose.override.yml`
is the filename Compose merges with no flags — committing it would make *every*
`docker compose up`, anywhere, silently run a dev configuration with the source
bind-mounted and the reloader attached. Keeping the override filename gitignored
makes activation an explicit local `cp`, while the template still travels with
the repo. Rejected: `-f docker-compose.yml -f docker-compose.dev.yml`, which
keeps the dev loop flag-laden and easy to forget; and Compose `develop.watch`,
which rebuilds the image per change rather than avoiding the rebuild.

`restart: "no"` overrides the base file's `unless-stopped` — while editing, an
import-time crash should leave the container down with a readable traceback
rather than restart-looping over it.

**Scope: backend only.** The UI is a static `vite build` written to
`/app/frontend/dist` at image build time (there is no node process in the
runtime image to reload), so frontend changes still need `--build`, or the
existing host-side `npm run dev` on :5173 proxying `/api` to :8000.

**Gotcha found while verifying this**, worth recording because it will mislead
the next person testing a route: appending a new `@app.get(...)` *after*
`create_app()` returns produces a 404, not a working route. Decision 16's
`SpaStaticFiles` is mounted at `/` inside `create_app()`, Starlette matches
routes in registration order, and that mount 404s anything under `api/`. Probe
hot reload by changing an **existing** endpoint's behaviour instead.

## 18. Dependabot targets `develop` and auto-merges patch/minor only · 2026-08-17

Both Dependabot ecosystems (`uv`, `github-actions`) now set
`target-branch: "develop"`. Without it Dependabot opens against the default
branch, which is `main` — and `main` is protected by the `block-main-push` and
`main-protection` rulesets, so every dependency PR landed on a branch that
cannot take direct integration. Integration happens on `develop`; that is where
updates belong.

`.github/workflows/dependabot-auto-merge.yml` then enables GitHub's own
auto-merge on those PRs. It merges nothing itself — auto-merge waits for the
checks `develop` marks required (Lint, Type-check, Tests (Python 3.14), Docs,
Gitleaks) and squashes only once they are all green. **The required-checks list
is load-bearing:** drop it and auto-merge has nothing to wait for, so this
becomes "merge immediately". For the same reason the trigger is scoped to
`branches: [develop]` — a Dependabot PR against any unprotected branch is left
alone rather than merged unguarded.

Patch and minor only. A major bump is where a green suite is least reassuring
(breaking changes surface at runtime, not in CI), so those stay open and get a
comment saying so — silence would read identically to broken automation. For a
grouped update `fetch-metadata` reports the group's highest semver change, so
one major holds the whole PR back.

The `permissions:` block grants `contents: write` / `pull-requests: write`
because Dependabot-triggered runs get a read-only `GITHUB_TOKEN` by default.
The job never checks out or executes the PR's code, so the elevated token never
runs anything Dependabot proposed.

**Known gap:** `frontend/package-lock.json` is not covered by any ecosystem, so
npm dependencies are not tracked. Adding `npm` is deliberately deferred — `ci.yml`
runs no frontend job, so an npm PR would auto-merge against a suite that never
builds or tests the frontend. Wire up frontend CI first.

Mirrors the setup in the phantasos repo.
