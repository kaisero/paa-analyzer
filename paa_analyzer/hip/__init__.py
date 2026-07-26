"""HIP (Host Information Profile) domain model, layered on top of parsers.py.

Turns already-parsed PACompliance*/PAComplianceMp* log entries (plain dicts
from parsers.structured_log()) into a structured HIP-cycle domain model:
policy, per-category OPSWAT results, missing patches, and dispatch status.

`build_hip_data()` is the one entry point: it composes cycle segmentation
(cycles.py), the hip-report XML (report.py), the missing-patches fragment
(patches.py), the policy blob (policy.py), OPSWAT detection and errors
(opswat.py) and the status heuristics (status.py) into the single HipData
object the API and CLI serve. Everything it returns is a plain
JSON-serializable dict/list, and every timestamp is an ISO-8601 UTC string --
the float epochs and tuples the lower layers use stop here.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from paa_analyzer.hip.cycle_scalars import (
    category_timings,
    dispatch,
    duration_s,
    first,
    generate_time,
    policy,
)
from paa_analyzer.hip.cycles import Cycle, pair_cycles, split_cycles
from paa_analyzer.hip.opswat import parse_detected_products, parse_opswat_errors
from paa_analyzer.hip.patches import parse_missing_patches
from paa_analyzer.hip.report import parse_hip_report
from paa_analyzer.hip.status import category_status, product_status
from paa_analyzer.parsers import format_ts

__all__ = ["build_hip_data"]

COMPLIANCE_SOURCE = "PACompliance"
MP_SOURCE = "PAComplianceMp"

_COMPLIANCE_LOG_KEY = f"Agent.Compliance.{COMPLIANCE_SOURCE}"
_MP_LOG_KEY = f"Agent.Compliance.{MP_SOURCE}"
_HIP_STATUS_STATE_KEY = "Agent.Compliance.hip_status"

_PATCH_CATEGORY = "patch-management"

_REPORT_END = "</hip-report>"
_XML_START = "<?xml"
_PATCHES_START = "<missing-patches>"
_PATCHES_END = "</missing-patches>"

_SECONDS_PER_DAY = 86400.0


def build_hip_data(
    logs: dict[str, Any],
    state: dict[str, Any],
    platform: str,
    tz_offset: str | None = None,
) -> dict[str, Any]:
    """Assemble the HipData object from a parsed bundle's logs and state.

    `logs` and `state` are the dicts `backend.pipeline.parse_zip` produces
    (`logs[key]["entries"]`, `state[key]["data"]`). Either compliance log may
    be absent, in which case the result simply carries no cycles.

    `tz_offset` is the bundle-wide UTC offset `parsers.extract_tz_offset()`
    recovers from `pacli_status.log` (e.g. `"+0200"`). When supplied, it
    resolves each cycle's `generate_time` authoritatively; when omitted, that
    resolution falls back to a same-cycle inference -- see
    `cycle_scalars.generate_time()`. Task 6 wires the real pipeline value
    through; the default keeps existing 3-arg callers working.

    Cycles come back newest-first with `index` 0..n-1. Raw XML is deliberately
    kept out of them and returned under the top-level `_raw` key, keyed by
    cycle index (as a string, so callers see the same shape in-process and
    after a JSON round-trip), so callers can serve the model without shipping
    megabytes of XML.
    """
    compliance_cycles = split_cycles(_entries(logs, _COMPLIANCE_LOG_KEY))
    mp_cycles = split_cycles(_entries(logs, _MP_LOG_KEY))
    pairs, _unpaired_mp = pair_cycles(compliance_cycles, mp_cycles)

    # Newest first. `None` start_ts (a rotation-truncated leading cycle with
    # no policy line to anchor it) sorts last.
    ordered = sorted(pairs, key=lambda pair: (pair[0]["start_ts"] is not None, pair[0]["start_ts"] or 0), reverse=True)

    cycles: list[dict[str, Any]] = []
    raw: dict[str, dict[str, Any]] = {}
    for index, (compliance_cycle, mp_cycle) in enumerate(ordered):
        cycle, cycle_raw = _build_cycle(index, compliance_cycle, mp_cycle, platform, tz_offset)
        cycles.append(cycle)
        raw[str(index)] = cycle_raw

    newest_ts = ordered[0][0]["start_ts"] if ordered else None
    status = _hip_status(state)

    return {
        "platform": platform,
        "collection": status.get("collection"),
        "next_check": status.get("next_check"),
        "gateways": [_gateway(gateway, newest_ts) for gateway in status.get("gateways") or []],
        "cycles": cycles,
        "_raw": raw,
    }


# ── inputs ───────────────────────────────────────────────────────────────────


def _entries(logs: dict[str, Any], key: str) -> list[dict[str, Any]]:
    source = logs.get(key) or {}
    entries: list[dict[str, Any]] = source.get("entries") or []
    return entries


def _hip_status(state: dict[str, Any]) -> dict[str, Any]:
    entry = state.get(_HIP_STATUS_STATE_KEY) or {}
    data: dict[str, Any] = entry.get("data") or {}
    return data


def _gateway(gateway: dict[str, Any], reference_ts: float | None) -> dict[str, Any]:
    """One HipGateway. `status` / `status_kind` are passed through when the
    state parser supplies them and are None otherwise, so the shape is stable
    either way."""
    last_report = gateway.get("last_report")
    return {
        "gateway": gateway.get("gateway"),
        "last_report": last_report,
        "status": gateway.get("status"),
        "status_kind": gateway.get("status_kind"),
        "age_days": _age_days(last_report, reference_ts),
    }


def _age_days(last_report: str | None, reference_ts: float | None) -> float | None:
    """How stale a gateway's last HIP report is, measured against the newest
    cycle in the bundle rather than wall-clock time -- a bundle is normally
    analysed days or weeks after it was captured."""
    if not last_report or reference_ts is None:
        return None
    try:
        reported = datetime.fromisoformat(last_report)
    except ValueError:
        return None
    # parsers.hip_status() emits offset-aware format_ts() strings today, so
    # this is a no-op in practice -- but a naive string must never be read
    # as the analysis host's local zone, so treat it as UTC explicitly.
    if reported.tzinfo is None:
        reported = reported.replace(tzinfo=UTC)
    return round((reference_ts - reported.timestamp()) / _SECONDS_PER_DAY, 1)


# ── one cycle ────────────────────────────────────────────────────────────────


def _build_cycle(
    index: int,
    compliance_cycle: Cycle,
    mp_cycle: Cycle | None,
    platform: str,
    tz_offset: str | None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Assemble one HipCycle and its raw-XML companion."""
    entries = compliance_cycle["entries"]
    mp_entries = mp_cycle["entries"] if mp_cycle else []

    report_entry = first(entries, lambda message: _REPORT_END in message)
    raw_xml = _slice(report_entry["message"], _XML_START, _REPORT_END) if report_entry else None
    report = parse_hip_report(report_entry["message"], platform) if report_entry else None

    patches_entry = first(mp_entries, lambda message: _PATCHES_START in message)
    raw_patches_xml = _slice(patches_entry["message"], _PATCHES_START, _PATCHES_END) if patches_entry else None
    patches = parse_missing_patches(patches_entry["message"]) if patches_entry else []

    signature_map = {**parse_detected_products(entries), **parse_detected_products(mp_entries)}
    errors: list[dict[str, Any]] = [
        dict(error)
        for error in parse_opswat_errors(entries, COMPLIANCE_SOURCE, signature_map)
        + parse_opswat_errors(mp_entries, MP_SOURCE, signature_map)
    ]

    if report is not None:
        _decorate_categories(
            report["categories"],
            errors=errors,
            signature_map=signature_map,
            patches=patches,
            patches_source=MP_SOURCE if patches_entry else None,
        )

    cycle = {
        "index": index,
        "started_at": format_ts(compliance_cycle["start_ts"]),
        "generate_time": generate_time(raw_xml, report_entry, tz_offset),
        "duration_s": duration_s(entries),
        "partial": compliance_cycle["partial"],
        "policy": policy(entries),
        "report": report,
        "opswat_errors": errors,
        "category_timings": category_timings(entries),
        "dispatch": dispatch(entries),
        "counts": _counts(report, errors),
    }
    return cycle, {"raw_xml": raw_xml, "raw_patches_xml": raw_patches_xml}


