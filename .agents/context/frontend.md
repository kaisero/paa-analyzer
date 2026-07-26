# frontend

Validated against cc3f0cc on 2026-07-26 · Purpose: the React SPA in `frontend/` — an Ant Design 6 UI over the `/api/v1` REST/SSE API, with its own npm/Vite/Vitest toolchain.

## Purpose & responsibilities

`frontend/` is the web UI: upload a troubleshooting bundle, then explore the
parsed session through a log viewer, an agent-status page, a dashboard, and a
HIP (Host Information Profile) page. It is a plain SPA — all data comes from
the backend's `/api/v1` API; the frontend holds no parsing or analysis logic
beyond presentation (the one exception being the SSE progress parsing in
`useUploadWithProgress`).

Stack (see `frontend/package.json`, name `frontend-antd`): React 19 +
TypeScript, Vite 8, **Ant Design 6** (`antd` + `@ant-design/icons` — NOT
Tailwind), TanStack Query 5, react-router-dom 7, recharts (dashboard charts),
dayjs. Test stack: Vitest 4 (jsdom) + MSW 2 + Testing Library.

## How it works

### Design system (`src/styles/global.css`, `src/contexts/ThemeContext.tsx`, `src/main.tsx`)

The UI uses a Palo Alto brand-aligned design system: PA orange (`#FA582D`) as
the primary accent, rectangular borders (`borderRadius: 0`), a dark base
(`#0C0F14`), Inter for UI copy, and JetBrains Mono for technical values.

**CSS custom properties** (`global.css`): a full token set declared on `:root`
for dark mode — `--accent`, `--accent-hover`, `--accent-dim`, `--accent-border`,
`--bg`, `--surface`, `--elevated`, `--border`, `--border-soft`, `--text`,
`--text-sec`, `--text-dim`, `--row-alt`, `--row-hover`, and per-severity
triples (`--err`/`--err-bg`/`--err-border`, `--warn-*`, `--info-*`, `--dbg-*`,
`--ok`/`--ok-bg`). `[data-theme="light"]` overrides every variable for the light
palette. Global antd overrides live here too: the active menu bar moves from
right to left (`::after { display:none }` + left-border via `.ant-menu-inline`),
tags are uppercased, and the expand-icon column is zeroed out.

**ThemeContext** (`src/contexts/ThemeContext.tsx`): provides `isDark` and
`toggle()` via React context; persists the choice to `localStorage("theme")` and
sets `data-theme` on `document.documentElement`. An inline script in
`index.html` reads `localStorage` before React hydrates to prevent a light-flash
on page load when dark mode is active.

**ConfigProvider** (`main.tsx`): `AppWithTheme` calls `useTheme()` and passes
`darkTokens` or `lightTokens` to antd `ConfigProvider`. Both token configs set
`borderRadius: 0`, map `colorPrimary` to the accent orange, and override
`Layout`, `Menu`, `Table`, `Tabs`, `Input`, `Button`, `Tag`, `Card`, `Select`,
and `DatePicker` component tokens to match the design system.

### Routing and shell (`src/App.tsx`, `src/main.tsx`)

`main.tsx` wraps the app in `ThemeProvider` and then `AppWithTheme`, which
resolves the current theme and passes it to antd `ConfigProvider`.
`App.tsx` sets up the `QueryClient` (staleTime 30 s, retry 1) and the routes:

- `/` — `UploadPage`.
- `/s/:sessionId` — `AppShell` layout route (`components/layout/`: `AppShell`
  with `Sidebar` + `TopNav` around an `Outlet`); children: index → `LogViewer`,
  `dashboard` → `DashboardPage`, `agent-status` → `AgentStatusPage`,
  `hip` → `HipPage`.
- `/proto` — `AntdProto` (design iteration sandbox; ships in the SPA but not
  linked from the main nav).
- `*` — redirect to `/`.

### API layer (`src/api/`)

- `client.ts` — a minimal `fetch` wrapper (`api.get/post/del`); non-2xx
  responses throw `ApiError(status, detail)` with the FastAPI `detail` string.
  URLs are relative (`/api/v1/...`) — no base-URL config.
