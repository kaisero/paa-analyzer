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
        assert "not support" in codes.error_explanation(-11).lower()

    def test_minus_12_means_not_implemented(self):
        assert "not implement" in codes.error_explanation(-12).lower()

    def test_minus_28_means_object_not_found(self):
        assert "not found" in codes.error_explanation(-28).lower()

    def test_unknown_code_returns_none(self):
        assert codes.error_explanation(-999) is None

    def test_never_raises_on_unexpected_input(self):
        assert codes.error_explanation(0) is None


class TestMethodQuery:
    """method_query: OESIS method ids observed in the HIP fixtures."""

    @pytest.mark.parametrize("method_id", [1001, 1004, 1008, 1013])
    def test_known_methods_return_a_non_empty_string(self, method_id):
        description = codes.method_query(method_id)
        assert isinstance(description, str)
        assert description

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
