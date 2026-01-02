"""Unit tests for the reporter service (JSON output generation)."""

import json
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any

import pytest

from src.models.quality_issue import DataQualityIssue
from src.models.reconciliation_result import ReconciliationResult


class TestReportMetadata:
    """Tests for ReportMetadata dataclass."""

    def test_metadata_creation(self) -> None:
        """Test basic ReportMetadata creation."""
        from src.models.report import ReportMetadata

        metadata = ReportMetadata(
            generated_at="2026-01-02T10:30:00Z",
            snapshot_1_path="data/snapshot_1.csv",
            snapshot_2_path="data/snapshot_2.csv",
            snapshot_1_rows=75,
            snapshot_2_rows=80,
            snapshot_1_valid_rows=73,
            snapshot_2_valid_rows=78,
        )

        assert metadata.generated_at == "2026-01-02T10:30:00Z"
        assert metadata.snapshot_1_path == "data/snapshot_1.csv"
        assert metadata.snapshot_2_path == "data/snapshot_2.csv"
        assert metadata.snapshot_1_rows == 75
        assert metadata.snapshot_2_rows == 80
        assert metadata.snapshot_1_valid_rows == 73
        assert metadata.snapshot_2_valid_rows == 78

    def test_metadata_to_dict(self) -> None:
        """Test metadata serialization to dictionary."""
        from src.models.report import ReportMetadata

        metadata = ReportMetadata(
            generated_at="2026-01-02T10:30:00Z",
            snapshot_1_path="data/snapshot_1.csv",
            snapshot_2_path="data/snapshot_2.csv",
            snapshot_1_rows=75,
            snapshot_2_rows=80,
            snapshot_1_valid_rows=73,
            snapshot_2_valid_rows=78,
        )

        result = metadata.to_dict()

        assert isinstance(result, dict)
        assert result["generated_at"] == "2026-01-02T10:30:00Z"
        assert result["snapshot_1_rows"] == 75


class TestReportSummary:
    """Tests for ReportSummary dataclass."""

    def test_summary_creation(self) -> None:
        """Test basic ReportSummary creation."""
        from src.models.report import ReportSummary

        summary = ReportSummary(
            total_items_compared=70,
            unchanged=50,
            quantity_changed=15,
            added=5,
            removed=2,
            quality_issues_count=8,
            quality_issues_by_severity={"error": 3, "warning": 4, "info": 1},
        )

        assert summary.total_items_compared == 70
        assert summary.unchanged == 50
        assert summary.quantity_changed == 15
        assert summary.added == 5
        assert summary.removed == 2
        assert summary.quality_issues_count == 8
        assert summary.quality_issues_by_severity["error"] == 3

    def test_summary_to_dict(self) -> None:
        """Test summary serialization to dictionary."""
        from src.models.report import ReportSummary

        summary = ReportSummary(
            total_items_compared=70,
            unchanged=50,
            quantity_changed=15,
            added=5,
            removed=2,
            quality_issues_count=8,
            quality_issues_by_severity={"error": 3, "warning": 4, "info": 1},
        )

        result = summary.to_dict()

        assert isinstance(result, dict)
        assert result["total_items_compared"] == 70
        assert result["quality_issues_by_severity"]["warning"] == 4


class TestResultsByStatus:
    """Tests for ResultsByStatus dataclass."""

    def test_results_by_status_creation(self) -> None:
        """Test basic ResultsByStatus creation."""
        from src.models.report import ResultsByStatus

        unchanged = [
            ReconciliationResult(
                sku="SKU-001",
                location="Warehouse A",
                status="unchanged",
                old_quantity=100,
                new_quantity=100,
                quantity_delta=0,
            )
        ]
        changed = [
            ReconciliationResult(
                sku="SKU-002",
                location="Warehouse A",
                status="quantity_changed",
                old_quantity=50,
                new_quantity=45,
                quantity_delta=-5,
            )
        ]
        added = [
            ReconciliationResult(
                sku="SKU-003",
                location="Warehouse B",
                status="added",
                new_quantity=25,
            )
        ]
        removed = [
            ReconciliationResult(
                sku="SKU-004",
                location="Warehouse A",
                status="removed",
                old_quantity=10,
            )
        ]

        results = ResultsByStatus(
            unchanged=unchanged,
            quantity_changed=changed,
            added=added,
            removed=removed,
        )

        assert len(results.unchanged) == 1
        assert len(results.quantity_changed) == 1
        assert len(results.added) == 1
        assert len(results.removed) == 1

    def test_results_by_status_to_dict(self) -> None:
        """Test results serialization to dictionary."""
        from src.models.report import ResultsByStatus

        results = ResultsByStatus(
            unchanged=[
                ReconciliationResult(
                    sku="SKU-001",
                    location="Warehouse A",
                    status="unchanged",
                    old_quantity=100,
                    new_quantity=100,
                    quantity_delta=0,
                )
            ],
            quantity_changed=[],
            added=[],
            removed=[],
        )

        result = results.to_dict()

        assert isinstance(result, dict)
        assert len(result["unchanged"]) == 1
        assert result["unchanged"][0]["sku"] == "SKU-001"


