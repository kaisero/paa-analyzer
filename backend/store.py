"""In-memory session store — logs in SQLite :memory:, state in Python dicts."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from typing import Any

from backend.models.session import LogSource
from paa_analyzer.parsers import beautify_message, format_ts
from paa_analyzer.taxonomy import PACLI_COMMAND_MAP

# Fields stored as dedicated columns (not in extra JSON)
_STANDARD_FIELDS = {"timestamp", "level", "message", "host", "pid", "beautified"}


class SessionStore:
    def __init__(self) -> None:
        self._sessions: dict[str, dict[str, Any]] = {}
        self._dbs: dict[str, sqlite3.Connection] = {}  # session -> SQLite connection
        self._log_meta: dict[str, dict[str, dict[str, Any]]] = {}  # session -> source_key -> {module, component, name}
        self._state: dict[str, dict[str, dict[str, Any]]] = {}  # session -> state_key -> data
        self._hip: dict[str, dict[str, Any]] = {}  # session -> HipData (see paa_analyzer.hip.build_hip_data)

    def add_session(
        self,
        session_dict: dict[str, Any],
        logs: dict[str, Any],
        state: dict[str, dict[str, Any]],
        hip: dict[str, Any],
    ) -> None:
        sid = session_dict["id"]
        self._sessions[sid] = session_dict
        self._state[sid] = state
        self._hip[sid] = hip
        self._log_meta[sid] = {}

        conn = sqlite3.connect(":memory:", check_same_thread=False)
        conn.execute("PRAGMA journal_mode = OFF")
        conn.execute("PRAGMA synchronous = 0")
        conn.execute("PRAGMA temp_store = MEMORY")
        conn.execute("""CREATE TABLE logs (
            id INTEGER PRIMARY KEY,
            source_key TEXT NOT NULL,
            timestamp REAL,
            level TEXT,
            message TEXT,
            host TEXT,
            pid TEXT,
            extra TEXT
        )""")

        row_id = 0
        for key, log_data in logs.items():
            meta = log_data["_meta"]
            self._log_meta[sid][key] = {
                "module": meta["module"],
                "component": meta["component"],
                "name": meta["name"],
            }
            batch = []
            for e in log_data["entries"]:
                row_id += 1
                extras = {k: v for k, v in e.items() if k not in _STANDARD_FIELDS}
                batch.append(
                    (
                        row_id,
                        key,
                        e.get("timestamp"),
                        e.get("level", ""),
                        e.get("message", ""),
                        e.get("host"),
                        e.get("pid"),
                        json.dumps(extras) if extras else None,
                    )
                )
                if len(batch) >= 50000:
                    conn.executemany("INSERT INTO logs VALUES (?,?,?,?,?,?,?,?)", batch)
                    batch = []
            if batch:
                conn.executemany("INSERT INTO logs VALUES (?,?,?,?,?,?,?,?)", batch)
            # Free parsed entries as we go to reduce peak memory
            log_data["entries"] = []

        # Create indexes after bulk insert (faster)
        conn.execute("CREATE INDEX idx_source_ts ON logs(source_key, timestamp)")
        conn.execute("CREATE INDEX idx_source_level ON logs(source_key, level)")
        conn.commit()
        self._dbs[sid] = conn

    def get_session(self, sid: str) -> dict[str, Any] | None:
        return self._sessions.get(sid)

    def list_sessions(self) -> list[dict[str, Any]]:
        return list(self._sessions.values())

    def delete_session(self, sid: str) -> bool:
        if sid not in self._sessions:
            return False
        del self._sessions[sid]
        conn = self._dbs.pop(sid, None)
        if conn:
            conn.close()
        self._log_meta.pop(sid, None)
        self._state.pop(sid, None)
        self._hip.pop(sid, None)
        return True

    def get_log_sources(self, sid: str) -> list[LogSource]:
        conn = self._dbs.get(sid)
        if not conn:
            return []

        # Aggregate counts, levels, and time ranges per source in SQL
        rows = conn.execute("""
            SELECT source_key, level, COUNT(*), MIN(timestamp), MAX(timestamp)
            FROM logs
            GROUP BY source_key, level
        """).fetchall()

        # Build per-source aggregates
        source_data: dict[str, dict[str, Any]] = {}
        for source_key, level, count, min_ts, max_ts in rows:
            if source_key not in source_data:
                source_data[source_key] = {"total": 0, "levels": {}, "min_ts": None, "max_ts": None}
            sd = source_data[source_key]
            sd["total"] += count
            if level:
                sd["levels"][level] = count
            if min_ts is not None and (sd["min_ts"] is None or min_ts < sd["min_ts"]):
                sd["min_ts"] = min_ts
            if max_ts is not None and (sd["max_ts"] is None or max_ts > sd["max_ts"]):
                sd["max_ts"] = max_ts

        sources: list[LogSource] = []
        for key, sd in source_data.items():
            meta = self._log_meta.get(sid, {}).get(key, {})
            sources.append(
                LogSource(
                    source=key,
                    total_entries=sd["total"],
                    levels=sd["levels"],
                    time_range={
                        "from": format_ts(sd["min_ts"]),
                        "to": format_ts(sd["max_ts"]),
                    },
                    module=meta.get("module", ""),
                    component=meta.get("component", ""),
                )
            )
        return sources

    def get_logs(
        self,
        sid: str,
        source: str | None = None,
        level: str | None = None,
        search: str | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
        sort: str = "desc",
        page: int = 1,
        page_size: int = 100,
    ) -> tuple[list[dict[str, Any]], int]:
        """Return (page_entries, total_matching). page_size=0 means all."""
        conn = self._dbs.get(sid)
        if not conn:
            return [], 0

        where_clauses: list[str] = []
        params: list[Any] = []

        if source:
            keys = [s.strip() for s in source.split(",")]
            where_clauses.append(f"source_key IN ({','.join('?' * len(keys))})")
            params.extend(keys)
        if level and level != "all":
            where_clauses.append("level = ?")
            params.append(level)
        if date_from:
            try:
                where_clauses.append("timestamp >= ?")
                params.append(datetime.fromisoformat(date_from).timestamp())
            except ValueError:
                pass
        if date_to:
            try:
                where_clauses.append("timestamp <= ?")
                params.append(datetime.fromisoformat(date_to).timestamp())
            except ValueError:
                pass
        if search:
            # Search across message and source_key (source name matched via key)
            where_clauses.append("(message LIKE ? ESCAPE '\\' OR source_key LIKE ? ESCAPE '\\')")
            like_pat = f"%{search}%"
            params.extend([like_pat, like_pat])

        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
        order_sql = "DESC" if sort == "desc" else "ASC"

        # Count total matching
        total = conn.execute(f"SELECT COUNT(*) FROM logs WHERE {where_sql}", params).fetchone()[0]

        # Fetch page
        if page_size == 0:
            rows = conn.execute(
                f"SELECT * FROM logs WHERE {where_sql} ORDER BY timestamp {order_sql}",
                params,
            ).fetchall()
        else:
            offset = (page - 1) * page_size
            rows = conn.execute(
                f"SELECT * FROM logs WHERE {where_sql} ORDER BY timestamp {order_sql} LIMIT ? OFFSET ?",
                [*params, page_size, offset],
            ).fetchall()

        # Convert rows to dicts for API response
        result: list[dict[str, Any]] = []
        for row in rows:
            # row: (id, source_key, timestamp, level, message, host, pid, extra)
            source_key = row[1]
            entry: dict[str, Any] = {
                "timestamp": format_ts(row[2]),
                "level": row[3] or "",
                "message": row[4] or "",
                "source": self._log_meta.get(sid, {}).get(source_key, {}).get("name", source_key),
            }
            if row[5]:
                entry["host"] = row[5]
            if row[6]:
                entry["pid"] = row[6]
            if row[7]:
                entry.update(json.loads(row[7]))
            # Lazy beautification: compute for this page only
            msg = entry.get("message", "")
            if "{" in msg:
                beautified = beautify_message(msg)
                if beautified:
                    entry["beautified"] = beautified
            result.append(entry)
        return result, total

    def get_log_entries(self, sid: str, source_key: str) -> list[dict[str, Any]]:
        """Return log entries for a given source key (used by forwarding-profile)."""
        conn = self._dbs.get(sid)
        if not conn:
            return []
        rows = conn.execute("SELECT message, extra FROM logs WHERE source_key = ?", (source_key,)).fetchall()
        entries: list[dict[str, Any]] = []
        for msg, extra in rows:
            e: dict[str, Any] = {"message": msg or ""}
            if extra:
                e.update(json.loads(extra))
            entries.append(e)
        return entries

    def get_state_keys(self, sid: str) -> list[dict[str, Any]]:
        if sid not in self._state:
            return []
        result: list[dict[str, Any]] = []
        for key, data in self._state[sid].items():
            meta = data.get("_meta", {})
            result.append(
                {
                    "key": key,
                    "module": meta.get("module", ""),
                    "component": meta.get("component", ""),
                    "name": meta.get("name", ""),
                    "pacli_command": PACLI_COMMAND_MAP.get(key),
                }
            )
        return result

    def get_state(self, sid: str, key: str) -> dict[str, Any] | None:
        return self._state.get(sid, {}).get(key)

    def get_hip(self, sid: str) -> dict[str, Any] | None:
        """The HIP model for a session, with the raw-XML `_raw` key stripped.

        The whole point of the raw/structured split is that this stays
        small, so `_raw` never leaves this method. None only when the
        session was never stored; a session whose bundle had no compliance
        logs still gets the full empty shape (`cycles: []`), since
        build_hip_data() always runs during parsing.
        """
        hip = self._hip.get(sid)
        if hip is None:
            return None
        return {key: value for key, value in hip.items() if key != "_raw"}

    def get_hip_raw(self, sid: str, index: str) -> dict[str, Any] | None:
        """The raw XML for one HIP cycle. `index` is the cycle's `str`-keyed
        position in `_raw` (build_hip_data keys it that way so the shape
        survives a JSON round-trip) -- an int here would never match."""
        hip = self._hip.get(sid)
        if hip is None:
            return None
        raw: dict[str, Any] = hip.get("_raw") or {}
        return raw.get(index)


store = SessionStore()