def _decorate_categories(
    categories: list[dict[str, Any]],
    errors: list[dict[str, Any]],
    signature_map: dict[int, dict[str, Any]],
    patches: list[dict[str, Any]],
    patches_source: str | None,
) -> None:
    """Attach signatures, OPSWAT errors, missing patches and statuses to the
    freshly parsed report, in place.

    Errors are attached to a product by matching the product's report name
    against the DETECT_PRODUCTS signature map; an error with no signature (the
    GetMissingPatchesForThisProduct lines never carry one) stays in the
    cycle-wide flat list only. This assumes a report's product name always
    resolves 1:1 to a DETECT_PRODUCTS `sig_name` -- true for all 22 products
    across both fixtures, but a report name that diverges from OPSWAT's
    `sig_name`, or two products sharing a name across categories, would drop
    the attachment silently rather than erroring.
    """
    signature_by_name = {entry["name"]: signature for signature, entry in signature_map.items() if entry.get("name")}
    errors_by_signature: dict[int, list[dict[str, Any]]] = {}
    for error in errors:
        signature = error.get("signature")
        if signature is not None:
            errors_by_signature.setdefault(signature, []).append(error)

    for category in categories:
        is_patch_category = category["name"] == _PATCH_CATEGORY
        category["missing_patches"] = patches if is_patch_category else []
        category["patches_source"] = patches_source if is_patch_category else None

        for product in category["products"]:
            # See the assumption noted above: matched by name, not a stable id.
            signature = signature_by_name.get(product["name"])
            product["signature"] = signature
            product["errors"] = errors_by_signature.get(signature, []) if signature is not None else []
            product["status"], product["status_reason"] = product_status(product)

        category["status"], category["status_reason"] = category_status(category["products"])


def _counts(
    report: dict[str, Any] | None,
    errors: list[dict[str, Any]],
) -> dict[str, int]:
    """`missing_patches` is read from the decorated patch-management category
    rather than the raw `patches` list, so a cycle with no report (hence no
    category to hold them) counts 0 instead of silently claiming patches no
    category displays."""
    categories = (report or {}).get("categories", [])
    statuses = [product["status"] for category in categories for product in category["products"]]
    patch_category = next((category for category in categories if category["name"] == _PATCH_CATEGORY), None)
    missing_patches = len(patch_category["missing_patches"]) if patch_category else 0
    return {
        "warn": statuses.count("warn"),
        "unknown": statuses.count("unknown"),
        "errors": len(errors),
        "missing_patches": missing_patches,
    }


# ── small helpers ────────────────────────────────────────────────────────────


def _slice(message: str, start_marker: str, end_marker: str) -> str | None:
    """The verbatim substring of a log message from `start_marker` through
    `end_marker`, or None if either boundary is missing."""
    start = message.find(start_marker)
    if start == -1:
        return None
    end = message.find(end_marker, start)
    if end == -1:
        return None
    return message[start : end + len(end_marker)]
