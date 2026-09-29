"""Unit tests for paa_analyzer.hip.report -- hip-report XML -> HipReport.

Driven off the redacted real fixtures in backend/tests/fixtures/hip/, not
hand-authored log lines or XML (see .superpowers/sdd/global-constraints.md).
"""

from pathlib import Path

from paa_analyzer.hip.report import parse_hip_report
from paa_analyzer.parsers import structured_log

FIXTURES = Path(__file__).parent / "fixtures" / "hip"


def _hip_report_message(filename):
    """The single log entry whose message carries the whole hip-report XML
    (structured_log folds the non-timestamped continuation lines into it --
    see docs/plans/hip-analytics-foundation.md finding 1)."""
    entries = structured_log((FIXTURES / filename).read_text())
    for entry in entries:
        if "GetHipReport report" in entry["message"]:
            return entry["message"]
    raise AssertionError(f"no GetHipReport entry found in {filename}")


MAC_MESSAGE = _hip_report_message("PACompliance.log")
WIN_MESSAGE = _hip_report_message("PACompliance_win.log")


# ── boundary extraction ──────────────────────────────────────────────────────


class TestBoundaryExtraction:
    def test_parses_real_message_with_leading_prefix_text(self):
        """The message starts with "GetHipReport report " before <?xml --
        parse_hip_report must locate the XML itself, not require a caller to
        pre-slice it."""
        assert MAC_MESSAGE.startswith("GetHipReport report ")
        report = parse_hip_report(MAC_MESSAGE, "macos")
        assert report is not None
        assert report["version"] == "4"

    def test_missing_xml_start_returns_none(self):
        # Slice off everything up to and including "<?xml" from the real
        # message -- a real fragment with the opening boundary removed.
        cut = MAC_MESSAGE[MAC_MESSAGE.index("<?xml") + len("<?xml") :]
        assert parse_hip_report(cut, "macos") is None

    def test_missing_closing_tag_returns_none(self):
        # Slice off everything from "</hip-report>" onward.
        cut = MAC_MESSAGE[: MAC_MESSAGE.index("</hip-report>")]
        assert parse_hip_report(cut, "macos") is None

    def test_platform_argument_does_not_affect_parsing(self):
        """host_id_kind must come from the value's shape, not this argument
        -- passing the "wrong" platform must not change the result."""
        assert parse_hip_report(MAC_MESSAGE, "windows") == parse_hip_report(MAC_MESSAGE, "macos")


# ── host-info ────────────────────────────────────────────────────────────────


class TestHostInfoMacOS:
    def setup_method(self):
        self.report = parse_hip_report(MAC_MESSAGE, "macos")
        assert self.report is not None
        self.host_info = self.report["host_info"]

    def test_flat_scalar_fields(self):
        assert self.host_info["os"] == "Apple Mac OS X 15.7.7"
        assert self.host_info["os_vendor"] == "Apple"
        assert self.host_info["client_version"] == "26.2.1.26"
        assert self.host_info["host_name"] == "testhost"
        assert self.host_info["host_id"] == "00:00:5e:00:53:01"

    def test_empty_domain_element_becomes_none(self):
        assert self.host_info["domain"] is None

    def test_host_id_kind_is_mac_address(self):
        assert self.host_info["host_id_kind"] == "mac-address"

    def test_interfaces_extracted(self):
        interfaces = self.host_info["interfaces"]
        assert len(interfaces) == 23
        by_name = {i["name"]: i for i in interfaces}
        en0 = by_name["en0"]
        assert en0["description"] == "en0"
        assert en0["mac"] == "00:00:5e:00:53:0a"
        assert en0["ipv4"] == ["192.0.2.2"]
        assert en0["ipv6"] == ["fe80::6"]

    def test_interface_with_empty_mac_and_no_ipv4(self):
        by_name = {i["name"]: i for i in self.host_info["interfaces"]}
        utun3 = by_name["utun3"]
        assert utun3["mac"] is None
        assert utun3["ipv4"] == []
        assert utun3["ipv6"] == ["fe80::2"]

    def test_loopback_interface_multiple_ipv6(self):
        by_name = {i["name"]: i for i in self.host_info["interfaces"]}
        lo0 = by_name["lo0"]
        assert lo0["ipv4"] == ["127.0.0.1"]
        assert lo0["ipv6"] == ["::1", "fe80::8"]


