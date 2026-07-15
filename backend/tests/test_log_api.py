"""Tests for log API endpoints."""


class TestGetLogSources:
    def test_returns_sources(self, app_client, session_id):
        resp = app_client.get(f"/api/v1/sessions/{session_id}/logs/sources")
        assert resp.status_code == 200
        sources = resp.json()["data"]
        source_keys = [s["source"] for s in sources]
        assert "Agent.Core.traffic_log_json" in source_keys

    def test_404_for_missing_session(self, app_client):
        resp = app_client.get("/api/v1/sessions/nonexistent/logs/sources")
        assert resp.status_code == 404


class TestGetLogs:
    def test_returns_paginated_entries(self, app_client, session_id):
        resp = app_client.get(
            f"/api/v1/sessions/{session_id}/logs",
            params={"source": "Agent.Core.traffic_log_json"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "data" in data
        assert "meta" in data
        assert data["meta"]["total"] == 3
        assert len(data["data"]) == 3

    def test_traffic_json_entries_have_source(self, app_client, session_id):
        resp = app_client.get(
            f"/api/v1/sessions/{session_id}/logs",
            params={"source": "Agent.Core.traffic_log_json"},
        )
        entries = resp.json()["data"]
        for entry in entries:
            assert entry["source"] == "traffic_log_json"

    def test_traffic_json_entries_have_enriched_message(self, app_client, session_id):
        resp = app_client.get(
            f"/api/v1/sessions/{session_id}/logs",
            params={"source": "Agent.Core.traffic_log_json"},
        )
        entry = resp.json()["data"][0]
        assert "\n" in entry["message"]
        assert "App:" in entry["message"]
        assert "Reason:" in entry["message"]

    def test_traffic_json_entries_have_raw_fields(self, app_client, session_id):
        resp = app_client.get(
            f"/api/v1/sessions/{session_id}/logs",
            params={"source": "Agent.Core.traffic_log_json"},
        )
        entry = resp.json()["data"][0]
        assert "index" in entry
        assert "traffic_type" in entry

    def test_search_across_fields(self, app_client, session_id):
        resp = app_client.get(
            f"/api/v1/sessions/{session_id}/logs",
            params={"source": "Agent.Core.traffic_log_json", "search": "netflix"},
        )
        assert resp.json()["meta"]["total"] == 1
        assert "netflix" in resp.json()["data"][0]["destination"]

    def test_search_on_reason_field(self, app_client, session_id):
        resp = app_client.get(
            f"/api/v1/sessions/{session_id}/logs",
            params={"source": "Agent.Core.traffic_log_json", "search": "Rule priority 1"},
        )
        assert resp.json()["meta"]["total"] == 1

    def test_pagination(self, app_client, session_id):
        resp = app_client.get(
            f"/api/v1/sessions/{session_id}/logs",
            params={"source": "Agent.Core.traffic_log_json", "page": 1, "page_size": 2},
        )
        data = resp.json()
        assert len(data["data"]) == 2
        assert data["meta"]["total"] == 3
        assert data["meta"]["has_next"] is True

    def test_sort_asc(self, app_client, session_id):
        resp = app_client.get(
            f"/api/v1/sessions/{session_id}/logs",
            params={"source": "Agent.Core.traffic_log_json", "sort": "asc"},
        )
        entries = resp.json()["data"]
        timestamps = [e["timestamp"] for e in entries]
        assert timestamps == sorted(timestamps)

    def test_beautified_field_for_json_entries(self, app_client, session_id):
        resp = app_client.get(
            f"/api/v1/sessions/{session_id}/logs",
            params={"source": "Agent.Core.PAS", "search": "config"},
        )
        entries = resp.json()["data"]
        assert len(entries) > 0
        entry = entries[0]
        assert "beautified" in entry
        assert '"server"' in entry["beautified"]

    def test_404_for_missing_session(self, app_client):
        resp = app_client.get("/api/v1/sessions/nonexistent/logs")
        assert resp.status_code == 404
