"""Unit tests for paa_analyzer.parsers."""

import json
from datetime import UTC

import pytest

from paa_analyzer import parsers
from paa_analyzer.parsers import beautify_message

# ── Timestamp parsing ────────────────────────────────────────────────────


class TestParseTs:
    """Tests for parse_ts — called on every log entry, handles 7 formats."""

    @pytest.mark.parametrize(
        "raw,expected_approx",
        [
            # ISO-8601 full with positive offset (+02:00 → UTC is 2h earlier)
            ("2026-04-03T09:24:40.100+02:00", 1775201080.1),
            # ISO-8601 full with negative offset (-05:00 → UTC is 5h later)
            ("2026-04-03T09:24:40.100-05:00", 1775226280.1),
            # ISO-8601 full with UTC offset
            ("2026-04-03T09:24:40.100+00:00", 1775208280.1),
        ],
        ids=["iso-positive", "iso-negative", "iso-utc"],
    )
    def test_iso_full_format(self, raw, expected_approx):
        result = parsers.parse_ts(raw)
        assert result == pytest.approx(expected_approx, abs=1.0)

    @pytest.mark.parametrize(
        "raw,expected_approx",
        [
            ("2026-04-03 09:24:40.100+0200", 1775201080.1),
            ("2026-04-03 09:24:40.100-0500", 1775226280.1),
        ],
        ids=["numeric-positive", "numeric-negative"],
    )
    def test_numeric_offset_format(self, raw, expected_approx):
        result = parsers.parse_ts(raw)
        assert result == pytest.approx(expected_approx, abs=1.0)

    def test_gmt_offset_positive(self):
        result = parsers.parse_ts("2026-04-04 22:18:34, GMT+0200")
        assert result is not None
        assert isinstance(result, float)

    def test_gmt_offset_negative(self):
        result = parsers.parse_ts("2026-04-04 22:18:34, GMT-0500")
        assert result is not None

    def test_gmt_offset_values_differ(self):
        pos = parsers.parse_ts("2026-04-04 22:18:34, GMT+0200")
        neg = parsers.parse_ts("2026-04-04 22:18:34, GMT-0500")
        assert pos is not None
        assert neg is not None
        # +0200 is ahead of UTC, -0500 is behind → UTC epoch for +0200 is smaller
        assert pos < neg

    def test_dlp_format(self):
        result = parsers.parse_ts("2026/01/08 16:27:19:278")
        assert result is not None

    def test_dlp_format_with_default_offset(self):
        without = parsers.parse_ts("2026/01/08 16:27:19:278")
        with_offset = parsers.parse_ts("2026/01/08 16:27:19:278", default_offset="+0200")
        assert without is not None
        assert with_offset is not None
        # With +0200, the UTC epoch should be smaller (timestamp is local time ahead of UTC)
        assert with_offset < without

    def test_bracketed_format(self):
        result = parsers.parse_ts("[2026-03-31 09:24:58]")
        assert result is not None

    def test_bracketed_with_default_offset(self):
        without = parsers.parse_ts("[2026-03-31 09:24:58]")
        with_offset = parsers.parse_ts("[2026-03-31 09:24:58]", default_offset="+0200")
        assert without is not None
        assert with_offset is not None
        assert with_offset < without

    def test_bare_datetime(self):
        result = parsers.parse_ts("2026-04-03 09:24:40")
        assert result is not None

    def test_bare_datetime_with_default_offset(self):
        without = parsers.parse_ts("2026-04-03 09:24:40")
        with_offset = parsers.parse_ts("2026-04-03 09:24:40", default_offset="+0200")
        assert without is not None
        assert with_offset is not None
        assert with_offset < without

    def test_empty_string_returns_none(self):
        assert parsers.parse_ts("") is None

    def test_garbage_returns_none(self):
        assert parsers.parse_ts("not a timestamp at all") is None

    def test_none_like_returns_none(self):
        assert parsers.parse_ts("   ") is None

    def test_iso_full_and_numeric_agree(self):
        """ISO-8601 full and numeric offset should produce same epoch for same time."""
        iso = parsers.parse_ts("2026-04-03T09:24:40.100+02:00")
        numeric = parsers.parse_ts("2026-04-03 09:24:40.100+0200")
        assert iso == pytest.approx(numeric, abs=0.01)

    def test_results_are_utc_epochs(self):
        """All formats should return UTC-normalized epoch floats."""
        # 2026-04-03T09:24:40+02:00 in UTC is 07:24:40
        result = parsers.parse_ts("2026-04-03T09:24:40.000+02:00")
        from datetime import datetime

        assert result is not None
        dt = datetime.fromtimestamp(result, tz=UTC)
        assert dt.hour == 7
        assert dt.minute == 24


