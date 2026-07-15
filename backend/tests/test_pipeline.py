"""Integration tests for the ZIP parsing pipeline."""

import zipfile
from io import BytesIO

from backend.pipeline import _parse_file, parse_zip


class TestParseFileRouting:
    """Test _parse_file routes files to correct parsers."""

    def test_routes_pacli_status(self):
        result = _parse_file("Pacli Output/pacli_status.log", "pacli_status.log", "State: Enabled", None)
        assert result is not None
        data_type, module, component, name, parsed, raw_text = result
        assert data_type == "state"
        assert module == "Agent"
        assert name == "status"
        assert raw_text is not None  # pacli state files keep raw text

    def test_routes_pacli_traffic_show(self):
        result = _parse_file(
            "Pacli Output/pacli_traffic_show.log",
            "pacli_traffic_show.log",
            "| 0 | Rule | Yes | Any | Any | Data | Direct | 5 |",
            None,
        )
        assert result is not None
        assert result[0] == "state"  # data_type
        assert result[3] == "traffic_show"  # name

    def test_routes_pacli_log_type(self):
        """pacli_connection_history is categorized as a log, not state."""
        result = _parse_file(
            "Pacli Output/pacli_connection_history.log",
            "pacli_connection_history.log",
            "Connection #1:\n  1. [2026-01-01 00:00:00] test",
            None,
        )
        assert result is not None
        assert result[0] == "log"
        assert result[5] is None  # log entries don't keep raw_text

    def test_routes_system_info(self):
        result = _parse_file("sw_vers.txt", "sw_vers.txt", "ProductName: macOS", None)
        assert result is not None
        assert result[0] == "state"
        assert result[1] == "Agent"

    def test_routes_system_info_with_raw_text(self):
        result = _parse_file("routing.txt", "routing.txt", "Internet:\ndefault 10.0.0.1 UGSc en0", None)
        assert result is not None
        assert result[5] is not None  # routing.txt preserves raw_text

    def test_routes_special_file(self):
        result = _parse_file("traffic_log_json.txt", "traffic_log_json.txt", "[]", None)
        assert result is not None
        assert result[0] == "log"

    def test_skips_large_files(self):
        result = _parse_file("networkextensions.txt", "networkextensions.txt", "data", None)
        assert result is None

    def test_routes_dlp_log(self):
        result = _parse_file(
            "DLP/PrismaAccessDLP.log", "PrismaAccessDLP.log", "2026/01/08 16:27:19:278  DLP started", None
        )
        assert result is not None
        assert result[0] == "log"
        assert result[2] == "DLP"

    def test_routes_dlp_netfilter(self):
        result = _parse_file(
            "DLP/netfilterdlp.log", "netfilterdlp.log", "[2026-01-08 16:27:19] [INFO] [f.mm:1] msg", None
        )
        assert result is not None
        assert result[3] == "netfilterdlp"

    def test_routes_dem_log(self):
        result = _parse_file("Logs/DEM/ADEM.log", "ADEM.log", "2026-04-03 11:00:00.000+0000 - info: test", None)
        assert result is not None
        assert result[0] == "log"
        assert result[2] == "ADEM"

    def test_routes_structured_log(self):
        result = _parse_file(
            "Logs/System/PAS.log", "PAS.log", "2026-04-03T09:24:40.100+02:00 <info> HOST [1:2] msg", None
        )
        assert result is not None
        assert result[0] == "log"
        assert result[3] == "PAS"

    def test_skips_unknown_files(self):
        result = _parse_file("random/unknown.txt", "unknown.txt", "data", None)
        assert result is None

    def test_skips_unknown_pacli_file(self):
        result = _parse_file("Pacli Output/pacli_unknown.log", "pacli_unknown.log", "data", None)
        assert result is None


