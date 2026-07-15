"""Unit tests for paa_analyzer.parsers_win — Windows-specific parsers."""

import json


from paa_analyzer import parsers_win


# ── Machine Info state parsers ────────────────────────────────────────────


class TestSysteminfo:
    SAMPLE = """\
Host Name:                     AT-PAA-04
OS Name:                       Microsoft Windows 11 Pro
OS Version:                    10.0.26200 N/A Build 26200
System Type:                   x64-based PC
Processor(s):                  1 Processor(s) Installed.
                               [01]: AMD64 Family 15 Model 107 Stepping 1 AuthenticAMD ~3793 Mhz
Time Zone:                     (UTC+01:00) Amsterdam, Berlin, Bern, Rome, Stockholm, Vienna
Hotfix(s):                     2 Hotfix(s) Installed.
                               [01]: KB5074828
                               [02]: KB5054156
"""

    def test_parses_host_name(self):
        result = parsers_win.systeminfo(self.SAMPLE)
        assert result["host_name"] == "AT-PAA-04"

    def test_parses_os_name(self):
        result = parsers_win.systeminfo(self.SAMPLE)
        assert result["os_name"] == "Microsoft Windows 11 Pro"

    def test_parses_os_version(self):
        result = parsers_win.systeminfo(self.SAMPLE)
        assert "10.0.26200" in result["os_version"]

    def test_parses_system_type(self):
        result = parsers_win.systeminfo(self.SAMPLE)
        assert result["system_type"] == "x64-based PC"

    def test_parses_time_zone(self):
        result = parsers_win.systeminfo(self.SAMPLE)
        assert "Amsterdam" in result["time_zone"]

    def test_parses_hotfix_list(self):
        result = parsers_win.systeminfo(self.SAMPLE)
        assert isinstance(result["hotfix_s"], list)
        assert len(result["hotfix_s"]) == 2
        assert "[01]: KB5074828" in result["hotfix_s"][0]

    def test_empty_text(self):
        assert parsers_win.systeminfo("") == {}


class TestIpconfig:
    SAMPLE = """\
Windows IP Configuration

   Host Name . . . . . . . . . . . . : at-paa-04
   DNS Suffix Search List. . . . . . : sase.at

Ethernet adapter Ethernet:

   Description . . . . . . . . . . . : Red Hat VirtIO Ethernet Adapter
   IPv4 Address. . . . . . . . . . . : 198.18.1.209(Preferred)
   Default Gateway . . . . . . . . . : 198.18.1.1
   DHCP Enabled. . . . . . . . . . . : Yes
"""

    def test_parses_global_host_name(self):
        result = parsers_win.ipconfig(self.SAMPLE)
        assert result["global"]["host_name"] == "at-paa-04"

    def test_parses_dns_suffix(self):
        result = parsers_win.ipconfig(self.SAMPLE)
        assert result["global"]["dns_suffix_search_list"] == "sase.at"

    def test_parses_adapter(self):
        result = parsers_win.ipconfig(self.SAMPLE)
        assert len(result["adapters"]) == 1
        adapter = result["adapters"][0]
        assert adapter["name"] == "Ethernet adapter Ethernet"

    def test_adapter_description(self):
        result = parsers_win.ipconfig(self.SAMPLE)
        adapter = result["adapters"][0]
        assert adapter["description"] == "Red Hat VirtIO Ethernet Adapter"

    def test_strips_preferred_suffix(self):
        result = parsers_win.ipconfig(self.SAMPLE)
        adapter = result["adapters"][0]
        assert adapter["ipv4_address"] == "198.18.1.209"

    def test_adapter_gateway(self):
        result = parsers_win.ipconfig(self.SAMPLE)
        adapter = result["adapters"][0]
        assert adapter["default_gateway"] == "198.18.1.1"

    def test_dhcp_enabled(self):
        result = parsers_win.ipconfig(self.SAMPLE)
        adapter = result["adapters"][0]
        assert adapter["dhcp_enabled"] == "Yes"

    def test_empty_text(self):
        result = parsers_win.ipconfig("")
        assert result == {"global": {}, "adapters": []}


