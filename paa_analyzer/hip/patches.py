"""Parse the ``<missing-patches>`` XML fragment embedded in a
PAComplianceMp log message into a list of ``MissingPatch`` dicts (Task 2 of
the HIP domain model -- see docs/plans/hip-analytics-foundation.md's "Data
model" section).

The <missing-patches> element inside the main hip-report XML (parsed by
paa_analyzer.hip.report) is always empty -- the Mp worker computes patches
separately and this module is what reads that separate document. Merging
the result into the patch-management category is Task 4's job.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from typing import Any

_FRAGMENT_START = "<missing-patches>"
_FRAGMENT_END = "</missing-patches>"

# MissingPatch's scalar fields: XML tag -> dict key.
_FIELD_TAGS = {
    "title": "title",
    "description": "description",
    "product": "product",
    "vendor": "vendor",
    "info-url": "info_url",
    "kb-article-id": "kb_article_id",
    "security-bulletin-id": "security_bulletin_id",
    "severity": "severity",
    "category": "category",
    "is-installed": "is_installed",
    "deadline-info": "deadline_info",
}


def parse_missing_patches(fragment_text: str) -> list[dict[str, Any]]:
    """Parse a <missing-patches>...</missing-patches> fragment (as embedded
    in a GetMissingPatchesReport log message) into a list of MissingPatch
    dicts. An empty fragment -- or text with no fragment at all -- yields [].
    """
    start = fragment_text.find(_FRAGMENT_START)
    if start == -1:
        return []
    end = fragment_text.find(_FRAGMENT_END, start)
    if end == -1:
        return []
    end += len(_FRAGMENT_END)

    root = ET.fromstring(fragment_text[start:end])

    patches = []
    for entry in root.findall("entry"):
        patch: dict[str, Any] = {key: _text_or_none(entry.find(tag)) for tag, key in _FIELD_TAGS.items()}
        # DERIVED: reboot_required has no XML field of its own -- it is
        # inferred from the description containing the literal substring
        # "Action: restart" (see the fixture's macOS Tahoe patch entry).
        # This is the only inference made in this module.
        patch["reboot_required"] = "Action: restart" in (patch["description"] or "")
        patches.append(patch)
    return patches


def _text_or_none(elem: ET.Element | None) -> str | None:
    if elem is None or elem.text is None:
        return None
    text = elem.text.strip()
    return text or None
