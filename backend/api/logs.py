"""Log source listing and paginated log queries."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from backend.config import settings
from backend.models.responses import DataResponse, PaginatedResponse, PaginationMeta
from backend.store import store

router = APIRouter(prefix="/sessions/{session_id}", tags=["logs"])


@router.get("/logs/sources")
async def get_log_sources(session_id: str) -> DataResponse:
    if not store.get_session(session_id):
        raise HTTPException(404, "Session not found")
    sources = store.get_log_sources(session_id)
    return DataResponse(data=[s.model_dump() for s in sources])


@router.get("/logs")
async def get_logs(
    session_id: str,
    source: str | None = Query(None, description="Comma-separated source keys"),
    level: str | None = Query(None, description="Filter by level"),
    search: str | None = Query(None, description="Substring search across all fields"),
    date_from: str | None = Query(None, description="ISO-8601 start timestamp"),
    date_to: str | None = Query(None, description="ISO-8601 end timestamp"),
    sort: str = Query("desc", description="Sort direction: asc or desc"),
    page: int = Query(1, ge=1),
    page_size: int = Query(settings.default_page_size, ge=0, le=settings.max_page_size),
) -> PaginatedResponse:
    if not store.get_session(session_id):
        raise HTTPException(404, "Session not found")

    entries, total = store.get_logs(
        session_id,
        source=source,
        level=level,
        search=search,
        date_from=date_from,
        date_to=date_to,
        sort=sort,
        page=page,
        page_size=page_size,
    )

    has_next = (page * page_size < total) if page_size > 0 else False
    return PaginatedResponse(
        data=entries,
        meta=PaginationMeta(total=total, page=page, page_size=page_size, has_next=has_next),
    )
