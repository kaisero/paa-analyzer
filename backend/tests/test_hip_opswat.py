"""Unit tests for paa_analyzer.hip.opswat -- DETECT_PRODUCTS signature
resolution and Opswat Error(-N) parsing.

Driven off the redacted real fixtures in backend/tests/fixtures/hip/, not
hand-authored log lines (see .superpowers/sdd/global-constraints.md).
"""

from pathlib import Path
from typing import Any

from paa_analyzer.hip.opswat import parse_detected_products, parse_opswat_errors
from paa_analyzer.parsers import structured_log

FIXTURES = Path(__file__).parent / "fixtures" / "hip"


def _entries(name: str) -> list[dict[str, Any]]:
    return structured_log((FIXTURES / name).read_text())


# ── parse_detected_products ─────────────────────────────────────────────────


class TestParseDetectedProductsMac:
    """PACompliance.log has 6 DETECT_PRODUCTS blobs across the one cycle --
    merging across all of them is exercised implicitly by asserting products
    from more than one blob are present in the same map."""

    def test_gatekeeper_and_xprotect_resolve(self):
        products = parse_detected_products(_entries("PACompliance.log"))
        assert products[100141] == {
            "name": "Gatekeeper",
            "vendor": "Apple Inc.",
            "product_id": 100137,
            "categories": [5],
        }
        assert products[100428] == {
            "name": "Xprotect",
            "vendor": "Apple Inc.",
            "product_id": 100366,
            "categories": [5],
        }

    def test_time_machine_from_a_later_blob_also_resolves(self):
        """Time Machine's signature (100191) is in the disk-backup category's
        DETECT_PRODUCTS blob, a later blob than Gatekeeper/Xprotect's -- this
        proves multiple blobs in one cycle are merged, not just the first."""
        products = parse_detected_products(_entries("PACompliance.log"))
        assert products[100191] == {
            "name": "Time Machine",
            "vendor": "Apple Inc.",
            "product_id": 100012,
            "categories": [2],
        }

    def test_empty_detected_products_blob_contributes_nothing(self):
        """The data-loss-prevention category's blob has an empty
        detected_products list in this bundle ("no products detected for
        category: 11") -- must not raise, and the map must hold exactly the
        11 signatures carried by the other, non-empty blobs."""
        products = parse_detected_products(_entries("PACompliance.log"))
        assert len(products) == 11


class TestParseDetectedProductsMp:
    """PAComplianceMp.log uses the "Detected patch products" prefix instead
    of "StartComplianceData (DETECT_PRODUCTS) output:"."""

    def test_jamf_pro_resolves(self):
        products = parse_detected_products(_entries("PAComplianceMp.log"))
        assert products[100493] == {
            "name": "Jamf Pro",
            "vendor": "JAMF Software",
            "product_id": 100432,
            "categories": [12],
        }


class TestParseDetectedProductsWindows:
    def test_microsoft_intune_resolves(self):
        products = parse_detected_products(_entries("PACompliance_win.log"))
        assert products[3298] == {
            "name": "Microsoft Intune Management Extension",
            "vendor": "Microsoft Corporation",
            "product_id": 3146,
            "categories": [12],
        }


# ── parse_opswat_errors ──────────────────────────────────────────────────────


class TestParseOpswatErrorsMac:
    """PACompliance.log carries the 4 distinct signature-bearing OPSWAT
    errors in this dataset -- 2 for Gatekeeper (methods 1001 and 1004), 1 for
    Xprotect, and the ForDLP-prefixed Time Machine one."""

    def _errors(self):
        entries = _entries("PACompliance.log")
        signature_map = parse_detected_products(entries)
        return parse_opswat_errors(entries, "PACompliance", signature_map)

    def test_four_signature_bearing_errors(self):
        errors = self._errors()
        assert len(errors) == 4
        assert all(e["signature"] is not None for e in errors)

    def test_xprotect_resolution(self):
        errors = self._errors()
        xprotect = next(e for e in errors if e["signature"] == 100428)
        assert xprotect["product"] == "Xprotect"
        assert xprotect["code"] == -12
        assert xprotect["method"] == 1004
        assert xprotect["category_id"] == 5
        assert xprotect["category"] == "anti-malware"
        assert xprotect["code_meaning"] is not None
        assert xprotect["method_name"] is not None
        assert xprotect["source"] == "PACompliance"
        assert "Signature: 100428" in xprotect["raw_message"]

    def test_gatekeeper_resolution_both_methods(self):
        errors = self._errors()
        gatekeeper_errors = [e for e in errors if e["signature"] == 100141]
        assert len(gatekeeper_errors) == 2
        assert {e["method"] for e in gatekeeper_errors} == {1001, 1004}
        for e in gatekeeper_errors:
            assert e["product"] == "Gatekeeper"
            assert e["code"] == -11
            assert e["category"] == "anti-malware"

    def test_time_machine_error_logged_under_dlp_prefix_resolves_to_disk_backup(self):
        """The log line's own function-name prefix is
        "CollectComplianceDataForDLP", not an anti-malware or backup-specific
        name -- only the Category: field (2) should drive resolution."""
        errors = self._errors()
        time_machine = next(e for e in errors if e["signature"] == 100191)
        assert time_machine["raw_message"].startswith("CollectComplianceDataForDLP")
        assert time_machine["category_id"] == 2
        assert time_machine["category"] == "disk-backup"
        assert time_machine["product"] == "Time Machine"
        assert time_machine["code"] == -28


class TestParseOpswatErrorsMp:
    """PAComplianceMp.log's GetMissingPatchesForThisProduct errors omit the
    Signature: field entirely."""

    def test_signature_less_errors_leave_signature_and_product_none(self):
        entries = _entries("PAComplianceMp.log")
        signature_map = parse_detected_products(entries)
        errors = parse_opswat_errors(entries, "PAComplianceMp", signature_map)
        assert len(errors) == 2
        for e in errors:
            assert e["signature"] is None
            assert e["product"] is None
            assert e["category_id"] == 12
            assert e["category"] == "patch-management"
            assert e["method"] == 1013
            assert e["source"] == "PAComplianceMp"


class TestParseOpswatErrorsUncataloguedMethod:
    """PACompliance_win.log's patch-management errors carry Method: 1012, an
    OESIS method id codes.py deliberately does not catalogue (only 1001,
    1004, 1008 and 1013 are). This is real fixture data, not an invented
    case -- see the task report for why method 1009 and category 11
    (mentioned in the task description) could not be exercised the same way:
    neither appears inside an "Opswat Error(...)" line in any fixture."""

    def test_uncatalogued_method_resolves_to_none_without_raising(self):
        entries = _entries("PACompliance_win.log")
        signature_map = parse_detected_products(entries)
        errors = parse_opswat_errors(entries, "PACompliance", signature_map)
        patch_errors = [e for e in errors if e["method"] == 1012]
        assert len(patch_errors) == 2
        for e in patch_errors:
            # The raw id survives even though it has no catalogued meaning.
            assert e["method_name"] is None
            # Its category (12, patch-management) IS catalogued, and its
            # product still resolves -- an unknown method doesn't take the
            # rest of the error down with it.
            assert e["category_id"] == 12
            assert e["category"] == "patch-management"
        assert {e["signature"] for e in patch_errors} == {3298, 3905}
        assert {e["product"] for e in patch_errors} == {
            "Microsoft Intune Management Extension",
            "Dell Command | Update",
        }
