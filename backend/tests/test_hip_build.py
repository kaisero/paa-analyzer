"""Tests for paa_analyzer.hip.status and paa_analyzer.hip.build_hip_data.

Every HIP input here is a redacted real fixture in backend/tests/fixtures/hip/
run through the real parsers — no hand-authored HIP log lines or HIP XML (see
.superpowers/sdd/global-constraints.md).
"""

from pathlib import Path
from typing import Any

import pytest

from paa_analyzer.hip import build_hip_data
from paa_analyzer.hip.cycle_scalars import generate_time
from paa_analyzer.hip.status import category_status, product_status
from paa_analyzer.parsers import LogEntry, hip_status, structured_log

FIXTURES = Path(__file__).parent / "fixtures" / "hip"

COMPLIANCE_KEY = "Agent.Compliance.PACompliance"
MP_KEY = "Agent.Compliance.PAComplianceMp"
HIP_STATUS_KEY = "Agent.Compliance.hip_status"


def _entries(name: str) -> list[LogEntry]:
    return structured_log((FIXTURES / name).read_text())


def _collapsed(*names: str) -> list[LogEntry]:
    """Concatenate log rotations and sort by timestamp, the way parse_zip
    collapses PACompliance.log + PACompliance.1.log into one entry stream."""
    merged: list[LogEntry] = []
    for name in names:
        merged.extend(_entries(name))
    merged.sort(key=lambda e: e["timestamp"])
    return merged


def macos_logs() -> dict[str, Any]:
    return {
        COMPLIANCE_KEY: {"entries": _collapsed("PACompliance.log", "PACompliance.1.log")},
        MP_KEY: {"entries": _collapsed("PAComplianceMp.log", "PAComplianceMp.1.log")},
    }


def windows_logs() -> dict[str, Any]:
    """The Windows bundle ships no PAComplianceMp log at all."""
    return {COMPLIANCE_KEY: {"entries": _entries("PACompliance_win.log")}}


def hip_status_state() -> dict[str, Any]:
    """The `Agent.Compliance.hip_status` state record for the macOS bundle,
    sourced from the redacted `pacli_hip_status.log` fixture committed
    alongside the other HIP fixtures.

    `collection` / `next_check` are parsed for real via `parsers.hip_status`
    -- it reads those two lines correctly today. The gateway rows are not:
    `parsers.hip_status`'s table detection looks for a "Last HIP Report"
    header, but this bundle's current table layout is `Name / Time / Status`
    (see fixture lines 4-5), so `in_table` is never set and parsing yields
    `gateways: []` for this file. That is Task 5's fix, not this one's.

    Until then, the two gateway rows used below are transcribed by hand from
    the fixture's own committed bytes, each cited by line number so the value
    is auditable against the file in this repo rather than an external bundle:
      - fixtures/hip/pacli_hip_status.log:8 -- "Finland ... 2026-07-14
        13:17:24, GMT+0200" -> 11:17:24 UTC.
      - fixtures/hip/pacli_hip_status.log:12 -- "South Korea ... 2026-06-16
        10:30:01, GMT+0200" -> 08:30:01 UTC.

    TODO(Task 5): once parsers.hip_status() reads the Name/Time/Status table,
    replace the hand-transcribed gateways below with
    hip_status(fixture_text, tz="+0200")["gateways"] and drop this docstring's
    caveat -- `status` / `status_kind` should also become tested for real then.
    """
    fixture_text = (FIXTURES / "pacli_hip_status.log").read_text()
    parsed = hip_status(fixture_text, tz="+0200")
    assert parsed["gateways"] == []  # confirms the Task 5 gap this docstring describes

    return {
        HIP_STATUS_KEY: {
            "data": {
                "collection": parsed["collection"],
                "next_check": parsed["next_check"],
                "gateways": [
                    {"gateway": "Finland", "last_report": "2026-07-14T11:17:24+00:00"},
                    {"gateway": "South Korea", "last_report": "2026-06-16T08:30:01+00:00"},
                ],
            }
        }
    }


def _category(cycle: dict[str, Any], name: str) -> dict[str, Any]:
    return next(c for c in cycle["report"]["categories"] if c["name"] == name)


