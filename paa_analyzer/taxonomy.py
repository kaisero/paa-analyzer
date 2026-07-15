"""Taxonomy: maps every known file in the troubleshooting bundle to its type, module, and component."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class FileMeta:
    data_type: str  # "state" or "log"
    module: str  # "Agent" or "System"
    component: str  # "Core", "Security", "Networking", etc.
    parser: str  # parser function name to use


# Pacli Output files — all state snapshots except connection_history and event which are logs
PACLI_FILES: dict[str, FileMeta] = {
    "pacli_status.log": FileMeta("state", "Agent", "Core", "key_value"),
    "pacli_epm_status.log": FileMeta("state", "Agent", "Core", "key_value"),
    "pacli_version.log": FileMeta("state", "Agent", "Core", "key_value"),
    "pacli_proxy_status.log": FileMeta("state", "Agent", "Core", "key_value"),
    "pacli_tunnel.log": FileMeta("state", "Agent", "Networking", "key_value"),
    "pacli_ep.log": FileMeta("state", "Agent", "Explicit Proxy", "key_value"),
    "pacli_browser_status.log": FileMeta("state", "Agent", "Core", "key_value"),
    "pacli_captive_portal.log": FileMeta("state", "Agent", "Core", "key_value"),
    "pacli_adns.log": FileMeta("state", "Agent", "ADNS Resolver", "key_value"),
    "pacli_dpa_project_list.log": FileMeta("state", "Agent", "Dynamic Privileged Access", "key_value"),
    "pacli_adem_status.log": FileMeta("state", "Agent", "ADEM", "key_value"),
    "pacli_dlp_status.log": FileMeta("state", "Agent", "DLP", "key_value"),
    "pacli_traffic_show.log": FileMeta("state", "Agent", "Networking", "forwarding_profile"),
    "pacli_gateways_list.log": FileMeta("state", "Agent", "Core", "gateway_list"),
    "pacli_hip_status.log": FileMeta("state", "Agent", "Compliance", "hip_status"),
    "pacli_protect.log": FileMeta("state", "Agent", "Security", "protection"),
    "pacli_epm_commands.log": FileMeta("state", "Agent", "Core", "epm_commands"),
    "pacli_traffic_rdns.log": FileMeta("state", "Agent", "Networking", "traffic_rdns"),
    "pacli_connection_history.log": FileMeta("log", "Agent", "Core", "connection_history"),
    "pacli_event.log": FileMeta("log", "Agent", "Core", "event_table"),
}

# System info text files — all state
SYSTEM_INFO_FILES: dict[str, FileMeta] = {
    "sw_vers.txt": FileMeta("state", "Agent", "Core", "system_info"),
    "uname.txt": FileMeta("state", "System", "Core", "system_info"),
    "external_ip.txt": FileMeta("state", "System", "Networking", "system_info"),
    "date_generated.txt": FileMeta("state", "Agent", "Core", "system_info"),
    "ifconfig.txt": FileMeta("state", "System", "Networking", "raw_text"),
    "routing.txt": FileMeta("state", "System", "Networking", "routing_table"),
    "system_extension_list.txt": FileMeta("state", "System", "Core", "system_extensions"),
    "installed_applications.txt": FileMeta("state", "System", "Core", "app_list"),
    "launchctl_list.txt": FileMeta("state", "System", "Core", "launchctl_list"),
    "ui_sample.txt": FileMeta("state", "System", "Core", "raw_text"),
    "PrismaAccessAgent_agent_version.log": FileMeta("state", "Agent", "Core", "system_info"),
    # Windows Machine Info files
    "systeminfo.log": FileMeta("state", "System", "Core", "systeminfo"),
    "ipconfig.log": FileMeta("state", "System", "Networking", "ipconfig"),
    "route.log": FileMeta("state", "System", "Networking", "win_routing_table"),
    "installed_applications.log": FileMeta("state", "System", "Core", "win_installed_apps"),
    "installed_drivers.log": FileMeta("state", "System", "Core", "win_installed_drivers"),
    "netstat.log": FileMeta("state", "System", "Networking", "win_netstat"),
    "dns_cache.log": FileMeta("state", "System", "Networking", "win_dns_cache"),
    "WindowsFirewallrules.json": FileMeta("state", "System", "Security", "win_firewall_rules"),
    "current_user_groups.log": FileMeta("state", "System", "Core", "win_user_groups"),
    "user_sessions.log": FileMeta("state", "System", "Core", "win_user_sessions"),
    "powercfg_all.log": FileMeta("state", "System", "Power", "win_powercfg"),
    "powercfg_query.log": FileMeta("state", "System", "Power", "win_powercfg_query"),
    "power_history_24h.log": FileMeta("state", "System", "Power", "win_power_history"),
    "nslookup_google_com.log": FileMeta("state", "System", "Networking", "win_nslookup"),
    "ping_8_8_8_8.log": FileMeta("state", "System", "Networking", "win_ping"),
    "windows_event_viewer_logs.xml": FileMeta("state", "System", "Core", "win_event_viewer"),
}

# Structured log sources — module/component mapping
LOG_SOURCES: dict[str, tuple[str, str]] = {
    "PAS": ("Agent", "Core"),
    "SecurityExtension": ("System", "Security"),
    "NetworkExtension": ("System", "Security"),
    "NetworkManager": ("System", "Networking"),
    "Proxy": ("Agent", "Proxy"),
    "PMTUDiscoverer": ("Agent", "Core"),
    "Adns": ("Agent", "Advanced DNS Resolver"),
    "TunneledPacket": ("Agent", "Core"),
    "PACompliance": ("Agent", "Compliance"),
    "PAComplianceMp": ("Agent", "Compliance"),
    "PADiagnostic": ("Agent", "Diagnostics"),
    "PACli": ("Agent", "Core"),
    "Uninstaller": ("Agent", "Core"),
    "uninstaller": ("Agent", "Core"),
    "PAUI": ("Agent", "Core"),
    # Windows-specific log sources
    "PABrowser": ("Agent", "Core"),
    "PaaCredentialProvider": ("Agent", "Core"),
    "pachecker": ("Agent", "Core"),
}

# Pacli command name mapping: state key → human-readable pacli command
PACLI_COMMAND_MAP: dict[str, str] = {
    "Agent.Core.status": "pacli status",
    "Agent.Core.epm_status": "pacli epm-status",
    "Agent.Core.version": "pacli version",
    "Agent.Core.proxy_status": "pacli proxy-status",
    "Agent.Networking.tunnel": "pacli tunnel",
    "Agent.Explicit Proxy.ep": "pacli ep",
    "Agent.Core.browser_status": "pacli browser-status",
    "Agent.Core.captive_portal": "pacli captive-portal",
    "Agent.ADNS Resolver.adns": "pacli adns",
    "Agent.Dynamic Privileged Access.dpa_project_list": "pacli dpa-project-list",
    "Agent.ADEM.adem_status": "pacli adem-status",
    "Agent.DLP.dlp_status": "pacli dlp-status",
    "Agent.Networking.traffic_show": "pacli traffic show",
    "Agent.Core.gateways_list": "pacli gateways-list",
    "Agent.Compliance.hip_status": "pacli hip-status",
    "Agent.Security.protect": "pacli protect",
    "Agent.Core.epm_commands": "pacli epm-commands",
    "Agent.Networking.traffic_rdns": "pacli traffic rdns",
}

# Skip patterns for binary/installer files (Windows)
SKIP_EXTENSIONS = {".dmp", ".etl"}
SKIP_PREFIXES = ("MSI", "setupapi.dev", "ADEM_install_")

# Special files
SPECIAL_FILES: dict[str, FileMeta] = {
    "traffic_log_json.txt": FileMeta("log", "Agent", "Core", "traffic_json"),
    "networkextensions.txt": FileMeta("log", "System", "Networking", "skip_large"),
    "unified_log_last_60minutes.txt": FileMeta("log", "System", "Core", "skip_large"),
    "remote-shell.log": FileMeta("log", "Agent", "Core", "remote_shell"),
    "fips_self_test.log": FileMeta("state", "Agent", "Core", "raw_text"),
}
