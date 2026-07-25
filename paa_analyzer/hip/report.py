"""Parse the ``<hip-report>`` XML embedded in a PACompliance* log message
into the structured ``HipReport`` shape (Task 2 of the HIP domain model --
see docs/plans/hip-analytics-foundation.md's "Data model" section).

Only the report document itself is parsed here. OPSWAT error resolution,
patch merging and status heuristics are layered on top by
paa_analyzer.hip.opswat / status / __init__ in later tasks.
"""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from typing import Any

from paa_analyzer.hip._xml import text_or_none as _text_or_none

_XML_START = "<?xml"
_REPORT_END = "</hip-report>"

# host-id shapes observed in the fixtures: macOS emits a colon-separated MAC
# address, Windows a hyphenated GUID. host_id_kind is derived from the
# value's shape, never from the `platform` argument (see parse_hip_report).
_MAC_RE = re.compile(r"^[0-9A-Fa-f]{2}(:[0-9A-Fa-f]{2}){5}$")
_GUID_RE = re.compile(r"^[0-9A-Fa-f]{8}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{12}$")

# host-info's own scalar fields: XML tag -> HipReport.host_info key.
_HOST_INFO_FIELDS = {
    "client-version": "client_version",
    "os": "os",
    "os-vendor": "os_vendor",
    "domain": "domain",
    "host-name": "host_name",
    "host-id": "host_id",
}

# Prod attributes already surfaced as named HipProduct fields -- everything
# else on Prod (e.g. engver, prodType, osType) passes through into
# attributes, see _parse_product.
_PROD_NAMED_ATTRS = {"name", "version", "vendor", "defver", "dateyear", "datemon", "dateday"}


def parse_hip_report(xml_text: str, platform: str) -> dict[str, Any] | None:
    """Parse a hip-report document out of a raw log entry message.

    `xml_text` is the full log message (e.g. "GetHipReport report <?xml
    ...>...</hip-report>"), not a pre-sliced XML string -- the document is
    located between the first "<?xml" and the closing "</hip-report>" and
    parsed from there. Returns None if either boundary is missing.

    `platform` is accepted for symmetry with the rest of the cycle-assembly
    API (Task 4) but does not influence parsing: host_id_kind is derived
    purely from the host-id value's shape, per the brief.
    """
    start = xml_text.find(_XML_START)
    if start == -1:
        return None
    end = xml_text.find(_REPORT_END, start)
    if end == -1:
        return None
    end += len(_REPORT_END)

    root = ET.fromstring(xml_text[start:end])

    host_info: dict[str, Any] | None = None
    categories: list[dict[str, Any]] = []
    for entry in root.findall("./categories/entry"):
        if entry.attrib.get("name") == "host-info":
            host_info = _parse_host_info(entry)
        else:
            categories.append(_parse_category(entry))

    return {
        "version": _text_or_none(root.find("hip-report-version")),
        "host_info": host_info,
        "categories": categories,
        "custom_checks": _parse_custom_checks(root),
    }


# ── host-info ────────────────────────────────────────────────────────────────


def _parse_host_info(entry: ET.Element) -> dict[str, Any]:
    info: dict[str, Any] = {key: _text_or_none(entry.find(tag)) for tag, key in _HOST_INFO_FIELDS.items()}
    info["host_id_kind"] = _host_id_kind(info["host_id"])
    info["interfaces"] = [_parse_interface(iface) for iface in entry.findall("./network-interface/entry")]
    return info


def _host_id_kind(host_id: str | None) -> str:
    if host_id and _MAC_RE.match(host_id):
        return "mac-address"
    if host_id and _GUID_RE.match(host_id):
        return "machine-guid"
    return "unknown"


def _parse_interface(entry: ET.Element) -> dict[str, Any]:
    return {
        "name": entry.attrib.get("name"),
        "description": _text_or_none(entry.find("description")),
        "mac": _text_or_none(entry.find("mac-address")),
        "ipv4": [ip.attrib.get("name") for ip in entry.findall("./ip-address/entry")],
        "ipv6": [ip.attrib.get("name") for ip in entry.findall("./ipv6-address/entry")],
    }


# ── categories / products ────────────────────────────────────────────────────


def _parse_category(entry: ET.Element) -> dict[str, Any]:
    """Any categories/entry other than host-info -- known or unknown alike,
    the category name and its products are read generically, not from a
    hardcoded name list, so an unrecognized category still survives."""
    return {
        "name": entry.attrib.get("name"),
        "products": [_parse_product(p) for p in entry.findall("./list/entry/ProductInfo")],
    }


