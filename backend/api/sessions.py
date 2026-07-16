"""Session management: upload, list, get, delete, SSE upload with progress."""

from __future__ import annotations

import asyncio
import json
import uuid
from collections.abc import AsyncIterator
from typing import Any

from fastapi import APIRouter, HTTPException, UploadFile
from fastapi.responses import StreamingResponse

from backend.config import settings
from backend.models.responses import DataResponse
from backend.models.session import Session
from backend.pipeline import parse_zip
from backend.store import store

router = APIRouter(prefix="/sessions", tags=["sessions"])


# ── SSE upload with real-time progress ────────────────────────────────────


@router.post("/upload")
async def create_session_stream(file: UploadFile) -> StreamingResponse:
    if not file.filename or not file.filename.endswith(".zip"):
        raise HTTPException(400, "Only .zip files are accepted")

    data = await file.read()
    if len(data) > settings.max_upload_bytes:
        raise HTTPException(400, f"File too large (max {settings.max_upload_bytes // 1024 // 1024} MB)")

    sid = uuid.uuid4().hex[:12]
    session = Session(id=sid, filename=file.filename or "unknown.zip", file_size=len(data), parse_status="parsing")

    async def event_stream() -> AsyncIterator[str]:
        queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue()
        loop = asyncio.get_event_loop()

        def on_progress(stage: str, pct: int, detail: str) -> None:
            loop.call_soon_threadsafe(queue.put_nowait, {"stage": stage, "progress": pct, "detail": detail})

        def run_pipeline() -> dict[str, Any]:
            return parse_zip(data, on_progress=on_progress)

        future = loop.run_in_executor(None, run_pipeline)

        # Stream progress events until pipeline completes
        while not future.done():
            try:
                event = await asyncio.wait_for(queue.get(), timeout=0.1)
                yield f"data: {json.dumps(event)}\n\n"
            except TimeoutError:
                continue

        # Drain remaining queued events
        while not queue.empty():
            event = queue.get_nowait()
            yield f"data: {json.dumps(event)}\n\n"

        # Check for errors
        try:
            result = future.result()
        except Exception as e:
            session.parse_status = "error"
            session.parse_error = str(e)
            store.add_session(session.model_dump(mode="json"), {}, {})
            yield f"data: {json.dumps({'stage': 'error', 'progress': -1, 'detail': str(e)})}\n\n"
            return

        # Store session
        manifest = result["manifest"]
        session.parse_status = "complete"
        session.parse_duration_ms = manifest["parse_time_ms"]
        session.platform = manifest.get("platform", "unknown")
        session.total_log_entries = manifest["total_log_entries"]
        session.total_log_sources = manifest["total_log_sources"]
        session.total_state_files = manifest["total_state_files"]
        store.add_session(session.model_dump(mode="json"), result["logs"], result["state"])

        complete_event = {
            "stage": "complete",
            "progress": 100,
            "detail": "Done",
            "session": session.model_dump(mode="json"),
        }
        yield f"data: {json.dumps(complete_event)}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


# ── Standard sync endpoints ──────────────────────────────────────────────


@router.post("", status_code=201)
async def create_session(file: UploadFile) -> DataResponse:
    if not file.filename or not file.filename.endswith(".zip"):
        raise HTTPException(400, "Only .zip files are accepted")

    data = await file.read()
    if len(data) > settings.max_upload_bytes:
        raise HTTPException(400, f"File too large (max {settings.max_upload_bytes // 1024 // 1024} MB)")

    sid = uuid.uuid4().hex[:12]
    session = Session(id=sid, filename=file.filename, file_size=len(data), parse_status="parsing")

    try:
        result = parse_zip(data)
    except Exception as e:
        session.parse_status = "error"
        session.parse_error = str(e)
        store.add_session(session.model_dump(mode="json"), {}, {})
        return DataResponse(data=session.model_dump(mode="json"))

    manifest = result["manifest"]
    session.parse_status = "complete"
    session.parse_duration_ms = manifest["parse_time_ms"]
    session.platform = manifest.get("platform", "unknown")
    session.total_log_entries = manifest["total_log_entries"]
    session.total_log_sources = manifest["total_log_sources"]
    session.total_state_files = manifest["total_state_files"]

    store.add_session(session.model_dump(mode="json"), result["logs"], result["state"])
    return DataResponse(data=session.model_dump(mode="json"))


@router.get("")
async def list_sessions() -> DataResponse:
    return DataResponse(data=store.list_sessions())


@router.get("/{session_id}")
async def get_session(session_id: str) -> DataResponse:
    session = store.get_session(session_id)
    if not session:
        raise HTTPException(404, "Session not found")
    return DataResponse(data=session)


@router.delete("/{session_id}")
async def delete_session(session_id: str) -> DataResponse:
    if not store.delete_session(session_id):
        raise HTTPException(404, "Session not found")
    return DataResponse(data={"deleted": True})