class TestHostInfoWindows:
    def setup_method(self):
        self.report = parse_hip_report(WIN_MESSAGE, "windows")
        assert self.report is not None
        self.host_info = self.report["host_info"]

    def test_domain_is_populated(self):
        assert self.host_info["domain"] == "example.com"

    def test_host_id_kind_is_machine_guid(self):
        assert self.host_info["host_id"] == "00000000-0000-0000-0000-000000000002"
        assert self.host_info["host_id_kind"] == "machine-guid"

    def test_interfaces_extracted(self):
        interfaces = self.host_info["interfaces"]
        assert len(interfaces) == 5
        loopback = next(i for i in interfaces if i["description"] == "Software Loopback Interface 1")
        assert loopback["mac"] is None
        assert loopback["ipv4"] == ["127.0.0.1"]
        assert loopback["ipv6"] == ["::1"]


# ── categories / products ────────────────────────────────────────────────────


class TestCategoriesMacOS:
    def setup_method(self):
        report = parse_hip_report(MAC_MESSAGE, "macos")
        assert report is not None
        self.categories = {c["name"]: c for c in report["categories"]}

    def test_category_set_excludes_host_info(self):
        assert set(self.categories) == {
            "anti-malware",
            "disk-backup",
            "disk-encryption",
            "firewall",
            "data-loss-prevention",
            "patch-management",
            "certificate",
        }

    def test_product_counts(self):
        assert len(self.categories["anti-malware"]["products"]) == 3
        assert len(self.categories["disk-backup"]["products"]) == 2
        assert len(self.categories["disk-encryption"]["products"]) == 1
        assert len(self.categories["firewall"]["products"]) == 2
        assert len(self.categories["patch-management"]["products"]) == 3

    def test_empty_list_categories_yield_empty_products_not_none(self):
        assert self.categories["data-loss-prevention"]["products"] == []
        assert self.categories["certificate"]["products"] == []

    def test_product_name_version_vendor(self):
        cortex = next(p for p in self.categories["anti-malware"]["products"] if p["name"] == "Cortex XDR")
        assert cortex["version"] == "9.0.0"
        assert cortex["vendor"] == "Palo Alto Networks, Inc."

    def test_def_version_and_def_date_assembled(self):
        cortex = next(p for p in self.categories["anti-malware"]["products"] if p["name"] == "Cortex XDR")
        assert cortex["def_version"] == "2026.07.25"
        assert cortex["def_date"] == "2026-07-25"

    def test_empty_defver_and_date_parts_become_none(self):
        gatekeeper = next(p for p in self.categories["anti-malware"]["products"] if p["name"] == "Gatekeeper")
        assert gatekeeper["def_version"] is None
        assert gatekeeper["def_date"] is None

    def test_non_prod_children_go_into_attributes_verbatim(self):
        cortex = next(p for p in self.categories["anti-malware"]["products"] if p["name"] == "Cortex XDR")
        assert cortex["attributes"]["real-time-protection"] == "yes"
        assert cortex["attributes"]["last-full-scan-time"] == "07/20/2026 12:50:41"

    def test_disk_backup_attribute(self):
        time_machine = next(p for p in self.categories["disk-backup"]["products"] if p["name"] == "Time Machine")
        assert time_machine["attributes"]["last-backup-time"] == "n/a"

    def test_firewall_and_patch_management_is_enabled_attribute(self):
        pf = next(p for p in self.categories["firewall"]["products"] if p["name"] == "Packet Filter")
        assert pf["attributes"]["is-enabled"] == "yes"
        autoupdate = next(
            p for p in self.categories["patch-management"]["products"] if p["name"] == "Microsoft AutoUpdate"
        )
        assert autoupdate["attributes"]["is-enabled"] == "no"

    def test_prods_extra_attributes_pass_through(self):
        """Cortex XDR's Prod carries prodType/osType (populated) alongside
        an empty engver -- all three must still land in attributes, with the
        empty one normalized to None like every other empty scalar."""
        cortex = next(p for p in self.categories["anti-malware"]["products"] if p["name"] == "Cortex XDR")
        assert cortex["attributes"]["prodType"] == "3"
        assert cortex["attributes"]["osType"] == "4"
        assert cortex["attributes"]["engver"] is None

    def test_prod_without_extra_attributes_gains_no_empty_keys(self):
        """Google Drive's Prod has no engver/prodType/osType/defver attributes
        at all -- they must not appear in attributes as spurious empty keys."""
        drive = next(p for p in self.categories["disk-backup"]["products"] if p["name"] == "Google Drive")
        assert "engver" not in drive["attributes"]
        assert "prodType" not in drive["attributes"]
        assert "osType" not in drive["attributes"]


