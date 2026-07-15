"""End-to-end tests using the real example troubleshooting ZIP.

These tests validate the full pipeline with production-like input data.
Skipped if examples/paa_macos_example.zip is not present.
"""

import pytest

from backend.main import create_app
from backend.store import store as global_store

pytestmark = [pytest.mark.e2e, pytest.mark.slow]


class TestE2ERealData:
    """Test parse_zip with the real 37MB example bundle."""

    def test_parses_without_errors(self, real_parsed_result):
        manifest = real_parsed_result["manifest"]
        assert manifest["errors"] == 0

    def test_has_state_entries(self, real_parsed_result):
        assert real_parsed_result["manifest"]["total_state_files"] > 10

    def test_has_log_sources(self, real_parsed_result):
        assert real_parsed_result["manifest"]["total_log_sources"] > 5

    def test_total_log_entries_reasonable(self, real_parsed_result):
        assert real_parsed_result["manifest"]["total_log_entries"] > 1000

    def test_expected_state_keys_present(self, real_parsed_result):
        state = real_parsed_result["state"]
        expected = ["Agent.Core.status", "Agent.Core.version", "Agent.Networking.traffic_show"]
        for key in expected:
            assert key in state, f"Expected state key {key} not found"

    def test_expected_log_sources_present(self, real_parsed_result):
        logs = real_parsed_result["logs"]
        # At minimum PAS and traffic_log_json should be present
        assert any("PAS" in k for k in logs), "PAS log source not found"
        assert any("traffic_log_json" in k for k in logs), "traffic_log_json not found"

    def test_structured_log_entries_have_fields(self, real_parsed_result):
        """PAS entries should have timestamp, level, host, pid, message."""
        pas_key = next((k for k in real_parsed_result["logs"] if "PAS" in k), None)
        assert pas_key is not None
        entries = real_parsed_result["logs"][pas_key]["entries"]
        assert len(entries) > 0
        entry = entries[0]
        assert "timestamp" in entry
        assert "level" in entry
        assert "message" in entry

    def test_forwarding_profile_has_rules(self, real_parsed_result):
        traffic_show = real_parsed_result["state"].get("Agent.Networking.traffic_show")
        if traffic_show:
            rules = traffic_show["data"].get("rules", [])
            assert len(rules) > 0

    def test_routing_table_has_ipv4(self, real_parsed_result):
        routing = real_parsed_result["state"].get("System.Networking.routing")
        if routing:
            assert len(routing["data"]["ipv4"]) > 0

    def test_timezone_offset_extracted(self, real_parsed_result):
        assert real_parsed_result["manifest"]["timezone_offset"] is not None

    def test_log_entries_sorted_by_timestamp(self, real_parsed_result):
        """All log sources should have entries sorted by timestamp."""
        for key, log_data in real_parsed_result["logs"].items():
            entries = log_data["entries"]
            if len(entries) < 2:
                continue
            timestamps = [e.get("timestamp") or 0 for e in entries]
            for i in range(1, len(timestamps)):
                assert timestamps[i] >= timestamps[i - 1], f"Unsorted entries in {key}"


