"""Shared API response envelopes."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class PaginationMeta(BaseModel):
    total: int
    page: int
    page_size: int
    has_next: bool


class DataResponse(BaseModel):
    data: Any


class PaginatedResponse(BaseModel):
    data: list[Any]
    meta: PaginationMeta