class TestFormatTs:
    def test_formats_epoch_to_iso_utc(self):
        result = parsers.format_ts(0.0)
        assert result is not None
        assert "1970-01-01" in result
        assert "+00:00" in result

    def test_none_returns_none(self):
        assert parsers.format_ts(None) is None

    def test_specific_epoch(self):
        # 2026-04-03T07:24:40+00:00
        result = parsers.format_ts(1775201080.0)
        assert result is not None
        assert "2026-04-03" in result

    def test_roundtrip(self):
        """parse_ts → format_ts should produce a parseable ISO string."""
        original = "2026-04-03T09:24:40.100+02:00"
        epoch = parsers.parse_ts(original)
        formatted = parsers.format_ts(epoch)
        assert formatted is not None
        assert "2026-04-03" in formatted


class TestExtractTzOffset:
    def test_extracts_positive_offset(self):
        text = "Current Time: 2026-04-04 22:18:34, GMT+0200"
        assert parsers.extract_tz_offset(text) == "+0200"

    def test_extracts_negative_offset(self):
        text = "Current Time: 2026-04-04 22:18:34, GMT-0500"
        assert parsers.extract_tz_offset(text) == "-0500"

    def test_returns_none_for_no_offset(self):
        assert parsers.extract_tz_offset("no offset here") is None

    def test_extracts_from_full_status_text(self):
        text = "State: Enabled\nMode: Always On\nCurrent Time: 2026-04-04 22:18:34, GMT+0200\nTunnel: Connected"
        assert parsers.extract_tz_offset(text) == "+0200"


class TestKeyValue:
    def test_basic_key_value(self):
        text = "State: Enabled\nMode: Always On\nTunnel: Connected"
        result = parsers.key_value(text)
        assert result["state"] == "Enabled"
        assert result["mode"] == "Always On"
        assert result["tunnel"] == "Connected"

    def test_normalizes_keys(self):
        text = "EPM Status: Up\nCaptive Portal Status: Not Detected"
        result = parsers.key_value(text)
        assert result["epm_status"] == "Up"
        assert result["captive_portal_status"] == "Not Detected"

    def test_single_value_without_colon(self):
        text = "SomeValue"
        result = parsers.key_value(text)
        assert result["value"] == "SomeValue"

    def test_empty_text(self):
        assert parsers.key_value("") == {}
        assert parsers.key_value("\n\n") == {}


class TestForwardingProfile:
    SAMPLE = """\
| Priority | Name          | Enabled | Source Apps | Destinations | Type     | Connect Through | Hits |
|----------|---------------|---------|------------|-------------|----------|-----------------|------|
| 0        | Implicit      | Yes     | Any        | Any          | Data     | Direct          | 5    |
| 1        | Exclude-Video | No      | Any        | *.netflix    | Data     | Direct          | 10   |
| 3        | Default       | Yes     | Any        | Any          | Data     | Best Available  | 0    |

 X - Block outbound LAN
 X - Block inbound connections
"""

    def test_parses_rules(self):
        result = parsers.forwarding_profile(self.SAMPLE)
        assert len(result["rules"]) == 3
        assert result["rules"][0]["priority"] == 0
        assert result["rules"][0]["name"] == "Implicit"
        assert result["rules"][0]["enabled"] is True
        assert result["rules"][0]["hits"] == 5

    def test_disabled_rule(self):
        result = parsers.forwarding_profile(self.SAMPLE)
        assert result["rules"][1]["enabled"] is False

    def test_parses_flags(self):
        result = parsers.forwarding_profile(self.SAMPLE)
        assert len(result["flags"]) == 2
        assert "Block outbound LAN" in result["flags"][0]

    def test_empty_text(self):
        result = parsers.forwarding_profile("")
        assert result == {"rules": [], "flags": []}