- `hooks.ts` — one TanStack Query hook per endpoint: `useSessions`,
  `useSession`, `useCreateSession`, `useDeleteSession`, `useLogSources`,
  `useLogs` (builds the filter query string; `placeholderData` keeps the
  previous page while fetching), `useStateKeys`, `useStateBatch`,
  `useStateEntry`, `useForwardingProfile`, `useHip`, `useHipRaw` (the latter
  takes an `enabled` flag — the raw endpoint is only fetched when the HIP
  panel's XML toggle is selected). Mutations invalidate the `['sessions']`
  query.
- `types.ts` — TypeScript mirrors of the backend pydantic models (`Session`,
  `LogSource`, `LogEntry`, `StateEntry`, …) and the `DataResponse` /
  `PaginatedResponse` envelopes. Hand-maintained — no codegen; change both
  sides together.

### Upload with progress (`src/hooks/useUploadWithProgress.ts`)

The one endpoint that bypasses `client.ts`: it `fetch`es
`POST /api/v1/sessions/upload` and hand-parses the SSE body from
`res.body.getReader()` (splitting on `\n\n`, matching `data:` lines), driving
`{status, stage, progress, detail}` state until the `complete` event carries
the session and the page navigates to `/s/{id}`.

### Log viewer (`src/components/log-viewer/`, `src/hooks/useLogViewer.ts`)

`useLogViewer` owns all viewer UI state — active source, level/search/date
filters, sort direction, pagination, expanded/raw/beautified row sets, column
definitions (visibility + resizable widths), and the custom multi-source view —
and seeds source/search from URL search params. `LogViewer` composes
`LogToolbar`, `LogTable`, and `LogPagination` around `useLogs`.

### Layout shell (`src/components/layout/`)

`TopNav` is a plain `<header>` (52 px, no antd `Layout.Header`): PA brand-mark
square on the left, "PAA ANALYZER" wordmark, underline `Tabs` for
Log Viewer / Dashboard / Agent Status navigation, a session ID chip, and the
dark/light theme toggle button (calls `useTheme().toggle()`).

`Sidebar` has a "LOG SOURCES" uppercase heading above the antd `Menu`; each
source item shows an error/warning count badge (`<Tag color="error|warning">`)
instead of a dot indicator. A side-footer below the menu shows aggregate
error and warning totals for the session.

`AppShell` is plain flex `<div>` containers (no antd `Layout`/`Layout.Content`).

### Shared chrome (`src/components/common/`)

Two components own all panel/view-mode chrome app-wide; nothing else should
restyle a `Card` or hand-roll a Grid/Table/XML-style toggle at a call site —
that inline-styling-per-call-site pattern is exactly what drifted into four
different card-header treatments and two different view-mode vocabularies
across HIP and agent-status (see `decisions.md`).

- **`Panel.tsx`** — the one card used by every panel in the app (HIP's
  `SystemCard`/`GatewayCard`/`ComplianceChecklist`/`MissingPatchesPanel`,
  agent-status's `OverviewCards`/`IpconfigTab` and siblings). A thin wrapper
  around antd `Card` (`size="small"`) fixing the header treatment — 11px,
  weight 700, 0.12em tracking, uppercase, `--text-sec`, antd's default header
  background/padding — and a `bodyPadding` prop (default `8px 16px`; pass `0`
  for a body that renders its own full-bleed rows). Takes `extra` for a
  right-aligned slot (a `ViewToggle`, a count, a version tag).
  **`Panel` renders no wrapper element of its own** — the `.ant-card` it
  renders is the direct child of whatever the call site lays out. This is
  load-bearing for HIP: `HipReportPanel` places `SystemCard`/`GatewayCard`
  directly in a CSS grid (`display: grid; alignItems: 'start'`), and
  `HipReportPanel.test.tsx` asserts the `.ant-card` is the grid's direct
  child — an extra wrapper `<div>` here would silently break that alignment
  fix (see the `Panel`-height gotcha below, and decision 15). Layout
  concerns (grid placement, margins) belong at the call site, never inside
  `Panel`.
- **`ViewToggle.tsx`** — the one view-mode control and its exported
  `ViewMode = 'View' | 'Raw' | 'JSON'` union. `View` names the structured
  rendering (a table, a key-value list, a folded checklist — most of these
  panels are not literally tables, hence `View` rather than `Table`/`Grid`);
  `Raw` names the original document the parser read (`Exclude<ViewMode,
  'View'>` where only Raw/JSON apply, e.g. `RawJsonView`). Every component
  that has a view mode imports `ViewMode` from here rather than redeclaring
  the union — it was copied by hand into nine agent-status components plus
  HIP's old `ModuleToggle` before this existed, and the vocabulary drifted
  every time it was copied. `RoutingTableTab`'s `IPv4 | IPv6` control is not
  a `ViewToggle` — it filters which rows are shown, it doesn't change how a
  fixed set of data is rendered, so it deliberately stays a plain
  `Segmented` outside this convention.

**Section titles belong to the page, not the component.** `SectionTitle` (a
small local component in `AgentStatusPage.tsx`) takes an optional `right`
slot; `AgentStatusPage` renders the heading once and passes a `ViewToggle`
into that slot for the sections that need one (`System Details`, `PACLI
Terminal`), which is also why `AgentStatusPage` owns `detailsView`/
`terminalView` state via `useState` instead of `SystemDetails`/
`PacliTerminal` owning it locally — three components (`SystemDetails`,
`ForwardingTable`, `PacliTerminal`) used to render their own duplicate
heading below the page's, one of them misspelling it ("PACli"). The rule
this leaves behind: pages own section titles, components own their content
underneath.

### Agent status (`src/components/agent-status/`, `src/pages/`)

`AgentStatusPage` adds a diagnostic report header ("Prisma Access Agent —
Diagnostic Report" + session ID) and `<SectionTitle>` orange-left-border
dividers above each section. It assembles `OverviewCards`, `FeaturesPanel`,
`ForwardingTable` (forwarding-profile rules + hitcount links into the log
viewer), `PacliTerminal` (command replay with autocomplete over
`useStateKeys`/`useStateEntry`), and `SystemDetails` — OS-adaptive tabs keyed
off the session's `platform` (macOS: `SystemExtensionsTab`, `LaunchctlTab`;
Windows: `FirewallRulesTab`, `InstalledDriversTab`, `IpconfigTab`,
`NetstatTab`, `RoutingTableTab`, `InstalledAppsTab`), plus `RawJsonView`.
`SystemDetails` and `PacliTerminal` take their `viewMode` as a prop from the
page rather than owning it (see "Shared chrome" above); `SystemDetails`
returns `null` when a bundle has no `System.*` keys, which leaves the page's
`SectionTitle` and a live, functioning toggle sitting above empty space —
accepted rather than gated, since a bundle with zero `System.*` keys isn't
expected to occur in practice.

`OverviewCards` uses a dot-indicator status pill (8 px circle + colored text)
instead of antd `Tag` for connection state. `FeaturesPanel` is an antd `Table`
(Module / Status / Details columns) rather than a flex card grid.

`DashboardPage` renders summary counts and recharts charts.

### HIP page (`src/components/hip/`, `src/pages/HipPage.tsx`)

`HipPage` fetches the session's `HipData` via `useHip`, shows a loading
spinner, and — keyed off `cycles.length === 0` rather than an empty
`gateways` list, since a bundle can have HIP cycles with no gateway rows —
an explained empty state instead of hiding the tab; the top-level nav tab is
always visible (`TopNav`'s `hip` entry) so a missing HIP section reads as
diagnostic, not broken. With cycles present the page is just a scroll
container around `HipReportPanel` — the page itself owns no HIP-specific
markup, not even a title.

`HipReportPanel` is thin: it owns only which cycle is selected (defaulting
to `cycles[0]`, the newest) and lays out four independent modules, each of
which manages its own view mode and (where relevant) its own raw-document
fetch:

- `HipReportHeader` — title, cycle `Select` (label = generate time, newest
  first), and the counts line (warn/unknown/errors/missing-patches/cycle
  duration plus platform, cycle count, collection, next check and dispatch
  status). "Cycle Duration" renders `"<n>s"` or a dash (never a bare `0`,
  which would read as a real zero-second cycle instead of "never logged").
  `fmtCycleTime` is a module-private formatter now — it was exported only for
  the deleted `CycleHeader`'s tests and has no other consumer.
- `SystemCard` / `GatewayCard` — the two header cards, laid out
  `display: grid; alignItems: 'start'` side by side. `alignItems: 'start'`
  keeps a card's height content-driven instead of stretching to the grid
  row's `1fr`, but it is necessary, not sufficient — see the `Panel`
  gotcha below for the other half of this fix. `SystemCard` no longer passes
  a `wide` prop to `HostInfoCard`: nothing else ever used the four-column
  "wide" field layout it existed for, and in a half-width header card it
  halved the row height and maximised the gaps instead of helping. Both
  render via the shared `Panel` (see "Shared chrome" above) with their own
  `ViewToggle` in `Panel`'s `extra` slot — `SystemCard` offers `View | JSON`,
  `GatewayCard` the same.
- `ComplianceChecklist` — the checklist module: one folded `ChecklistRow`
  per category plus a synthetic "Custom Checks" row, each row showing a
  `StatusDot`, a one-line verdict (`hipVerdict.ts`), and product/error/patch
  counts; expanding a row reveals its `ProductRow`s, any unattached OPSWAT
  errors (see below), and — if the category carries missing patches — an
  inline `MissingPatchesTable`. Owns Expand All / Collapse All and its own
  `View | Raw | JSON` `ViewToggle` (shared component, see "Shared chrome"
  above); calls `useHipRaw` itself when Raw is selected. Its title stays
  "Compliance Checklist" in every view mode — the category count renders as
  a separate note beside the toggle instead of being baked into the title,
  so switching modes doesn't change the header's shape. Only the View mode
  bails out on a cycle with no `report` (truncated by log rotation); Raw and
  JSON render regardless, because a truncated cycle is exactly when the raw
  document matters most. `MissingPatchesPanel` follows the identical
  fixed-title/separate-count pattern.
- `MissingPatchesPanel` — all missing patches across categories in one
  table (with a `categoryNames` column), plus its own `ViewToggle` and its
  own `useHipRaw` call. Both this and `ComplianceChecklist` share the
  identical `queryKey: ['hipRaw', sessionId, cycle.index]`, so TanStack
  Query dedupes them into one request even when both are in Raw mode at
  once — neither owns the raw document, and selecting Raw in one does not
  cancel the other's fetch. Covered by a test that flips both modules to Raw
  in the same tick (`fireEvent`, not `userEvent`, so no await separates the
  two clicks) and asserts exactly one network request.
- `hipErrors.ts` — `categoryErrors`/`unattachedErrors`: per-category error
  counts derived from the cycle's flat `opswat_errors` list, not summed from
  `product.errors`. The `GetMissingPatchesForThisProduct` OPSWAT error
  carries no `Signature`, so it resolves to no product — summing per-product
  counts silently drops it (this was the "Patch Management shows 0 errors
  when it actually has 2" bug the checklist rework fixes). Unattached errors
  render as their own "Other OPSWAT errors" list inside the expanded row.
- `hipVerdict.ts` — pure synthesis of the one-line category/custom-checks
  verdict text shown next to each `StatusDot`.
- `ChecklistRow` — one folded row; collapsed height is uniform regardless of
  content, expanding reveals `children` below the summary line.
- Each module's `View | Raw | JSON` (or `View | JSON`) control is not its own
  component — it's the shared `ViewToggle` (`../common/ViewToggle.tsx`; not
  a page-level toggle — each module's view mode is independent). HIP used to
  have its own `ModuleToggle` here; it's deleted, replaced by the shared
  component described under "Shared chrome" above.
- `HostInfoCard` — host-info fields (no `Panel` chrome of its own — it
  renders inside `SystemCard`/`ChecklistRow`, and no `wide` prop — see
  `SystemCard` above), with interfaces collapsed behind a "show N
  interfaces" `.hip-ghost-btn` toggle.
- `CustomChecksCard`, `MissingPatchesTable` (no `Panel` chrome of their own
  either — the parent module owns the card), `RawBlock` (a labelled
  raw-document block; distinct from `RawJsonView` because HIP has two
  separate raw documents — hip-report from `PACompliance`, missing-patches
  from `PAComplianceMp` — logged seconds apart by different sources, not one
  JSON blob). The shared card chrome the modules render into is `Panel`
  (`../common/Panel.tsx`; HIP's own `HipCard` is deleted, see "Shared
  chrome" above).
- Shared HIP CSS (`global.css`): `.hip-ghost-btn` (checklist Expand/Collapse
  All, gateway show-all, host-info interfaces toggle — a bordered
  transparent button with a `:hover` state inline styles can't express),
  `.hip-row` (border-bottom between checklist rows, none on `:last-child`),
  `.hip-row-summary:hover` (row hover affordance). Added because inline
  `style` objects can't express `:hover` or `:last-child`; before this, two
  prototype rules were silently dropped.
- `StatusDot` (`src/components/common/`) — the shared 4-state indicator
  (`ok`/`warn`/`unknown`/`not-detected`) using `--ok`/`--warn`/`--info`/
  `--text-dim`, with `status_reason` as its tooltip. Its colour scale tracks
  the backend's `_SEVERITY` ordering (`ok` 0 < `unknown` 1 < `warn` 2) —
  `unknown` uses `--info`, not `--err`, so a collection gap doesn't read
  louder than an actual bad finding.

One data-driven checklist serves both macOS and Windows reports — the XML
schema is identical across platforms; OS-specific semantics (`host_id_kind`,
`custom_checks.kind`) are already resolved server-side, so no component
hardcodes a platform assumption.

**Fixture generation.** Unlike every other frontend fixture, `hip.json`
(`src/test/fixtures/hip.json`) is not hand-written: it is generated by
`src/test/fixtures/generate-hip-fixture.py`, which runs the real
`paa_analyzer.hip.build_hip_data()` over the same redacted Python fixtures
`backend/tests/test_hip_build.py` uses (`backend/tests/fixtures/hip/`) and
writes the structured model (`macos`/`windows`/`empty`, `_raw` stripped) plus
the raw XML (`macosRaw`/`windowsRaw`) to one JSON file. `handlers.ts` serves
it from `hip.json`, never inline data. Regenerate with `uv run python
frontend/src/test/fixtures/generate-hip-fixture.py` after any HIP fixture or
model-shape change; do not hand-edit the output.

### Dev vs production wiring

In development `vite.config.ts` proxies `/api` to `http://localhost:8000`
(run `uv run paa-server` alongside `npm run dev`). In production the backend
serves `frontend/dist` as static files — one process, one port. `vite.config.ts`
also defines `__APP_VERSION__` from `package.json` (surfaced via
`src/constants.ts`).

### Tests (`src/test/`, `vitest.config.ts`)

Vitest runs in jsdom with `src/test/setup.ts`: jest-dom matchers, a
`window.matchMedia` stub (antd responsive layouts need it), and the MSW server
lifecycle with `onUnhandledRequest: 'error'`. `handlers.ts` holds the MSW
route handlers plus data factories (`makeSession`, `makeLogSource`, …);
`wrapper.tsx` provides `renderWithProviders` (fresh `QueryClient` with retries
off + `MemoryRouter`). Tests are colocated (`src/**/*.test.{ts,tsx}`).

## Build / run pointers

All from `frontend/`:

- `npm run dev` — Vite dev server on :5173, proxying `/api` to :8000.
- `npm run build` — `vitest run && tsc -b && vite build` → `dist/` (tests and
  type-check gate the build).
- `npm test` (watch) / `npm run test:run` (single) / `npm run test:coverage`.
- `npm run lint` — eslint (flat config, `eslint.config.js`).

## Gotchas / invariants

- **This doc is hand-maintained — no generated blocks.** The context-docs
  generator (`tools/context_docs.py`) is Python-AST-only by design; keep this
  narrative current by hand when the frontend changes.
- **The frontend is outside the Python quality gates.** `nox -s gate`,
  pre-commit hygiene hooks, and codespell all exclude `frontend/`; CI has no
  frontend job. The only automated frontend test run is the one embedded in
  `npm run build` (and hence the Docker image build) — a failing Vitest suite
  blocks the build.
- **`types.ts` is a hand-mirror of the backend models.** An API/model change in
  `backend/models/` needs a matching edit here; nothing enforces it.
- **MSW errors on unhandled requests** (`onUnhandledRequest: 'error'`): any
  fetch a test triggers must have a handler in `handlers.ts` or an override.
- **antd needs the `matchMedia` stub** in jsdom — don't remove it from
  `setup.ts`.
- **Releases bump two versions**: `pyproject.toml` AND `frontend/package.json`
  (see `CLAUDE.md` "Releasing"); the UI shows `__APP_VERSION__` from the latter.
- **Design tokens must be semantic, not literal.** Use `--accent`, `--err`,
  `--ok`, `--info`, `--text-sec`, `--text-dim`, etc. from `global.css`. The old
  cyan aliases (`--blue`, `--green`, `--orange`, `--text2`, `--text3`) no longer
  exist — using them compiles fine but renders nothing.
- **antd active menu bar is on the left.** Global CSS in `global.css` suppresses
  the default right-side `::after` bar and adds a left-border + padding shift for
  `.ant-menu-inline .ant-menu-item-selected`. Don't fight this with inline styles.
- **Table expand icon column.** Any antd `Table` with `expandable` will render a
  zero-width ghost column. It's hidden globally via `.ant-table-row-expand-icon-cell`
  and `.ant-table-expand-icon-col` in `global.css`; don't add per-table workarounds.
- **`hip.json` is generated, not hand-written.** Never edit
  `src/test/fixtures/hip.json` directly, and never add a HIP test case with
  inline mock data imitating parser output — regenerate the fixture from the
  redacted Python logs instead (see the HIP page section above). This mirrors
  the project-wide rule that every HIP test input, frontend or backend, must
  trace back to a real bundle.
- **HIP status colour must track the backend's severity ordering.** `warn`
  outranks `unknown` (`StatusDot`'s `COLOR` map uses `--info` for `unknown`,
  not `--err`) because a known-bad value is a firmer finding than one that
  simply couldn't be collected — painting `unknown` as loud as `warn`/error
  would invert that.
- **`Panel` must never declare its own `height`, and must never wrap its
  `Card` in an element of its own.** `Panel`'s predecessor, `HipCard`, used
  to set `height: '100%'` on the antd `Card`; that was inert while the grid
  item was a wrapper `<div>` (`height: auto`), but once `HipReportPanel`
  made the `.ant-card` itself the direct CSS grid item, the percentage
  resolved against the grid *row's* height (the taller of
  `SystemCard`/`GatewayCard`) and filled the shorter card with dead space
  inside its own border — a declared height wins over the container's
  `align-self`/`alignItems: 'start'`, it doesn't just default to it. Fixed
  in `a6f194e`; the same trap will recur for any future card placed
  directly in a CSS grid, so don't re-add a height to `Panel`, and don't add
  a wrapper element around the `Card` it renders — either one would put a
  new `height: auto` element back between the grid and the card and revive
  the bug. `HipReportPanel.test.tsx` asserts the `.ant-card` is the grid's
  direct child specifically to guard this.

## See also

- `backend.md` — the API this SPA consumes (routes, envelopes, SSE upload).
- `index.md` — entry point for all agent-context docs.
- `../../docs/architecture.md` — the human-facing architecture narrative,
  including the frontend request-flow diagrams.
- `../../CLAUDE.md` — working agreement, including the read-before /
  update-after contract for these docs.
