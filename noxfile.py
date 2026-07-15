"""Task runner for paa-analyzer.

One source of truth for the checks run both locally and in CI. Run everything
with `uv run nox` or a single session with `uv run nox -s tests`.
"""
from __future__ import annotations

import os

import nox

nox.options.default_venv_backend = "uv"
nox.options.reuse_existing_virtualenvs = True
nox.options.sessions = ["lint", "type_check", "tests", "docs"]

PYTHON_VERSIONS = ["3.14"]


def _sync(session: nox.Session, *groups: str) -> None:
    """Install the project plus the given dependency groups into the session."""
    args = ["uv", "sync", "--no-default-groups"]
    if os.environ.get("CI"):
        args.append("--frozen")
    for group in groups:
        args += ["--group", group]
    session.run_install(
        *args,
        env={"UV_PROJECT_ENVIRONMENT": session.virtualenv.location},
    )


@nox.session
def lint(session: nox.Session) -> None:
    """Check code style and formatting with ruff."""
    _sync(session, "lint")
    session.run("ruff", "check", ".")
    session.run("ruff", "format", "--check", ".")


@nox.session
def type_check(session: nox.Session) -> None:
    """Run static type checking with mypy."""
    _sync(session, "typecheck")
    session.run("mypy")


@nox.session(python=PYTHON_VERSIONS)
def tests(session: nox.Session) -> None:
    """Run the test suite with coverage."""
    _sync(session, "test")
    session.run(
        "pytest",
        "--cov",
        "--cov-report=term-missing",
        *session.posargs,
    )


@nox.session
def audit(session: nox.Session) -> None:
    """Audit dependencies for known vulnerabilities."""
    _sync(session, "audit")
    session.run("pip-audit")


@nox.session
def docs(session: nox.Session) -> None:
    """Build the documentation site."""
    _sync(session, "docs")
    session.run("mkdocs", "build", "--strict")


@nox.session(name="docs-serve")
def docs_serve(session: nox.Session) -> None:
    """Serve the documentation site locally with live reload."""
    _sync(session, "docs")
    session.run("mkdocs", "serve")


@nox.session(venv_backend="none")
def gate(session: nox.Session) -> None:
    """Fast, offline pre-commit gate run in the invoking environment."""
    session.run("ruff", "check", ".")
    session.run("ruff", "format", "--check", ".")
    session.run("mypy")
    session.run("pytest", "-q", "-m", "not slow")