class TestGatewayList:
    SAMPLE = """\
Agent Location: AT

External Gateways
Name                     Priority Address
----                     -------- -------
US Northwest             5        us-nw.example.com
Austria                  1        at.example.com
"""

    def test_parses_location(self):
        result = parsers.gateway_list(self.SAMPLE)
        assert result["agent_location"] == "AT"

    def test_parses_gateways(self):
        result = parsers.gateway_list(self.SAMPLE)
        assert len(result["gateways"]) == 2
        assert result["gateways"][0]["name"] == "US Northwest"
        assert result["gateways"][0]["priority"] == 5
        assert result["gateways"][0]["address"] == "us-nw.example.com"


class TestSystemInfo:
    def test_sw_vers(self):
        text = "ProductName: macOS\nProductVersion: 26.2\nBuildVersion: 25C56"
        result = parsers.system_info(text, filename="sw_vers.txt")
        assert result["productname"] == "macOS"
        assert result["productversion"] == "26.2"

    def test_uname(self):
        text = "Darwin HOST 25.2.0 Kernel arm64"
        result = parsers.system_info(text, filename="uname.txt")
        assert result["architecture"] == "arm64"
        assert "Darwin" in result["kernel"]

    def test_external_ip_json(self):
        text = '{"origin": "1.2.3.4"}'
        result = parsers.system_info(text, filename="external_ip.txt")
        assert result["external_ip"] == "1.2.3.4"

    def test_external_ip_plain(self):
        result = parsers.system_info("1.2.3.4", filename="external_ip.txt")
        assert result["external_ip"] == "1.2.3.4"

    def test_agent_version(self):
        text = "Version: 26.1.2.4"
        result = parsers.system_info(text, filename="PrismaAccessAgent_agent_version.log")
        assert result["agent_version"] == "26.1.2.4"


class TestHipStatus:
    SAMPLE = """\
HIP Collection: Enabled
Next HIP Check: 2026-04-04 20:49:25

Gateway                 Last HIP Report
-------                 ---------------
Austria                 2026-04-03 06:57:30
"""

    def test_parses_collection(self):
        result = parsers.hip_status(self.SAMPLE)
        assert result["collection"] == "Enabled"

    def test_parses_next_check(self):
        result = parsers.hip_status(self.SAMPLE)
        assert result["next_check"] is not None
        assert "2026-04" in result["next_check"]

    def test_parses_gateways(self):
        result = parsers.hip_status(self.SAMPLE)
        assert len(result["gateways"]) == 1
        assert result["gateways"][0]["gateway"] == "Austria"


class TestProtection:
    def test_parses_features(self):
        text = "Protection Features\n---\nFirewall Enabled\nAV Enabled\nDisk NotConfigured"
        result = parsers.protection(text)
        assert len(result) == 3
        assert result[0]["name"] == "Firewall"
        assert result[0]["state"] == "Enabled"

    def test_empty(self):
        assert parsers.protection("") == []