class TestWindowsRouting:
    """Test _parse_file routing for Windows-specific files."""

    def test_routes_machine_info_systeminfo(self):
        result = _parse_file("Machine Info/systeminfo.log", "systeminfo.log", "Host Name: TEST", None)
        assert result is not None
        assert result[0] == "state"
        assert result[1] == "System"
        assert result[2] == "Core"
        assert result[5] is not None  # Machine Info files keep raw_text

    def test_routes_machine_info_ipconfig(self):
        result = _parse_file("Machine Info/ipconfig.log", "ipconfig.log", "Windows IP Configuration", None)
        assert result is not None
        assert result[0] == "state"
        assert result[2] == "Networking"

    def test_routes_machine_info_route(self):
        result = _parse_file("Machine Info/route.log", "route.log", "Interface List", None)
        assert result is not None
        assert result[0] == "state"

    def test_skips_dmp_files(self):
        result = _parse_file("Dumps/PASrv.exe.3504.dmp", "PASrv.exe.3504.dmp", "", None)
        assert result is None

    def test_skips_etl_files(self):
        result = _parse_file("Logs/System/PrismaAccessAgentLog.etl.001", "PrismaAccessAgentLog.etl.001", "", None)
        assert result is None

    def test_skips_msi_logs(self):
        result = _parse_file("Machine Info/MSI logs/MSI76a20.LOG", "MSI76a20.LOG", "data", None)
        assert result is None

    def test_skips_setupapi_logs(self):
        result = _parse_file("Machine Info/setupapi.dev.log", "setupapi.dev.log", "data", None)
        assert result is None

    def test_routes_win_paui_log(self):
        text = "PAUI Information: 0 : 08/01/2026 15:46:48 Test message"
        result = _parse_file("Logs/OliverKaiser/PAUI_OliverKaiser.log", "PAUI_OliverKaiser.log", text, None)
        assert result is not None
        assert result[0] == "log"
        assert result[3] == "PAUI"

    def test_routes_win_dem_before_mac_dem(self):
        """Windows DEM files (palo_alto_networks_dem_*) must use win_dem_log parser."""
        text = "[2026-03-18 13:32:34.071] [default] [info] Agent started"
        result = _parse_file(
            "Logs/DEM/System/palo_alto_networks_dem_agent.log", "palo_alto_networks_dem_agent.log", text, None
        )
        assert result is not None
        assert result[0] == "log"
        assert result[2] == "ADEM"
        assert result[3] == "agent"

    def test_routes_pabrowser(self):
        text = "[4936:6668:0408/103854.684:WARNING:main.cc(1)] Test"
        result = _parse_file("Logs/OliverKaiser/PABrowser.log", "PABrowser.log", text, None)
        assert result is not None
        assert result[0] == "log"
        assert result[3] == "PABrowser"

    def test_skips_guid_paui_files(self):
        result = _parse_file(
            "Logs/OliverKaiser/16d8de08-7144-4c2d-b57c-f1cfa120379cPAUI_OliverKaiser.log",
            "16d8de08-7144-4c2d-b57c-f1cfa120379cPAUI_OliverKaiser.log",
            "",
            None,
        )
        assert result is None

    def test_machine_info_unknown_file_skipped(self):
        result = _parse_file("Machine Info/MSI logs/MSIffa05.LOG", "MSIffa05.LOG", "data", None)
        assert result is None


