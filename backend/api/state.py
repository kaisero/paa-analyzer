"""State data endpoints."""

from __future__ import annotations

import re
from collections import Counter

from fastapi import APIRouter, HTTPException

from backend.models.responses import DataResponse
from backend.store import store

router = APIRouter(prefix="/sessions/{session_id}", tags=["state"])


@router.get("/state")
async def list_state(session_id: str) -> DataResponse:
    if not store.get_session(session_id):
        raise HTTPException(404, "Session not found")
    return DataResponse(data=store.get_state_keys(session_id))


@router.get("/state/batch")
async def get_state_batch(session_id: str, keys: str = "") -> DataResponse:
    """Return multiple state entries in a single response."""
    if not store.get_session(session_id):
        raise HTTPException(404, "Session not found")
    requested_keys = [k.strip() for k in keys.split(",") if k.strip()]
    result = {}
    for key in requested_keys:
        data = store.get_state(session_id, key)
        if data is not None:
            result[key] = data
    return DataResponse(data=result)


@router.get("/state/forwarding-profile")
async def get_forwarding_profile(session_id: str) -> DataResponse:
    """Return forwarding rules enriched with hitcounts computed from traffic_log."""
    if not store.get_session(session_id):
        raise HTTPException(404, "Session not found")

    # Get forwarding rules from state
    traffic_show = store.get_state(session_id, "Agent.Networking.traffic_show")
    rules = traffic_show["data"]["rules"] if traffic_show else []
    flags = traffic_show["data"]["flags"] if traffic_show else []

    # Compute hitcounts from traffic_json log entries
    traffic_entries = store.get_log_entries(session_id, "Agent.Core.traffic_log_json")
    hit_counts: Counter[int] = Counter()
    for entry in traffic_entries:
        m = re.search(r"Rule priority (\d+) matched", entry.get("reason", ""))
        if m:
            hit_counts[int(m.group(1))] += 1

    # Enrich rules with computed hitcounts
    enriched_rules = [{**rule, "traffic_log_hits": hit_counts.get(rule["priority"], 0)} for rule in rules]

    return DataResponse(data={"rules": enriched_rules, "flags": flags})


@router.get("/state/{key:path}")
async def get_state(session_id: str, key: str) -> DataResponse:
    if not store.get_session(session_id):
        raise HTTPException(404, "Session not found")
    data = store.get_state(session_id, key)
    if data is None:
        raise HTTPException(404, "State key not found")
    return DataResponse(data=data)