class TestTrafficJson:
    SAMPLE_ENTRY = {
        "index": 42,
        "timeAndDate": "2026-04-03 09:24:40",
        "destination": "example.com:443",
        "protocol": "TCP",
        "verdict": "Tunnel",
        "sourceApp": "/Apps/Chrome",
        "reason": "Rule priority 3 matched",
        "trafficType": "kData",
    }

    def _parse_one(self, entry=None):
        import json as _json

        entries_json = _json.dumps([entry or self.SAMPLE_ENTRY])
        return parsers.traffic_json(
            f"Network connection log:\n{entries_json}",
            source="traffic_log_json",
            source_file="traffic_log_json.txt",
        )

    def test_parses_entries(self):
        result = self._parse_one()
        assert len(result) == 1
        assert result[0]["destination"] == "example.com:443"
        assert result[0]["protocol"] == "TCP"
        assert result[0]["verdict"] == "Tunnel"
        assert "Rule priority 3" in result[0]["reason"]
        assert result[0]["source_app"] == "/Apps/Chrome"

    def test_source_not_on_entries(self):
        """Source is no longer stored per entry — injected by store at query time."""
        result = self._parse_one()
        assert "source" not in result[0]

    def test_includes_raw_fields(self):
        result = self._parse_one()
        assert result[0]["index"] == 42
        assert result[0]["traffic_type"] == "kData"

    def test_comprehensive_message(self):
        result = self._parse_one()
        msg = result[0]["message"]
        # First line is the summary
        assert "Tunnel TCP example.com:443 app=Chrome" in msg
        # Subsequent lines contain full details
        assert "App: /Apps/Chrome" in msg
        assert "Reason: Rule priority 3 matched" in msg

    def test_empty_json(self):
        assert parsers.traffic_json("no json here") == []

    def test_constructs_message(self):
        import json as _json

        entries_json = _json.dumps(
            [
                {
                    "timeAndDate": "2026-04-03 09:00:00",
                    "destination": "x.com:80",
                    "protocol": "TCP",
                    "verdict": "Allow",
                    "sourceApp": "/a/b/MyApp",
                    "reason": "test",
                }
            ]
        )
        result = parsers.traffic_json(f"Log:\n{entries_json}")
        assert "Allow TCP x.com:80 app=MyApp" in result[0]["message"]
        assert "App: /a/b/MyApp" in result[0]["message"]
        assert "Reason: test" in result[0]["message"]


class TestRoutingTable:
    SAMPLE = """\
Routing tables

Internet:
Destination        Gateway            Flags               Netif Expire
default            198.18.1.1         UGScg                 en0
10.0.0.0/8         198.18.1.1         UGSc                  en0
127.0.0.1          127.0.0.1          UH                    lo0

Internet6:
Destination        Gateway            Flags               Netif Expire
::1                ::1                UHL                   lo0
fe80::%lo0/64      fe80::1%lo0        UcI                   lo0
"""

    def test_parses_ipv4_routes(self):
        result = parsers.routing_table(self.SAMPLE)
        assert len(result["ipv4"]) == 3
        assert result["ipv4"][0]["destination"] == "default"
        assert result["ipv4"][0]["gateway"] == "198.18.1.1"
        assert result["ipv4"][0]["flags"] == "UGScg"
        assert result["ipv4"][0]["netif"] == "en0"

    def test_parses_ipv6_routes(self):
        result = parsers.routing_table(self.SAMPLE)
        assert len(result["ipv6"]) == 2
        assert result["ipv6"][0]["destination"] == "::1"

    def test_expire_field_optional(self):
        result = parsers.routing_table(self.SAMPLE)
        assert result["ipv4"][0]["expire"] is None

    def test_expire_field_present(self):
        text = "Internet:\nDestination Gateway Flags Netif Expire\n10.0.0.1 10.0.0.2 UGSc en0 300"
        result = parsers.routing_table(text)
        assert result["ipv4"][0]["expire"] == "300"

    def test_empty_text(self):
        result = parsers.routing_table("")
        assert result == {"ipv4": [], "ipv6": []}


class TestLaunchctlList:
    SAMPLE = """\
PID\tStatus\tLabel
-\t0\tcom.apple.Spotlight
1234\t0\tcom.paloaltonetworks.gp.pangps
-\t78\tcom.apple.SafariBookmarksSyncAgent
"""

    def test_parses_entries(self):
        result = parsers.launchctl_list(self.SAMPLE)
        assert len(result) == 3

    def test_running_process(self):
        result = parsers.launchctl_list(self.SAMPLE)
        assert result[1]["pid"] == 1234
        assert result[1]["status"] == 0
        assert result[1]["label"] == "com.paloaltonetworks.gp.pangps"

    def test_not_running_process(self):
        result = parsers.launchctl_list(self.SAMPLE)
        assert result[0]["pid"] is None
        assert result[0]["label"] == "com.apple.Spotlight"

    def test_nonzero_status(self):
        result = parsers.launchctl_list(self.SAMPLE)
        assert result[2]["status"] == 78

    def test_skips_header(self):
        result = parsers.launchctl_list(self.SAMPLE)
        assert all(item["label"] != "Label" for item in result)

    def test_empty_text(self):
        assert parsers.launchctl_list("") == []