class TestReconciliationReport:
    """Tests for ReconciliationReport dataclass."""

    def test_report_creation(self) -> None:
        """Test basic ReconciliationReport creation."""
        from src.models.report import (
            ReconciliationReport,
            ReportMetadata,
            ReportSummary,
            ResultsByStatus,
        )

        metadata = ReportMetadata(
            generated_at="2026-01-02T10:30:00Z",
            snapshot_1_path="data/snapshot_1.csv",
            snapshot_2_path="data/snapshot_2.csv",
            snapshot_1_rows=75,
            snapshot_2_rows=80,
            snapshot_1_valid_rows=73,
            snapshot_2_valid_rows=78,
        )
        summary = ReportSummary(
            total_items_compared=70,
            unchanged=50,
            quantity_changed=15,
            added=5,
            removed=2,
            quality_issues_count=0,
            quality_issues_by_severity={"error": 0, "warning": 0, "info": 0},
        )
        results = ResultsByStatus(
            unchanged=[],
            quantity_changed=[],
            added=[],
            removed=[],
        )

        report = ReconciliationReport(
            metadata=metadata,
            summary=summary,
            results=results,
            quality_issues=[],
        )

        assert report.metadata.snapshot_1_rows == 75
        assert report.summary.total_items_compared == 70
        assert len(report.quality_issues) == 0

    def test_report_to_dict(self) -> None:
        """Test report serialization to dictionary."""
        from src.models.report import (
            ReconciliationReport,
            ReportMetadata,
            ReportSummary,
            ResultsByStatus,
        )

        metadata = ReportMetadata(
            generated_at="2026-01-02T10:30:00Z",
            snapshot_1_path="data/snapshot_1.csv",
            snapshot_2_path="data/snapshot_2.csv",
            snapshot_1_rows=75,
            snapshot_2_rows=80,
            snapshot_1_valid_rows=73,
            snapshot_2_valid_rows=78,
        )
        summary = ReportSummary(
            total_items_compared=70,
            unchanged=50,
            quantity_changed=15,
            added=5,
            removed=2,
            quality_issues_count=0,
            quality_issues_by_severity={"error": 0, "warning": 0, "info": 0},
        )
        results = ResultsByStatus(
            unchanged=[],
            quantity_changed=[],
            added=[],
            removed=[],
        )

        report = ReconciliationReport(
            metadata=metadata,
            summary=summary,
            results=results,
            quality_issues=[],
        )

        result = report.to_dict()

        assert isinstance(result, dict)
        assert "metadata" in result
        assert "summary" in result
        assert "results" in result
        assert "quality_issues" in result