def _parse_product(product_info: ET.Element) -> dict[str, Any]:
    prod = product_info.find("Prod")
    # UNREACHED: every ProductInfo in both fixtures has a Prod child; the
    # `prod is None` fallback below is defensive only.
    attrib = prod.attrib if prod is not None else {}

    product: dict[str, Any] = {
        "name": attrib.get("name") or None,
        "version": attrib.get("version") or None,
        "vendor": attrib.get("vendor") or None,
        "def_version": attrib.get("defver") or None,
        "def_date": _def_date(attrib),
        "attributes": {},
    }

    # Any other Prod attribute (e.g. engver, prodType, osType -- real,
    # populated fields on the anti-malware/EDR products in both platforms'
    # fixtures) passes through into attributes verbatim, keyed by its own
    # attribute name, so nothing on Prod is silently dropped.
    for key, value in attrib.items():
        if key in _PROD_NAMED_ATTRS:
            continue
        product["attributes"][key] = value or None

    # Every ProductInfo child other than Prod also goes verbatim into
    # attributes, keyed by its own tag -- this is what makes unknown fields
    # (and unknown categories, via _parse_category above) survive into the
    # model. Assigned after the Prod-attribute loop above so that, if a Prod
    # attribute name ever collided with a child element's tag, the child
    # element wins (it carries richer structure) -- no such collision exists
    # in the current fixtures since Prod attributes are camelCase and child
    # tags are hyphenated, so this is a guard, not an observed case.
    for child in product_info:
        if child is prod:
            continue
        product["attributes"][child.tag] = _passthrough_value(child)
        if child.tag == "drives":
            product["drives"] = _lift_drives(child)

    return product


def _def_date(attrib: dict[str, str]) -> str | None:
    year, month, day = attrib.get("dateyear", ""), attrib.get("datemon", ""), attrib.get("dateday", "")
    if year and month and day:
        return f"{year}-{month}-{day}"
    return None


def _passthrough_value(elem: ET.Element) -> Any:
    """Verbatim value for a ProductInfo child other than Prod: plain text
    for a leaf element, or a list of {tag: text} dicts for a container of
    <entry> children (e.g. disk-encryption's <drives>)."""
    entries = elem.findall("entry")
    if entries:
        return [{child.tag: _text_or_none(child) for child in e} for e in entries]
    return _text_or_none(elem)


def _lift_drives(drives_elem: ET.Element) -> list[dict[str, Any]]:
    """disk-encryption's <drives> lifted to the friendly {name, enc_state}
    shape the HipProduct data model expects, on top of the raw passthrough
    already kept in attributes["drives"]."""
    return [
        {"name": _text_or_none(d.find("drive-name")), "enc_state": _text_or_none(d.find("enc-state"))}
        for d in drives_elem.findall("entry")
    ]


# ── custom-checks ────────────────────────────────────────────────────────────


def _parse_custom_checks(root: ET.Element) -> dict[str, Any] | None:
    cc = root.find("custom-checks")
    if cc is None:
        # The Windows fixture has no <custom-checks> element at all.
        return None
    plist = cc.find("plist")
    if plist is not None:
        return {"kind": "plist", "entries": _parse_check_entries(plist)}
    registry = cc.find("registry")
    if registry is not None:
        # UNTESTED: no available bundle contains a <registry> custom-checks
        # block -- this branch is inferred defensively from the <plist>
        # shape's symmetry (both are a container of named <entry> elements
        # with a nested preference-value/member list). Revisit if a real
        # Windows custom-checks sample surfaces.
        return {"kind": "registry", "entries": _parse_check_entries(registry)}
    return {"kind": "unknown", "entries": []}


def _parse_check_entries(container: ET.Element) -> list[dict[str, Any]]:
    """Recursively parse a container of <entry name="..."> elements, as
    found under custom-checks/plist (and, untested, custom-checks/registry).
    A child that itself contains <entry> elements (e.g. preference-value) is
    recursed into rather than treated as a scalar leaf."""
    entries = []
    for entry in container.findall("entry"):
        item: dict[str, Any] = {"name": entry.attrib.get("name")}
        for child in entry:
            item[child.tag] = _parse_check_entries(child) if child.findall("entry") else _text_or_none(child)
        entries.append(item)
    return entries
