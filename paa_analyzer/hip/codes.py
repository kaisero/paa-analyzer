"""OESIS code catalog: error codes, method ids, and OPSWAT category ids.

Built only from codes actually observed in the HIP fixtures
(backend/tests/fixtures/hip/). All lookups are total functions: unknown ids
return None, they never raise.
"""

from __future__ import annotations

# ── OESIS error codes ───────────────────────────────────────────────────────
# Explanations are the OPSWAT (OESIS V4) error text as it appears verbatim in
# the PACompliance*/PAComplianceMp* logs, e.g.:
#   "CollectComplianceDataForAV: Opswat Error(-11): An error when a method
#   call was made on a component that does not support it, ..."
_ERROR_EXPLANATIONS: dict[int, str] = {
    -11: "An error when a method call was made on a component that does not support it.",
    -12: "An error when a method call was made on a component that does not implement it.",
    -28: (
        "An error when an object is not found. This can be objects held internally, "
        "or objects on the endpoint, such as files, backup times, etc."
    ),
}

# ── OESIS method ids ─────────────────────────────────────────────────────────
# The *category/function* each id belongs to is grounded in the fixtures:
#   Category: 5 (anti-malware),      Method: 1001, 1004 -- CollectComplianceDataForAV
#   Category: 2 (disk-backup),       Method: 1008       -- CollectComplianceDataForDLP
#   Category: 12 (patch-management), Method: 1013       -- GetMissingPatchesForThisProduct
# The *exact wording* below (e.g. distinguishing 1001's "real-time protection"
# from 1004's "last full scan time") is this author's inference from that
# context plus general OESIS V4 API knowledge -- it is NOT a quoted line from
# an OPSWAT/OESIS document; the fixtures never spell out what 1001 vs 1004
# individually query. Treat the wording as best-effort description, not a
# verified fact, and revisit if official OESIS method documentation surfaces.
_METHOD_QUERIES: dict[int, str] = {
    1001: "Antivirus real-time protection status.",
    1004: "Antivirus last full scan time.",
    1008: "Last backup time for a disk-backup product.",
    1013: "Missing patches for a patch-management product.",
}

# OESIS method id -> the hip-report attribute that method queries. Used by
# status.py to decide whether an error *covers* (makes untrustworthy) a
# product's key attribute. Kept beside _METHOD_QUERIES because it is indexed
# by the same four method ids observed in the fixtures; an uncatalogued
# method (e.g. Windows' 1012) covers nothing, so it never suppresses a value.
_METHOD_ATTRIBUTES: dict[int, str] = {
    1001: "real-time-protection",
    1004: "last-full-scan-time",
    1008: "last-backup-time",
    1013: "missing-patches",
}

# ── OPSWAT category ids → HIP category name ─────────────────────────────────
_CATEGORY_NAMES: dict[int, str] = {
    2: "disk-backup",
    5: "anti-malware",
    12: "patch-management",
}


def error_explanation(code: int) -> str | None:
    """Human explanation for an OESIS error code, or None if unknown."""
    return _ERROR_EXPLANATIONS.get(code)


def method_query(method_id: int) -> str | None:
    """What an OESIS method id queries, or None if unknown."""
    return _METHOD_QUERIES.get(method_id)


def method_attribute(method_id: int) -> str | None:
    """The hip-report attribute an OESIS method id queries, or None if the
    method is uncatalogued (in which case it covers nothing)."""
    return _METHOD_ATTRIBUTES.get(method_id)


def category_name(category_id: int) -> str | None:
    """HIP category name for an OPSWAT category id, or None if unknown."""
    return _CATEGORY_NAMES.get(category_id)