def _product(cycle: dict[str, Any], category: str, name: str) -> dict[str, Any]:
    return next(p for p in _category(cycle, category)["products"] if p["name"] == name)


@pytest.fixture(scope="module")
def macos() -> dict[str, Any]:
    return build_hip_data(macos_logs(), hip_status_state(), "macos")


@pytest.fixture(scope="module")
def windows() -> dict[str, Any]:
    return build_hip_data(windows_logs(), {}, "windows")


# ── Top-level shape ──────────────────────────────────────────────────────────


class TestTopLevel:
    def test_platform_and_gateway_fields_are_present(self, macos):
        assert macos["platform"] == "macos"
        assert macos["collection"] == "Enabled"
        assert macos["next_check"] == "2026-07-25T16:07:43+00:00"

    def test_two_macos_cycles_newest_first_with_sequential_indexes(self, macos):
        cycles = macos["cycles"]
        assert [c["index"] for c in cycles] == [0, 1]
        assert cycles[0]["started_at"] == "2026-07-25T15:07:43.640000+00:00"
        assert cycles[1]["started_at"] == "2026-07-25T14:07:43.507000+00:00"
        assert cycles[0]["started_at"] > cycles[1]["started_at"]

    def test_no_cycle_is_partial(self, macos):
        assert [c["partial"] for c in macos["cycles"]] == [False, False]

    def test_raw_xml_is_kept_out_of_the_cycles_under_a_separate_key(self, macos):
        # String keys, not int: json.dumps would stringify int keys, so a
        # CLI round-trip through hip.json would disagree with the in-process
        # shape unless both use strings from the start.
        assert set(macos["_raw"]) == {"0", "1"}
        for cycle in macos["cycles"]:
            assert "raw_xml" not in cycle
            raw = macos["_raw"][str(cycle["index"])]
            assert raw["raw_xml"].startswith("<?xml")
            assert raw["raw_xml"].endswith("</hip-report>")
            assert raw["raw_patches_xml"].startswith("<missing-patches>")
            assert raw["raw_patches_xml"].endswith("</missing-patches>")

    def test_windows_cycle_has_no_paired_patches_xml(self, windows):
        assert windows["_raw"]["0"]["raw_xml"].startswith("<?xml")
        assert windows["_raw"]["0"]["raw_patches_xml"] is None


class TestEmptyShape:
    def test_missing_log_sources_yield_no_cycles(self):
        data = build_hip_data({}, hip_status_state(), "macos")
        assert data["cycles"] == []
        assert data["_raw"] == {}
        assert data["collection"] == "Enabled"
        # No cycle to measure against, so nothing to compare a report time to.
        assert [g["age_days"] for g in data["gateways"]] == [None, None]

    def test_empty_input_yields_the_empty_shape(self):
        assert build_hip_data({}, {}, "unknown") == {
            "platform": "unknown",
            "collection": None,
            "next_check": None,
            "gateways": [],
            "cycles": [],
            "_raw": {},
        }

    def test_empty_entry_lists_yield_no_cycles(self):
        data = build_hip_data({COMPLIANCE_KEY: {"entries": []}, MP_KEY: {"entries": []}}, {}, "macos")
        assert data["cycles"] == []


# ── Gateways ─────────────────────────────────────────────────────────────────


class TestGateways:
    def test_age_days_is_measured_against_the_newest_cycle_not_wall_clock(self, macos):
        # Newest cycle started 2026-07-25T15:07:43.640Z; ages are relative to
        # that, never to time.time(), so they stay stable forever.
        assert [(g["gateway"], g["last_report"], g["age_days"]) for g in macos["gateways"]] == [
            ("Finland", "2026-07-14T11:17:24+00:00", 11.2),
            ("South Korea", "2026-06-16T08:30:01+00:00", 39.3),
        ]

    def test_status_fields_default_to_none_until_the_state_parser_supplies_them(self, macos):
        gateway = macos["gateways"][0]
        assert gateway["status"] is None
        assert gateway["status_kind"] is None

    def test_status_fields_are_passed_through_when_present(self):
        state = hip_status_state()
        gateways = state[HIP_STATUS_KEY]["data"]["gateways"]
        gateways[0] = {**gateways[0], "status": "Failed to send HIP report", "status_kind": "failed"}
        data = build_hip_data(macos_logs(), state, "macos")
        assert data["gateways"][0]["status"] == "Failed to send HIP report"
        assert data["gateways"][0]["status_kind"] == "failed"

    def test_no_hip_status_state_entry_means_no_gateways(self, windows):
        assert windows["gateways"] == []
        assert windows["collection"] is None
        assert windows["next_check"] is None


