"""Unit tests for paa_analyzer.hip.patches -- <missing-patches> XML fragment
-> list of MissingPatch dicts.

Driven off the redacted real fixtures in backend/tests/fixtures/hip/, not
hand-authored log lines or XML (see .superpowers/sdd/global-constraints.md).
"""

from pathlib import Path

from paa_analyzer.hip.patches import parse_missing_patches
from paa_analyzer.parsers import structured_log

FIXTURES = Path(__file__).parent / "fixtures" / "hip"


def _missing_patches_message(filename):
    entries = structured_log((FIXTURES / filename).read_text())
    for entry in entries:
        if "GetMissingPatchesReport report:" in entry["message"]:
            return entry["message"]
    raise AssertionError(f"no GetMissingPatchesReport entry found in {filename}")


class TestPopulatedFragment:
    """Both real Mp rotations carry the same 2 patches (macOS Tahoe + Safari)
    -- see docs/plans/hip-analytics-foundation.md's 2026-07-26 correction."""

    def setup_method(self):
        message = _missing_patches_message("PAComplianceMp.log")
        self.patches = parse_missing_patches(message)

    def test_two_patches_parsed(self):
        assert len(self.patches) == 2

    def test_safari_patch_fields(self):
        safari = next(p for p in self.patches if p["title"].startswith("Safari"))
        assert safari["kb_article_id"] == "127685"
        assert safari["severity"] == "moderate"
        assert safari["category"] == "update"
        assert safari["product"] is None
        assert safari["vendor"] is None
        assert safari["is_installed"] == "n/a"
        assert safari["deadline_info"] == "n/a"

    def test_safari_patch_does_not_require_reboot(self):
        safari = next(p for p in self.patches if p["title"].startswith("Safari"))
        assert safari["reboot_required"] is False

    def test_macos_tahoe_patch_fields(self):
        tahoe = next(p for p in self.patches if p["title"].startswith("macOS Tahoe"))
        assert tahoe["product"] == "macOS Tahoe"
        assert tahoe["kb_article_id"] == "127595"
        assert tahoe["severity"] == "important"

    def test_macos_tahoe_patch_requires_reboot(self):
        """reboot_required is derived from the description containing the
        literal substring "Action: restart" -- the only inference here."""
        tahoe = next(p for p in self.patches if p["title"].startswith("macOS Tahoe"))
        assert "Action: restart" in tahoe["description"]
        assert tahoe["reboot_required"] is True

    def test_preceding_rotation_carries_the_same_two_patches(self):
        message = _missing_patches_message("PAComplianceMp.1.log")
        patches = parse_missing_patches(message)
        assert len(patches) == 2


class TestEmptyFragment:
    def test_windows_hip_report_has_no_patches(self):
        """Windows has no separate Mp log; its main hip-report XML carries a
        genuinely empty <missing-patches> element -- the real source of the
        empty-fragment case (not PAComplianceMp.1.log, which is populated)."""
        text = (FIXTURES / "PACompliance_win.log").read_text()
        start = text.index("<missing-patches>")
        end = text.index("</missing-patches>", start) + len("</missing-patches>")
        fragment = text[start:end]
        assert parse_missing_patches(fragment) == []

    def test_text_with_no_missing_patches_tag_yields_empty_list(self):
        assert parse_missing_patches("no xml here at all") == []


class TestMalformedXml:
    """One malformed character in a real patch fragment must degrade to [],
    not propagate ET.ParseError -- see
    docs/plans/hip-analytics-foundation.md's Important 2 finding. The input
    is the real fixture message with a single unescaped "&" injected into
    its <title> element, not hand-authored XML."""

    def test_unescaped_ampersand_returns_empty_list_instead_of_raising(self):
        message = _missing_patches_message("PAComplianceMp.log")
        assert "<title>Safari26.5.2SequoiaAuto-26.5.2</title>" in message
        malformed = message.replace(
            "<title>Safari26.5.2SequoiaAuto-26.5.2</title>",
            "<title>Safari & Friends</title>",
        )
        assert parse_missing_patches(malformed) == []
