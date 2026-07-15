"""Tests for session API endpoints: upload, list, get, delete."""

import zipfile
from io import BytesIO


class TestSessionUpload:
    def test_upload_valid_zip(self, app_client, sample_zip_bytes):
        resp = app_client.post(
            "/api/v1/sessions",
            files={"file": ("test.zip", sample_zip_bytes, "application/zip")},
        )
        assert resp.status_code == 201
        data = resp.json()["data"]
        assert data["parse_status"] == "complete"
        assert data["id"]
        assert data["filename"] == "test.zip"

    def test_upload_non_zip_returns_400(self, app_client):
        resp = app_client.post(
            "/api/v1/sessions",
            files={"file": ("test.txt", b"not a zip", "text/plain")},
        )
        assert resp.status_code == 400

    def test_upload_no_file_returns_422(self, app_client):
        resp = app_client.post("/api/v1/sessions")
        assert resp.status_code == 422

    def test_session_has_manifest_fields(self, app_client, sample_zip_bytes):
        resp = app_client.post(
            "/api/v1/sessions",
            files={"file": ("test.zip", sample_zip_bytes, "application/zip")},
        )
        data = resp.json()["data"]
        assert data["total_log_entries"] > 0
        assert data["total_log_sources"] > 0
        assert data["total_state_files"] > 0
        assert data["parse_duration_ms"] is not None

    def test_upload_invalid_zip_content(self, app_client):
        """Uploading a .zip file with invalid content should result in error status."""
        resp = app_client.post(
            "/api/v1/sessions",
            files={"file": ("bad.zip", b"not-actually-a-zip", "application/zip")},
        )
        data = resp.json()["data"]
        assert data["parse_status"] == "error"
        assert data["parse_error"] is not None

    def test_upload_empty_zip(self, app_client):
        """Uploading an empty (but valid) ZIP should succeed with zero entries."""
        buf = BytesIO()
        with zipfile.ZipFile(buf, "w"):
            pass
        resp = app_client.post(
            "/api/v1/sessions",
            files={"file": ("empty.zip", buf.getvalue(), "application/zip")},
        )
        assert resp.status_code == 201
        data = resp.json()["data"]
        assert data["parse_status"] == "complete"
        assert data["total_log_entries"] == 0


class TestSessionCRUD:
    def test_list_empty(self, app_client):
        resp = app_client.get("/api/v1/sessions")
        assert resp.status_code == 200
        assert resp.json()["data"] == []

    def test_list_after_upload(self, app_client, session_id):
        resp = app_client.get("/api/v1/sessions")
        sessions = resp.json()["data"]
        assert len(sessions) >= 1
        assert any(s["id"] == session_id for s in sessions)

    def test_get_existing_session(self, app_client, session_id):
        resp = app_client.get(f"/api/v1/sessions/{session_id}")
        assert resp.status_code == 200
        assert resp.json()["data"]["id"] == session_id

    def test_get_nonexistent_returns_404(self, app_client):
        resp = app_client.get("/api/v1/sessions/nonexistent")
        assert resp.status_code == 404

    def test_delete_existing(self, app_client, session_id):
        resp = app_client.delete(f"/api/v1/sessions/{session_id}")
        assert resp.status_code == 200
        assert resp.json()["data"]["deleted"] is True

    def test_delete_nonexistent_returns_404(self, app_client):
        resp = app_client.delete("/api/v1/sessions/nonexistent")
        assert resp.status_code == 404

    def test_deleted_session_not_in_list(self, app_client, session_id):
        app_client.delete(f"/api/v1/sessions/{session_id}")
        resp = app_client.get("/api/v1/sessions")
        ids = [s["id"] for s in resp.json()["data"]]
        assert session_id not in ids
