"""FastAPI application factory."""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.responses import Response
from starlette.types import Scope

from backend.api import dashboard, hip, logs, sessions, state

try:
    __version__ = version("paa-analyzer")
except PackageNotFoundError:
    __version__ = "dev"


class SpaStaticFiles(StaticFiles):
    """StaticFiles with a single-page-app fallback.

    React Router owns every path under `/s/<session>/…`, but those paths exist
    only in the browser — there is no matching file on disk. Plain
    `StaticFiles` 404s them, including with `html=True`, which maps only a
    *directory* to its `index.html`. The visible symptom is that a hard
    refresh or a shared session link fails while `/` works.

    The fallback is deliberately narrow, because two kinds of 404 must
    survive it:

    - **A request carrying a file extension is asking for a real asset.** If a
      missing `/assets/app.js` returned `index.html`, a broken build would
      look like a working one and the browser would report a baffling syntax
      error instead of a 404.
    - **A request under `api/` is an API call.** A typo'd endpoint must return
      the API's own 404, not a page, or every client sees HTML where it
      expects JSON.
    """

    async def get_response(self, path: str, scope: Scope) -> Response:
        try:
            return await super().get_response(path, scope)
        except StarletteHTTPException as exc:
            is_client_route = not Path(path).suffix and not path.startswith("api/")
            if exc.status_code != 404 or not is_client_route:
                raise
            return await super().get_response("index.html", scope)


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
    app.include_router(hip.router, prefix="/api/v1")

    # Serve frontend static files (after API routes so /api/* takes priority).
    # SpaStaticFiles, not StaticFiles: client-side routes have no file on disk.
    dist = Path(__file__).parent.parent / "frontend" / "dist"
    if dist.is_dir():
        app.mount("/", SpaStaticFiles(directory=str(dist), html=True), name="frontend")

    return app


app = create_app()


def run() -> None:
    import uvicorn

    # Bind on all interfaces so the diagnostic web UI is reachable from the host.
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)  # noqa: S104
