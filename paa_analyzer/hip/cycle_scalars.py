"""Log-line scrapers for one HIP cycle.

Split out of `__init__.py` (Task 4 review, finding 12): assembling a
`HipData` object is `__init__.py`'s job, while pulling scalar values out of
individual `PACompliance*`/`PAComplianceMp*` log lines -- category timings,
creation duration, dispatch status, the policy blob, and the report's
generate-time -- is a separate, independently-testable concern.
"""

from __future__ import annotations

import re
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

from paa_analyzer.hip.policy import parse_policy
from paa_analyzer.parsers import format_ts, parse_ts

_CATEGORY_TIMING_RE = re.compile(r"^Category (?P<name>.+): took (?P<seconds>\d+) seconds?$")
_DURATION_RE = re.compile(r"^HIP creation done, took (?P<seconds>\d+) second")
_STATUS_CODE_RE = re.compile(r"^Finished with status code: (?P<code>-?\d+)")
_SENT_MESSAGE = "Send hip report to service"
_SUCCEEDED_MESSAGE = "SetHipReport succeeded"

_GENERATE_TIME_RE = re.compile(r"<generate-time>([^<]*)</generate-time>")
_GENERATE_TIME_FORMAT = "%m/%d/%Y %H:%M:%S"
_BARE_FORMAT = "%Y-%m-%d %H:%M:%S"
# Real-world UTC offsets are whole quarter hours; see generate_time()'s
# fallback path.
_OFFSET_STEP_S = 900


def policy(entries: list[dict[str, Any]]) -> dict[str, Any] | None:
    for entry in entries:
        parsed = parse_policy(entry.get("message") or "")
        if parsed is not None:
            return parsed
    return None


def category_timings(entries: list[dict[str, Any]]) -> dict[str, int]:
    """Every `Category X: took N seconds` line in the cycle, verbatim. The
    agent emits an aggregate `Category All` row alongside the real categories;
    it is kept under that name rather than dropped or renamed."""
    timings: dict[str, int] = {}
    for entry in entries:
        match = _CATEGORY_TIMING_RE.match(entry.get("message") or "")
        if match:
            timings[match.group("name")] = int(match.group("seconds"))
    return timings


def duration_s(entries: list[dict[str, Any]]) -> float | None:
    for entry in entries:
        match = _DURATION_RE.match(entry.get("message") or "")
        if match:
            return float(match.group("seconds"))
    return None


def dispatch(entries: list[dict[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {"sent": False, "succeeded": False, "status_code": None}
    for entry in entries:
        message = entry.get("message") or ""
        if message == _SENT_MESSAGE:
            result["sent"] = True
        elif message == _SUCCEEDED_MESSAGE:
            result["succeeded"] = True
        else:
            match = _STATUS_CODE_RE.match(message)
            if match:
                result["status_code"] = int(match.group("code"))
    return result


def generate_time(
    raw_xml: str | None,
    report_entry: dict[str, Any] | None,
    tz_offset: str | None = None,
) -> str | None:
    """`<generate-time>` as an ISO-8601 UTC string.

    The element carries the endpoint's *local* wall clock with no offset (e.g.
    "07/25/2026 17:07:44"), while the rest of the model is UTC.

    When `tz_offset` is supplied (the bundle-wide offset
    `parsers.extract_tz_offset()` recovers from `pacli_status.log`, threaded
    in by `build_hip_data`'s caller), it is applied directly via
    `parsers.parse_ts()` -- the authoritative source, since it is read from
    the same endpoint rather than inferred.

    When `tz_offset` is `None`, the offset falls back to an inference: the
    gap between generate-time and the timestamp of the log entry that carried
    the XML (normally written within seconds of generate-time), snapped to
    the nearest quarter hour, the granularity of real UTC offsets. This
    fallback is a guess and can be silently wrong -- e.g. a gateway-triggered
    `GetHipReport` re-emitting a *cached* report widens the gap well past the
    quarter-hour snap tolerance, snapping to the wrong offset with no error
    raised. Prefer supplying `tz_offset` whenever it is known.
    """
    if raw_xml is None:
        return None
    match = _GENERATE_TIME_RE.search(raw_xml)
    if not match:
        return None
    try:
        local = datetime.strptime(match.group(1).strip(), _GENERATE_TIME_FORMAT)
    except ValueError:
        return None

    if tz_offset is not None:
        return format_ts(parse_ts(local.strftime(_BARE_FORMAT), tz_offset))

    local_utc_guess = local.replace(tzinfo=UTC)
    anchor = report_entry.get("timestamp") if report_entry else None
    if anchor is None:
        return format_ts(local_utc_guess.timestamp())
    offset = round((local_utc_guess.timestamp() - anchor) / _OFFSET_STEP_S) * _OFFSET_STEP_S
    return format_ts(local_utc_guess.timestamp() - offset)


def first(entries: list[dict[str, Any]], matches: Callable[[str], bool]) -> dict[str, Any] | None:
    for entry in entries:
        if matches(entry.get("message") or ""):
            return entry
    return None
