"""Shared XML helper for the HIP report and missing-patches parsers."""

from __future__ import annotations

import xml.etree.ElementTree as ET


def text_or_none(elem: ET.Element | None) -> str | None:
    if elem is None or elem.text is None:
        return None
    text = elem.text.strip()
    return text or None