# ── Cycle scalars ────────────────────────────────────────────────────────────


class TestCycleScalars:
    def test_generate_time_is_iso_utc(self, macos):
        # <generate-time>07/25/2026 17:07:44</generate-time>, local time +02:00.
        assert macos["cycles"][0]["generate_time"] == "2026-07-25T15:07:44+00:00"
        assert macos["cycles"][1]["generate_time"] == "2026-07-25T14:07:45+00:00"

    def test_windows_generate_time_is_iso_utc(self, windows):
        assert windows["cycles"][0]["generate_time"] == "2026-07-23T12:28:19+00:00"

    def test_duration_comes_from_the_hip_creation_done_line(self, macos, windows):
        assert macos["cycles"][0]["duration_s"] == 7.0
        assert windows["cycles"][0]["duration_s"] == 8.0

    def test_category_timings(self, macos):
        assert macos["cycles"][0]["category_timings"] == {
            "host-info": 0,
            "anti-malware": 1,
            "disk-backup": 0,
            "disk-encryption": 0,
            "firewall": 0,
            "data-loss-prevention": 0,
            "patch-management": 0,
            "All": 1,
        }
        assert macos["cycles"][1]["category_timings"]["All"] == 2

    def test_dispatch(self, macos):
        assert macos["cycles"][0]["dispatch"] == {"sent": True, "succeeded": True, "status_code": 0}

    def test_policy_is_parsed_from_the_cycle_boundary_line(self, macos):
        policy = macos["cycles"][0]["policy"]
        assert policy["collection_hip_data"] is True
        assert policy["max_wait_time"] == 20
        assert "anti-malware" in policy["default_categories"]

    def test_report_host_info(self, macos):
        host_info = macos["cycles"][0]["report"]["host_info"]
        assert host_info["os"] == "Apple Mac OS X 15.7.7"
        assert host_info["host_id_kind"] == "mac-address"


# ── generate_time offset resolution ─────────────────────────────────────────


class TestGenerateTimeOffset:
    """<generate-time>07/25/2026 17:07:44</generate-time> is the endpoint's
    local wall clock. build_hip_data resolves it to UTC either from an
    explicit tz_offset (authoritative) or, absent that, a same-cycle
    quarter-hour-snap fallback -- see cycle_scalars.generate_time()."""

    def test_explicit_tz_offset_is_applied_directly(self):
        data = build_hip_data(macos_logs(), hip_status_state(), "macos", tz_offset="+0200")
        assert data["cycles"][0]["generate_time"] == "2026-07-25T15:07:44+00:00"
        assert data["cycles"][1]["generate_time"] == "2026-07-25T14:07:45+00:00"

    def test_without_tz_offset_falls_back_to_the_quarter_hour_snap(self, macos):
        # macos() is built with the default 3-arg call (no tz_offset), so this
        # is the fallback path -- and it agrees with the explicit-offset
        # result above because the real gap here is only ~2.7s, well inside
        # the snap tolerance.
        assert macos["cycles"][0]["generate_time"] == "2026-07-25T15:07:44+00:00"

    def test_fallback_can_be_fooled_by_a_delayed_anchor_but_tz_offset_is_not(self, macos):
        """The fallback infers the offset from the gap between generate-time
        and the log entry that carried the XML. A gateway-triggered
        GetHipReport that re-emits a *cached* report would widen that gap --
        e.g. by an hour -- and the snap would silently lock onto the wrong
        quarter hour. Demonstrated directly against generate_time() using the
        real raw_xml from the macOS fixture (cycle 0) with a synthetic anchor
        standing in for that delayed re-send; the anchor delay is the only
        non-fixture value here, not the HIP content itself.
        """
        raw_xml = macos["_raw"]["0"]["raw_xml"]
        real_anchor = 1784992066.668  # the actual </hip-report> entry's timestamp
        cached_anchor = real_anchor + 3600  # pretend it was replayed an hour later

        assert generate_time(raw_xml, {"timestamp": real_anchor}) == "2026-07-25T15:07:44+00:00"
        assert generate_time(raw_xml, {"timestamp": cached_anchor}) != "2026-07-25T15:07:44+00:00"
        assert generate_time(raw_xml, {"timestamp": cached_anchor}, tz_offset="+0200") == "2026-07-25T15:07:44+00:00"


