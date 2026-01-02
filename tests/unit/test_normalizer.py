"""Unit tests for normalizer service."""

import pandas as pd
import pytest

from src.services.normalizer import (
    normalize_dataframe,
    normalize_name,
    normalize_sku,
)


class TestNormalizeSku:
    """Tests for normalize_sku() function."""

    def test_standard_format_unchanged(self) -> None:
        """SKU in standard format should be unchanged."""
        assert normalize_sku("SKU-001") == "SKU-001"
        assert normalize_sku("SKU-123") == "SKU-123"

    def test_missing_hyphen_inserted(self) -> None:
        """SKU without hyphen should have hyphen inserted."""
        assert normalize_sku("SKU001") == "SKU-001"
        assert normalize_sku("SKU123") == "SKU-123"

    def test_lowercase_uppercased(self) -> None:
        """Lowercase SKU should be uppercased."""
        assert normalize_sku("sku-001") == "SKU-001"
        assert normalize_sku("sku-123") == "SKU-123"

    def test_lowercase_missing_hyphen(self) -> None:
        """Lowercase SKU without hyphen should be normalized."""
        assert normalize_sku("sku001") == "SKU-001"
        assert normalize_sku("sku123") == "SKU-123"

    def test_whitespace_stripped(self) -> None:
        """Whitespace should be stripped from SKU."""
        assert normalize_sku(" SKU-001 ") == "SKU-001"
        assert normalize_sku("  SKU001  ") == "SKU-001"

    def test_empty_string_returns_empty(self) -> None:
        """Empty string should return empty string."""
        assert normalize_sku("") == ""

    def test_nan_returns_empty(self) -> None:
        """NaN/None should return empty string."""
        assert normalize_sku(None) == ""
        assert normalize_sku(float("nan")) == ""


class TestNormalizeName:
    """Tests for normalize_name() function."""

    def test_clean_name_unchanged(self) -> None:
        """Clean name should be unchanged."""
        assert normalize_name("Widget A") == "Widget A"

    def test_leading_whitespace_trimmed(self) -> None:
        """Leading whitespace should be trimmed."""
        assert normalize_name("  Widget A") == "Widget A"

    def test_trailing_whitespace_trimmed(self) -> None:
        """Trailing whitespace should be trimmed."""
        assert normalize_name("Widget A  ") == "Widget A"

    def test_both_ends_trimmed(self) -> None:
        """Whitespace on both ends should be trimmed."""
        assert normalize_name("  Widget A  ") == "Widget A"

    def test_internal_whitespace_preserved(self) -> None:
        """Internal whitespace should be preserved."""
        assert normalize_name("Widget  A") == "Widget  A"
        assert normalize_name("Gadget Pro Max") == "Gadget Pro Max"

    def test_empty_string_returns_empty(self) -> None:
        """Empty string should return empty string."""
        assert normalize_name("") == ""

    def test_nan_returns_empty(self) -> None:
        """NaN/None should return empty string."""
        assert normalize_name(None) == ""
        assert normalize_name(float("nan")) == ""


class TestNormalizeDataframe:
    """Tests for normalize_dataframe() function."""

    def test_clean_dataframe_unchanged(self) -> None:
        """Clean DataFrame should have minimal normalizations."""
        df = pd.DataFrame({
            "sku": ["SKU-001", "SKU-002"],
            "name": ["Widget A", "Widget B"],
            "quantity": [100, 50],
            "location": ["Warehouse A", "Warehouse B"],
            "last_counted": ["2024-01-08", "2024-01-08"],
        })
        result, normalizations = normalize_dataframe(df)

        assert list(result["sku"]) == ["SKU-001", "SKU-002"]
        assert list(result["name"]) == ["Widget A", "Widget B"]
        assert len(normalizations["sku_normalized"]) == 0
        assert len(normalizations["name_trimmed"]) == 0

    def test_sku_normalization_tracked(self) -> None:
        """SKU normalizations should be tracked."""
        df = pd.DataFrame({
            "sku": ["SKU001", "sku-002", "SKU-003"],
            "name": ["A", "B", "C"],
            "quantity": [1, 2, 3],
            "location": ["W", "W", "W"],
            "last_counted": ["2024-01-01", "2024-01-01", "2024-01-01"],
        })
        result, normalizations = normalize_dataframe(df)

        assert result["sku"].tolist() == ["SKU-001", "SKU-002", "SKU-003"]
        # SKU001 -> SKU-001 (index 0), sku-002 -> SKU-002 (index 1)
        assert 0 in normalizations["sku_normalized"]
        assert 1 in normalizations["sku_normalized"]

    def test_name_trimming_tracked(self) -> None:
        """Name trimming should be tracked."""
        df = pd.DataFrame({
            "sku": ["SKU-001", "SKU-002"],
            "name": [" Widget A ", "Widget B"],
            "quantity": [100, 50],
            "location": ["W", "W"],
            "last_counted": ["2024-01-01", "2024-01-01"],
        })
        result, normalizations = normalize_dataframe(df)

        assert result["name"].tolist() == ["Widget A", "Widget B"]
        assert 0 in normalizations["name_trimmed"]
        assert 1 not in normalizations["name_trimmed"]

    def test_quantity_coercion(self) -> None:
        """Quantity should be coerced to int."""
        df = pd.DataFrame({
            "sku": ["SKU-001", "SKU-002"],
            "name": ["A", "B"],
            "quantity": [100.0, 50.5],  # Floats
            "location": ["W", "W"],
            "last_counted": ["2024-01-01", "2024-01-01"],
        })
        result, _ = normalize_dataframe(df)

        assert result["quantity"].dtype == int
        assert result["quantity"].tolist() == [100, 50]

    def test_location_trimming_tracked(self) -> None:
        """Location trimming should be tracked."""
        df = pd.DataFrame({
            "sku": ["SKU-001"],
            "name": ["A"],
            "quantity": [100],
            "location": [" Warehouse A "],
            "last_counted": ["2024-01-01"],
        })
        result, normalizations = normalize_dataframe(df)

        assert result["location"].tolist() == ["Warehouse A"]
        assert 0 in normalizations["location_trimmed"]

    def test_original_dataframe_unchanged(self) -> None:
        """Original DataFrame should not be modified."""
        df = pd.DataFrame({
            "sku": ["SKU001"],
            "name": [" Widget "],
            "quantity": [100],
            "location": ["W"],
            "last_counted": ["2024-01-01"],
        })
        original_sku = df["sku"].tolist()
        original_name = df["name"].tolist()

        normalize_dataframe(df)

        assert df["sku"].tolist() == original_sku
        assert df["name"].tolist() == original_name
