"""Generate frontend/src/test/fixtures/hip.json for the frontend test suite.

DO NOT HAND-EDIT hip.json. Per docs/plans/hip-analytics-foundation.md's
"Global Constraints" (data authenticity), every HIP fixture must come from
running the real parser over a real, redacted troubleshooting bundle -- never
hand-written JSON that imitates parser output.

This script runs paa_analyzer.hip.build_hip_data() over the redacted Python
fixtures in backend/tests/fixtures/hip/ (the same files backend/tests/
test_hip_build.py loads) and writes the result to hip.json, split the same
way backend.store.SessionStore does for the real API: the structured model
(no raw XML) under "macos" / "windows" / "empty", and the raw XML for the
`/hip/cycles/{index}/raw` endpoint under "macosRaw" / "windowsRaw".

Regenerate with, from the repository root:

    uv run python frontend/src/test/fixtures/generate-hip-fixture.py
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from paa_analyzer.hip import build_hip_data
from paa_analyzer.parsers import LogEntry, hip_status, structured_log

REPO_ROOT = Path(__file__).resolve().parents[4]
PY_FIXTURES = REPO_ROOT / "backend" / "tests" / "fixtures" / "hip"
OUTPUT = Path(__file__).resolve().parent / "hip.json"

COMPLIANCE_KEY = "Agent.Compliance.PACompliance"
MP_KEY = "Agent.Compliance.PAComplianceMp"
HIP_STATUS_KEY = "Agent.Compliance.hip_status"


def _entries(name: str) -> list[LogEntry]:
    return structured_log((PY_FIXTURES / name).read_text())


def _collapsed(*names: str) -> list[LogEntry]:
    """Concatenate log rotations and sort by timestamp, the way parse_zip
    collapses PACompliance.log + PACompliance.1.log into one entry stream."""
    merged: list[LogEntry] = []
    for name in names:
        merged.extend(_entries(name))
    merged.sort(key=lambda e: e["timestamp"])
    return merged


def _macos_logs() -> dict[str, Any]:
    return {
        COMPLIANCE_KEY: {"entries": _collapsed("PACompliance.log", "PACompliance.1.log")},
        MP_KEY: {"entries": _collapsed("PAComplianceMp.log", "PAComplianceMp.1.log")},
    }


def _windows_logs() -> dict[str, Any]:
    """The Windows bundle ships no PAComplianceMp log at all."""
    return {COMPLIANCE_KEY: {"entries": _entries("PACompliance_win.log")}}


def _hip_status_state() -> dict[str, Any]:
    """The `Agent.Compliance.hip_status` state record for the macOS bundle,
    parsed for real via parsers.hip_status from the redacted
    pacli_hip_status.log fixture."""
    text = (PY_FIXTURES / "pacli_hip_status.log").read_text()
    parsed = hip_status(text, tz="+0200")
    return {
        HIP_STATUS_KEY: {
            "data": {
                "collection": parsed["collection"],
                "next_check": parsed["next_check"],
                "gateways": parsed["gateways"],
            }
        }
    }


def _strip_raw(hip_data: dict[str, Any]) -> dict[str, Any]:
    """Mirror backend.store.SessionStore.get_hip: the /hip endpoint never
    ships raw XML, only /hip/cycles/{index}/raw does."""
    return {key: value for key, value in hip_data.items() if key != "_raw"}


def main() -> None:
    # tz_offset matches the "+0200" already passed to hip_status() below (the
    # real bundle-wide offset) -- backend/pipeline.py always supplies it, so
    # the fixture must too. Omitting it would silently exercise
    # cycle_scalars.generate_time()'s quarter-hour-snap fallback instead of
    # the path production actually takes (Minor 3 finding).
    macos_full = build_hip_data(_macos_logs(), _hip_status_state(), "macos", tz_offset="+0200")
    windows_full = build_hip_data(_windows_logs(), {}, "windows")
    # A real, exercised code path (not fabricated data): a bundle with no
    # PACompliance*/PAComplianceMp* entries and no hip_status state at all,
    # e.g. because HIP collection is disabled by gateway policy -- see
    # test_hip_build.py::TestEmptyShape::test_empty_input_yields_the_empty_shape.
    empty = build_hip_data({}, {}, "unknown")

    fixture = {
        "macos": _strip_raw(macos_full),
        "macosRaw": macos_full["_raw"],
        "windows": _strip_raw(windows_full),
        "windowsRaw": windows_full["_raw"],
        "empty": _strip_raw(empty),
    }

    OUTPUT.write_text(json.dumps(fixture, indent=2) + "\n")
    print(f"Wrote {OUTPUT}")


if __name__ == "__main__":
    main()