class TestBuildReport:
    """Tests for build_report function."""

    def test_build_report_basic(self) -> None:
        """Test building a report from reconciliation data."""
        from src.services.reporter import build_report

        reconciliation_results = [
            ReconciliationResult(
                sku="SKU-001",
                location="Warehouse A",
                status="unchanged",
                old_quantity=100,
                new_quantity=100,
                quantity_delta=0,
                old_name="Widget A",
                new_name="Widget A",
            ),
            ReconciliationResult(
                sku="SKU-002",
                location="Warehouse A",
                status="quantity_changed",
                old_quantity=50,
                new_quantity=45,
                quantity_delta=-5,
                old_name="Widget B",
                new_name="Widget B",
            ),
            ReconciliationResult(
                sku="SKU-003",
                location="Warehouse B",
                status="added",
                new_quantity=25,
                new_name="Widget C",
            ),
            ReconciliationResult(
                sku="SKU-004",
                location="Warehouse A",
                status="removed",
                old_quantity=10,
                old_name="Widget D",
            ),
        ]
        quality_issues: list[DataQualityIssue] = []

        report = build_report(
            results=reconciliation_results,
            quality_issues=quality_issues,
            snapshot_1_path="data/snapshot_1.csv",
            snapshot_2_path="data/snapshot_2.csv",
            snapshot_1_rows=10,
            snapshot_2_rows=10,
            snapshot_1_valid_rows=10,
            snapshot_2_valid_rows=10,
        )

        assert report.summary.unchanged == 1
        assert report.summary.quantity_changed == 1
        assert report.summary.added == 1
        assert report.summary.removed == 1
        assert report.summary.total_items_compared == 4

    def test_build_report_with_quality_issues(self) -> None:
        """Test building a report with quality issues."""
        from src.services.reporter import build_report

        quality_issues = [
            DataQualityIssue(
                issue_type="duplicate_key",
                severity="error",
                source_file="snapshot_1",
                description="Duplicate key found",
                row_number=5,
            ),
            DataQualityIssue(
                issue_type="sku_format_normalized",
                severity="warning",
                source_file="snapshot_1",
                description="SKU format normalized",
                row_number=3,
            ),
            DataQualityIssue(
                issue_type="column_name_mismatch",
                severity="info",
                source_file="snapshot_2",
                description="Column mapped",
            ),
        ]

        report = build_report(
            results=[],
            quality_issues=quality_issues,
            snapshot_1_path="data/snapshot_1.csv",
            snapshot_2_path="data/snapshot_2.csv",
            snapshot_1_rows=10,
            snapshot_2_rows=10,
            snapshot_1_valid_rows=8,
            snapshot_2_valid_rows=10,
        )

        assert report.summary.quality_issues_count == 3
        assert report.summary.quality_issues_by_severity["error"] == 1
        assert report.summary.quality_issues_by_severity["warning"] == 1
        assert report.summary.quality_issues_by_severity["info"] == 1

    def test_build_report_groups_results_by_status(self) -> None:
        """Test that build_report correctly groups results by status."""
        from src.services.reporter import build_report

        results = [
            ReconciliationResult(sku="SKU-001", location="WA", status="unchanged"),
            ReconciliationResult(sku="SKU-002", location="WA", status="unchanged"),
            ReconciliationResult(sku="SKU-003", location="WA", status="quantity_changed"),
            ReconciliationResult(sku="SKU-004", location="WA", status="added"),
            ReconciliationResult(sku="SKU-005", location="WA", status="removed"),
            ReconciliationResult(sku="SKU-006", location="WA", status="removed"),
        ]

        report = build_report(
            results=results,
            quality_issues=[],
            snapshot_1_path="s1.csv",
            snapshot_2_path="s2.csv",
            snapshot_1_rows=5,
            snapshot_2_rows=5,
            snapshot_1_valid_rows=5,
            snapshot_2_valid_rows=5,
        )

        assert len(report.results.unchanged) == 2
        assert len(report.results.quantity_changed) == 1
        assert len(report.results.added) == 1
        assert len(report.results.removed) == 2


