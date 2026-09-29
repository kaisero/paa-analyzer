"""Freshness gate: the .agents/context/ generated blocks must match the code.

If a documented subsystem's code changes the module map, public API, taxonomy
routing table, or route table but the owning doc's GENERATED blocks are not
regenerated, this test fails in the offline gate. Fix with
``uv run nox -s context`` then re-run.
"""

from __future__ import annotations

from tools import context_docs


def test_context_docs_generated_blocks_are_current() -> None:
    assert context_docs.main(["--check"]) == 0, "Stale .agents/context/ generated blocks — run `uv run nox -s context`."
