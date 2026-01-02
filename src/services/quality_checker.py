"""Quality checker service for detecting data quality issues."""

import re
from typing import Optional

import pandas as pd

from src.models.quality_issue import DataQualityIssue
from src.services.normalizer import normalize_sku


def check_duplicates(
    df: pd.DataFrame,
    source_file: str,
    key_cols: Optional[list[str]] = None,
) -> list[DataQualityIssue]:
    """Check for duplicate composite keys.

    Args:
        df: DataFrame to check.
        source_file: Source file identifier ("snapshot_1" or "snapshot_2").
        key_cols: Columns forming composite key. Defaults to ["sku", "location"].

    Returns:
        List of DataQualityIssue for each duplicate row.
    """
    if key_cols is None:
        key_cols = ["sku", "location"]

    issues: list[DataQualityIssue] = []

    # Find all rows with duplicate keys (keep=False marks ALL occurrences)
    duplicates = df[df.duplicated(subset=key_cols, keep=False)]

    for idx, row in duplicates.iterrows():
        # Row number is 1-indexed (excluding header)
        row_num = int(idx) + 1
        key_value = f"{row['sku']}@{row['location']}"

        issues.append(
            DataQualityIssue(
                issue_type="duplicate_key",
                severity="error",
                source_file=source_file,  # type: ignore
                row_number=row_num,
                field="sku,location",
                original_value=key_value,
                normalized_value=None,
                description=f"Duplicate key {key_value} at row {row_num}",
            )
        )

    return issues


def check_negative_quantities(
    df: pd.DataFrame,
    source_file: str,
) -> list[DataQualityIssue]:
    """Check for negative quantity values.

    Args:
        df: DataFrame to check.
        source_file: Source file identifier.

    Returns:
        List of DataQualityIssue for each negative quantity.
    """
    issues: list[DataQualityIssue] = []

    if "quantity" not in df.columns:
        return issues

    negative_mask = df["quantity"] < 0

    for idx in df[negative_mask].index:
        row_num = int(idx) + 1
        qty = df.loc[idx, "quantity"]
        sku = df.loc[idx, "sku"] if "sku" in df.columns else "unknown"

        issues.append(
            DataQualityIssue(
                issue_type="negative_quantity",
                severity="error",
                source_file=source_file,  # type: ignore
                row_number=row_num,
                field="quantity",
                original_value=str(qty),
                normalized_value=None,
                description=f"Negative quantity {qty} for SKU {sku} at row {row_num}",
            )
        )

    return issues


def check_sku_format(
    df: pd.DataFrame,
    source_file: str,
) -> list[DataQualityIssue]:
    """Check for SKUs that require normalization.

    Args:
        df: DataFrame to check.
        source_file: Source file identifier.

    Returns:
        List of DataQualityIssue for each SKU requiring normalization.
    """
    issues: list[DataQualityIssue] = []

    if "sku" not in df.columns:
        return issues

    # Standard format is SKU-NNN (uppercase with hyphen)
    standard_pattern = re.compile(r"^SKU-\d{3}$")

    for idx, row in df.iterrows():
        original_sku = str(row["sku"]).strip()
        normalized_sku = normalize_sku(original_sku)

        # If normalization changed the SKU, it needed fixing
        if original_sku != normalized_sku and normalized_sku:
            row_num = int(idx) + 1
            issues.append(
                DataQualityIssue(
                    issue_type="sku_format_normalized",
                    severity="warning",
                    source_file=source_file,  # type: ignore
                    row_number=row_num,
                    field="sku",
                    original_value=original_sku,
                    normalized_value=normalized_sku,
                    description=f"SKU normalized from '{original_sku}' to '{normalized_sku}' at row {row_num}",
                )
            )

    return issues


def check_whitespace(
    df: pd.DataFrame,
    source_file: str,
) -> list[DataQualityIssue]:
    """Check for leading/trailing whitespace in text fields.

    Args:
        df: DataFrame to check.
        source_file: Source file identifier.

    Returns:
        List of DataQualityIssue for each whitespace issue.
    """
    issues: list[DataQualityIssue] = []
    text_fields = ["name", "location"]

    for field in text_fields:
        if field not in df.columns:
            continue

        for idx, row in df.iterrows():
            original = str(row[field])
            trimmed = original.strip()

            if original != trimmed:
                row_num = int(idx) + 1
                issues.append(
                    DataQualityIssue(
                        issue_type="whitespace_trimmed",
                        severity="warning",
                        source_file=source_file,  # type: ignore
                        row_number=row_num,
                        field=field,
                        original_value=repr(original),
                        normalized_value=trimmed,
                        description=f"Whitespace trimmed from {field} at row {row_num}",
                    )
                )

    return issues


