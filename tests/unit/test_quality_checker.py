"""Unit tests for quality checker service."""

import pandas as pd
import pytest


class TestCheckDuplicates:
    """Tests for check_duplicates() function."""

    def test_no_duplicates_returns_empty(self) -> None:
        """No duplicates should return empty list."""
        from src.services.quality_checker import check_duplicates

        df = pd.DataFrame({
            "sku": ["SKU-001", "SKU-002"],
            "location": ["Warehouse A", "Warehouse B"],
            "quantity": [100, 50],
        })
        issues = check_duplicates(df, "snapshot_1")
        assert len(issues) == 0

    def test_duplicate_key_returns_error(self) -> None:
        """Duplicate composite key should return error issues."""
        from src.services.quality_checker import check_duplicates

        df = pd.DataFrame({
            "sku": ["SKU-001", "SKU-001", "SKU-002"],
            "location": ["Warehouse A", "Warehouse A", "Warehouse B"],
            "quantity": [100, 150, 50],
        })
        issues = check_duplicates(df, "snapshot_1")

        assert len(issues) == 2  # Both duplicate rows
        assert all(i.issue_type == "duplicate_key" for i in issues)
        assert all(i.severity == "error" for i in issues)
        assert all(i.source_file == "snapshot_1" for i in issues)

    def test_same_sku_different_location_not_duplicate(self) -> None:
        """Same SKU in different locations is not a duplicate."""
        from src.services.quality_checker import check_duplicates

        df = pd.DataFrame({
            "sku": ["SKU-001", "SKU-001"],
            "location": ["Warehouse A", "Warehouse B"],
            "quantity": [100, 150],
        })
        issues = check_duplicates(df, "snapshot_1")
        assert len(issues) == 0


class TestCheckNegativeQuantities:
    """Tests for check_negative_quantities() function."""

    def test_positive_quantities_returns_empty(self) -> None:
        """All positive quantities should return empty list."""
        from src.services.quality_checker import check_negative_quantities

        df = pd.DataFrame({
            "sku": ["SKU-001", "SKU-002"],
            "quantity": [100, 50],
        })
        issues = check_negative_quantities(df, "snapshot_1")
        assert len(issues) == 0

    def test_negative_quantity_returns_error(self) -> None:
        """Negative quantity should return error issue."""
        from src.services.quality_checker import check_negative_quantities

        df = pd.DataFrame({
            "sku": ["SKU-001", "SKU-002", "SKU-003"],
            "quantity": [100, -5, 50],
        })
        issues = check_negative_quantities(df, "snapshot_1")

        assert len(issues) == 1
        assert issues[0].issue_type == "negative_quantity"
        assert issues[0].severity == "error"
        assert issues[0].row_number == 2  # 1-indexed, row with SKU-002
        assert issues[0].original_value == "-5"

    def test_zero_quantity_is_valid(self) -> None:
        """Zero quantity should not be flagged."""
        from src.services.quality_checker import check_negative_quantities

        df = pd.DataFrame({
            "sku": ["SKU-001"],
            "quantity": [0],
        })
        issues = check_negative_quantities(df, "snapshot_1")
        assert len(issues) == 0


