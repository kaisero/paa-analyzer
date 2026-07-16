"""Session and log source models."""

from __future__ import annotations

from datetime import UTC, datetime

from pydantic import BaseModel, Field


class Session(BaseModel):
    id: str
    filename: str
    file_size: int
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    parse_status: str = "pending"  # pending | parsing | complete | error
    parse_error: str | None = None
    parse_duration_ms: int | None = None
    platform: str = "unknown"  # "macos", "windows", or "unknown"
    total_log_entries: int = 0
    total_log_sources: int = 0
    total_state_files: int = 0


class LogSource(BaseModel):
    source: str
    total_entries: int
    levels: dict[str, int]
    time_range: dict[str, str | None]
    module: str
    component: str