class TestCategoriesWindows:
    def setup_method(self):
        report = parse_hip_report(WIN_MESSAGE, "windows")
        assert report is not None
        self.categories = {c["name"]: c for c in report["categories"]}

    def test_category_set_matches_macos(self):
        assert set(self.categories) == {
            "anti-malware",
            "disk-backup",
            "disk-encryption",
            "firewall",
            "data-loss-prevention",
            "patch-management",
            "certificate",
        }

    def test_product_counts(self):
        assert len(self.categories["anti-malware"]["products"]) == 2
        assert len(self.categories["disk-backup"]["products"]) == 3
        assert len(self.categories["firewall"]["products"]) == 1
        assert len(self.categories["patch-management"]["products"]) == 4

    def test_prods_engver_is_distinct_from_def_version(self):
        """Windows Defender's Prod carries both a populated engver (engine
        version) and defver (signature version) -- distinct values that must
        both surface, engver via attributes and defver via def_version."""
        defender = next(p for p in self.categories["anti-malware"]["products"] if p["name"] == "Windows Defender")
        assert defender["def_version"] == "1.455.279.0"
        assert defender["attributes"]["engver"] == "1.1.26060.3008"
        assert defender["attributes"]["prodType"] == "3"
        assert defender["attributes"]["osType"] == "1"


class TestDrivesLifting:
    """disk-encryption drives are lifted to {name, enc_state} on the product,
    while the raw <drives> structure is kept verbatim in attributes too."""

    def test_macos_filevault_three_drives(self):
        report = parse_hip_report(MAC_MESSAGE, "macos")
        assert report is not None
        categories = {c["name"]: c for c in report["categories"]}
        filevault = categories["disk-encryption"]["products"][0]
        assert filevault["name"] == "FileVault"
        assert filevault["drives"] == [
            {"name": "Macintosh HD - Data", "enc_state": "encrypted"},
            {"name": "Macintosh HD", "enc_state": "encrypted"},
            {"name": "All", "enc_state": "encrypted"},
        ]
        assert filevault["attributes"]["drives"] == [
            {"drive-name": "Macintosh HD - Data", "enc-state": "encrypted"},
            {"drive-name": "Macintosh HD", "enc-state": "encrypted"},
            {"drive-name": "All", "enc-state": "encrypted"},
        ]

    def test_windows_bitlocker_two_drives(self):
        """The task brief describes the Windows fixture's <drives> as empty;
        the real redacted fixture instead carries 2 entries (C:\\ and All).
        Asserting against the actual fixture content per the brief's own
        "real fixture content" instruction -- see task-2-report.md Concerns."""
        report = parse_hip_report(WIN_MESSAGE, "windows")
        assert report is not None
        categories = {c["name"]: c for c in report["categories"]}
        bitlocker = categories["disk-encryption"]["products"][0]
        assert bitlocker["name"] == "BitLocker Drive Encryption"
        assert bitlocker["drives"] == [
            {"name": "C:\\", "enc_state": "encrypted"},
            {"name": "All", "enc_state": "encrypted"},
        ]

    def test_products_without_drives_have_no_drives_key(self):
        report = parse_hip_report(MAC_MESSAGE, "macos")
        assert report is not None
        categories = {c["name"]: c for c in report["categories"]}
        cortex = next(p for p in categories["anti-malware"]["products"] if p["name"] == "Cortex XDR")
        assert "drives" not in cortex


# ── custom-checks ────────────────────────────────────────────────────────────


class TestCustomChecks:
    def test_macos_plist_custom_checks(self):
        report = parse_hip_report(MAC_MESSAGE, "macos")
        assert report is not None
        custom_checks = report["custom_checks"]
        assert custom_checks["kind"] == "plist"
        assert custom_checks["entries"] == [
            {
                "name": "com.jamfsoftware.jamf",
                "exist": "yes",
                "value": None,
                "preference-value": [
                    {
                        "name": "jss_url",
                        "exist": "yes",
                        "value": "https://jss.example.com:8443/",
                    }
                ],
            }
        ]

    def test_windows_has_no_custom_checks_element(self):
        report = parse_hip_report(WIN_MESSAGE, "windows")
        assert report is not None
        assert report["custom_checks"] is None


# ── malformed XML ─────────────────────────────────────────────────────────────


class TestMalformedXml:
    """One malformed character in a real report must degrade to None, not
    propagate ET.ParseError -- see docs/plans/hip-analytics-foundation.md's
    Important 2 finding. The input is the real fixture message with a single
    unescaped "&" injected into its <os> element, not hand-authored XML."""

    def test_unescaped_ampersand_returns_none_instead_of_raising(self):
        assert "<os>Apple Mac OS X 15.7.7</os>" in MAC_MESSAGE
        malformed = MAC_MESSAGE.replace(
            "<os>Apple Mac OS X 15.7.7</os>",
            "<os>Apple Mac OS X 15.7.7 & Friends</os>",
        )
        assert parse_hip_report(malformed, "macos") is None