class TestCheckQuantityFormat:
    """Tests for check_quantity_format() function."""

    def test_integer_quantities_returns_empty(self) -> None:
        """Integer quantities should return empty list (no float rows detected)."""
        from src.services.quality_checker import check_quantity_format

        df = pd.DataFrame({
            "sku": ["SKU-001", "SKU-002"],
            "quantity": [100, 50],
        })
        # No rows had float format in original CSV
        issues = check_quantity_format(df, "snapshot_1", float_qty_rows={})
        assert len(issues) == 0

    def test_float_whole_number_returns_warning(self) -> None:
        """Float quantities like 70.0 should return warning when detected in CSV."""
        from src.services.quality_checker import check_quantity_format

        df = pd.DataFrame({
            "sku": ["SKU-001", "SKU-002"],
            "quantity": [70.0, 50.0],  # pandas converts all to float
        })
        # Only row 0 had float format in original CSV (e.g., "70.0")
        issues = check_quantity_format(df, "snapshot_1", float_qty_rows={0: "70.0"})

        assert len(issues) == 1
        assert issues[0].issue_type == "quantity_coerced"
        assert issues[0].severity == "warning"
        assert issues[0].row_number == 1
        assert issues[0].original_value == "70.0"
        assert issues[0].normalized_value == "70"
        assert "SKU-001" in issues[0].description

    def test_preserves_original_string_format(self) -> None:
        """Original string format like 77.00 should be preserved in report."""
        from src.services.quality_checker import check_quantity_format

        df = pd.DataFrame({
            "sku": ["SKU-001"],
            "quantity": [77.0],  # pandas converts 77.00 to 77.0
        })
        # Original CSV had "77.00" with two decimal places
        issues = check_quantity_format(df, "snapshot_1", float_qty_rows={0: "77.00"})

        assert len(issues) == 1
        assert issues[0].original_value == "77.00"  # Preserved!
        assert issues[0].normalized_value == "77"
        assert "77.00" in issues[0].description

    def test_multiple_float_rows_returns_multiple_warnings(self) -> None:
        """Multiple rows with float format should return multiple warnings."""
        from src.services.quality_checker import check_quantity_format

        df = pd.DataFrame({
            "sku": ["SKU-001", "SKU-002", "SKU-003"],
            "quantity": [70.0, 50.0, 30.0],
        })
        # Rows 0 and 2 had float format in original CSV
        issues = check_quantity_format(df, "snapshot_1", float_qty_rows={0: "70.0", 2: "30.00"})

        assert len(issues) == 2
        assert all(i.issue_type == "quantity_coerced" for i in issues)

    def test_no_float_rows_returns_empty(self) -> None:
        """No warnings when float_qty_rows is empty even if DataFrame has floats."""
        from src.services.quality_checker import check_quantity_format

        df = pd.DataFrame({
            "sku": ["SKU-001"],
            "quantity": [70.0],  # pandas may convert, but CSV had "70"
        })
        # Empty dict means no rows had decimal points in original CSV
        issues = check_quantity_format(df, "snapshot_1", float_qty_rows={})
        assert len(issues) == 0

    def test_missing_quantity_column_returns_empty(self) -> None:
        """Missing quantity column should return empty list."""
        from src.services.quality_checker import check_quantity_format

        df = pd.DataFrame({
            "sku": ["SKU-001"],
        })
        issues = check_quantity_format(df, "snapshot_1", float_qty_rows={0: "70.0"})
        assert len(issues) == 0


class TestCheckSkuFormat:
    """Tests for check_sku_format() function."""

    def test_standard_format_returns_empty(self) -> None:
        """Standard SKU format should return empty list."""
        from src.services.quality_checker import check_sku_format

        df = pd.DataFrame({
            "sku": ["SKU-001", "SKU-002"],
        })
        issues = check_sku_format(df, "snapshot_1")
        assert len(issues) == 0

    def test_missing_hyphen_returns_warning(self) -> None:
        """SKU missing hyphen should return warning."""
        from src.services.quality_checker import check_sku_format

        df = pd.DataFrame({
            "sku": ["SKU001", "SKU-002"],
        })
        issues = check_sku_format(df, "snapshot_1")

        assert len(issues) == 1
        assert issues[0].issue_type == "sku_format_normalized"
        assert issues[0].severity == "warning"
        assert issues[0].original_value == "SKU001"
        assert issues[0].normalized_value == "SKU-001"

    def test_lowercase_returns_warning(self) -> None:
        """Lowercase SKU should return warning."""
        from src.services.quality_checker import check_sku_format

        df = pd.DataFrame({
            "sku": ["sku-001"],
        })
        issues = check_sku_format(df, "snapshot_1")

        assert len(issues) == 1
        assert issues[0].issue_type == "sku_format_normalized"
        assert issues[0].severity == "warning"
        assert issues[0].original_value == "sku-001"
        assert issues[0].normalized_value == "SKU-001"