class TestBeautifyMessage:
    def test_simple_json(self):
        msg = 'Received config: {"server":"epm.example.com","port":443}'
        result = beautify_message(msg)
        assert result is not None
        assert '"server": "epm.example.com"' in result
        assert "Received config:" in result

    def test_no_json(self):
        assert beautify_message("plain text message") is None

    def test_no_braces(self):
        assert beautify_message("no json at all") is None

    def test_escaped_json(self):
        msg = r"data: {\"key\":\"val\",\"num\":42}"
        result = beautify_message(msg)
        assert result is not None
        assert '"key": "val"' in result

    def test_python_dict(self):
        msg = "config: {'host': 'example.com', 'port': 443}"
        result = beautify_message(msg)
        assert result is not None
        assert '"host": "example.com"' in result

    def test_trivial_json_skipped(self):
        msg = 'value: {"a":1}'
        result = beautify_message(msg)
        assert result is None  # only 1 key, too trivial

    def test_nested_json(self):
        msg = 'result: {"outer":{"inner":"value"},"count":5}'
        result = beautify_message(msg)
        assert result is not None
        assert '"outer": {' in result
        assert '"inner": "value"' in result

    def test_json_in_middle(self):
        msg = 'prefix {"a":1,"b":2} suffix text'
        result = beautify_message(msg)
        assert result is not None
        assert result.startswith("prefix ")
        assert result.endswith(" suffix text")
        assert '"a": 1' in result

    def test_preserves_surrounding_text(self):
        msg = 'START {"x":1,"y":2} END'
        result = beautify_message(msg)
        assert result is not None
        assert "START " in result
        assert " END" in result


# ── Log parsers ──────────────────────────────────────────────────────────


class TestStructuredLog:
    SAMPLE = (
        "2026-04-03T09:24:40.100+02:00 <info> TEST-HOST [1234:5678] Plain message\n"
        "2026-04-03T09:24:41.200+02:00 <error> TEST-HOST [1234:5678] Something broke\n"
    )

    def test_parses_single_entry(self):
        text = "2026-04-03T09:24:40.100+02:00 <info> TEST-HOST [1234:5678] Hello world\n"
        result = parsers.structured_log(text)
        assert len(result) == 1
        assert result[0]["message"] == "Hello world"

    def test_parses_multiple_entries(self):
        result = parsers.structured_log(self.SAMPLE)
        assert len(result) == 2

    def test_multiline_message(self):
        text = (
            "2026-04-03T09:24:40.100+02:00 <info> HOST [1:2] First line\n"
            "  continuation line\n"
            "  another continuation\n"
            "2026-04-03T09:24:41.100+02:00 <info> HOST [1:2] Next entry\n"
        )
        result = parsers.structured_log(text)
        assert len(result) == 2
        assert "continuation line" in result[0]["message"]
        assert "another continuation" in result[0]["message"]

    def test_extracts_level(self):
        result = parsers.structured_log(self.SAMPLE)
        assert result[0]["level"] == "info"
        assert result[1]["level"] == "error"

    def test_extracts_host_and_pid(self):
        result = parsers.structured_log(self.SAMPLE)
        assert result[0]["host"] == "TEST-HOST"
        assert result[0]["pid"] == "1234:5678"

    def test_extracts_timestamp(self):
        result = parsers.structured_log(self.SAMPLE)
        assert result[0]["timestamp"] is not None
        assert isinstance(result[0]["timestamp"], float)

    def test_empty_text(self):
        assert parsers.structured_log("") == []

    def test_no_matching_lines(self):
        assert parsers.structured_log("random text\nno log entries\n") == []