# ── Patch merging ────────────────────────────────────────────────────────────


class TestPatchMerging:
    def test_patches_merged_into_both_macos_cycles(self, macos):
        for cycle in macos["cycles"]:
            category = _category(cycle, "patch-management")
            assert category["patches_source"] == "PAComplianceMp"
            assert [p["title"] for p in category["missing_patches"]] == [
                "Safari26.5.2SequoiaAuto-26.5.2",
                "macOS Tahoe 26.5.2-25F84",
            ]
            assert [p["reboot_required"] for p in category["missing_patches"]] == [False, True]

    def test_windows_cycle_has_no_patches_and_no_source(self, windows):
        category = _category(windows["cycles"][0], "patch-management")
        assert category["missing_patches"] == []
        assert category["patches_source"] is None

    def test_other_categories_carry_no_patches(self, macos):
        category = _category(macos["cycles"][0], "anti-malware")
        assert category["missing_patches"] == []
        assert category["patches_source"] is None


# ── OPSWAT error attachment ──────────────────────────────────────────────────


class TestOpswatErrors:
    def test_flat_cycle_wide_error_list_spans_both_sources(self, macos):
        errors = macos["cycles"][0]["opswat_errors"]
        assert [e["source"] for e in errors] == ["PACompliance"] * 4 + ["PAComplianceMp"] * 2

    def test_errors_are_attached_to_the_product_that_owns_the_signature(self, macos):
        cycle = macos["cycles"][0]
        gatekeeper = _product(cycle, "anti-malware", "Gatekeeper")
        assert gatekeeper["signature"] == 100141
        assert [(e["code"], e["method"]) for e in gatekeeper["errors"]] == [(-11, 1001), (-11, 1004)]

        xprotect = _product(cycle, "anti-malware", "Xprotect")
        assert [(e["code"], e["method"]) for e in xprotect["errors"]] == [(-12, 1004)]

        assert _product(cycle, "anti-malware", "Cortex XDR")["errors"] == []
        assert [e["method"] for e in _product(cycle, "disk-backup", "Time Machine")["errors"]] == [1008]

    def test_signature_less_errors_stay_flat_only(self, macos):
        cycle = macos["cycles"][0]
        assert all(e["signature"] is None for e in cycle["opswat_errors"] if e["source"] == "PAComplianceMp")
        attached = [e for c in cycle["report"]["categories"] for p in c["products"] for e in p["errors"]]
        assert all(e["source"] == "PACompliance" for e in attached)

    def test_windows_errors_attach_to_patch_management_products(self, windows):
        cycle = windows["cycles"][0]
        assert [e["method"] for e in _product(cycle, "patch-management", "Dell Command | Update")["errors"]] == [1012]
        assert _product(cycle, "patch-management", "Windows Update Agent")["errors"] == []


# ── Counts ───────────────────────────────────────────────────────────────────


class TestCounts:
    def test_macos_counts(self, macos):
        assert macos["cycles"][0]["counts"] == {
            "warn": 2,
            "unknown": 3,
            "errors": 6,
            "missing_patches": 2,
        }

    def test_windows_counts(self, windows):
        assert windows["cycles"][0]["counts"] == {
            "warn": 0,
            "unknown": 5,
            "errors": 2,
            "missing_patches": 0,
        }