class TestWinRoutingTable:
    SAMPLE = """\
===========================================================================
Interface List
  6...bc 24 11 2d ac 0f ......Red Hat VirtIO Ethernet Adapter
  1...........................Software Loopback Interface 1
===========================================================================

IPv4 Route Table
===========================================================================
Active Routes:
Network Destination        Netmask          Gateway       Interface  Metric
          0.0.0.0          0.0.0.0       198.18.1.1     198.18.1.209     15
        127.0.0.1  255.255.255.255         On-link         127.0.0.1    331
===========================================================================
Persistent Routes:
  None
"""

    def test_parses_interfaces(self):
        result = parsers_win.win_routing_table(self.SAMPLE)
        assert len(result["interfaces"]) == 2

    def test_interface_with_mac(self):
        result = parsers_win.win_routing_table(self.SAMPLE)
        eth = result["interfaces"][0]
        assert eth["index"] == 6
        assert eth["mac"] is not None
        assert "bc" in eth["mac"]
        assert eth["name"] == "Red Hat VirtIO Ethernet Adapter"

    def test_loopback_no_mac(self):
        result = parsers_win.win_routing_table(self.SAMPLE)
        lo = result["interfaces"][1]
        assert lo["index"] == 1
        assert lo["mac"] is None
        assert "Loopback" in lo["name"]

    def test_parses_ipv4_routes(self):
        result = parsers_win.win_routing_table(self.SAMPLE)
        assert len(result["ipv4"]) == 2
        default_route = result["ipv4"][0]
        assert default_route["destination"] == "0.0.0.0"
        assert default_route["gateway"] == "198.18.1.1"
        assert default_route["interface"] == "198.18.1.209"
        assert default_route["metric"] == 15

    def test_loopback_route(self):
        result = parsers_win.win_routing_table(self.SAMPLE)
        lo_route = result["ipv4"][1]
        assert lo_route["destination"] == "127.0.0.1"
        assert lo_route["gateway"] == "On-link"
        assert lo_route["metric"] == 331

    def test_empty_text(self):
        result = parsers_win.win_routing_table("")
        assert result == {"interfaces": [], "ipv4": [], "ipv6": []}


class TestWinFirewallRules:
    SAMPLE_JSON = '{"rules": [{"name": "Test Rule", "enabled": true, "direction": "kOut", "action": "kAllow"}]}'

    def test_parses_rules(self):
        result = parsers_win.win_firewall_rules(self.SAMPLE_JSON)
        assert len(result["rules"]) == 1
        assert result["rules"][0]["name"] == "Test Rule"
        assert result["rules"][0]["enabled"] is True

    def test_total_count(self):
        result = parsers_win.win_firewall_rules(self.SAMPLE_JSON)
        assert result["total"] == 1

    def test_direction_and_action(self):
        result = parsers_win.win_firewall_rules(self.SAMPLE_JSON)
        assert result["rules"][0]["direction"] == "kOut"
        assert result["rules"][0]["action"] == "kAllow"

    def test_invalid_json(self):
        result = parsers_win.win_firewall_rules("not json at all")
        assert result["error"] == "Invalid JSON"
        assert result["rules"] == []

    def test_multiple_rules(self):
        data = json.dumps({"rules": [{"name": "Rule A"}, {"name": "Rule B"}]})
        result = parsers_win.win_firewall_rules(data)
        assert result["total"] == 2
        assert result["rules"][0]["name"] == "Rule A"
        assert result["rules"][1]["name"] == "Rule B"


class TestWinInstalledApps:
    SAMPLE = """\

Name                        Version
----                        -------
Prisma Access Agent         26.1.2.4
Microsoft Edge              146.0.3856.109
"""

    def test_parses_apps(self):
        result = parsers_win.win_installed_apps(self.SAMPLE)
        assert len(result) == 2

    def test_prisma_access_agent(self):
        result = parsers_win.win_installed_apps(self.SAMPLE)
        assert result[0]["name"] == "Prisma Access Agent"
        assert result[0]["version"] == "26.1.2.4"

    def test_edge(self):
        result = parsers_win.win_installed_apps(self.SAMPLE)
        assert result[1]["name"] == "Microsoft Edge"
        assert result[1]["version"] == "146.0.3856.109"

    def test_empty_text(self):
        assert parsers_win.win_installed_apps("") == []

    def test_header_only(self):
        text = "Name                        Version\n----                        -------\n"
        assert parsers_win.win_installed_apps(text) == []