class TestCheckWhitespace:
    """Tests for check_whitespace() function."""

    def test_clean_text_returns_empty(self) -> None:
        """Clean text fields should return empty list."""
        from src.services.quality_checker import check_whitespace

        df = pd.DataFrame({
            "name": ["Widget A", "Widget B"],
            "location": ["Warehouse A", "Warehouse B"],
        })
        issues = check_whitespace(df, "snapshot_1")
        assert len(issues) == 0

    def test_leading_whitespace_returns_warning(self) -> None:
        """Leading whitespace should return warning."""
        from src.services.quality_checker import check_whitespace

        df = pd.DataFrame({
            "sku": ["SKU-001", "SKU-002"],
            "name": [" Widget A", "Widget B"],
            "location": ["Warehouse A", "Warehouse B"],
        })
        issues = check_whitespace(df, "snapshot_1")

        assert len(issues) == 1
        assert issues[0].issue_type == "whitespace_trimmed"
        assert issues[0].severity == "warning"
        assert issues[0].field == "name"
        assert "SKU-001" in issues[0].description

    def test_trailing_whitespace_returns_warning(self) -> None:
        """Trailing whitespace should return warning."""
        from src.services.quality_checker import check_whitespace

        df = pd.DataFrame({
            "sku": ["SKU-001", "SKU-002"],
            "name": ["Widget A ", "Widget B"],
            "location": ["Warehouse A", "Warehouse B"],
        })
        issues = check_whitespace(df, "snapshot_1")

        assert len(issues) == 1
        assert issues[0].issue_type == "whitespace_trimmed"
        assert "SKU-001" in issues[0].description


class TestCheckDateFormat:
    """Tests for check_date_format() function."""

    def test_iso_format_returns_empty(self) -> None:
        """ISO date format should return empty list."""
        from src.services.quality_checker import check_date_format

        df = pd.DataFrame({
            "last_counted": ["2024-01-08", "2024-01-15"],
        })
        issues = check_date_format(df, "snapshot_1")
        assert len(issues) == 0

    def test_non_iso_format_returns_warning(self) -> None:
        """Non-ISO date format should return warning."""
        from src.services.quality_checker import check_date_format

        df = pd.DataFrame({
            "last_counted": ["01/08/2024", "2024-01-15"],
        })
        issues = check_date_format(df, "snapshot_1")

        assert len(issues) == 1
        assert issues[0].issue_type == "date_format_inconsistent"
        assert issues[0].severity == "warning"
        assert issues[0].original_value == "01/08/2024"


class TestCheckDateRegression:
    """Tests for check_date_regression() function."""

    def test_same_dates_returns_empty(self) -> None:
        """Same dates should return empty list."""
        from src.services.quality_checker import check_date_regression

        df1 = pd.DataFrame({
            "sku": ["SKU-001"],
            "location": ["Warehouse A"],
            "last_counted": ["2024-01-08"],
        })
        df2 = pd.DataFrame({
            "sku": ["SKU-001"],
            "location": ["Warehouse A"],
            "last_counted": ["2024-01-08"],
        })
        issues = check_date_regression(df1, df2)
        assert len(issues) == 0

    def test_newer_date_in_snapshot2_returns_empty(self) -> None:
        """Date in snapshot_2 that is newer should return empty list."""
        from src.services.quality_checker import check_date_regression

        df1 = pd.DataFrame({
            "sku": ["SKU-001"],
            "location": ["Warehouse A"],
            "last_counted": ["2024-01-08"],
        })
        df2 = pd.DataFrame({
            "sku": ["SKU-001"],
            "location": ["Warehouse A"],
            "last_counted": ["2024-01-15"],
        })
        issues = check_date_regression(df1, df2)
        assert len(issues) == 0

    def test_older_date_in_snapshot2_returns_warning(self) -> None:
        """Date in snapshot_2 that is older should return warning."""
        from src.services.quality_checker import check_date_regression

        df1 = pd.DataFrame({
            "sku": ["SKU-001"],
            "location": ["Warehouse A"],
            "last_counted": ["2024-01-15"],
        })
        df2 = pd.DataFrame({
            "sku": ["SKU-001"],
            "location": ["Warehouse A"],
            "last_counted": ["2024-01-08"],
        })
        issues = check_date_regression(df1, df2)

        assert len(issues) == 1
        assert issues[0].issue_type == "date_regression"
        assert issues[0].severity == "warning"
        assert issues[0].source_file == "both"
        assert issues[0].original_value == "2024-01-15"
        assert issues[0].normalized_value == "2024-01-08"

    def test_non_iso_dates_skipped(self) -> None:
        """Non-ISO dates should be skipped (handled by date format check)."""
        from src.services.quality_checker import check_date_regression

        df1 = pd.DataFrame({
            "sku": ["SKU-001"],
            "location": ["Warehouse A"],
            "last_counted": ["01/15/2024"],  # Non-ISO format
        })
        df2 = pd.DataFrame({
            "sku": ["SKU-001"],
            "location": ["Warehouse A"],
            "last_counted": ["2024-01-08"],
        })
        issues = check_date_regression(df1, df2)
        assert len(issues) == 0  # Skipped because old date is not ISO format


