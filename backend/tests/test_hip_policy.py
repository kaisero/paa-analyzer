"""Unit tests for paa_analyzer.hip.policy -- the "Try to parse hip policy"
JSON blob.

Driven off the redacted real fixtures in backend/tests/fixtures/hip/, not
hand-authored log lines (see .superpowers/sdd/global-constraints.md).
"""

import json
from pathlib import Path
from typing import Any

from paa_analyzer.hip.policy import parse_policy
from paa_analyzer.parsers import structured_log

FIXTURES = Path(__file__).parent / "fixtures" / "hip"


def _entries(name: str) -> list[dict[str, Any]]:
    return structured_log((FIXTURES / name).read_text())


# The default_categories list is identical across both platforms' fixtures.
_EXPECTED_DEFAULT_CATEGORIES = [
    "host-info",
    "data-loss-prevention",
    "patch-management",
    "firewall",
    "anti-malware",
    "disk-backup",
    "disk-encryption",
]


class TestParsePolicyMac:
    """PACompliance.log's policy line -- a jamf plist custom_check."""

    def test_top_level_fields(self):
        message = _entries("PACompliance.log")[0]["message"]
        policy = parse_policy(message)
        assert policy is not None
        assert policy["collection_hip_data"] is True
        assert policy["max_wait_time"] == 20
        assert policy["certs"] == []
        assert policy["exclusion_categories"] == []
        assert policy["default_categories"] == _EXPECTED_DEFAULT_CATEGORIES

    def test_custom_check_mac_os_plist_block(self):
        message = _entries("PACompliance.log")[0]["message"]
        policy = parse_policy(message)
        assert policy is not None
        mac_os = policy["custom_check"]["mac_os"]
        assert mac_os["plist"] == [{"name": "com.jamfsoftware.jamf", "member": ["jss_url"]}]
        assert mac_os["process_list"] == []

    def test_custom_check_windows_registry_key_block(self):
        """The policy JSON carries both platforms' custom_check blocks
        regardless of which OS produced this log -- the mac bundle's policy
        still has a populated windows.registry_key entry."""
        message = _entries("PACompliance.log")[0]["message"]
        policy = parse_policy(message)
        assert policy is not None
        windows = policy["custom_check"]["windows"]
        assert windows["registry_key"] == [
            {
                "name": (
                    "HKEY_LOCAL_MACHINE\\SYSTEM\\CurrentControlSet\\Control\\"
                    "CloudDomainJoin\\TenantInfo\\00000000-0000-0000-0000-000000000001"
                ),
                "member": ["DisplayName"],
            }
        ]
        assert windows["process_list"] == []

    def test_raw_is_the_full_decoded_object(self):
        message = _entries("PACompliance.log")[0]["message"]
        policy = parse_policy(message)
        assert policy is not None
        expected_raw = json.loads(message[len("Try to parse hip policy: ") :])
        assert policy["raw"] == expected_raw


class TestParsePolicyWindows:
    """PACompliance_win.log's policy line -- an empty custom_check (no
    registry_key/plist entries configured on that bundle)."""

    def test_top_level_fields(self):
        message = _entries("PACompliance_win.log")[0]["message"]
        policy = parse_policy(message)
        assert policy is not None
        assert policy["collection_hip_data"] is True
        assert policy["max_wait_time"] == 20
        assert policy["default_categories"] == _EXPECTED_DEFAULT_CATEGORIES
        assert policy["exclusion_categories"] == []
        assert policy["certs"] == []

    def test_custom_check_is_present_but_empty(self):
        message = _entries("PACompliance_win.log")[0]["message"]
        policy = parse_policy(message)
        assert policy is not None
        assert policy["custom_check"] == {
            "windows": {"registry_key": [], "process_list": []},
            "mac_os": {"plist": [], "process_list": []},
        }


class TestParsePolicyErrorHandling:
    """Missing prefix / malformed JSON must yield None, never raise."""

    def test_message_without_policy_prefix_returns_none(self):
        # A real, unrelated line from the same fixture -- not hand-authored.
        message = _entries("PACompliance.log")[1]["message"]
        assert message == "HIP policy parsing is completed"
        assert parse_policy(message) is None

    def test_truncated_json_returns_none(self):
        """Slice a real policy line's JSON short (mirrors the technique used
        in test_hip_cycles.py for a truncated leading cycle) rather than
        hand-authoring a malformed blob."""
        message = _entries("PACompliance.log")[0]["message"]
        truncated = message[: len(message) - 5]
        assert parse_policy(truncated) is None

    def test_empty_string_returns_none(self):
        assert parse_policy("") is None
