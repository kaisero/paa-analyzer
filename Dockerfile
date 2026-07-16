# syntax=docker/dockerfile:1
#
# Single self-contained image: builds the React frontend, then runs the FastAPI
# backend which serves BOTH the JSON API and the built SPA on port 8000.
# `backend/main.py` mounts `frontend/dist` as static files when present, so one
# uvicorn process is all that's needed — no nginx, no second container.

# ---- Stage 1: build the React frontend into frontend/dist ---------------------
FROM node:22-slim AS frontend
WORKDIR /app/frontend
# Install dependencies first for better layer caching. No lockfile is committed,
# so use `npm install` (not `npm ci`).
COPY frontend/package.json ./
RUN npm install
# Build the production bundle. We call `vite build` directly rather than the
# package.json `build` script (which also runs the test suite + tsc): tests and
# type-checks belong in CI, not in the image build, and skipping them keeps the
# image build fast and robust.
COPY frontend/ ./
RUN npx vite build

# ---- Stage 2: python runtime that serves the API + the built SPA --------------
FROM python:3.14-slim AS runtime
# uv provides fast, lock-faithful installs. Pin a version instead of :latest for
# fully reproducible builds.
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PYTHONUNBUFFERED=1

# Install the runtime dependencies first (cached unless pyproject/uv.lock change).
# --no-dev skips the dev tools; --frozen uses the committed uv.lock verbatim.
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

# Application code + the frontend built in stage 1.
COPY backend/ ./backend/
COPY paa_analyzer/ ./paa_analyzer/
COPY --from=frontend /app/frontend/dist ./frontend/dist

# Install the project itself (so importlib.metadata reports the real version).
RUN uv sync --frozen --no-dev

EXPOSE 8000

# Production server: uvicorn WITHOUT --reload. (The `paa-server` entry point runs
# uvicorn with reload=True, which is for local development only.)
CMD ["/app/.venv/bin/uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
