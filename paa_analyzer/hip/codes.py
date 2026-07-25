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
# What each method queries, inferred from the OPSWAT category/product context
# each id is called under in the fixtures (e.g. method 1013 is called from
# GetMissingPatchesForThisProduct under patch-management; method 1009 is
# called from CollectComplianceDataForDisks under disk-encryption).
_METHOD_QUERIES: dict[int, str] = {
    1001: "Antivirus real-time protection status.",
    1004: "Antivirus last full scan time.",
    1008: "Last backup time for a disk-backup product.",
    1013: "Missing patches for a patch-management product.",
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


def category_name(category_id: int) -> str | None:
    """HIP category name for an OPSWAT category id, or None if unknown."""
    return _CATEGORY_NAMES.get(category_id)
