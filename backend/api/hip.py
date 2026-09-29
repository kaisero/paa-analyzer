"""HIP (Host Information Profile) endpoints.

Serves the structured `paa_analyzer.hip.build_hip_data()` model for a session
plus, separately, the raw XML it was built from -- kept out of the main
endpoint so a session with many HIP cycles stays cheap to fetch and display.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from backend.models.responses import DataResponse
from backend.store import store

router = APIRouter(prefix="/sessions/{session_id}", tags=["hip"])


@router.get("/hip")
async def get_hip(session_id: str) -> DataResponse:
    if not store.get_session(session_id):
        raise HTTPException(404, "Session not found")
    return DataResponse(data=store.get_hip(session_id))


@router.get("/hip/cycles/{index}/raw")
async def get_hip_raw(session_id: str, index: str) -> DataResponse:
    if not store.get_session(session_id):
        raise HTTPException(404, "Session not found")
    raw = store.get_hip_raw(session_id, index)
    if raw is None:
        raise HTTPException(404, "HIP cycle not found")
    return DataResponse(data=raw)