class TestDemLog:
    SAMPLE = (
        "2026-04-03 11:08:50.885+0000 - info: Agent is enabled\n"
        "2026-04-03 11:08:50.886+0000 - warning: WiFi snapshot failed\n"
    )

    def test_parses_entries(self):
        result = parsers.dem_log(self.SAMPLE)
        assert len(result) == 2
        assert result[0]["message"] == "Agent is enabled"

    def test_extracts_level(self):
        result = parsers.dem_log(self.SAMPLE)
        assert result[0]["level"] == "info"
        assert result[1]["level"] == "warning"

    def test_extracts_timestamp(self):
        result = parsers.dem_log(self.SAMPLE)
        assert result[0]["timestamp"] is not None

    def test_multiline_continuation(self):
        text = (
            "2026-04-03 11:08:50.885+0000 - info: First line\n"
            "  continued here\n"
            "2026-04-03 11:08:51.000+0000 - info: Second\n"
        )
        result = parsers.dem_log(text)
        assert len(result) == 2
        assert "continued here" in result[0]["message"]

    def test_empty_text(self):
        assert parsers.dem_log("") == []


class TestDlpLog:
    SAMPLE = "2026/01/08 16:27:19:278  DLPLogger init completed\n2026/01/08 16:27:20:100  DLPLog Logger started\n"

    def test_parses_entries(self):
        result = parsers.dlp_log(self.SAMPLE)
        assert len(result) == 2
        assert result[0]["message"] == "DLPLogger init completed"
        assert result[0]["level"] == "info"

    def test_timestamp_extracted(self):
        result = parsers.dlp_log(self.SAMPLE)
        assert result[0]["timestamp"] is not None

    def test_uses_default_tz_offset(self):
        result_utc = parsers.dlp_log(self.SAMPLE)
        result_offset = parsers.dlp_log(self.SAMPLE, tz="+0200")
        # With +0200, timestamps should be earlier in UTC
        assert result_offset[0]["timestamp"] < result_utc[0]["timestamp"]

    def test_empty_text(self):
        assert parsers.dlp_log("") == []


class TestDlpNetfilter:
    SAMPLE = (
        "[2026-01-08 16:27:19] [INFO] [path/to/file.mm:72] IPC Server running\n"
        "[2026-02-09 22:29:39] [DEBUG] [path/to/file.mm:72] Connection established\n"
    )

    def test_parses_entries(self):
        result = parsers.dlp_netfilter(self.SAMPLE)
        assert len(result) == 2
        assert result[0]["message"] == "IPC Server running"

    def test_extracts_level(self):
        result = parsers.dlp_netfilter(self.SAMPLE)
        assert result[0]["level"] == "info"
        assert result[1]["level"] == "debug"

    def test_strips_source_path_from_message(self):
        result = parsers.dlp_netfilter(self.SAMPLE)
        # The source path [path/to/file.mm:72] should be consumed by the regex, not in message
        assert "path/to/file.mm" not in result[0]["message"]

    def test_empty_text(self):
        assert parsers.dlp_netfilter("") == []


class TestConnectionHistory:
    SAMPLE = """\
Connection History:

Connection #98:
  1. [2026-03-31 09:24:58] Starting connection attempt (best gateway available)
  2. [2026-03-31 09:24:58] Attempting a connection to gateway "Austria"
  3. [2026-03-31 09:25:03] Connected successfully to "Austria" gateway

Connection #99:
  1. [2026-03-31 10:00:00] Starting connection attempt
  2. [2026-03-31 10:00:02] Failed to establish IPSEC tunnel with "US" gateway
  3. [2026-03-31 10:00:03] Could not raise tunnel of any kind with "US" gateway
"""

    def test_parses_successful_connection(self):
        result = parsers.connection_history(self.SAMPLE)
        # Connection #98 has 3 steps → 3 entries
        conn98 = [e for e in result if "#98" in e["message"]]
        assert len(conn98) == 3

    def test_parses_failed_connection(self):
        result = parsers.connection_history(self.SAMPLE)
        conn99 = [e for e in result if "#99" in e["message"]]
        assert len(conn99) == 3

    def test_sets_level_from_outcome(self):
        result = parsers.connection_history(self.SAMPLE)
        conn98 = [e for e in result if "#98" in e["message"]]
        conn99 = [e for e in result if "#99" in e["message"]]
        # Successful connection → info
        assert all(e["level"] == "info" for e in conn98)
        # Failed connection → error
        assert all(e["level"] == "error" for e in conn99)

    def test_extracts_gateway(self):
        result = parsers.connection_history(self.SAMPLE)
        conn98 = [e for e in result if "#98" in e["message"]]
        assert any("Austria" in e["message"] for e in conn98)

    def test_connection_label_format(self):
        result = parsers.connection_history(self.SAMPLE)
        # Should contain "Connection #98 [Austria] (connected) — ..."
        assert any("(connected)" in e["message"] for e in result)
        assert any("(failed)" in e["message"] for e in result)

    def test_timestamps_extracted(self):
        result = parsers.connection_history(self.SAMPLE)
        for entry in result:
            assert entry["timestamp"] is not None

    def test_total_entries(self):
        result = parsers.connection_history(self.SAMPLE)
        assert len(result) == 6  # 3 steps per connection x 2 connections

    def test_empty_text(self):
        assert parsers.connection_history("") == []


