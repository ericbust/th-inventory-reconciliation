"""Data quality issue model."""

from dataclasses import dataclass
from typing import Literal, Optional


IssueType = Literal[
    "duplicate_key",
    "negative_quantity",
    "quantity_coerced",
    "column_name_mismatch",
    "sku_format_normalized",
    "whitespace_trimmed",
    "date_format_inconsistent",
    "date_regression",
    "name_drift",
    "empty_file",
    "missing_required_column",
]

Severity = Literal["error", "warning", "info"]

SourceFile = Literal["snapshot_1", "snapshot_2", "both"]


@dataclass
class DataQualityIssue:
    """Represents a detected data quality problem.

    Issue Types and Severities:
    - duplicate_key (error): Same SKU+Warehouse appears multiple times
    - negative_quantity (error): Quantity < 0
    - quantity_coerced (warning): Quantity was coerced from float to int
    - column_name_mismatch (info): Column names differ from canonical names
    - sku_format_normalized (warning): SKU required normalization
    - whitespace_trimmed (warning): Leading/trailing whitespace removed
    - date_format_inconsistent (warning): Date format differs from ISO
    - date_regression (warning): Date in snapshot_2 is earlier than snapshot_1
    - name_drift (warning): Product name changed between snapshots
    - empty_file (error): Snapshot file contains no data rows
    - missing_required_column (error): Required column not found
    """

    issue_type: IssueType
    severity: Severity
    source_file: SourceFile
    description: str
    row_number: Optional[int] = None
    field: Optional[str] = None
    original_value: Optional[str] = None
    normalized_value: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "issue_type": self.issue_type,
            "severity": self.severity,
            "source_file": self.source_file,
            "row_number": self.row_number,
            "field": self.field,
            "original_value": self.original_value,
            "normalized_value": self.normalized_value,
            "description": self.description,
        }
