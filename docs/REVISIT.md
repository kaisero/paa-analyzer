# Deferred Features — Revisit Later

Items that were implemented in the backend (parsers exist, data is stored) but not yet surfaced in the Agent Status UI. These can be added as dedicated table view tabs when needed.

## Windows System Details — Hidden Tabs

The following Windows state keys are parsed and available via the API but not shown as tabs in System Details. They can be accessed via the PACli Terminal (JSON view) or the state API directly.

| State Key | Data | Why Deferred |
|-----------|------|-------------|
| `System.Core.systeminfo` | Windows systeminfo output (OS, hardware, hotfixes, NICs) | Data already shown in OverviewCards; raw text available in PaCli Terminal |
| `System.Networking.dns_cache` | DNS cache entries from `ipconfig /displaydns` | Rarely needed for troubleshooting; raw view in terminal is sufficient |
| `System.Core.current_user_groups` | Security groups from `whoami /groups` | Low priority; raw view sufficient |
| `System.Core.user_sessions` | RDP/console sessions from `query session` | Low priority; raw view sufficient |
| `System.Power.powercfg_all` | Available sleep states | Niche use case; raw view sufficient |
| `System.Power.powercfg_query` | Power scheme settings | Niche use case; raw view sufficient |
| `System.Power.power_history_24h` | Power/wake events from Event Log | Could be useful for sleep/wake debugging; consider adding later |
| `System.Networking.nslookup_google_com` | DNS resolution test | Single data point; raw view sufficient |
| `System.Networking.ping_8_8_8_8` | Connectivity test | Single data point; raw view sufficient |
| `System.Core.windows_event_viewer_logs` | Windows Event Viewer export (XML) | Large dataset (34 events); could add a dedicated table view later |

## macOS System Details — Potential Additions

| State Key | Data | Status |
|-----------|------|--------|
| `System.Networking.ifconfig` | Network interface config | Currently raw_text only; could add a parsed table view |
| `System.Networking.external_ip` | External IP address | Single value; shown in OverviewCards when available |
| `System.Core.uname` | Kernel version | Already shown in OverviewCards |
