"""SPA routing for the served frontend.

The frontend is a single-page app: React Router owns `/s/<session>/…`, so those
paths must serve `index.html` instead of 404ing on a hard refresh or a shared
link. Equally, the fallback must not swallow a missing asset or an API typo.

These tests mount `SpaStaticFiles` on a throwaway app over a temp directory
rather than going through `create_app()`, because `create_app()` resolves
`frontend/dist` from the repo layout and only mounts anything when a build
happens to be present.
"""

from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.main import SpaStaticFiles

INDEX_MARKER = '<div id="root"></div>'


@pytest.fixture
def spa_client(tmp_path):
    (tmp_path / "index.html").write_text(
        f"<!doctype html><html><body>{INDEX_MARKER}</body></html>",
        encoding="utf-8",
    )
    assets = tmp_path / "assets"
    assets.mkdir()
    (assets / "app.js").write_text("console.log('real asset')", encoding="utf-8")

    app = FastAPI()

    @app.get("/api/v1/ping")
    async def ping() -> dict[str, bool]:
        return {"ok": True}

    # Same order as create_app(): API routes first, static mount last.
    app.mount("/", SpaStaticFiles(directory=str(tmp_path), html=True), name="frontend")
    return TestClient(app)


class TestSpaFallback:
    def test_serves_index_at_root(self, spa_client):
        response = spa_client.get("/")
        assert response.status_code == 200
        assert INDEX_MARKER in response.text

    def test_serves_a_real_asset_unchanged(self, spa_client):
        response = spa_client.get("/assets/app.js")
        assert response.status_code == 200
        assert "real asset" in response.text

    def test_session_route_falls_back_to_index(self, spa_client):
        """The exact URL a user shares or hard-refreshes."""
        response = spa_client.get("/s/3c6b87b81ff7/hip")
        assert response.status_code == 200
        assert INDEX_MARKER in response.text

    @pytest.mark.parametrize("route", ["hip", "logs", "dashboard", "agent-status"])
    def test_every_session_route_falls_back(self, spa_client, route):
        response = spa_client.get(f"/s/3c6b87b81ff7/{route}")
        assert response.status_code == 200
        assert INDEX_MARKER in response.text


class TestFallbackStaysNarrow:
    """Two kinds of 404 must survive the fallback."""

    def test_missing_asset_still_404s(self, spa_client):
        """A broken build must look broken.

        Serving index.html here would turn a missing bundle into a baffling
        JavaScript syntax error instead of an honest 404.
        """
        response = spa_client.get("/assets/missing.js")
        assert response.status_code == 404
        assert INDEX_MARKER not in response.text

    def test_unknown_api_path_is_not_swallowed(self, spa_client):
        """A typo'd endpoint must not answer with a page."""
        response = spa_client.get("/api/v1/nope")
        assert response.status_code == 404
        assert INDEX_MARKER not in response.text

    def test_real_api_route_still_works(self, spa_client):
        response = spa_client.get("/api/v1/ping")
        assert response.status_code == 200
        assert response.json() == {"ok": True}
