"""Unit tests for paa_analyzer.hip.cycles — cycle segmentation and pairing.

Driven off the redacted real fixtures in backend/tests/fixtures/hip/, not
hand-authored log lines (see .superpowers/sdd/global-constraints.md).
"""

from pathlib import Path

import pytest

from paa_analyzer.hip.cycles import pair_cycles, split_cycles
from paa_analyzer.parsers import structured_log

FIXTURES = Path(__file__).parent / "fixtures" / "hip"


def _entries(name: str) -> list[dict]:
    return structured_log((FIXTURES / name).read_text())


# ── split_cycles ─────────────────────────────────────────────────────────────


class TestSplitCycles:
    """Each macOS fixture file is exactly one hip-policy-to-hip-policy cycle."""

    @pytest.mark.parametrize(
        "filename,expected_start_ts",
        [
            ("PACompliance.log", 1784992063.64),
            ("PACompliance.1.log", 1784988463.507),
            ("PAComplianceMp.log", 1784992063.64),
            ("PAComplianceMp.1.log", 1784988463.507),
            ("PACompliance_win.log", 1784809698.748),
        ],
    )
    def test_one_cycle_per_fixture_with_correct_start_ts(self, filename, expected_start_ts):
        entries = _entries(filename)
        cycles = split_cycles(entries)
        assert len(cycles) == 1
        cycle = cycles[0]
        assert cycle["start_ts"] == pytest.approx(expected_start_ts, abs=1e-3)
        assert cycle["partial"] is False
        assert cycle["entries"] == entries

    def test_cycle_entries_all_start_with_policy_line_first(self):
        entries = _entries("PACompliance.log")
        cycles = split_cycles(entries)
        assert cycles[0]["entries"][0]["message"].startswith("Try to parse hip policy")

    def test_empty_entries_returns_no_cycles(self):
        assert split_cycles([]) == []

    def test_truncated_leading_cycle_is_marked_partial(self):
        """Slice off a fixture's own leading policy line to build a real
        "entries before the first policy line" case, per the brief's
        instruction not to hand-author new HIP log lines."""
        entries = _entries("PACompliance.log")
        # Drop the very first entry (the "Try to parse hip policy" line) so
        # the remaining leading entries have no policy-line boundary yet.
        truncated = entries[1:5]
        cycles = split_cycles(truncated)
        assert len(cycles) == 1
        assert cycles[0]["partial"] is True
        assert cycles[0]["entries"] == truncated
        assert cycles[0]["start_ts"] == truncated[0]["timestamp"]

    def test_two_fixtures_concatenated_yield_two_cycles(self):
        """Concatenating two real cycles (as the collapsed multi-rotation
        entry stream would) must split back into exactly those two cycles."""
        newest = _entries("PACompliance.log")
        preceding = _entries("PACompliance.1.log")
        combined = sorted(preceding + newest, key=lambda e: e["timestamp"])
        cycles = split_cycles(combined)
        assert len(cycles) == 2
        assert cycles[0]["start_ts"] == pytest.approx(1784988463.507, abs=1e-3)
        assert cycles[1]["start_ts"] == pytest.approx(1784992063.64, abs=1e-3)
        assert not cycles[0]["partial"]
        assert not cycles[1]["partial"]


# ── pair_cycles ──────────────────────────────────────────────────────────────


class TestPairCycles:
    """Pairing compliance cycles with their matching Mp cycle by start_ts."""

    def test_exact_pairing_across_the_two_real_sources(self):
        compliance_cycles = [
            split_cycles(_entries("PACompliance.1.log"))[0],
            split_cycles(_entries("PACompliance.log"))[0],
        ]
        mp_cycles = [
            split_cycles(_entries("PAComplianceMp.1.log"))[0],
            split_cycles(_entries("PAComplianceMp.log"))[0],
        ]
        pairs, unpaired_mp = pair_cycles(compliance_cycles, mp_cycles)
        assert unpaired_mp == []
        assert len(pairs) == 2
        for compliance_cycle, mp_cycle in pairs:
            assert mp_cycle is not None
            assert mp_cycle["start_ts"] == pytest.approx(compliance_cycle["start_ts"], abs=1e-3)

    def test_compliance_cycle_with_no_matching_mp_cycle_is_none(self):
        compliance_cycles = [split_cycles(_entries("PACompliance_win.log"))[0]]
        mp_cycles = [split_cycles(_entries("PAComplianceMp.log"))[0]]
        pairs, unpaired_mp = pair_cycles(compliance_cycles, mp_cycles)
        assert pairs == [(compliance_cycles[0], None)]
        assert unpaired_mp == mp_cycles

    def test_unpaired_mp_cycle_is_reported_not_dropped_silently(self):
        compliance_cycles = [split_cycles(_entries("PACompliance.log"))[0]]
        # Two Mp cycles, but only one compliance cycle to claim one of them.
        mp_cycles = [
            split_cycles(_entries("PAComplianceMp.log"))[0],
            split_cycles(_entries("PAComplianceMp.1.log"))[0],
        ]
        pairs, unpaired_mp = pair_cycles(compliance_cycles, mp_cycles)
        assert len(pairs) == 1
        assert pairs[0][1] is mp_cycles[0]
        assert unpaired_mp == [mp_cycles[1]]

    def test_tolerance_boundary_is_inclusive(self):
        base = {"start_ts": 1000.0, "entries": [], "partial": False}
        mp_within = {"start_ts": 1005.0, "entries": [], "partial": False}
        pairs, unpaired_mp = pair_cycles([base], [mp_within], tolerance_s=5.0)
        assert pairs == [(base, mp_within)]
        assert unpaired_mp == []

    def test_just_outside_tolerance_is_unpaired(self):
        base = {"start_ts": 1000.0, "entries": [], "partial": False}
        mp_outside = {"start_ts": 1005.001, "entries": [], "partial": False}
        pairs, unpaired_mp = pair_cycles([base], [mp_outside], tolerance_s=5.0)
        assert pairs == [(base, None)]
        assert unpaired_mp == [mp_outside]

    def test_each_compliance_cycle_takes_at_most_one_mp_cycle(self):
        """mp is strictly closer to c1 (delta 0.3) than to c2 (delta 1.2), so
        c1 must claim it -- not just "some cycle claims it" (that would pass
        for any implementation, including a buggy one that always picks the
        last candidate)."""
        c1 = {"start_ts": 1000.0, "entries": [], "partial": False}
        c2 = {"start_ts": 1001.5, "entries": [], "partial": False}
        mp = {"start_ts": 1000.3, "entries": [], "partial": False}
        pairs, unpaired_mp = pair_cycles([c1, c2], [mp], tolerance_s=5.0)
        assert pairs[0][1] is mp
        assert pairs[1][1] is None
        assert unpaired_mp == []

    def test_no_compliance_cycles_reports_all_mp_as_unpaired(self):
        mp_cycles = [split_cycles(_entries("PAComplianceMp.log"))[0]]
        pairs, unpaired_mp = pair_cycles([], mp_cycles)
        assert pairs == []
        assert unpaired_mp == mp_cycles
