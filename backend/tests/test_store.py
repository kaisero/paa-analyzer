"""Tests for SQLite-backed SessionStore."""

from backend.pipeline import parse_zip
from backend.store import SessionStore


def _build_store_with_session(sid="test123"):
    """Helper: create a fresh store with one parsed session."""
    from backend.tests.conftest import build_sample_zip

    st = SessionStore()
    result = parse_zip(build_sample_zip())
    st.add_session(
        {"id": sid, "filename": "test.zip", "file_size": 1000, "parse_status": "complete"},
        result["logs"],
        result["state"],
        result["hip"],
    )
    return st


class TestSessionLifecycle:
    """Test SessionStore session management operations directly."""

    def test_add_and_retrieve_session(self):
        st = _build_store_with_session()
        session = st.get_session("test123")
        assert session is not None
        assert session["id"] == "test123"

    def test_list_sessions(self):
        st = _build_store_with_session()
        sessions = st.list_sessions()
        assert len(sessions) == 1
        assert sessions[0]["id"] == "test123"

    def test_list_sessions_empty(self):
        st = SessionStore()
        assert st.list_sessions() == []

    def test_get_missing_session(self):
        st = SessionStore()
        assert st.get_session("nonexistent") is None

    def test_delete_returns_true(self):
        st = _build_store_with_session()
        assert st.delete_session("test123") is True

    def test_delete_nonexistent_returns_false(self):
        st = SessionStore()
        assert st.delete_session("nonexistent") is False

    def test_delete_cleans_all_internal_state(self):
        st = _build_store_with_session()
        st.delete_session("test123")
        assert "test123" not in st._sessions
        assert "test123" not in st._dbs
        assert "test123" not in st._log_meta
        assert "test123" not in st._state
        assert "test123" not in st._hip

    def test_multiple_sessions_independent(self):
        from backend.tests.conftest import build_sample_zip

        st = SessionStore()
        result = parse_zip(build_sample_zip())
        st.add_session({"id": "a", "filename": "a.zip"}, result["logs"], result["state"], result["hip"])
        result2 = parse_zip(build_sample_zip())
        st.add_session({"id": "b", "filename": "b.zip"}, result2["logs"], result2["state"], result2["hip"])
        assert len(st.list_sessions()) == 2
        st.delete_session("a")
        assert st.get_session("a") is None
        assert st.get_session("b") is not None


class TestLogQueryEdgeCases:
    """Test log query filtering, pagination, and edge cases."""

    def test_filter_by_level(self):
        st = _build_store_with_session("q1")
        entries, total = st.get_logs("q1", source="Agent.Core.PAS", level="error")
        assert total > 0
        assert all(e["level"] == "error" for e in entries)

    def test_filter_by_level_all_returns_everything(self):
        st = _build_store_with_session("q1")
        _, total_all = st.get_logs("q1", source="Agent.Core.PAS", level="all")
        _, total_none = st.get_logs("q1", source="Agent.Core.PAS")
        assert total_all == total_none

    def test_search_matches_message(self):
        st = _build_store_with_session("q1")
        _, total = st.get_logs("q1", search="config")
        assert total > 0

    def test_sort_ascending(self):
        st = _build_store_with_session("q1")
        entries, _ = st.get_logs("q1", sort="asc", page_size=0)
        timestamps = [e["timestamp"] for e in entries if e["timestamp"]]
        for i in range(1, len(timestamps)):
            assert timestamps[i] >= timestamps[i - 1]

    def test_sort_descending(self):
        st = _build_store_with_session("q1")
        entries, _ = st.get_logs("q1", sort="desc", page_size=0)
        timestamps = [e["timestamp"] for e in entries if e["timestamp"]]
        for i in range(1, len(timestamps)):
            assert timestamps[i] <= timestamps[i - 1]

    def test_page_size_zero_returns_all(self):
        st = _build_store_with_session("q1")
        entries, total = st.get_logs("q1", page_size=0)
        assert len(entries) == total

    def test_pagination_beyond_total(self):
        st = _build_store_with_session("q1")
        entries, total = st.get_logs("q1", page=9999, page_size=10)
        assert entries == []
        assert total > 0

    def test_missing_session_returns_empty(self):
        st = SessionStore()
        entries, total = st.get_logs("nonexistent")
        assert entries == []
        assert total == 0