def check_date_format(
    df: pd.DataFrame,
    source_file: str,
) -> list[DataQualityIssue]:
    """Check for non-ISO date formats.

    Args:
        df: DataFrame to check.
        source_file: Source file identifier.

    Returns:
        List of DataQualityIssue for each non-ISO date.
    """
    issues: list[DataQualityIssue] = []

    if "last_counted" not in df.columns:
        return issues

    # ISO 8601 date format: YYYY-MM-DD
    iso_pattern = re.compile(r"^\d{4}-\d{2}-\d{2}$")

    for idx, row in df.iterrows():
        date_value = str(row["last_counted"]).strip()

        if not iso_pattern.match(date_value):
            row_num = int(idx) + 1
            issues.append(
                DataQualityIssue(
                    issue_type="date_format_inconsistent",
                    severity="warning",
                    source_file=source_file,  # type: ignore
                    row_number=row_num,
                    field="last_counted",
                    original_value=date_value,
                    normalized_value=None,
                    description=f"Date '{date_value}' is not in ISO format (YYYY-MM-DD) at row {row_num}",
                )
            )

    return issues


def check_date_regression(
    df1: pd.DataFrame,
    df2: pd.DataFrame,
    key_cols: list[str] | None = None,
) -> list[DataQualityIssue]:
    """Check for dates in snapshot_2 that are earlier than snapshot_1.

    This detects cases where the last_counted date goes backwards between
    snapshots, which likely indicates a data quality issue.

    Args:
        df1: First snapshot DataFrame (older).
        df2: Second snapshot DataFrame (newer).
        key_cols: Columns forming composite key.

    Returns:
        List of DataQualityIssue for each date regression.
    """
    from datetime import date

    if key_cols is None:
        key_cols = ["sku", "location"]

    issues: list[DataQualityIssue] = []

    if "last_counted" not in df1.columns or "last_counted" not in df2.columns:
        return issues

    # Merge to find common items
    merged = pd.merge(
        df1[key_cols + ["last_counted"]],
        df2[key_cols + ["last_counted"]],
        on=key_cols,
        how="inner",
        suffixes=("_old", "_new"),
    )

    # ISO 8601 date format: YYYY-MM-DD
    iso_pattern = re.compile(r"^(\d{4})-(\d{2})-(\d{2})$")

    def parse_date(date_str: str) -> date | None:
        """Parse ISO date string to date object."""
        match = iso_pattern.match(str(date_str).strip())
        if match:
            try:
                return date(int(match.group(1)), int(match.group(2)), int(match.group(3)))
            except ValueError:
                return None
        return None

    for _, row in merged.iterrows():
        old_date_str = str(row["last_counted_old"]).strip()
        new_date_str = str(row["last_counted_new"]).strip()

        old_date = parse_date(old_date_str)
        new_date = parse_date(new_date_str)

        if old_date and new_date and new_date < old_date:
            key_value = f"{row['sku']}@{row['location']}"
            issues.append(
                DataQualityIssue(
                    issue_type="date_regression",
                    severity="warning",
                    source_file="both",
                    row_number=None,
                    field="last_counted",
                    original_value=old_date_str,
                    normalized_value=new_date_str,
                    description=f"Date regressed for {key_value}: '{old_date_str}' -> '{new_date_str}'",
                )
            )

    return issues


def check_column_names(
    mapped_columns: list[str],
    source_file: str,
) -> list[DataQualityIssue]:
    """Check for non-canonical column names that were mapped.

    Args:
        mapped_columns: List of original column names that were mapped.
        source_file: Source file identifier.

    Returns:
        List of DataQualityIssue for each mapped column.
    """
    issues: list[DataQualityIssue] = []

    # Mapping from non-canonical to canonical names
    column_mapping = {
        "product_name": "name",
        "qty": "quantity",
        "warehouse": "location",
        "updated_at": "last_counted",
    }

    for original_name in mapped_columns:
        canonical_name = column_mapping.get(original_name.lower(), original_name)
        issues.append(
            DataQualityIssue(
                issue_type="column_name_mismatch",
                severity="info",
                source_file=source_file,  # type: ignore
                row_number=None,
                field=original_name,
                original_value=original_name,
                normalized_value=canonical_name,
                description=f"Column '{original_name}' mapped to '{canonical_name}'",
            )
        )

    return issues


