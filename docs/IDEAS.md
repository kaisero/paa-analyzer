# State Viewer — Feature Ideas

Brainstormed 2026-04-07. Data availability refers to what `paa_analyzer/parsers.py` already extracts.

---

## Already parsed but not displayed

### 1. Gateway List
- **Data source:** `Agent.Core.gateways_list` (parser: `gateway_list`)
- Agent location, gateway names/priorities/addresses
- Shows the failover chain — is the agent hitting the right gateway or stuck on a low-priority one?

### 2. HIP Status
- **Data source:** `Agent.Compliance.hip_status` (parser: `hip_status`)
- Collection name, next check time, per-gateway last-report timestamps
- Critical for compliance tickets: "when did HIP last report to this gateway?"

### 3. Protection Modules
- **Data source:** `Agent.Security.protect` (parser: `protection`)
- Array of `{name, state}` — quick posture check: are all protection modules active?

### 4. EPM Commands
- **Data source:** `Agent.Core.epm_commands` (parser: `epm_commands`)
- Command ID, state (pending/completed), received/finished timestamps
- Answers "did the EPM command reach the agent and execute?"

### 5. System Extensions (macOS)
- **Data source:** `System.Core.system_extensions` (parser: `system_extensions`)
- Network/security extensions with enabled/active state, version, bundle ID
- Top troubleshooting target on macOS — extensions failing to load is a common issue class

### 6. Traffic RDNS Cache
- **Data source:** `Agent.Networking.traffic_rdns` (parser: `traffic_rdns`)
- CNAME and IP records
- Useful for "why is this domain being matched/not matched by a forwarding rule?"

### 7. Installed Applications
- **Data source:** `System.Core.installed_applications` (parser: `app_list`)
- Relevant when forwarding rules reference source apps

---

## New derived / analytical views

### 8. Health Check / Diagnostic Summary
Run heuristic rules across all state and flag issues automatically. Examples:
- Agent state is not "connected"
- Tunnel is down but forwarding rules expect tunnel
- System extension is not active
- HIP hasn't reported in >24h
- EPM commands stuck in "pending"
- Forwarding rules with 0 hitcount (dead rules)
- GP status mismatch with agent mode

**Highest-value addition** — a single panel that says "here are the 3 things that look wrong."

### 9. Connection Timeline
- Visualize connection history as a timeline/swimlane (connect → auth → tunnel up → disconnect)
- Data already parsed from `pacli_connection_history.log`
- Quick picture of stability: is the agent reconnecting every 5 minutes?

### 10. Network Topology View
- Combine gateway list + forwarding profile + tunnel status into a simple diagram
- Agent → Tunnel → Gateway (name, IP) with forwarding rule counts per path type
- Gives spatial understanding of traffic flow

### 11. Log Cross-Reference Badges
- On each state panel, show a count of ERROR/WARN log entries from the relevant component's log files
- E.g., the Tunnel card shows "12 errors in NetworkExtension.log"
- Clicking navigates to the Log Viewer pre-filtered

### 12. Config Drift Detector
- Compare "last successful config" timestamp to bundle generation time to surface stale config
- If multiple snapshots exist, surface what changed recently (forwarding rules modified, agent version changed, etc.)