class TestStateQueryEdgeCases:
    def test_get_state_keys(self):
        st = _build_store_with_session("s1")
        keys = st.get_state_keys("s1")
        assert len(keys) > 0
        key_names = [k["key"] for k in keys]
        assert "Agent.Core.status" in key_names

    def test_get_state_returns_data(self):
        st = _build_store_with_session("s1")
        state = st.get_state("s1", "Agent.Core.status")
        assert state is not None
        assert "data" in state
        assert "_meta" in state

    def test_get_state_missing_key(self):
        st = _build_store_with_session("s1")
        assert st.get_state("s1", "nonexistent.key") is None

    def test_get_state_keys_missing_session(self):
        st = SessionStore()
        assert st.get_state_keys("nonexistent") == []


class TestSQLiteStore:
    def test_session_creates_sqlite_db(self, app_client, session_id):
        """Uploading a session should create a SQLite database."""
        from backend.store import store

        assert session_id in store._dbs
        conn = store._dbs[session_id]
        count = conn.execute("SELECT COUNT(*) FROM logs").fetchone()[0]
        assert count > 0

    def test_delete_session_closes_db(self, app_client, session_id):
        from backend.store import store

        resp = app_client.delete(f"/api/v1/sessions/{session_id}")
        assert resp.status_code == 200
        assert session_id not in store._dbs


class TestLogSources:
    def test_returns_correct_counts(self, app_client, session_id):
        resp = app_client.get(f"/api/v1/sessions/{session_id}/logs/sources")
        sources = resp.json()["data"]
        traffic = next(s for s in sources if s["source"] == "Agent.Core.traffic_log_json")
        assert traffic["total_entries"] == 3

    def test_time_range_is_iso_string(self, app_client, session_id):
        resp = app_client.get(f"/api/v1/sessions/{session_id}/logs/sources")
        sources = resp.json()["data"]
        for src in sources:
            tr = src["time_range"]
            if tr["from"]:
                assert isinstance(tr["from"], str)
                assert "T" in tr["from"]

    def test_level_distribution(self, app_client, session_id):
        resp = app_client.get(f"/api/v1/sessions/{session_id}/logs/sources")
        sources = resp.json()["data"]
        traffic = next(s for s in sources if s["source"] == "Agent.Core.traffic_log_json")
        assert "info" in traffic["levels"]


class TestQueryResults:
    def test_source_field_injected(self, app_client, session_id):
        """API response entries should have source field injected from metadata."""
        resp = app_client.get(
            f"/api/v1/sessions/{session_id}/logs",
            params={"source": "Agent.Core.traffic_log_json"},
        )
        entries = resp.json()["data"]
        for entry in entries:
            assert entry["source"] == "traffic_log_json"

    def test_timestamp_is_iso_string(self, app_client, session_id):
        resp = app_client.get(
            f"/api/v1/sessions/{session_id}/logs",
            params={"source": "Agent.Core.traffic_log_json"},
        )
        entries = resp.json()["data"]
        for entry in entries:
            assert isinstance(entry["timestamp"], str)
            assert "T" in entry["timestamp"]

    def test_extra_fields_unpacked(self, app_client, session_id):
        """Parser-specific fields (stored as JSON) should be unpacked in response."""
        resp = app_client.get(
            f"/api/v1/sessions/{session_id}/logs",
            params={"source": "Agent.Core.traffic_log_json"},
        )
        entry = resp.json()["data"][0]
        assert "destination" in entry
        assert "protocol" in entry
        assert "verdict" in entry
        assert "reason" in entry

    def test_search_matches_source_name(self, app_client, session_id):
        """Searching by source name should find entries."""
        resp = app_client.get(
            f"/api/v1/sessions/{session_id}/logs",
            params={"search": "traffic_log_json"},
        )
        assert resp.json()["meta"]["total"] > 0

    def test_beautified_computed_lazily(self, app_client, session_id):
        """Beautified field should be computed at query time for eligible entries."""
        resp = app_client.get(
            f"/api/v1/sessions/{session_id}/logs",
            params={"source": "Agent.Core.PAS", "search": "config"},
        )
        entries = resp.json()["data"]
        assert len(entries) > 0
        assert "beautified" in entries[0]

    def test_forwarding_profile_entries_have_reason(self, app_client, session_id):
        """get_log_entries used by forwarding-profile should include reason field."""
        from backend.store import store

        entries = store.get_log_entries(session_id, "Agent.Core.traffic_log_json")
        assert len(entries) > 0
        reasons = [e.get("reason", "") for e in entries]
        assert any("Rule priority" in r for r in reasons)
