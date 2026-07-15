# Changelog

## [0.0.1] - 2026-07-15

### Added

- **Full-stack diagnostic tool**: Upload a Prisma Access Agent troubleshooting ZIP, parse it, view logs/state/dashboard in a React frontend
- **46 parsers**: 27 cross-platform (Pacli Output, structured logs, traffic JSON, remote shell) + 19 Windows-specific (systeminfo, ipconfig, route print, firewall rules, installed drivers, netstat, DNS cache, power config, event viewer, PAUI, DEM, Chromium logs)
- **Multi-OS support**: Auto-detects macOS vs Windows bundles from directory structure; platform stored in session metadata
- **Agent Status page**: Overview cards (OS, architecture, hostname, agent state), module status badges, forwarding profile with hitcount links, PaCli terminal with autocomplete
- **System Details tabs**: macOS (System Extensions, Autostart Programs, Routing Table) and Windows (Network Config, Routing Table, Firewall Rules, Network Connections, Installed Apps, Installed Drivers)
- **Unified routing table**: Single component auto-detects macOS (flags) vs Windows (netmask/CIDR) format; IPv6 with interface name resolution
- **Log Viewer**: Sidebar with source grouping, custom view multi-select, search with 150ms debounce, level/date filtering, resizable columns, expandable rows with raw/beautified JSON toggle
- **Upload with SSE progress**: Real-time parsing progress streamed to the browser
- **Backend testing**: 403 pytest tests at 92% coverage (parsers, store, pipeline, API, CLI, e2e with real ZIPs)
- **Frontend testing**: 65 Vitest tests (API client, hooks, format detection, component logic) with MSW for API mocking
- **CLI tool**: `paa-parse <zip> [output/]` for offline parsing to JSON files
- **Version display**: Version from pyproject.toml shown in TopNav and FastAPI /docs

### Fixed

- Windows IPv6 routing table: correct field parsing (If/Metric/Destination/Gateway), multi-line continuation support, interface name resolution from Interface List
- Routing table crash on IPv6 tab click when format detection checked current family instead of IPv4
- Raw/JSON view crash: RawJsonView now handles undefined entries and memoizes JSON.stringify
- System Details LABELS key mismatch: fixed state key names to match backend output