class TestWriteJson:
    """Tests for write_json function."""

    def test_write_json_creates_file(self) -> None:
        """Test that write_json creates a JSON file."""
        from src.models.report import (
            ReconciliationReport,
            ReportMetadata,
            ReportSummary,
            ResultsByStatus,
        )
        from src.services.reporter import write_json

        report = ReconciliationReport(
            metadata=ReportMetadata(
                generated_at="2026-01-02T10:30:00Z",
                snapshot_1_path="s1.csv",
                snapshot_2_path="s2.csv",
                snapshot_1_rows=10,
                snapshot_2_rows=10,
                snapshot_1_valid_rows=10,
                snapshot_2_valid_rows=10,
            ),
            summary=ReportSummary(
                total_items_compared=5,
                unchanged=3,
                quantity_changed=1,
                added=1,
                removed=0,
                quality_issues_count=0,
                quality_issues_by_severity={"error": 0, "warning": 0, "info": 0},
            ),
            results=ResultsByStatus(
                unchanged=[],
                quantity_changed=[],
                added=[],
                removed=[],
            ),
            quality_issues=[],
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "report.json"
            write_json(report, output_path)

            assert output_path.exists()

            with open(output_path) as f:
                loaded = json.load(f)

            assert loaded["summary"]["unchanged"] == 3

    def test_write_json_sorted_keys_for_determinism(self) -> None:
        """Test that write_json produces deterministic output with sorted keys."""
        from src.models.report import (
            ReconciliationReport,
            ReportMetadata,
            ReportSummary,
            ResultsByStatus,
        )
        from src.services.reporter import write_json

        report = ReconciliationReport(
            metadata=ReportMetadata(
                generated_at="2026-01-02T10:30:00Z",
                snapshot_1_path="s1.csv",
                snapshot_2_path="s2.csv",
                snapshot_1_rows=10,
                snapshot_2_rows=10,
                snapshot_1_valid_rows=10,
                snapshot_2_valid_rows=10,
            ),
            summary=ReportSummary(
                total_items_compared=5,
                unchanged=3,
                quantity_changed=1,
                added=1,
                removed=0,
                quality_issues_count=0,
                quality_issues_by_severity={"error": 0, "warning": 0, "info": 0},
            ),
            results=ResultsByStatus(
                unchanged=[],
                quantity_changed=[],
                added=[],
                removed=[],
            ),
            quality_issues=[],
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            path1 = Path(tmpdir) / "report1.json"
            path2 = Path(tmpdir) / "report2.json"

            write_json(report, path1)
            write_json(report, path2)

            with open(path1) as f1, open(path2) as f2:
                content1 = f1.read()
                content2 = f2.read()

            assert content1 == content2, "Output should be deterministic"

    def test_write_json_creates_parent_directory(self) -> None:
        """Test that write_json creates parent directories if missing."""
        from src.models.report import (
            ReconciliationReport,
            ReportMetadata,
            ReportSummary,
            ResultsByStatus,
        )
        from src.services.reporter import write_json

        report = ReconciliationReport(
            metadata=ReportMetadata(
                generated_at="2026-01-02T10:30:00Z",
                snapshot_1_path="s1.csv",
                snapshot_2_path="s2.csv",
                snapshot_1_rows=10,
                snapshot_2_rows=10,
                snapshot_1_valid_rows=10,
                snapshot_2_valid_rows=10,
            ),
            summary=ReportSummary(
                total_items_compared=0,
                unchanged=0,
                quantity_changed=0,
                added=0,
                removed=0,
                quality_issues_count=0,
                quality_issues_by_severity={"error": 0, "warning": 0, "info": 0},
            ),
            results=ResultsByStatus(
                unchanged=[],
                quantity_changed=[],
                added=[],
                removed=[],
            ),
            quality_issues=[],
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "nested" / "output" / "report.json"
            write_json(report, output_path)

            assert output_path.exists()

    def test_write_json_with_quality_issues(self) -> None:
        """Test that quality issues are correctly serialized."""
        from src.models.report import (
            ReconciliationReport,
            ReportMetadata,
            ReportSummary,
            ResultsByStatus,
        )
        from src.services.reporter import write_json

        report = ReconciliationReport(
            metadata=ReportMetadata(
                generated_at="2026-01-02T10:30:00Z",
                snapshot_1_path="s1.csv",
                snapshot_2_path="s2.csv",
                snapshot_1_rows=10,
                snapshot_2_rows=10,
                snapshot_1_valid_rows=10,
                snapshot_2_valid_rows=10,
            ),
            summary=ReportSummary(
                total_items_compared=0,
                unchanged=0,
                quantity_changed=0,
                added=0,
                removed=0,
                quality_issues_count=1,
                quality_issues_by_severity={"error": 1, "warning": 0, "info": 0},
            ),
            results=ResultsByStatus(
                unchanged=[],
                quantity_changed=[],
                added=[],
                removed=[],
            ),
            quality_issues=[
                DataQualityIssue(
                    issue_type="duplicate_key",
                    severity="error",
                    source_file="snapshot_1",
                    description="Duplicate found",
                    row_number=5,
                    field="sku",
                    original_value="SKU-001",
                )
            ],
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "report.json"
            write_json(report, output_path)

            with open(output_path) as f:
                loaded = json.load(f)

            assert len(loaded["quality_issues"]) == 1
            assert loaded["quality_issues"][0]["issue_type"] == "duplicate_key"
            assert loaded["quality_issues"][0]["row_number"] == 5

    def test_write_json_with_reconciliation_results(self) -> None:
        """Test that reconciliation results are correctly serialized."""
        from src.models.report import (
            ReconciliationReport,
            ReportMetadata,
            ReportSummary,
            ResultsByStatus,
        )
        from src.services.reporter import write_json

        report = ReconciliationReport(
            metadata=ReportMetadata(
                generated_at="2026-01-02T10:30:00Z",
                snapshot_1_path="s1.csv",
                snapshot_2_path="s2.csv",
                snapshot_1_rows=10,
                snapshot_2_rows=10,
                snapshot_1_valid_rows=10,
                snapshot_2_valid_rows=10,
            ),
            summary=ReportSummary(
                total_items_compared=1,
                unchanged=0,
                quantity_changed=1,
                added=0,
                removed=0,
                quality_issues_count=0,
                quality_issues_by_severity={"error": 0, "warning": 0, "info": 0},
            ),
            results=ResultsByStatus(
                unchanged=[],
                quantity_changed=[
                    ReconciliationResult(
                        sku="SKU-001",
                        location="Warehouse A",
                        status="quantity_changed",
                        old_quantity=100,
                        new_quantity=95,
                        quantity_delta=-5,
                        old_name="Widget",
                        new_name="Widget",
                    )
                ],
                added=[],
                removed=[],
            ),
            quality_issues=[],
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "report.json"
            write_json(report, output_path)

            with open(output_path) as f:
                loaded = json.load(f)

            assert len(loaded["results"]["quantity_changed"]) == 1
            assert loaded["results"]["quantity_changed"][0]["quantity_delta"] == -5


class TestJsonSchemaCompliance:
    """Tests for JSON schema compliance."""

    def test_output_matches_schema_structure(self) -> None:
        """Test that generated output has all required schema fields."""
        from src.models.report import (
            ReconciliationReport,
            ReportMetadata,
            ReportSummary,
            ResultsByStatus,
        )
        from src.services.reporter import write_json

        report = ReconciliationReport(
            metadata=ReportMetadata(
                generated_at="2026-01-02T10:30:00Z",
                snapshot_1_path="s1.csv",
                snapshot_2_path="s2.csv",
                snapshot_1_rows=10,
                snapshot_2_rows=10,
                snapshot_1_valid_rows=8,
                snapshot_2_valid_rows=10,
            ),
            summary=ReportSummary(
                total_items_compared=5,
                unchanged=2,
                quantity_changed=1,
                added=1,
                removed=1,
                quality_issues_count=2,
                quality_issues_by_severity={"error": 1, "warning": 1, "info": 0},
            ),
            results=ResultsByStatus(
                unchanged=[
                    ReconciliationResult(
                        sku="SKU-001",
                        location="Warehouse A",
                        status="unchanged",
                        old_quantity=100,
                        new_quantity=100,
                        quantity_delta=0,
                    )
                ],
                quantity_changed=[],
                added=[],
                removed=[],
            ),
            quality_issues=[
                DataQualityIssue(
                    issue_type="duplicate_key",
                    severity="error",
                    source_file="snapshot_1",
                    description="Test issue",
                )
            ],
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "report.json"
            write_json(report, output_path)

            with open(output_path) as f:
                loaded = json.load(f)

            # Check top-level required fields
            assert "metadata" in loaded
            assert "summary" in loaded
            assert "results" in loaded
            assert "quality_issues" in loaded

            # Check metadata required fields
            assert "generated_at" in loaded["metadata"]
            assert "snapshot_1_path" in loaded["metadata"]
            assert "snapshot_2_path" in loaded["metadata"]
            assert "snapshot_1_rows" in loaded["metadata"]
            assert "snapshot_2_rows" in loaded["metadata"]
            assert "snapshot_1_valid_rows" in loaded["metadata"]
            assert "snapshot_2_valid_rows" in loaded["metadata"]

            # Check summary required fields
            assert "total_items_compared" in loaded["summary"]
            assert "unchanged" in loaded["summary"]
            assert "quantity_changed" in loaded["summary"]
            assert "added" in loaded["summary"]
            assert "removed" in loaded["summary"]
            assert "quality_issues_count" in loaded["summary"]
            assert "quality_issues_by_severity" in loaded["summary"]

            # Check results required fields
            assert "unchanged" in loaded["results"]
            assert "quantity_changed" in loaded["results"]
            assert "added" in loaded["results"]
            assert "removed" in loaded["results"]