class TestParseZipEdgeCases:
    def test_empty_zip(self):
        buf = BytesIO()
        with zipfile.ZipFile(buf, "w"):
            pass
        result = parse_zip(buf.getvalue())
        assert result["state"] == {}
        assert result["logs"] == {}
        assert result["manifest"]["total_log_entries"] == 0

    def test_zip_with_directories_only(self):
        buf = BytesIO()
        with zipfile.ZipFile(buf, "w") as zf:
            zf.mkdir("Pacli Output/")
            zf.mkdir("Logs/System/")
        result = parse_zip(buf.getvalue())
        assert result["state"] == {}
        assert result["logs"] == {}

    def test_zip_with_unrecognized_files_skipped(self):
        buf = BytesIO()
        with zipfile.ZipFile(buf, "w") as zf:
            zf.writestr("random_file.txt", "some content")
            zf.writestr("another/file.dat", "more content")
        result = parse_zip(buf.getvalue())
        assert result["state"] == {}
        assert result["logs"] == {}
        assert result["manifest"]["skipped"] == 2

    def test_progress_callback_called(self):
        from backend.tests.conftest import build_sample_zip

        events = []

        def on_progress(stage, pct, detail):
            events.append((stage, pct, detail))

        parse_zip(build_sample_zip(), on_progress=on_progress)
        assert len(events) > 0
        stages = [e[0] for e in events]
        assert "extracting" in stages
        assert "parsing" in stages

    def test_manifest_has_required_fields(self):
        from backend.tests.conftest import build_sample_zip

        result = parse_zip(build_sample_zip())
        manifest = result["manifest"]
        assert "parse_time_ms" in manifest
        assert "timezone_offset" in manifest
        assert "total_log_sources" in manifest
        assert "total_log_entries" in manifest
        assert "total_state_files" in manifest
        assert "errors" in manifest


class TestRawTextStorage:
    def test_pacli_state_files_have_raw_text(self, parsed_result):
        """Pacli state files should store the original raw text."""
        status = parsed_result["state"]["Agent.Core.status"]
        assert "raw_text" in status
        assert isinstance(status["raw_text"], str)
        assert "State:" in status["raw_text"]
        assert "EPM Status:" in status["raw_text"]

    def test_pacli_version_has_raw_text(self, parsed_result):
        version = parsed_result["state"]["Agent.Core.version"]
        assert "raw_text" in version
        assert "26.1.2.4" in version["raw_text"]

    def test_system_info_has_no_raw_text(self, parsed_result):
        """System info files should NOT have raw_text."""
        sw_vers = parsed_result["state"]["Agent.Core.sw_vers"]
        assert "raw_text" not in sw_vers

    def test_uname_has_no_raw_text(self, parsed_result):
        uname = parsed_result["state"]["System.Core.uname"]
        assert "raw_text" not in uname

    def test_routing_has_raw_text(self, parsed_result):
        routing = parsed_result["state"]["System.Networking.routing"]
        assert "raw_text" in routing
        assert "Internet:" in routing["raw_text"]

    def test_launchctl_has_raw_text(self, parsed_result):
        launchctl = parsed_result["state"]["System.Core.launchctl_list"]
        assert "raw_text" in launchctl
        assert "paloaltonetworks" in launchctl["raw_text"]

    def test_system_extensions_has_raw_text(self, parsed_result):
        extensions = parsed_result["state"]["System.Core.system_extension_list"]
        assert "raw_text" in extensions
        assert "network_extension" in extensions["raw_text"]


class TestParseZipStructure:
    def test_state_and_log_separation(self, parsed_result):
        """State and log entries should be correctly categorized."""
        state = parsed_result["state"]
        logs = parsed_result["logs"]

        # Pacli state files → state
        assert "Agent.Core.status" in state
        assert "Agent.Core.version" in state
        assert "Agent.Networking.traffic_show" in state

        # Traffic JSON → logs
        assert "Agent.Core.traffic_log_json" in logs

    def test_manifest_metadata(self, parsed_result):
        manifest = parsed_result["manifest"]
        assert manifest["total_state_files"] > 0
        assert manifest["total_log_sources"] > 0
        assert manifest["parse_time_ms"] >= 0
        assert isinstance(manifest["timezone_offset"], str)

    def test_state_has_meta_and_data(self, parsed_result):
        for key, entry in parsed_result["state"].items():
            assert "_meta" in entry, f"State entry {key} missing _meta"
            assert "data" in entry, f"State entry {key} missing data"
            assert entry["_meta"]["type"] == "state"

    def test_log_entries_have_timestamps(self, parsed_result):
        traffic = parsed_result["logs"]["Agent.Core.traffic_log_json"]
        assert len(traffic["entries"]) == 3
        for entry in traffic["entries"]:
            assert entry.get("timestamp") is not None


