"""Tests for session API endpoints: upload, list, get, delete."""

import json
import zipfile
from io import BytesIO

import pytest


def _parse_sse_events(body: str) -> list[dict]:
    """Split an SSE ``text/event-stream`` body into decoded JSON payloads.

    TestClient is synchronous, so ``resp.text`` holds the fully materialized
    stream of ``data: {json}\\n\\n`` events.
    """
    events = []
    for block in body.split("\n\n"):
        block = block.strip()
        if not block.startswith("data:"):
            continue
        events.append(json.loads(block[len("data:") :].strip()))
    return events


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


@pytest.mark.api
class TestSessionUploadStream:
    """Tests for the SSE streaming upload endpoint POST /api/v1/sessions/upload."""

    def test_stream_happy_path(self, app_client, sample_zip_bytes):
        resp = app_client.post(
            "/api/v1/sessions/upload",
            files={"file": ("test.zip", sample_zip_bytes, "application/zip")},
        )
        assert resp.status_code == 200
        assert resp.headers["content-type"].startswith("text/event-stream")

        events = _parse_sse_events(resp.text)
        assert events, "expected at least one SSE event"

        # Every progress event (if any survive the race — see below) carries the
        # stage/progress/detail shape the frontend relies on.
        progress_events = [e for e in events if e.get("stage") != "complete"]
        assert all(
            {"stage", "progress", "detail"} <= e.keys() for e in progress_events
        )

        # Terminal event is the completion event with the stored session.
        final = events[-1]
        assert final["stage"] == "complete"
        assert final["progress"] == 100
        session = final["session"]
        assert session["parse_status"] == "complete"
        assert session["id"]

        # The session is actually retrievable — proves it was stored.
        get_resp = app_client.get(f"/api/v1/sessions/{session['id']}")
        assert get_resp.status_code == 200
        assert get_resp.json()["data"]["id"] == session["id"]

    def test_stream_emits_progress_events(self, app_client, sample_zip_bytes, monkeypatch):
        """A slow parse deterministically surfaces the progress-streaming path.

        The real pipeline runs in a thread-pool executor, so for a tiny bundle it
        can finish before the streaming loop drains any progress event. Slowing the
        stub down forces the endpoint's progress-emit and drain branches to run so
        we can assert the SSE progress contract without relying on that race.
        """
        import time

        def slow_parse(data, on_progress=None):
            if on_progress:
                on_progress("extracting", 0, "Opening ZIP...")
                on_progress("parsing", 50, "Parsing files")
            time.sleep(0.3)
            from backend.pipeline import parse_zip as real_parse_zip

            return real_parse_zip(data)

        monkeypatch.setattr("backend.api.sessions.parse_zip", slow_parse)

        resp = app_client.post(
            "/api/v1/sessions/upload",
            files={"file": ("test.zip", sample_zip_bytes, "application/zip")},
        )
        assert resp.status_code == 200

        events = _parse_sse_events(resp.text)
        progress_events = [e for e in events if e.get("stage") != "complete"]
        assert progress_events, "slow parse should surface progress events"
        assert {e["stage"] for e in progress_events} >= {"extracting", "parsing"}
        assert all(isinstance(e["progress"], int) for e in progress_events)

        assert events[-1]["stage"] == "complete"
        assert events[-1]["session"]["parse_status"] == "complete"

    def test_stream_non_zip_returns_400(self, app_client):
        resp = app_client.post(
            "/api/v1/sessions/upload",
            files={"file": ("notes.txt", b"not a zip", "text/plain")},
        )
        assert resp.status_code == 400
        assert "zip" in resp.json()["detail"].lower()

    def test_stream_invalid_zip_content_emits_error_event(self, app_client):
        resp = app_client.post(
            "/api/v1/sessions/upload",
            files={"file": ("bad.zip", b"not-actually-a-zip", "application/zip")},
        )
        assert resp.status_code == 200

        events = _parse_sse_events(resp.text)
        final = events[-1]
        assert final["stage"] == "error"
        assert final["progress"] == -1
        assert final["detail"]

        # An errored session was stored — confirm via the list endpoint.
        listed = app_client.get("/api/v1/sessions").json()["data"]
        errored = [s for s in listed if s["parse_status"] == "error"]
        assert errored
        assert errored[0]["parse_error"]


@pytest.mark.api
class TestUploadSizeGuard:
    """The file-too-large guard on both the streaming and sync endpoints."""

    def test_stream_upload_too_large_returns_400(self, app_client, monkeypatch):
        monkeypatch.setattr("backend.api.sessions.settings.max_upload_bytes", 10)
        resp = app_client.post(
            "/api/v1/sessions/upload",
            files={"file": ("big.zip", b"x" * 64, "application/zip")},
        )
        assert resp.status_code == 400
        assert "too large" in resp.json()["detail"].lower()

    def test_sync_upload_too_large_returns_400(self, app_client, monkeypatch):
        monkeypatch.setattr("backend.api.sessions.settings.max_upload_bytes", 10)
        resp = app_client.post(
            "/api/v1/sessions",
            files={"file": ("big.zip", b"x" * 64, "application/zip")},
        )
        assert resp.status_code == 400
        assert "too large" in resp.json()["detail"].lower()

    def test_within_limit_is_not_rejected(self, app_client, monkeypatch, sample_zip_bytes):
        # A payload at/under the limit must not hit the size guard, proving the
        # 400 above comes from the size check and not the monkeypatch itself.
        monkeypatch.setattr(
            "backend.api.sessions.settings.max_upload_bytes", len(sample_zip_bytes)
        )
        resp = app_client.post(
            "/api/v1/sessions",
            files={"file": ("test.zip", sample_zip_bytes, "application/zip")},
        )
        assert resp.status_code == 201
        assert resp.json()["data"]["parse_status"] == "complete"