class TestEventTable:
    SAMPLE = """\
Id          Local Time           Event Type              Details
----------- -------------------- ----------------------- ------
126273      2026-04-02 00:51:26  Tamper Detection        Sprot: blocking read dir event
126274      2026-04-02 00:53:28  Configuration Change    Config updated successfully
"""

    def test_parses_entries(self):
        result = parsers.event_table(self.SAMPLE)
        assert len(result) == 2

    def test_extracts_event_type(self):
        result = parsers.event_table(self.SAMPLE)
        assert result[0]["event_type"] == "Tamper Detection"
        assert result[1]["event_type"] == "Configuration Change"

    def test_message_includes_event_type(self):
        result = parsers.event_table(self.SAMPLE)
        assert "[Tamper Detection]" in result[0]["message"]
        assert "Sprot:" in result[0]["message"]

    def test_skips_header_and_separator(self):
        result = parsers.event_table(self.SAMPLE)
        assert all(e["id"] != 0 for e in result)
        assert all("Id" not in e.get("event_type", "") for e in result)

    def test_empty_text(self):
        assert parsers.event_table("") == []


class TestRemoteShell:
    SAMPLE = (
        "2026-03-18T12:43:10.990+01:00 | INFO     | 63397 | MainThread       "
        "| remote_shell | Starting ZTNA Remote Shell v24.5\n"
        "2026-03-18T12:43:11.100+01:00 | DEBUG    | 63397 | MainThread       "
        "| remote_shell | Configuration loaded\n"
    )

    def test_parses_entries(self):
        result = parsers.remote_shell(self.SAMPLE)
        assert len(result) == 2

    def test_extracts_level(self):
        result = parsers.remote_shell(self.SAMPLE)
        assert result[0]["level"] == "info"
        assert result[1]["level"] == "debug"

    def test_extracts_timestamp(self):
        result = parsers.remote_shell(self.SAMPLE)
        assert result[0]["timestamp"] is not None

    def test_empty_text(self):
        assert parsers.remote_shell("") == []


# ── Untested state parsers ───────────────────────────────────────────────


class TestEpmCommands:
    # Parser uses split() and takes parts[-5] as state, parts[-4:-2] as received, parts[-2:] as finished.
    # Priority/Retry fields get lumped into command — that's the current parser behavior.
    SAMPLE = """\
ID                                   Command           State     Priority Retry Received            Finished
d59cb947-6969-49ab-a80b-64a647039159 Get Configuration Completed 0        0     2026-03-24 02:51:45 2026-03-24 02:51:47
"""

    def test_parses_entries(self):
        result = parsers.epm_commands(self.SAMPLE)
        assert len(result) == 1

    def test_extracts_uuid(self):
        result = parsers.epm_commands(self.SAMPLE)
        assert result[0]["id"] == "d59cb947-6969-49ab-a80b-64a647039159"

    def test_extracts_command_includes_extra_fields(self):
        """Parser lumps Priority/Retry into command — test actual behavior."""
        result = parsers.epm_commands(self.SAMPLE)
        assert "Get" in result[0]["command"]
        assert "Configuration" in result[0]["command"]

    def test_extracts_timestamps(self):
        result = parsers.epm_commands(self.SAMPLE)
        assert result[0]["received"] is not None
        assert result[0]["finished"] is not None

    def test_empty_text(self):
        assert parsers.epm_commands("") == []