class TestParseZipContent:
    def test_forwarding_rules_parsed(self, parsed_result):
        traffic_show = parsed_result["state"]["Agent.Networking.traffic_show"]
        rules = traffic_show["data"]["rules"]
        assert len(rules) == 3
        assert rules[0]["name"] == "ImplicitForwardingRule"
        assert rules[0]["hits"] == 5

    def test_gateway_list_parsed(self, parsed_result):
        gateways = parsed_result["state"]["Agent.Core.gateways_list"]
        assert gateways["data"]["agent_location"] == "AT"
        assert len(gateways["data"]["gateways"]) == 2

    def test_traffic_json_parsed_as_log(self, parsed_result):
        traffic = parsed_result["logs"]["Agent.Core.traffic_log_json"]
        entries = traffic["entries"]
        assert len(entries) == 3
        assert entries[0]["protocol"] == "TCP"
        assert "Rule priority" in entries[0]["reason"]

    def test_traffic_json_entries_no_redundant_fields(self, parsed_result):
        """source and source_file are not stored on entries (memory optimization)."""
        entries = parsed_result["logs"]["Agent.Core.traffic_log_json"]["entries"]
        assert "source" not in entries[0]
        assert "source_file" not in entries[0]

    def test_traffic_json_has_enriched_message(self, parsed_result):
        entries = parsed_result["logs"]["Agent.Core.traffic_log_json"]["entries"]
        msg = entries[0]["message"]
        # Multi-line: summary + app + reason
        assert "\n" in msg
        assert "App:" in msg
        assert "Reason:" in msg

    def test_traffic_json_has_raw_fields(self, parsed_result):
        entries = parsed_result["logs"]["Agent.Core.traffic_log_json"]["entries"]
        assert entries[0]["index"] == 1001
        assert entries[0]["traffic_type"] == "kData"

    def test_routing_table_parsed(self, parsed_result):
        routing = parsed_result["state"]["System.Networking.routing"]
        data = routing["data"]
        assert len(data["ipv4"]) == 3
        assert data["ipv4"][0]["destination"] == "default"
        assert len(data["ipv6"]) == 2

    def test_launchctl_list_parsed(self, parsed_result):
        launchctl = parsed_result["state"]["System.Core.launchctl_list"]
        data = launchctl["data"]
        assert len(data) == 4
        running = [e for e in data if e["pid"] is not None]
        assert len(running) == 2
        assert any("paloaltonetworks" in e["label"] for e in data)

    def test_system_extensions_parsed(self, parsed_result):
        extensions = parsed_result["state"]["System.Core.system_extension_list"]
        data = extensions["data"]
        assert len(data) == 3
        network_exts = [e for e in data if e["category"] == "network_extension"]
        assert len(network_exts) == 2
        security_exts = [e for e in data if e["category"] == "endpoint_security"]
        assert len(security_exts) == 1


class TestBeautification:
    def test_beautified_not_precomputed(self, parsed_result):
        """Beautification is lazy — not stored on entries during parsing."""
        pas_entries = parsed_result["logs"]["Agent.Core.PAS"]["entries"]
        for e in pas_entries:
            assert "beautified" not in e, "beautified should not be pre-computed"

    def test_beautified_computed_lazily_in_api(self, app_client, session_id):
        """Beautification should be computed at query time in the API response."""
        resp = app_client.get(
            f"/api/v1/sessions/{session_id}/logs",
            params={"source": "Agent.Core.PAS", "search": "config"},
        )
        entries = resp.json()["data"]
        assert len(entries) > 0
        entry = entries[0]
        assert "beautified" in entry
        assert '"server": "epm.example.com"' in entry["beautified"]