def check_name_drift(
    df1: pd.DataFrame,
    df2: pd.DataFrame,
    key_cols: Optional[list[str]] = None,
) -> list[DataQualityIssue]:
    """Check for product name changes between snapshots.

    Args:
        df1: First snapshot DataFrame.
        df2: Second snapshot DataFrame.
        key_cols: Columns forming composite key.

    Returns:
        List of DataQualityIssue for each name drift.
    """
    if key_cols is None:
        key_cols = ["sku", "location"]

    issues: list[DataQualityIssue] = []

    if "name" not in df1.columns or "name" not in df2.columns:
        return issues

    # Merge to find common items
    merged = pd.merge(
        df1[key_cols + ["name"]],
        df2[key_cols + ["name"]],
        on=key_cols,
        how="inner",
        suffixes=("_old", "_new"),
    )

    for _, row in merged.iterrows():
        old_name = str(row["name_old"]).strip()
        new_name = str(row["name_new"]).strip()

        if old_name != new_name:
            key_value = f"{row['sku']}@{row['location']}"
            issues.append(
                DataQualityIssue(
                    issue_type="name_drift",
                    severity="warning",
                    source_file="both",
                    row_number=None,
                    field="name",
                    original_value=old_name,
                    normalized_value=new_name,
                    description=f"Name changed for {key_value}: '{old_name}' -> '{new_name}'",
                )
            )

    return issues


def check_empty_file(
    df: pd.DataFrame,
    source_file: str,
) -> list[DataQualityIssue]:
    """Check if file is empty.

    Args:
        df: DataFrame to check.
        source_file: Source file identifier.

    Returns:
        List with single DataQualityIssue if file is empty.
    """
    if df.empty:
        return [
            DataQualityIssue(
                issue_type="empty_file",
                severity="error",
                source_file=source_file,  # type: ignore
                row_number=None,
                field=None,
                original_value=None,
                normalized_value=None,
                description=f"File {source_file} contains no data rows",
            )
        ]
    return []


def check_missing_columns(
    missing_columns: list[str],
    source_file: str,
) -> list[DataQualityIssue]:
    """Check for missing required columns.

    Args:
        missing_columns: List of missing column names.
        source_file: Source file identifier.

    Returns:
        List of DataQualityIssue for each missing column.
    """
    issues: list[DataQualityIssue] = []

    for col in missing_columns:
        issues.append(
            DataQualityIssue(
                issue_type="missing_required_column",
                severity="error",
                source_file=source_file,  # type: ignore
                row_number=None,
                field=col,
                original_value=None,
                normalized_value=None,
                description=f"Required column '{col}' not found in {source_file}",
            )
        )

    return issues


def run_all_checks(
    df1: pd.DataFrame,
    df2: pd.DataFrame,
    mapped_columns_1: list[str],
    mapped_columns_2: list[str],
    missing_columns_1: Optional[list[str]] = None,
    missing_columns_2: Optional[list[str]] = None,
) -> list[DataQualityIssue]:
    """Run all quality checks on both snapshots.

    Args:
        df1: First snapshot DataFrame.
        df2: Second snapshot DataFrame.
        mapped_columns_1: Columns mapped in snapshot 1.
        mapped_columns_2: Columns mapped in snapshot 2.
        missing_columns_1: Missing columns in snapshot 1.
        missing_columns_2: Missing columns in snapshot 2.

    Returns:
        Combined list of all DataQualityIssues.
    """
    if missing_columns_1 is None:
        missing_columns_1 = []
    if missing_columns_2 is None:
        missing_columns_2 = []

    issues: list[DataQualityIssue] = []

    # Check for empty files
    issues.extend(check_empty_file(df1, "snapshot_1"))
    issues.extend(check_empty_file(df2, "snapshot_2"))

    # Check for missing columns
    issues.extend(check_missing_columns(missing_columns_1, "snapshot_1"))
    issues.extend(check_missing_columns(missing_columns_2, "snapshot_2"))

    # Column name mapping issues
    issues.extend(check_column_names(mapped_columns_1, "snapshot_1"))
    issues.extend(check_column_names(mapped_columns_2, "snapshot_2"))

    # Per-snapshot checks
    for df, source in [(df1, "snapshot_1"), (df2, "snapshot_2")]:
        if df.empty:
            continue

        issues.extend(check_duplicates(df, source))
        issues.extend(check_negative_quantities(df, source))
        issues.extend(check_sku_format(df, source))
        issues.extend(check_whitespace(df, source))
        issues.extend(check_date_format(df, source))

    # Cross-snapshot checks
    if not df1.empty and not df2.empty:
        issues.extend(check_name_drift(df1, df2))
        issues.extend(check_date_regression(df1, df2))

    return issues
