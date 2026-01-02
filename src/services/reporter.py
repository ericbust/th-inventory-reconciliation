"""Reporter service for JSON output generation."""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from src.models.quality_issue import DataQualityIssue
from src.models.reconciliation_result import ReconciliationResult
from src.models.report import (
    ReconciliationReport,
    ReportMetadata,
    ReportSummary,
    ResultsByStatus,
)


def build_report(
    results: list[ReconciliationResult],
    quality_issues: list[DataQualityIssue],
    snapshot_1_path: str,
    snapshot_2_path: str,
    snapshot_1_rows: int,
    snapshot_2_rows: int,
    snapshot_1_valid_rows: int,
    snapshot_2_valid_rows: int,
    generated_at: Optional[str] = None,
) -> ReconciliationReport:
    """Build a complete reconciliation report from results and quality issues.

    Args:
        results: List of reconciliation results.
        quality_issues: List of data quality issues.
        snapshot_1_path: Path to first snapshot file.
        snapshot_2_path: Path to second snapshot file.
        snapshot_1_rows: Total rows in first snapshot.
        snapshot_2_rows: Total rows in second snapshot.
        snapshot_1_valid_rows: Valid rows in first snapshot (after filtering duplicates).
        snapshot_2_valid_rows: Valid rows in second snapshot (after filtering duplicates).
        generated_at: Optional ISO 8601 timestamp. If None, uses current time.

    Returns:
        A complete ReconciliationReport ready for JSON serialization.
    """
    # Generate timestamp if not provided
    if generated_at is None:
        generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    # Group results by status
    unchanged = sorted(
        [r for r in results if r.status == "unchanged"],
        key=lambda r: (r.sku, r.location),
    )
    quantity_changed = sorted(
        [r for r in results if r.status == "quantity_changed"],
        key=lambda r: (r.sku, r.location),
    )
    added = sorted(
        [r for r in results if r.status == "added"],
        key=lambda r: (r.sku, r.location),
    )
    removed = sorted(
        [r for r in results if r.status == "removed"],
        key=lambda r: (r.sku, r.location),
    )

    # Count quality issues by severity
    quality_by_severity = {"error": 0, "warning": 0, "info": 0}
    for issue in quality_issues:
        if issue.severity in quality_by_severity:
            quality_by_severity[issue.severity] += 1

    # Sort quality issues for deterministic output
    sorted_quality_issues = sorted(
        quality_issues,
        key=lambda i: (
            i.severity,
            i.issue_type,
            i.source_file,
            i.row_number or 0,
        ),
    )

    # Build report components
    metadata = ReportMetadata(
        generated_at=generated_at,
        snapshot_1_path=snapshot_1_path,
        snapshot_2_path=snapshot_2_path,
        snapshot_1_rows=snapshot_1_rows,
        snapshot_2_rows=snapshot_2_rows,
        snapshot_1_valid_rows=snapshot_1_valid_rows,
        snapshot_2_valid_rows=snapshot_2_valid_rows,
    )

    summary = ReportSummary(
        total_items_compared=len(results),
        unchanged=len(unchanged),
        quantity_changed=len(quantity_changed),
        added=len(added),
        removed=len(removed),
        quality_issues_count=len(quality_issues),
        quality_issues_by_severity=quality_by_severity,
    )

    results_by_status = ResultsByStatus(
        unchanged=unchanged,
        quantity_changed=quantity_changed,
        added=added,
        removed=removed,
    )

    return ReconciliationReport(
        metadata=metadata,
        summary=summary,
        results=results_by_status,
        quality_issues=sorted_quality_issues,
    )


def write_json(report: ReconciliationReport, output_path: Path) -> None:
    """Write a reconciliation report to a JSON file.

    Uses sort_keys=True for deterministic output.
    Creates parent directories if they don't exist.

    Args:
        report: The reconciliation report to write.
        output_path: Path where the JSON file should be written.
    """
    # Create parent directories if needed
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Convert to dict and write with sorted keys for determinism
    report_dict = report.to_dict()

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report_dict, f, indent=2, sort_keys=True, ensure_ascii=False)
        f.write("\n")  # Add trailing newline
