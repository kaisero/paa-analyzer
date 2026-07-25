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
   its OESIS method id maps to that attribute in `codes.method_attribute()`,
   which is why an error on a different method (e.g. Xprotect's method 1004,
   last full scan time) leaves `real-time-protection=no` standing as `warn`.
3. Otherwise the value speaks for itself: good -> `ok`, explicitly bad ->
   `warn`, anything else (e.g. Windows' `is-enabled=n/a`) -> `unknown`.

A category with zero products is `not-detected`; otherwise its status is the
worst of its products'.
"""

from __future__ import annotations

from typing import Any

from paa_analyzer.hip.codes import method_attribute

# The attribute a product's verdict is based on, in precedence order. No
# product in either fixture reports more than one of these.
_KEY_ATTRIBUTES = ("real-time-protection", "is-enabled", "drives")

_DRIVES = "drives"
_GOOD_VALUE = "yes"
_BAD_VALUE = "no"
_ENCRYPTED = "encrypted"

# Worst-wins ordering for rolling product statuses up into a category status.
# `warn` outranks `unknown`: a known-bad value is a firmer finding than an
# unreadable one. Only product-level statuses ever appear here -- a product
# is never `not-detected` (that's a category-only verdict for zero products),
# so it has no entry; an unexpected status falls back to `_SEVERITY.get(status,
# 0)`, the same severity as `ok`, which is deliberately the least alarming
# choice rather than a guess at where it should rank.
_SEVERITY = {"ok": 0, "unknown": 1, "warn": 2}


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

    covering = next((error for error in errors if method_attribute(error["method"]) == key), None)
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
    """Return `(status, reason)` for a HipCategory, given its products.

    Reads each product's already-computed `status` -- set by
    `_decorate_categories` before this runs -- rather than recomputing it via
    `product_status()`, so the two can never disagree. Falls back to
    `product_status()` for a product dict that hasn't been decorated yet.
    """
    if not products:
        return "not-detected", "No products were detected in this category."

    statuses = [product.get("status") or product_status(product)[0] for product in products]
    total = len(products)
    warn = statuses.count("warn")
    unknown = statuses.count("unknown")
    worst = max(statuses, key=lambda status: _SEVERITY.get(status, 0))
    noun = _plural(total, "product", "products")

    if worst == "warn":
        reason = f"{warn} of {total} {noun} {_plural(warn, 'reports', 'report')} a bad value."
        if unknown:
            # Don't let a second-worst finding go invisible behind the worst
            # one -- a category whose reason only ever names the top status
            # can hide an equally-unresolved product.
            reason += f" {unknown} more could not be queried."
        return "warn", reason
    if worst == "unknown":
        return "unknown", f"{unknown} of {total} {noun} could not be queried."
    return "ok", f"All {total} {noun} {_plural(total, 'reports', 'report')} a good value."


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
    attribute = method_attribute(method) or "the value it reports"
    return f"OPSWAT method {method} failed with error {code}, so {attribute} could not be queried."


def _plural(count: int, singular: str, plural: str) -> str:
    """`singular` for a count of exactly 1, `plural` otherwise. Used for both
    nouns (`_plural(total, "product", "products")`) and verbs
    (`_plural(warn, "reports", "report")` -- singular subject, singular verb
    form ending in `s`)."""
    return singular if count == 1 else plural
