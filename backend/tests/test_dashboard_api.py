"""Tests for the dashboard API endpoint."""


class TestDashboard:
    def test_returns_summary(self, app_client, session_id):
        resp = app_client.get(f"/api/v1/sessions/{session_id}/dashboard")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["session_id"] == session_id

    def test_includes_all_fields(self, app_client, session_id):
        resp = app_client.get(f"/api/v1/sessions/{session_id}/dashboard")
        data = resp.json()["data"]
        assert "filename" in data
        assert "total_log_entries" in data
        assert "total_log_sources" in data
        assert "total_state_files" in data
        assert "parse_duration_ms" in data

    def test_counts_match_session(self, app_client, session_id):
        session_resp = app_client.get(f"/api/v1/sessions/{session_id}")
        session = session_resp.json()["data"]
        dash_resp = app_client.get(f"/api/v1/sessions/{session_id}/dashboard")
        dash = dash_resp.json()["data"]
        assert dash["total_log_entries"] == session["total_log_entries"]
        assert dash["total_log_sources"] == session["total_log_sources"]

    def test_404_for_missing_session(self, app_client):
        resp = app_client.get("/api/v1/sessions/nonexistent/dashboard")
        assert resp.status_code == 404
