"""Report data models for JSON output generation."""

from dataclasses import dataclass, field
from typing import Any

from src.models.quality_issue import DataQualityIssue
from src.models.reconciliation_result import ReconciliationResult


@dataclass
class ReportMetadata:
    """Metadata about the reconciliation report execution.

    Contains information about when the report was generated and
    which files were processed.
    """

    generated_at: str
    snapshot_1_path: str
    snapshot_2_path: str
    snapshot_1_rows: int
    snapshot_2_rows: int
    snapshot_1_valid_rows: int
    snapshot_2_valid_rows: int

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "generated_at": self.generated_at,
            "snapshot_1_path": self.snapshot_1_path,
            "snapshot_2_path": self.snapshot_2_path,
            "snapshot_1_rows": self.snapshot_1_rows,
            "snapshot_2_rows": self.snapshot_2_rows,
            "snapshot_1_valid_rows": self.snapshot_1_valid_rows,
            "snapshot_2_valid_rows": self.snapshot_2_valid_rows,
        }


@dataclass
class ReportSummary:
    """Summary counts for the reconciliation report.

    Contains aggregate counts of items by status and quality issues
    by severity.
    """

    total_items_compared: int
    unchanged: int
    quantity_changed: int
    added: int
    removed: int
    quality_issues_count: int
    quality_issues_by_severity: dict[str, int] = field(
        default_factory=lambda: {"error": 0, "warning": 0, "info": 0}
    )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "total_items_compared": self.total_items_compared,
            "unchanged": self.unchanged,
            "quantity_changed": self.quantity_changed,
            "added": self.added,
            "removed": self.removed,
            "quality_issues_count": self.quality_issues_count,
            "quality_issues_by_severity": self.quality_issues_by_severity,
        }


@dataclass
class ResultsByStatus:
    """Reconciliation results grouped by status.

    Contains lists of results categorized as unchanged, quantity_changed,
    added, or removed.
    """

    unchanged: list[ReconciliationResult] = field(default_factory=list)
    quantity_changed: list[ReconciliationResult] = field(default_factory=list)
    added: list[ReconciliationResult] = field(default_factory=list)
    removed: list[ReconciliationResult] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "unchanged": [r.to_dict() for r in self.unchanged],
            "quantity_changed": [r.to_dict() for r in self.quantity_changed],
            "added": [r.to_dict() for r in self.added],
            "removed": [r.to_dict() for r in self.removed],
        }


@dataclass
class ReconciliationReport:
    """Complete reconciliation report structure.

    The top-level data structure containing all report components:
    metadata, summary, results grouped by status, and quality issues.
    """

    metadata: ReportMetadata
    summary: ReportSummary
    results: ResultsByStatus
    quality_issues: list[DataQualityIssue] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "metadata": self.metadata.to_dict(),
            "summary": self.summary.to_dict(),
            "results": self.results.to_dict(),
            "quality_issues": [i.to_dict() for i in self.quality_issues],
        }