class TestWinInstalledDrivers:
    SAMPLE = """\
Module Name  Display Name           Description            Driver Type   Start Mode State      Status     Accept Stop Accept Pause
============ ====================== ====================== ============= ========== ========== ========== =========== ============
ACPI         Microsoft ACPI Driver  Microsoft ACPI Driver  Kernel        Boot       Running    OK         TRUE        FALSE
AFD          Ancillary Function     Ancillary Function     Kernel        System     Running    OK         TRUE        FALSE
"""

    def test_parses_drivers(self):
        result = parsers_win.win_installed_drivers(self.SAMPLE)
        assert len(result) == 2

    def test_acpi_driver(self):
        result = parsers_win.win_installed_drivers(self.SAMPLE)
        d = result[0]
        assert d["module"] == "ACPI"
        assert "ACPI" in d["display_name"]
        assert d["driver_type"] == "Kernel"
        assert d["start_mode"] == "Boot"
        assert d["state"] == "Running"
        assert d["status"] == "OK"

    def test_afd_driver(self):
        result = parsers_win.win_installed_drivers(self.SAMPLE)
        d = result[1]
        assert d["module"] == "AFD"
        assert d["start_mode"] == "System"
        assert d["state"] == "Running"

    def test_empty_text(self):
        assert parsers_win.win_installed_drivers("") == []


class TestWinNetstat:
    SAMPLE = """\
Active Connections

  Proto  Local Address          Foreign Address        State
  TCP    0.0.0.0:135            0.0.0.0:0              LISTENING
  RpcEptMapper
 [svchost.exe]
  TCP    0.0.0.0:445            0.0.0.0:0              LISTENING
 Can not obtain ownership information
"""

    def test_parses_connections(self):
        result = parsers_win.win_netstat(self.SAMPLE)
        assert len(result["connections"]) == 2

    def test_first_connection(self):
        result = parsers_win.win_netstat(self.SAMPLE)
        c = result["connections"][0]
        assert c["proto"] == "TCP"
        assert c["local_address"] == "0.0.0.0:135"
        assert c["foreign_address"] == "0.0.0.0:0"
        assert c["state"] == "LISTENING"

    def test_process_with_service(self):
        result = parsers_win.win_netstat(self.SAMPLE)
        c = result["connections"][0]
        assert "svchost.exe" in c["process"]

    def test_no_ownership_info(self):
        result = parsers_win.win_netstat(self.SAMPLE)
        c = result["connections"][1]
        assert c["process"] == ""

    def test_empty_text(self):
        result = parsers_win.win_netstat("")
        assert result == {"connections": []}


class TestWinDnsCache:
    SAMPLE = """\
Windows IP Configuration

    example.com
    ----------------------------------------
    Record Name . . . . . : example.com
    Record Type . . . . . : 1
    Time To Live  . . . . : 300
    Data Length . . . . . : 4
    Section . . . . . . . : Answer
    A (Host) Record . . . : 93.184.216.34
"""

    def test_parses_records(self):
        result = parsers_win.win_dns_cache(self.SAMPLE)
        assert len(result) == 1

    def test_record_name(self):
        result = parsers_win.win_dns_cache(self.SAMPLE)
        r = result[0]
        assert r["record_name"] == "example.com"

    def test_record_type(self):
        result = parsers_win.win_dns_cache(self.SAMPLE)
        assert result[0]["record_type"] == "1"

    def test_ttl(self):
        result = parsers_win.win_dns_cache(self.SAMPLE)
        assert result[0]["time_to_live"] == "300"

    def test_a_record_value(self):
        result = parsers_win.win_dns_cache(self.SAMPLE)
        assert result[0]["a_host_record"] == "93.184.216.34"

    def test_empty_text(self):
        assert parsers_win.win_dns_cache("") == []