class TestTrafficRdns:
    def test_parses_valid_json(self):
        text = json.dumps(
            {
                "ReverseDnsCache": {
                    "cname_record": [{"cname": "a.com", "hostnames": ["b.com"]}],
                    "ip_record": [{"ip": "1.2.3.4", "hostnames": ["c.com"]}],
                }
            }
        )
        result = parsers.traffic_rdns(text)
        assert "error" not in result

    def test_extracts_cname_records(self):
        text = json.dumps(
            {
                "ReverseDnsCache": {
                    "cname_record": [{"cname": "a.com", "hostnames": ["b.com"]}],
                    "ip_record": [],
                }
            }
        )
        result = parsers.traffic_rdns(text)
        assert len(result["cname_records"]) == 1
        assert result["cname_records"][0]["cname"] == "a.com"

    def test_extracts_ip_records(self):
        text = json.dumps(
            {
                "ReverseDnsCache": {
                    "cname_record": [],
                    "ip_record": [{"ip": "1.2.3.4", "hostnames": ["example.com"]}],
                }
            }
        )
        result = parsers.traffic_rdns(text)
        assert len(result["ip_records"]) == 1
        assert result["ip_records"][0]["ip"] == "1.2.3.4"

    def test_invalid_json(self):
        result = parsers.traffic_rdns("not valid json")
        assert result == {"error": "Invalid JSON"}


class TestSystemExtensions:
    SAMPLE = """\
--- com.apple.system_extension.network_extension
enabled\tactive\tteamID\tbundleID (version)\tname\t[state]
*\t*\tPALO_ID\tcom.paloaltonetworks.GlobalProtect.network-extension (26.1.2)\tGlobalProtect Network Extension\t[activated enabled]
--- com.apple.system_extension.endpoint_security
enabled\tactive\tteamID\tbundleID (version)\tname\t[state]
*\t-\tPALO_ID\tcom.paloaltonetworks.GlobalProtect.endpoint-security (26.1.2)\tGlobalProtect Endpoint Security\t[terminated]
"""

    def test_parses_extensions(self):
        result = parsers.system_extensions(self.SAMPLE)
        assert len(result) == 2

    def test_categorizes_network_extension(self):
        result = parsers.system_extensions(self.SAMPLE)
        net_exts = [e for e in result if e["category"] == "network_extension"]
        assert len(net_exts) == 1

    def test_categorizes_endpoint_security(self):
        result = parsers.system_extensions(self.SAMPLE)
        sec_exts = [e for e in result if e["category"] == "endpoint_security"]
        assert len(sec_exts) == 1

    def test_extracts_version(self):
        result = parsers.system_extensions(self.SAMPLE)
        assert result[0]["version"] == "26.1.2"

    def test_detects_enabled_active_state(self):
        result = parsers.system_extensions(self.SAMPLE)
        assert result[0]["enabled"] is True
        assert result[0]["active"] is True
        assert result[1]["active"] is False

    def test_empty_text(self):
        assert parsers.system_extensions("") == []


class TestAppList:
    def test_parses_app_names(self):
        text = "Google Chrome\nSafari\nSlack\n"
        result = parsers.app_list(text)
        assert result == ["Google Chrome", "Safari", "Slack"]

    def test_strips_whitespace(self):
        text = "  App One  \n  App Two  \n"
        result = parsers.app_list(text)
        assert result == ["App One", "App Two"]

    def test_empty_text(self):
        assert parsers.app_list("") == []


class TestRawText:
    def test_returns_text_as_is(self):
        text = "some raw text\nwith lines"
        assert parsers.raw_text(text) == text

    def test_preserves_whitespace(self):
        text = "  leading spaces  \n\ttabs\n"
        assert parsers.raw_text(text) == text
