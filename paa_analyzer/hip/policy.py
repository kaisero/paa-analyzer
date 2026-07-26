"""Parse the ``Try to parse hip policy: {...}`` JSON blob embedded in a
PACompliance*/PAComplianceMp* log message (Task 3 of the HIP domain model --
see docs/plans/hip-analytics-foundation.md's "Data model" section).
"""

from __future__ import annotations

import json
from typing import Any

_POLICY_PREFIX = "Try to parse hip policy: "

# HipPolicy's fields: JSON key -> dict key (identical names -- kept for
# symmetry with the rest of the hip/ package's field-mapping tables).
_FIELDS = (
    "collection_hip_data",
    "max_wait_time",
    "default_categories",
    "exclusion_categories",
    "custom_check",
    "certs",
)


def parse_policy(message: str) -> dict[str, Any] | None:
    """Parse a policy-line log message into a HipPolicy dict.

    Returns ``{collection_hip_data, max_wait_time, default_categories,
    exclusion_categories, custom_check, certs, raw}`` where ``raw`` is the
    full decoded JSON object. Returns None if the message doesn't start with
    the policy-line prefix, or if the JSON after it is malformed -- never
    raises.
    """
    if not message.startswith(_POLICY_PREFIX):
        return None

    json_text = message[len(_POLICY_PREFIX) :]
    try:
        raw = json.loads(json_text)
    except (json.JSONDecodeError, ValueError):
        return None
    if not isinstance(raw, dict):
        return None

    policy: dict[str, Any] = {field: raw.get(field) for field in _FIELDS}
    policy["raw"] = raw
    return policy