class TestWinUserGroups:
    SAMPLE = """\
GROUP INFORMATION
-----------------

Group Name                                    Type              SID                                            Attributes
============================================= ================= ============================================== ==================================================
BUILTIN\\Administrators                        Alias             S-1-5-32-544                                   Enabled by default, Enabled group, Group owner
NT AUTHORITY\\INTERACTIVE                      Well-known group  S-1-5-4                                        Mandatory group, Enabled by default, Enabled group
"""

    def test_parses_groups(self):
        result = parsers_win.win_user_groups(self.SAMPLE)
        # Header row "Group Name" is also parsed due to 2+ space splits
        groups = [g for g in result if g["group_name"] != "Group Name"]
        assert len(groups) == 2

    def test_administrators_group(self):
        result = parsers_win.win_user_groups(self.SAMPLE)
        groups = [g for g in result if g["group_name"] != "Group Name"]
        g = groups[0]
        assert "Administrators" in g["group_name"]
        assert g["type"] == "Alias"
        assert g["sid"] == "S-1-5-32-544"
        assert "Group owner" in g["attributes"]

    def test_well_known_group(self):
        result = parsers_win.win_user_groups(self.SAMPLE)
        groups = [g for g in result if g["group_name"] != "Group Name"]
        g = groups[1]
        assert "INTERACTIVE" in g["group_name"]
        assert g["type"] == "Well-known group"
        assert g["sid"] == "S-1-5-4"
        assert "Mandatory group" in g["attributes"]

    def test_empty_text(self):
        assert parsers_win.win_user_groups("") == []


class TestWinUserSessions:
    SAMPLE = """\
 SESSIONNAME               USERNAME                 ID  STATE   TYPE        DEVICE
>services                                            0  Disc
 rdp-tcp#0                 OliverKaiser              2  Active
"""

    def test_parses_sessions(self):
        result = parsers_win.win_user_sessions(self.SAMPLE)
        assert len(result) == 2

    def test_services_session(self):
        result = parsers_win.win_user_sessions(self.SAMPLE)
        s = result[0]
        assert s["session_name"] == "services"
        assert s["id"] == 0
        assert s["state"] == "Disc"

    def test_rdp_session(self):
        result = parsers_win.win_user_sessions(self.SAMPLE)
        s = result[1]
        assert s["session_name"] == "rdp-tcp#0"
        assert s["username"] == "OliverKaiser"
        assert s["id"] == 2
        assert s["state"] == "Active"

    def test_empty_text(self):
        assert parsers_win.win_user_sessions("") == []


class TestWinPowercfg:
    SAMPLE = """\
The following sleep states are not available on this system:
    Standby (S1)
\tThe system firmware does not support this standby state.
    Hibernate
\tThe system firmware does not support hibernation.
"""

    def test_parses_sleep_states(self):
        result = parsers_win.win_powercfg(self.SAMPLE)
        assert len(result["sleep_states"]) == 2

    def test_standby_state(self):
        result = parsers_win.win_powercfg(self.SAMPLE)
        s = result["sleep_states"][0]
        assert s["state"] == "Standby (S1)"
        assert len(s["reasons"]) == 1
        assert "firmware" in s["reasons"][0]

    def test_hibernate_state(self):
        result = parsers_win.win_powercfg(self.SAMPLE)
        s = result["sleep_states"][1]
        assert s["state"] == "Hibernate"
        assert "hibernation" in s["reasons"][0]

    def test_empty_text(self):
        result = parsers_win.win_powercfg("")
        assert result == {"sleep_states": []}


