"""Dashboard summary endpoint (stub for v2)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from backend.models.responses import DataResponse
from backend.store import store

router = APIRouter(prefix="/sessions/{session_id}", tags=["dashboard"])


@router.get("/dashboard")
async def get_dashboard(session_id: str) -> DataResponse:
    session = store.get_session(session_id)
    if not session:
        raise HTTPException(404, "Session not found")
    return DataResponse(
        data={
            "session_id": session["id"],
            "filename": session["filename"],
            "total_log_entries": session.get("total_log_entries", 0),
            "total_log_sources": session.get("total_log_sources", 0),
            "total_state_files": session.get("total_state_files", 0),
            "parse_duration_ms": session.get("parse_duration_ms"),
        }
    )