# ── Status heuristics ────────────────────────────────────────────────────────


class TestProductStatus:
    def test_good_key_attribute_with_no_error_is_ok(self, macos):
        product = _product(macos["cycles"][0], "anti-malware", "Cortex XDR")
        assert product_status(product) == (
            "ok",
            "real-time-protection is yes and no OPSWAT error covers it.",
        )
        assert (product["status"], product["status_reason"]) == product_status(product)

    def test_bad_key_attribute_with_no_covering_error_is_warn(self, macos):
        """Xprotect's only error is method 1004 (last full scan time), which
        does not cover real-time-protection — so real-time-protection=no is
        taken at face value."""
        product = _product(macos["cycles"][0], "anti-malware", "Xprotect")
        assert product_status(product) == (
            "warn",
            "real-time-protection is no and no OPSWAT error explains it.",
        )

    def test_covering_error_makes_the_value_untrustworthy(self, macos):
        product = _product(macos["cycles"][0], "anti-malware", "Gatekeeper")
        assert product_status(product) == (
            "unknown",
            "OPSWAT method 1001 failed with error -11, so real-time-protection could not be queried.",
        )

    def test_product_with_no_judgeable_attribute_reports_its_error(self, macos):
        product = _product(macos["cycles"][0], "disk-backup", "Time Machine")
        assert product_status(product) == (
            "unknown",
            "OPSWAT method 1008 failed with error -28, so last-backup-time could not be queried.",
        )

    def test_product_with_no_judgeable_attribute_and_no_error(self, macos):
        product = _product(macos["cycles"][0], "disk-backup", "Google Drive")
        assert product_status(product) == (
            "unknown",
            "This product reports no attribute whose value can be judged.",
        )

    def test_fully_encrypted_drives_are_ok(self, macos):
        product = _product(macos["cycles"][0], "disk-encryption", "FileVault")
        assert product_status(product) == ("ok", "All 3 drives report enc-state encrypted.")

    def test_unjudgeable_value_is_unknown(self, windows):
        product = _product(windows["cycles"][0], "patch-management", "Dell Command | Update")
        assert product_status(product) == (
            "unknown",
            "is-enabled is n/a, which is neither yes nor no.",
        )

    def test_is_enabled_no_is_warn(self, macos):
        product = _product(macos["cycles"][0], "patch-management", "Microsoft AutoUpdate")
        assert product_status(product) == (
            "warn",
            "is-enabled is no and no OPSWAT error explains it.",
        )


class TestCategoryStatus:
    def test_category_takes_the_worst_product_status(self, macos):
        # anti-malware: Xprotect is warn, Gatekeeper is unknown (its method
        # 1001 error covers real-time-protection), Cortex XDR is ok. The
        # reason names both the worst finding and the second-worst one --
        # Gatekeeper's unknown must not go invisible behind Xprotect's warn.
        cycle = macos["cycles"][0]
        anti_malware = _category(cycle, "anti-malware")
        expected = ("warn", "1 of 3 products reports a bad value. 1 more could not be queried.")
        assert category_status(anti_malware["products"]) == expected
        assert (anti_malware["status"], anti_malware["status_reason"]) == expected

    def test_all_good_category_is_ok(self, macos):
        firewall = _category(macos["cycles"][0], "firewall")
        assert category_status(firewall["products"]) == ("ok", "All 2 products report a good value.")

    def test_singular_product_grammar(self, macos):
        disk_encryption = _category(macos["cycles"][0], "disk-encryption")
        assert category_status(disk_encryption["products"]) == ("ok", "All 1 product reports a good value.")

    def test_unqueryable_category_is_unknown(self, macos):
        disk_backup = _category(macos["cycles"][0], "disk-backup")
        assert category_status(disk_backup["products"]) == ("unknown", "2 of 2 products could not be queried.")

    def test_category_with_no_products_is_not_detected(self, macos):
        certificate = _category(macos["cycles"][0], "certificate")
        assert certificate["products"] == []
        assert category_status([]) == ("not-detected", "No products were detected in this category.")
        assert certificate["status"] == "not-detected"