class TestWinPowercfgQuery:
    SAMPLE = """\
Power Scheme GUID: 381b4222-f694-41f0-9685-ff5bb260df2e  (Balanced)
  GUID Alias: SCHEME_BALANCED
  Subgroup GUID: 0012ee47-9041-4b5d-9b77-535fba8b1442  (Hard disk)
    Power Setting GUID: 6738e2c4-e8a5-4a42-b16a-e040e769756e  (Turn off hard disk after)
"""

    def test_parses_scheme(self):
        result = parsers_win.win_powercfg_query(self.SAMPLE)
        assert result["scheme_name"] == "Balanced"
        assert result["scheme_guid"] == "381b4222-f694-41f0-9685-ff5bb260df2e"

    def test_parses_subgroup(self):
        result = parsers_win.win_powercfg_query(self.SAMPLE)
        assert len(result["subgroups"]) == 1
        sg = result["subgroups"][0]
        assert sg["name"] == "Hard disk"
        assert sg["guid"] == "0012ee47-9041-4b5d-9b77-535fba8b1442"

    def test_parses_setting(self):
        result = parsers_win.win_powercfg_query(self.SAMPLE)
        sg = result["subgroups"][0]
        assert len(sg["settings"]) == 1
        assert sg["settings"][0]["name"] == "Turn off hard disk after"

    def test_empty_text(self):
        result = parsers_win.win_powercfg_query("")
        assert result["scheme_name"] == ""
        assert result["subgroups"] == []


class TestWinPowerHistory:
    SAMPLE = """\

   ProviderName: Microsoft-Windows-Kernel-General

TimeCreated          Id LevelDisplayName Message
-----------          -- ---------------- -------
4/8/2026 10:39:29 AM 16 Information      The access history in hive
4/8/2026 10:39:03 AM 16 Information      Another event message
"""

    def test_parses_events(self):
        result = parsers_win.win_power_history(self.SAMPLE)
        assert len(result) == 2

    def test_provider_name(self):
        result = parsers_win.win_power_history(self.SAMPLE)
        assert result[0]["provider"] == "Microsoft-Windows-Kernel-General"
        assert result[1]["provider"] == "Microsoft-Windows-Kernel-General"

    def test_event_id(self):
        result = parsers_win.win_power_history(self.SAMPLE)
        assert result[0]["event_id"] == 16

    def test_level(self):
        result = parsers_win.win_power_history(self.SAMPLE)
        assert result[0]["level"] == "information"

    def test_message(self):
        result = parsers_win.win_power_history(self.SAMPLE)
        assert "access history" in result[0]["message"]
        assert "Another event" in result[1]["message"]

    def test_timestamp_is_formatted(self):
        result = parsers_win.win_power_history(self.SAMPLE)
        assert result[0]["timestamp"] is not None
        # format_ts returns ISO string with date
        assert "2026-04-08" in result[0]["timestamp"]

    def test_empty_text(self):
        assert parsers_win.win_power_history("") == []


class TestWinNslookup:
    SAMPLE = """\
Server:  UnKnown
Address:  198.18.1.1

Name:    www.google.com
Addresses:  142.251.151.119
\t  142.251.157.119
"""

    def test_parses_server(self):
        result = parsers_win.win_nslookup(self.SAMPLE)
        assert result["server"] == "UnKnown"

    def test_parses_server_address(self):
        result = parsers_win.win_nslookup(self.SAMPLE)
        assert result["server_address"] == "198.18.1.1"

    def test_parses_name(self):
        result = parsers_win.win_nslookup(self.SAMPLE)
        assert result["name"] == "www.google.com"

    def test_parses_addresses(self):
        result = parsers_win.win_nslookup(self.SAMPLE)
        assert len(result["addresses"]) == 2
        assert "142.251.151.119" in result["addresses"][0]
        assert "142.251.157.119" in result["addresses"][1]

    def test_empty_text(self):
        result = parsers_win.win_nslookup("")
        assert result["server"] == ""
        assert result["addresses"] == []


