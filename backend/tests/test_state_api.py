"""Tests for state API endpoints."""


class TestListState:
    def test_returns_state_keys(self, app_client, session_id):
        resp = app_client.get(f"/api/v1/sessions/{session_id}/state")
        assert resp.status_code == 200
        keys = resp.json()["data"]
        key_names = [k["key"] for k in keys]
        assert "Agent.Core.status" in key_names
        assert "Agent.Networking.traffic_show" in key_names

    def test_includes_pacli_command(self, app_client, session_id):
        resp = app_client.get(f"/api/v1/sessions/{session_id}/state")
        keys = resp.json()["data"]
        status_key = next(k for k in keys if k["key"] == "Agent.Core.status")
        assert status_key["pacli_command"] == "pacli status"

    def test_non_pacli_has_null_command(self, app_client, session_id):
        resp = app_client.get(f"/api/v1/sessions/{session_id}/state")
        keys = resp.json()["data"]
        sw_vers_key = next(k for k in keys if k["key"] == "Agent.Core.sw_vers")
        assert sw_vers_key["pacli_command"] is None

    def test_404_for_missing_session(self, app_client):
        resp = app_client.get("/api/v1/sessions/nonexistent/state")
        assert resp.status_code == 404


class TestGetState:
    def test_returns_state_data(self, app_client, session_id):
        resp = app_client.get(f"/api/v1/sessions/{session_id}/state/Agent.Core.status")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["data"]["state"] == "Enabled"
        assert data["data"]["epm_status"] == "Up"

    def test_returns_raw_text_for_pacli(self, app_client, session_id):
        resp = app_client.get(f"/api/v1/sessions/{session_id}/state/Agent.Core.status")
        data = resp.json()["data"]
        assert "raw_text" in data
        assert "State:" in data["raw_text"]

    def test_no_raw_text_for_system_info(self, app_client, session_id):
        resp = app_client.get(f"/api/v1/sessions/{session_id}/state/Agent.Core.sw_vers")
        data = resp.json()["data"]
        assert "raw_text" not in data

    def test_404_for_missing_key(self, app_client, session_id):
        resp = app_client.get(f"/api/v1/sessions/{session_id}/state/Nonexistent.Key")
        assert resp.status_code == 404


class TestBatchState:
    def test_returns_multiple_keys(self, app_client, session_id):
        resp = app_client.get(
            f"/api/v1/sessions/{session_id}/state/batch",
            params={"keys": "Agent.Core.status,Agent.Core.version"},
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert "Agent.Core.status" in data
        assert "Agent.Core.version" in data

    def test_omits_missing_keys(self, app_client, session_id):
        resp = app_client.get(
            f"/api/v1/sessions/{session_id}/state/batch",
            params={"keys": "Agent.Core.status,Nonexistent.Key"},
        )
        data = resp.json()["data"]
        assert "Agent.Core.status" in data
        assert "Nonexistent.Key" not in data

    def test_empty_keys(self, app_client, session_id):
        resp = app_client.get(
            f"/api/v1/sessions/{session_id}/state/batch",
            params={"keys": ""},
        )
        assert resp.json()["data"] == {}

    def test_404_for_missing_session(self, app_client):
        resp = app_client.get(
            "/api/v1/sessions/nonexistent/state/batch",
            params={"keys": "Agent.Core.status"},
        )
        assert resp.status_code == 404


class TestForwardingProfile:
    def test_returns_enriched_rules(self, app_client, session_id):
        resp = app_client.get(f"/api/v1/sessions/{session_id}/state/forwarding-profile")
        assert resp.status_code == 200
        data = resp.json()["data"]
        rules = data["rules"]
        assert len(rules) == 3

    def test_computed_hitcounts(self, app_client, session_id):
        resp = app_client.get(f"/api/v1/sessions/{session_id}/state/forwarding-profile")
        rules = resp.json()["data"]["rules"]
        # Rule priority 3 should have 2 hits from traffic log
        default_rule = next(r for r in rules if r["priority"] == 3)
        assert default_rule["traffic_log_hits"] == 2
        # Rule priority 1 should have 1 hit
        video_rule = next(r for r in rules if r["priority"] == 1)
        assert video_rule["traffic_log_hits"] == 1
        # Rule priority 0 should have 0 hits
        implicit_rule = next(r for r in rules if r["priority"] == 0)
        assert implicit_rule["traffic_log_hits"] == 0

    def test_includes_flags(self, app_client, session_id):
        resp = app_client.get(f"/api/v1/sessions/{session_id}/state/forwarding-profile")
        flags = resp.json()["data"]["flags"]
        assert len(flags) == 2
        assert "Block outbound LAN" in flags[0]

    def test_preserves_pacli_hits(self, app_client, session_id):
        resp = app_client.get(f"/api/v1/sessions/{session_id}/state/forwarding-profile")
        rules = resp.json()["data"]["rules"]
        assert rules[0]["hits"] == 5  # original pacli hits preserved

    def test_404_for_missing_session(self, app_client):
        resp = app_client.get("/api/v1/sessions/nonexistent/state/forwarding-profile")
        assert resp.status_code == 404
