"""FastAPI application factory."""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.api import dashboard, logs, sessions, state

try:
    __version__ = version("paa-analyzer")
except PackageNotFoundError:
    __version__ = "dev"


def create_app() -> FastAPI:
    app = FastAPI(title="PAA Analyzer", version=__version__)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # API routes
    app.include_router(sessions.router, prefix="/api/v1")
    app.include_router(logs.router, prefix="/api/v1")
    app.include_router(state.router, prefix="/api/v1")
    app.include_router(dashboard.router, prefix="/api/v1")

    # Serve frontend static files (after API routes so /api/* takes priority)
    dist = Path(__file__).parent.parent / "frontend" / "dist"
    if dist.is_dir():
        app.mount("/", StaticFiles(directory=str(dist), html=True), name="frontend")

    return app


app = create_app()


def run() -> None:
    import uvicorn

    # Bind on all interfaces so the diagnostic web UI is reachable from the host.
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)  # noqa: S104