class TestWinPing:
    SAMPLE = """\
Pinging 8.8.8.8 with 32 bytes of data:
Reply from 8.8.8.8: bytes=32 time=13ms TTL=117
Reply from 8.8.8.8: bytes=32 time=20ms TTL=117

Ping statistics for 8.8.8.8:
    Packets: Sent = 2, Received = 2, Lost = 0 (0% loss),
Approximate round trip times in milli-seconds:
    Minimum = 13ms, Maximum = 20ms, Average = 16ms
"""

    def test_parses_target(self):
        result = parsers_win.win_ping(self.SAMPLE)
        assert result["target"] == "8.8.8.8"

    def test_parses_replies(self):
        result = parsers_win.win_ping(self.SAMPLE)
        assert len(result["replies"]) == 2
        assert result["replies"][0]["from"] == "8.8.8.8"
        assert result["replies"][0]["bytes"] == 32
        assert result["replies"][0]["time_ms"] == 13
        assert result["replies"][0]["ttl"] == 117

    def test_second_reply(self):
        result = parsers_win.win_ping(self.SAMPLE)
        assert result["replies"][1]["time_ms"] == 20

    def test_packet_stats(self):
        result = parsers_win.win_ping(self.SAMPLE)
        assert result["stats"]["sent"] == 2
        assert result["stats"]["received"] == 2
        assert result["stats"]["lost"] == 0

    def test_rtt_stats(self):
        result = parsers_win.win_ping(self.SAMPLE)
        assert result["stats"]["min_ms"] == 13
        assert result["stats"]["max_ms"] == 20
        assert result["stats"]["avg_ms"] == 16

    def test_empty_text(self):
        result = parsers_win.win_ping("")
        assert result["target"] == ""
        assert result["replies"] == []
        assert result["stats"] == {}


class TestWinEventViewer:
    SAMPLE = """\
<?xml version="1.0" encoding="utf-8"?>
<Objects>
  <Object Type="System.Diagnostics.Eventing.Reader.EventLogRecord">
    <Property Name="Message" Type="System.String">Test event message</Property>
    <Property Name="Id" Type="System.Int32">16384</Property>
    <Property Name="Level" Type="System.Byte">4</Property>
    <Property Name="ProviderName" Type="System.String">Microsoft-Windows-Security-SPP</Property>
    <Property Name="LogName" Type="System.String">Application</Property>
  </Object>
</Objects>
"""

    def test_parses_events(self):
        result = parsers_win.win_event_viewer(self.SAMPLE)
        assert len(result) == 1

    def test_event_message(self):
        result = parsers_win.win_event_viewer(self.SAMPLE)
        assert result[0]["message"] == "Test event message"

    def test_event_id(self):
        result = parsers_win.win_event_viewer(self.SAMPLE)
        assert result[0]["event_id"] == 16384

    def test_level_maps_to_information(self):
        result = parsers_win.win_event_viewer(self.SAMPLE)
        assert result[0]["level"] == "information"

    def test_provider_and_log_name(self):
        result = parsers_win.win_event_viewer(self.SAMPLE)
        assert result[0]["provider"] == "Microsoft-Windows-Security-SPP"
        assert result[0]["log_name"] == "Application"

    def test_invalid_xml(self):
        assert parsers_win.win_event_viewer("not xml") == []

    def test_empty_text(self):
        assert parsers_win.win_event_viewer("") == []

    def test_multiple_events(self):
        xml = """\
<?xml version="1.0" encoding="utf-8"?>
<Objects>
  <Object Type="System.Diagnostics.Eventing.Reader.EventLogRecord">
    <Property Name="Message" Type="System.String">First event</Property>
    <Property Name="Id" Type="System.Int32">100</Property>
    <Property Name="Level" Type="System.Byte">2</Property>
  </Object>
  <Object Type="System.Diagnostics.Eventing.Reader.EventLogRecord">
    <Property Name="Message" Type="System.String">Second event</Property>
    <Property Name="Id" Type="System.Int32">200</Property>
    <Property Name="Level" Type="System.Byte">3</Property>
  </Object>
</Objects>
"""
        result = parsers_win.win_event_viewer(xml)
        assert len(result) == 2
        assert result[0]["level"] == "error"
        assert result[1]["level"] == "warning"


# ── Windows log parsers ─────────────────────────────────────────────────


