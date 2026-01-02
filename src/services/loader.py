"""CSV snapshot loading service with column mapping."""

from pathlib import Path
from typing import Any

import pandas as pd

from src.schemas.inventory_schema import CANONICAL_COLUMNS

# Known column name variations mapped to canonical names
# Keys are non-canonical names, values are canonical names
COLUMN_MAPPING: dict[str, str] = {
    "product_name": "name",
    "qty": "quantity",
    "warehouse": "location",
    "updated_at": "last_counted",
}

# Required columns that must exist after mapping
REQUIRED_COLUMNS = set(CANONICAL_COLUMNS)


def _apply_column_mapping(df: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    """Apply column name mapping to DataFrame.

    Args:
        df: Input DataFrame with potentially non-canonical column names.

    Returns:
        Tuple of (DataFrame with renamed columns, list of mapped column names).
    """
    # Track which columns were mapped
    mapped_columns: list[str] = []

    # Build rename dict for columns that need mapping
    rename_dict: dict[str, str] = {}
    for col in df.columns:
        col_lower = col.lower().strip()
        if col_lower in COLUMN_MAPPING:
            rename_dict[col] = COLUMN_MAPPING[col_lower]
            mapped_columns.append(col)

    # Apply renaming
    if rename_dict:
        df = df.rename(columns=rename_dict)

    # Also lowercase any remaining columns for consistency
    df.columns = df.columns.str.lower().str.strip()

    return df, mapped_columns


def _validate_required_columns(df: pd.DataFrame, file_path: str) -> list[str]:
    """Check that all required columns are present.

    Args:
        df: DataFrame to validate.
        file_path: Path to file (for error messages).

    Returns:
        List of missing column names.
    """
    present_columns = set(df.columns)
    missing = REQUIRED_COLUMNS - present_columns
    return list(missing)


def _detect_float_quantities(path: Path, qty_column: str) -> dict[int, str]:
    """Detect which rows have float-formatted quantities in the raw CSV.

    Args:
        path: Path to the CSV file.
        qty_column: Name of the quantity column to check.

    Returns:
        Dict mapping row indices (0-based) to original string values for
        quantities that have decimal points.
    """
    float_rows: dict[int, str] = {}

    # Read CSV as strings to preserve original format
    df_str = pd.read_csv(path, dtype=str)

    # Apply column mapping to find the quantity column
    for col in df_str.columns:
        col_lower = col.lower().strip()
        if col_lower in COLUMN_MAPPING:
            df_str = df_str.rename(columns={col: COLUMN_MAPPING[col_lower]})
    df_str.columns = df_str.columns.str.lower().str.strip()

    if qty_column not in df_str.columns:
        return float_rows

    for idx, val in enumerate(df_str[qty_column]):
        if pd.notna(val) and "." in str(val):
            float_rows[idx] = str(val).strip()

    return float_rows


def load_snapshot(
    file_path: str | Path,
) -> tuple[pd.DataFrame, list[str], list[str], dict[int, str]]:
    """Load inventory snapshot from CSV file with column mapping.

    Reads a CSV file, applies column name mapping, and validates required
    columns are present. Does NOT apply data normalization (SKU format, etc.)
    - that is handled by the normalizer service.

    Args:
        file_path: Path to the CSV file.

    Returns:
        Tuple containing:
        - DataFrame with mapped column names
        - List of columns that were mapped (for quality reporting)
        - List of missing required columns (for quality reporting)
        - Dict mapping row indices to original string values for float quantities

    Raises:
        FileNotFoundError: If the file does not exist.
        pd.errors.EmptyDataError: If the file is empty.
    """
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"Snapshot file not found: {file_path}")

    # Detect float-formatted quantities before pandas converts them
    float_qty_rows = _detect_float_quantities(path, "quantity")

    # Read CSV with pandas
    df = pd.read_csv(path)

    # Check for empty file
    if df.empty:
        return df, [], list(REQUIRED_COLUMNS), {}

    # Apply column mapping
    df, mapped_columns = _apply_column_mapping(df)

    # Check for missing required columns
    missing_columns = _validate_required_columns(df, str(file_path))

    return df, mapped_columns, missing_columns, float_qty_rows
