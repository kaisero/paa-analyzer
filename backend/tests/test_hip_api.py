"""Tests for HIP (Host Information Profile) API endpoints.

`session_id` (see conftest.py) is built from `build_sample_zip()`, which now
bundles the real redacted PACompliance*/PAComplianceMp* fixtures under
backend/tests/fixtures/hip/ alongside a real pacli_hip_status.log -- so these
tests exercise the actual parse -> build_hip_data -> store -> API path, not
hand-authored HIP data.
"""

from __future__ import annotations

import zipfile
from io import BytesIO


def _upload_empty_zip(app_client) -> str:
    """A valid ZIP with no compliance logs at all -- the case build_hip_data
    must still turn into the documented empty shape rather than a 404."""
    buf = BytesIO()
    with zipfile.ZipFile(buf, "w"):
        pass
    resp = app_client.post(
        "/api/v1/sessions",
        files={"file": ("empty.zip", buf.getvalue(), "application/zip")},
    )
    assert resp.status_code == 201
    session_id: str = resp.json()["data"]["id"]
    return session_id


class TestGetHip:
    def test_returns_expected_top_level_shape(self, app_client, session_id):
        resp = app_client.get(f"/api/v1/sessions/{session_id}/hip")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert set(data) == {"platform", "collection", "next_check", "gateways", "cycles"}

    def test_platform_is_macos(self, app_client, session_id):
        resp = app_client.get(f"/api/v1/sessions/{session_id}/hip")
        assert resp.json()["data"]["platform"] == "macos"

    def test_two_cycles_from_the_sample_bundle(self, app_client, session_id):
        resp = app_client.get(f"/api/v1/sessions/{session_id}/hip")
        cycles = resp.json()["data"]["cycles"]
        assert [c["index"] for c in cycles] == [0, 1]

    def test_gateways_come_from_the_real_hip_status_fixture(self, app_client, session_id):
        resp = app_client.get(f"/api/v1/sessions/{session_id}/hip")
        gateways = resp.json()["data"]["gateways"]
        assert len(gateways) == 10
        assert gateways[0]["gateway"] == "EPM"

    def test_does_not_leak_raw_xml(self, app_client, session_id):
        resp = app_client.get(f"/api/v1/sessions/{session_id}/hip")
        data = resp.json()["data"]
        assert "_raw" not in data
        for cycle in data["cycles"]:
            assert "raw_xml" not in cycle
            assert "raw_patches_xml" not in cycle

    def test_404_for_missing_session(self, app_client):
        resp = app_client.get("/api/v1/sessions/nonexistent/hip")
        assert resp.status_code == 404

    def test_empty_shape_when_bundle_has_no_compliance_logs(self, app_client):
        sid = _upload_empty_zip(app_client)
        resp = app_client.get(f"/api/v1/sessions/{sid}/hip")
        assert resp.status_code == 200
        assert resp.json()["data"] == {
            "platform": "unknown",
            "collection": None,
            "next_check": None,
            "gateways": [],
            "cycles": [],
        }

    def test_empty_shape_for_a_session_whose_parse_failed(self, app_client):
        """The parse-failure path (backend/api/sessions.py) stores `hip={}`
        for an errored session, not the build_hip_data() shape -- get_hip()
        must still hand back the documented empty shape rather than `{}`, or
        the frontend HIP page crashes on `hip.cycles.length` (see
        HipPage.test.tsx's matching case)."""
        resp = app_client.post(
            "/api/v1/sessions",
            files={"file": ("bad.zip", b"not-actually-a-zip", "application/zip")},
        )
        assert resp.status_code == 201
        session = resp.json()["data"]
        assert session["parse_status"] == "error"

        hip_resp = app_client.get(f"/api/v1/sessions/{session['id']}/hip")
        assert hip_resp.status_code == 200
        assert hip_resp.json()["data"] == {
            "platform": "unknown",
            "collection": None,
            "next_check": None,
            "gateways": [],
            "cycles": [],
        }


class TestGetHipRaw:
    def test_returns_raw_xml_for_a_valid_cycle(self, app_client, session_id):
        resp = app_client.get(f"/api/v1/sessions/{session_id}/hip/cycles/0/raw")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["raw_xml"].startswith("<?xml")
        assert data["raw_xml"].endswith("</hip-report>")
        assert data["raw_patches_xml"].startswith("<missing-patches>")
        assert data["raw_patches_xml"].endswith("</missing-patches>")

    def test_404_for_out_of_range_cycle_index(self, app_client, session_id):
        resp = app_client.get(f"/api/v1/sessions/{session_id}/hip/cycles/99/raw")
        assert resp.status_code == 404

    def test_404_for_missing_session(self, app_client):
        resp = app_client.get("/api/v1/sessions/nonexistent/hip/cycles/0/raw")
        assert resp.status_code == 404

    def test_404_when_bundle_has_no_cycles(self, app_client):
        sid = _upload_empty_zip(app_client)
        resp = app_client.get(f"/api/v1/sessions/{sid}/hip/cycles/0/raw")
        assert resp.status_code == 404