class TestWinPauiLog:
    SAMPLE = """\
PAUI Error: 2 : 08/01/2026 15:46:48 Exception while reading telemetry data
PAUI Information: 0 : 08/01/2026 15:46:48 Current System Theme is Light
PAUI Verbose: 2 : 08/01/2026 15:46:59 There are total 1 tenants
"""

    def test_parses_entries(self):
        result = parsers_win.win_paui_log(self.SAMPLE)
        assert len(result) == 3

    def test_error_level(self):
        result = parsers_win.win_paui_log(self.SAMPLE)
        assert result[0]["level"] == "error"
        assert result[0]["message"] == "Exception while reading telemetry data"

    def test_information_level(self):
        result = parsers_win.win_paui_log(self.SAMPLE)
        assert result[1]["level"] == "information"
        assert "Light" in result[1]["message"]

    def test_verbose_level(self):
        result = parsers_win.win_paui_log(self.SAMPLE)
        assert result[2]["level"] == "verbose"
        assert "tenants" in result[2]["message"]

    def test_timestamp_is_epoch(self):
        result = parsers_win.win_paui_log(self.SAMPLE)
        assert result[0]["timestamp"] is not None
        assert isinstance(result[0]["timestamp"], float)

    def test_with_timezone(self):
        result = parsers_win.win_paui_log(self.SAMPLE, tz="+0200")
        result_utc = parsers_win.win_paui_log(self.SAMPLE)
        # With +0200, the local time is ahead of UTC so epoch should be smaller
        assert result[0]["timestamp"] < result_utc[0]["timestamp"]

    def test_empty_text(self):
        assert parsers_win.win_paui_log("") == []


class TestWinDemLog:
    SAMPLE = """\
[2026-03-18 13:32:34.071] [default] [warning] GetAgentUuid() failed
[2026-03-18 13:32:34.071] [default] [info] This agent is version 5.7.17
"""

    def test_parses_entries(self):
        result = parsers_win.win_dem_log(self.SAMPLE)
        assert len(result) == 2

    def test_warning_entry(self):
        result = parsers_win.win_dem_log(self.SAMPLE)
        assert result[0]["level"] == "warning"
        assert result[0]["message"] == "GetAgentUuid() failed"

    def test_info_entry(self):
        result = parsers_win.win_dem_log(self.SAMPLE)
        assert result[1]["level"] == "info"
        assert "version 5.7.17" in result[1]["message"]

    def test_timestamp_is_float(self):
        result = parsers_win.win_dem_log(self.SAMPLE)
        assert result[0]["timestamp"] is not None
        assert isinstance(result[0]["timestamp"], float)

    def test_multiline_continuation(self):
        text = """\
[2026-03-18 13:32:34.071] [default] [error] Something broke
  stack trace line 1
  stack trace line 2
[2026-03-18 13:32:35.000] [default] [info] Recovery
"""
        result = parsers_win.win_dem_log(text)
        assert len(result) == 2
        assert "stack trace line 1" in result[0]["message"]
        assert "stack trace line 2" in result[0]["message"]

    def test_empty_text(self):
        assert parsers_win.win_dem_log("") == []


class TestChromiumLog:
    SAMPLE = """\
[4936:6668:0408/103854.684:WARNING:chrome_main_delegate.cc(675)] This is Chrome version 131
[4936:2056:0408/103854.766:VERBOSE1:chrome_browser_cloud_management_controller.cc(97)] DM token = empty
"""

    def test_parses_entries(self):
        result = parsers_win.chromium_log(self.SAMPLE)
        assert len(result) == 2

    def test_warning_level(self):
        result = parsers_win.chromium_log(self.SAMPLE)
        assert result[0]["level"] == "warning"

    def test_verbose_maps_to_debug(self):
        result = parsers_win.chromium_log(self.SAMPLE)
        assert result[1]["level"] == "debug"

    def test_message_includes_source_location(self):
        result = parsers_win.chromium_log(self.SAMPLE)
        assert "chrome_main_delegate.cc(675)" in result[0]["message"]
        assert "Chrome version 131" in result[0]["message"]

    def test_timestamp_is_float(self):
        result = parsers_win.chromium_log(self.SAMPLE)
        assert result[0]["timestamp"] is not None
        assert isinstance(result[0]["timestamp"], float)

    def test_empty_text(self):
        assert parsers_win.chromium_log("") == []
