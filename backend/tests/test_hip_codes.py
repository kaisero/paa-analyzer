"""Unit tests for paa_analyzer.hip.codes — the OESIS code catalog."""

import pytest

from paa_analyzer.hip import codes


class TestErrorExplanation:
    """error_explanation: OESIS error codes observed in the HIP fixtures."""

    @pytest.mark.parametrize(
        "code",
        [-11, -12, -28],
        ids=["not-supported", "not-implemented", "object-not-found"],
    )
    def test_known_codes_return_a_non_empty_string(self, code):
        explanation = codes.error_explanation(code)
        assert isinstance(explanation, str)
        assert explanation

    def test_minus_11_means_not_supported(self):
        explanation = codes.error_explanation(-11)
        assert explanation is not None
        assert "not support" in explanation.lower()

    def test_minus_12_means_not_implemented(self):
        explanation = codes.error_explanation(-12)
        assert explanation is not None
        assert "not implement" in explanation.lower()

    def test_minus_28_means_object_not_found(self):
        explanation = codes.error_explanation(-28)
        assert explanation is not None
        assert "not found" in explanation.lower()

    def test_unknown_code_returns_none(self):
        assert codes.error_explanation(-999) is None

    def test_never_raises_on_unexpected_input(self):
        assert codes.error_explanation(0) is None


class TestMethodQuery:
    """method_query: OESIS method ids observed in the HIP fixtures.

    Grounded in the fixtures' Category/Method pairing (see fixtures'
    ``Category: N, Method: M`` OPSWAT error lines and codes.py's comment):
    ``Category: 5, Method: 1001``, ``Category: 5, Method: 1004``,
    ``Category: 2, Method: 1008``, ``Category: 12, Method: 1013``.
    """

    @pytest.mark.parametrize("method_id", [1001, 1004, 1008, 1013])
    def test_known_methods_return_a_non_empty_string(self, method_id):
        description = codes.method_query(method_id)
        assert isinstance(description, str)
        assert description

    @pytest.mark.parametrize("method_id", [1001, 1004])
    def test_category_5_methods_mention_antivirus(self, method_id):
        """Category: 5, Method: 1001 / 1004 -- CollectComplianceDataForAV."""
        description = codes.method_query(method_id)
        assert description is not None
        assert "antivirus" in description.lower()

    def test_method_1008_mentions_backup(self):
        """Category: 2, Method: 1008 -- CollectComplianceDataForDLP."""
        description = codes.method_query(1008)
        assert description is not None
        assert "backup" in description.lower()

    def test_method_1013_mentions_patch(self):
        """Category: 12, Method: 1013 -- GetMissingPatchesForThisProduct."""
        description = codes.method_query(1013)
        assert description is not None
        assert "patch" in description.lower()

    def test_unknown_method_returns_none(self):
        assert codes.method_query(9999) is None


class TestCategoryName:
    """category_name: OPSWAT category id -> HIP category name."""

    @pytest.mark.parametrize(
        "category_id,expected",
        [
            (2, "disk-backup"),
            (5, "anti-malware"),
            (12, "patch-management"),
        ],
    )
    def test_known_categories(self, category_id, expected):
        assert codes.category_name(category_id) == expected

    def test_unknown_category_returns_none(self):
        assert codes.category_name(-1) is None
        assert codes.category_name(100) is None
