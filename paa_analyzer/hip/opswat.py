"""Parse OPSWAT product detection and Opswat Error(-N) lines out of a HIP
cycle's log entries (Task 3 of the HIP domain model -- see
docs/plans/hip-analytics-foundation.md's "Data model" section).

Two independent extractions live here:

- `parse_detected_products` builds the signature -> product map from the
  `DETECT_PRODUCTS` / `Detected patch products` JSON blobs.
- `parse_opswat_errors` parses the `Opswat Error(-N): ..., Signature: S,
  Category: C, Method: M` lines and resolves them against that map and
  against `codes.py`. Category/method/error-code resolution never trusts the
  log line's own function-name prefix (e.g. `CollectComplianceDataForDLP`
  can carry a disk-backup product's error) -- only the `Category:` field is
  authoritative, per the brief.
"""

from __future__ import annotations

import json
import re
from typing import Any, TypedDict

from paa_analyzer.hip import codes

# Both prefixes are followed directly by the JSON blob's opening brace, on
# the same or (usually) the next physical line -- structured_log() has
# already merged those continuation lines into this one entry's message.
_DETECT_PRODUCTS_PREFIXES = (
    "StartComplianceData (DETECT_PRODUCTS) output: ",
    "Detected patch products ",
)

# e.g. "CollectComplianceDataForAV: Opswat Error(-11): An error when a method
# call was made on a component that does not support it, Signature: 100141,
# Category: 5, Method: 1001, OESIS (V4 ver: 4.3.4222.0)"
# The GetMissingPatchesForThisProduct variant omits ", Signature: S" entirely.
_ERROR_RE = re.compile(
    r"Opswat Error\((?P<code>-?\d+)\):.*?"
    r"(?:Signature:\s*(?P<signature>\d+),\s*)?"
    r"Category:\s*(?P<category>\d+),\s*"
    r"Method:\s*(?P<method>\d+)"
)


class OpswatError(TypedDict):
    code: int
    code_meaning: str | None
    method: int
    method_name: str | None
    signature: int | None
    category_id: int
    category: str | None
    product: str | None
    source: str
    raw_message: str


def parse_detected_products(cycle_entries: list[dict[str, Any]]) -> dict[int, dict[str, Any]]:
    """Build the signature -> product map for one HIP cycle.

    Scans every entry in `cycle_entries` for a DETECT_PRODUCTS-style blob
    (either prefix), decoding from the first `{` in the message. A cycle
    typically has several such blobs (one per category); their
    detected_products lists are merged into one map keyed by signature. If
    the same signature appears in more than one blob, the later blob wins
    (in practice they are identical). Entries that aren't a detection blob,
    or whose JSON fails to decode, are skipped rather than raising.
    """
    products: dict[int, dict[str, Any]] = {}

    for entry in cycle_entries:
        message = entry.get("message") or ""
        if not any(message.startswith(prefix) for prefix in _DETECT_PRODUCTS_PREFIXES):
            continue

        brace_index = message.find("{")
        if brace_index == -1:
            continue
        try:
            blob = json.loads(message[brace_index:])
        except (json.JSONDecodeError, ValueError):
            continue

        detected = blob.get("result", {}).get("detected_products") or []
        for item in detected:
            signature = item.get("signature")
            if signature is None:
                continue
            product = item.get("product") or {}
            vendor = item.get("vendor") or {}
            products[int(signature)] = {
                "name": item.get("sig_name"),
                "vendor": vendor.get("name"),
                "product_id": product.get("id"),
                "categories": item.get("categories") or [],
            }

    return products


def parse_opswat_errors(
    cycle_entries: list[dict[str, Any]],
    source: str,
    signature_map: dict[int, dict[str, Any]],
) -> list[OpswatError]:
    """Parse every Opswat Error(-N) line in one HIP cycle's log entries.

    `source` is attached verbatim to each resulting error (e.g.
    "PACompliance" / "PAComplianceMp") so a caller merging errors from both
    logs' cycles can tell them apart. `signature_map` -- as returned by
    `parse_detected_products` for the *same* cycle -- resolves `product` to
    that signature's name; a signature-less error (the
    GetMissingPatchesForThisProduct line never carries one) leaves both
    `signature` and `product` as None rather than guessing from category.

    `category`, `code_meaning` and `method_name` are resolved through
    codes.py and are None for an uncatalogued id -- the raw `category_id`
    and `method` ints, plus the full `raw_message`, are always kept, so an
    error with an uncatalogued id is still returned intact, never dropped.
    """
    errors: list[OpswatError] = []

    for entry in cycle_entries:
        message = entry.get("message") or ""
        match = _ERROR_RE.search(message)
        if not match:
            continue

        code = int(match.group("code"))
        category_id = int(match.group("category"))
        method = int(match.group("method"))
        signature_text = match.group("signature")
        signature = int(signature_text) if signature_text is not None else None

        product_entry = signature_map.get(signature) if signature is not None else None

        errors.append(
            {
                "code": code,
                "code_meaning": codes.error_explanation(code),
                "method": method,
                "method_name": codes.method_query(method),
                "signature": signature,
                "category_id": category_id,
                "category": codes.category_name(category_id),
                "product": product_entry["name"] if product_entry else None,
                "source": source,
                "raw_message": message,
            }
        )

    return errors