class TestE2EWindowsData:
    """Test parse_zip with the real Windows example bundle."""

    def test_parses_without_errors(self, win_parsed_result):
        assert win_parsed_result["manifest"]["errors"] == 0

    def test_platform_detected_as_windows(self, win_parsed_result):
        assert win_parsed_result["manifest"]["platform"] == "windows"

    def test_has_state_entries(self, win_parsed_result):
        assert win_parsed_result["manifest"]["total_state_files"] > 20

    def test_has_log_sources(self, win_parsed_result):
        assert win_parsed_result["manifest"]["total_log_sources"] > 10

    def test_total_log_entries(self, win_parsed_result):
        assert win_parsed_result["manifest"]["total_log_entries"] > 10000

    def test_windows_state_keys_present(self, win_parsed_result):
        state = win_parsed_result["state"]
        expected = [
            "System.Core.systeminfo",
            "System.Networking.ipconfig",
            "System.Networking.route",
            "System.Security.WindowsFirewallrules",
        ]
        for key in expected:
            assert key in state, f"Expected Windows state key {key} not found"

    def test_shared_pacli_keys_present(self, win_parsed_result):
        state = win_parsed_result["state"]
        expected = ["Agent.Core.status", "Agent.Core.version"]
        for key in expected:
            assert key in state, f"Expected shared key {key} not found"

    def test_dem_log_entries_parsed(self, win_parsed_result):
        logs = win_parsed_result["logs"]
        dem_keys = [k for k in logs if "ADEM" in k]
        assert len(dem_keys) > 0, "No DEM log sources found"
        total = sum(logs[k]["_meta"]["entry_count"] for k in dem_keys)
        assert total > 100

    def test_paui_log_entries_parsed(self, win_parsed_result):
        logs = win_parsed_result["logs"]
        assert any("PAUI" in k for k in logs), "No PAUI log source found"

    def test_binary_files_skipped(self, win_parsed_result):
        assert win_parsed_result["manifest"]["skipped"] > 10

    def test_timezone_extracted(self, win_parsed_result):
        assert win_parsed_result["manifest"]["timezone_offset"] is not None

    def test_systeminfo_parsed_correctly(self, win_parsed_result):
        si = win_parsed_result["state"]["System.Core.systeminfo"]["data"]
        assert si["host_name"] == "AT-PAA-04"
        assert "Windows" in si.get("os_name", "")


class TestE2EApiRealData:
    """Test the API with real data uploaded through the endpoints."""

    @pytest.fixture(scope="module")
    def real_app_client(self, real_zip_bytes):
        from starlette.testclient import TestClient

        app = create_app()
        client = TestClient(app)
        yield client, real_zip_bytes
        # Cleanup
        global_store._sessions.clear()
        for conn in global_store._dbs.values():
            conn.close()
        global_store._dbs.clear()
        global_store._log_meta.clear()
        global_store._state.clear()

    @pytest.fixture(scope="module")
    def real_session_id(self, real_app_client):
        client, zip_bytes = real_app_client
        resp = client.post(
            "/api/v1/sessions",
            files={"file": ("paa_macos_example.zip", zip_bytes, "application/zip")},
        )
        assert resp.status_code == 201
        return resp.json()["data"]["id"], client

    def test_upload_succeeds(self, real_session_id):
        sid, client = real_session_id
        resp = client.get(f"/api/v1/sessions/{sid}")
        assert resp.status_code == 200
        assert resp.json()["data"]["parse_status"] == "complete"

    def test_log_sources_count(self, real_session_id):
        sid, client = real_session_id
        resp = client.get(f"/api/v1/sessions/{sid}/logs/sources")
        sources = resp.json()["data"]
        assert len(sources) > 5

    def test_query_logs_returns_entries(self, real_session_id):
        sid, client = real_session_id
        resp = client.get(f"/api/v1/sessions/{sid}/logs", params={"page_size": 10})
        assert resp.status_code == 200
        data = resp.json()
        assert data["meta"]["total"] > 0
        assert len(data["data"]) <= 10

    def test_search_filter_works(self, real_session_id):
        sid, client = real_session_id
        resp = client.get(f"/api/v1/sessions/{sid}/logs", params={"search": "tunnel"})
        assert resp.status_code == 200

    def test_state_keys_available(self, real_session_id):
        sid, client = real_session_id
        resp = client.get(f"/api/v1/sessions/{sid}/state")
        keys = resp.json()["data"]
        assert len(keys) > 10

    def test_dashboard_correct(self, real_session_id):
        sid, client = real_session_id
        resp = client.get(f"/api/v1/sessions/{sid}/dashboard")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["total_log_entries"] > 1000