class TestCheckColumnNames:
    """Tests for check_column_names() function."""

    def test_canonical_names_returns_empty(self) -> None:
        """Canonical column names should return empty list."""
        from src.services.quality_checker import check_column_names

        mapped_columns: list[str] = []
        issues = check_column_names(mapped_columns, "snapshot_1")
        assert len(issues) == 0

    def test_mapped_names_returns_info(self) -> None:
        """Mapped column names should return info issues."""
        from src.services.quality_checker import check_column_names

        mapped_columns = ["product_name", "qty", "warehouse"]
        issues = check_column_names(mapped_columns, "snapshot_1")

        assert len(issues) == 3
        assert all(i.issue_type == "column_name_mismatch" for i in issues)
        assert all(i.severity == "info" for i in issues)


class TestCheckNameDrift:
    """Tests for check_name_drift() function."""

    def test_same_names_returns_empty(self) -> None:
        """Same names for same SKU should return empty list."""
        from src.services.quality_checker import check_name_drift

        df1 = pd.DataFrame({
            "sku": ["SKU-001"],
            "location": ["Warehouse A"],
            "name": ["Widget A"],
        })
        df2 = pd.DataFrame({
            "sku": ["SKU-001"],
            "location": ["Warehouse A"],
            "name": ["Widget A"],
        })
        issues = check_name_drift(df1, df2)
        assert len(issues) == 0

    def test_different_names_returns_warning(self) -> None:
        """Different names for same SKU should return warning."""
        from src.services.quality_checker import check_name_drift

        df1 = pd.DataFrame({
            "sku": ["SKU-001"],
            "location": ["Warehouse A"],
            "name": ["Widget A"],
        })
        df2 = pd.DataFrame({
            "sku": ["SKU-001"],
            "location": ["Warehouse A"],
            "name": ["Widget A Updated"],
        })
        issues = check_name_drift(df1, df2)

        assert len(issues) == 1
        assert issues[0].issue_type == "name_drift"
        assert issues[0].severity == "warning"
        assert issues[0].source_file == "both"


class TestRunAllChecks:
    """Tests for run_all_checks() function."""

    def test_clean_data_returns_minimal_issues(self) -> None:
        """Clean data should return minimal issues."""
        from src.services.quality_checker import run_all_checks

        df1 = pd.DataFrame({
            "sku": ["SKU-001"],
            "name": ["Widget A"],
            "quantity": [100],
            "location": ["Warehouse A"],
            "last_counted": ["2024-01-08"],
        })
        df2 = pd.DataFrame({
            "sku": ["SKU-001"],
            "name": ["Widget A"],
            "quantity": [100],
            "location": ["Warehouse A"],
            "last_counted": ["2024-01-08"],
        })
        issues = run_all_checks(df1, df2, [], [])

        # Should have no issues for clean data
        assert len(issues) == 0

    def test_data_with_issues_returns_all_issues(self) -> None:
        """Data with quality issues should return all issues."""
        from src.services.quality_checker import run_all_checks

        df1 = pd.DataFrame({
            "sku": ["SKU001", "SKU-002"],  # SKU format issue
            "name": [" Widget A ", "Widget B"],  # Whitespace issue
            "quantity": [100, -5],  # Negative quantity
            "location": ["Warehouse A", "Warehouse B"],
            "last_counted": ["01/08/2024", "2024-01-15"],  # Date format issue
        })
        df2 = pd.DataFrame({
            "sku": ["SKU-001"],
            "name": ["Widget A Updated"],  # Name drift
            "quantity": [100],
            "location": ["Warehouse A"],
            "last_counted": ["2024-01-15"],
        })
        issues = run_all_checks(df1, df2, ["product_name"], [])

        # Should have multiple issues
        assert len(issues) > 0

        # Check for specific issue types
        issue_types = {i.issue_type for i in issues}
        assert "sku_format_normalized" in issue_types
        assert "whitespace_trimmed" in issue_types
        assert "negative_quantity" in issue_types
        assert "date_format_inconsistent" in issue_types
        assert "column_name_mismatch" in issue_types
