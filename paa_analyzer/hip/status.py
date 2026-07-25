"""Status heuristics for HIP products and categories (Task 4 of the HIP
domain model -- see docs/plans/hip-analytics-foundation.md's "Status
heuristics" section).

Together with `MissingPatch.reboot_required` these are the only inferences in
the model, which is why every verdict is returned with a plain-English
`status_reason` so the UI can show its work.

The rules, in the order they are applied to a product:

1. A product is judged on exactly one *key attribute* -- the first of
   `real-time-protection`, `is-enabled`, `drives` that it reports. A product
   reporting none of them (every disk-backup product in both fixtures reports
   only `last-backup-time`) cannot be judged and is `unknown`: there is no
   defined threshold that makes a backup time good or bad.
2. If an OPSWAT error covers the key attribute, the reported value cannot be
   trusted and the product is `unknown`. An error *covers* an attribute when
   its OESIS method id maps to that attribute in `_METHOD_ATTRIBUTES` below,
   which is why an error on a different method (e.g. Xprotect's method 1004,
   last full scan time) leaves `real-time-protection=no` standing as `warn`.
3. Otherwise the value speaks for itself: good -> `ok`, explicitly bad ->
   `warn`, anything else (e.g. Windows' `is-enabled=n/a`) -> `unknown`.

A category with zero products is `not-detected`; otherwise its status is the
worst of its products'.
"""

from __future__ import annotations

from typing import Any

# OESIS method id -> the hip-report attribute that method queries. Kept in
# step with the method ids catalogued in codes.py; an uncatalogued method
# (e.g. Windows' 1012) covers nothing, so it never suppresses a value.
_METHOD_ATTRIBUTES: dict[int, str] = {
    1001: "real-time-protection",
    1004: "last-full-scan-time",
    1008: "last-backup-time",
    1013: "missing-patches",
}

# The attribute a product's verdict is based on, in precedence order. No
# product in either fixture reports more than one of these.
_KEY_ATTRIBUTES = ("real-time-protection", "is-enabled", "drives")

_DRIVES = "drives"
_GOOD_VALUE = "yes"
_BAD_VALUE = "no"
_ENCRYPTED = "encrypted"

# Worst-wins ordering for rolling product statuses up into a category status.
# `warn` outranks `unknown`: a known-bad value is a firmer finding than an
# unreadable one.
_SEVERITY = {"ok": 0, "not-detected": 1, "unknown": 2, "warn": 3}


def product_status(product: dict[str, Any]) -> tuple[str, str]:
    """Return `(status, reason)` for one HipProduct.

    `product` is a product dict as assembled by `build_hip_data` -- its
    `attributes` and, for disk-encryption, `drives` supply the value being
    judged, and its `errors` are the OPSWAT errors already attached to it by
    signature.
    """
    attributes = product.get("attributes") or {}
    errors = product.get("errors") or []

    key = next((attribute for attribute in _KEY_ATTRIBUTES if attribute in attributes), None)
    if key is None:
        if errors:
            return "unknown", _error_reason(errors[0])
        return "unknown", "This product reports no attribute whose value can be judged."

    covering = next((error for error in errors if _METHOD_ATTRIBUTES.get(error["method"]) == key), None)
    if covering is not None:
        return "unknown", _error_reason(covering)

    if key == _DRIVES:
        return _drive_status(product)

    value = attributes.get(key)
    if value == _GOOD_VALUE:
        return "ok", f"{key} is {_GOOD_VALUE} and no OPSWAT error covers it."
    if value == _BAD_VALUE:
        return "warn", f"{key} is {_BAD_VALUE} and no OPSWAT error explains it."
    if value is None:
        return "unknown", f"{key} was reported without a value."
    return "unknown", f"{key} is {value}, which is neither {_GOOD_VALUE} nor {_BAD_VALUE}."


def category_status(products: list[dict[str, Any]]) -> tuple[str, str]:
    """Return `(status, reason)` for a HipCategory, given its products."""
    if not products:
        return "not-detected", "No products were detected in this category."

    statuses = [product_status(product)[0] for product in products]
    worst = max(statuses, key=lambda status: _SEVERITY.get(status, 0))
    affected = statuses.count(worst)
    total = len(products)

    if worst == "warn":
        return worst, f"{affected} of {total} products {_reports(affected)} a bad value."
    if worst == "unknown":
        return worst, f"{affected} of {total} products could not be queried."
    return "ok", f"All {total} products report a good value."


def _drive_status(product: dict[str, Any]) -> tuple[str, str]:
    drives = product.get("drives") or []
    if not drives:
        return "unknown", "No drives were reported for this product."
    unencrypted = [drive for drive in drives if drive.get("enc_state") != _ENCRYPTED]
    if unencrypted:
        return (
            "warn",
            f"{len(unencrypted)} of {len(drives)} drives report an enc-state other than {_ENCRYPTED}.",
        )
    return "ok", f"All {len(drives)} drives report enc-state {_ENCRYPTED}."


def _error_reason(error: dict[str, Any]) -> str:
    method, code = error["method"], error["code"]
    attribute = _METHOD_ATTRIBUTES.get(method) or "the value it reports"
    return f"OPSWAT method {method} failed with error {code}, so {attribute} could not be queried."


def _reports(count: int) -> str:
    return "reports" if count == 1 else "report"
