"""Integration tests for full reconciliation flow."""

import json
import tempfile
from pathlib import Path

import pandas as pd
import pytest


class TestBasicReconciliationFlow:
    """Integration tests for basic reconciliation (User Story 1)."""

    def test_full_reconciliation_with_fixture_files(
        self, sample_snapshot_1: Path, sample_snapshot_2: Path
    ) -> None:
        """Test complete reconciliation flow with fixture files."""
        from src.services.loader import load_snapshot
        from src.services.normalizer import normalize_dataframe
        from src.services.reconciler import reconcile

        # Load snapshots
        df1, mapped1, missing1, _ = load_snapshot(sample_snapshot_1)
        df2, mapped2, missing2, _ = load_snapshot(sample_snapshot_2)

        assert len(missing1) == 0, f"Missing columns in snapshot_1: {missing1}"
        assert len(missing2) == 0, f"Missing columns in snapshot_2: {missing2}"

        # Normalize data
        df1_norm, _ = normalize_dataframe(df1)
        df2_norm, _ = normalize_dataframe(df2)

        # Reconcile
        results = reconcile(df1_norm, df2_norm)

        # Verify we get results
        assert len(results) > 0

        # Categorize results
        unchanged = [r for r in results if r.status == "unchanged"]
        changed = [r for r in results if r.status == "quantity_changed"]
        added = [r for r in results if r.status == "added"]
        removed = [r for r in results if r.status == "removed"]

        # Based on fixture files:
        # snapshot_clean.csv: SKU-001 (100), SKU-002 (50), SKU-003 (200), SKU-004 (75), SKU-005 (500)
        # snapshot_with_changes.csv: SKU-001 (95), SKU-002 (50), SKU-003 (180), SKU-005 (480), SKU-006 (40)
        # Expected:
        # - unchanged: SKU-002 (qty 50 in both)
        # - changed: SKU-001 (100->95), SKU-003 (200->180), SKU-005 (500->480)
        # - added: SKU-006 (new item)
        # - removed: SKU-004 (only in snapshot_1)

        assert len(unchanged) == 1, f"Expected 1 unchanged, got {len(unchanged)}"
        assert len(changed) == 3, f"Expected 3 changed, got {len(changed)}"
        assert len(added) == 1, f"Expected 1 added, got {len(added)}"
        assert len(removed) == 1, f"Expected 1 removed, got {len(removed)}"

        # Verify specific items
        unchanged_skus = {r.sku for r in unchanged}
        assert "SKU-002" in unchanged_skus

        changed_skus = {r.sku for r in changed}
        assert "SKU-001" in changed_skus
        assert "SKU-003" in changed_skus
        assert "SKU-005" in changed_skus

        added_skus = {r.sku for r in added}
        assert "SKU-006" in added_skus

        removed_skus = {r.sku for r in removed}
        assert "SKU-004" in removed_skus

    def test_reconciliation_with_column_mapping(
        self, fixtures_dir: Path
    ) -> None:
        """Test reconciliation when column names need mapping."""
        from src.services.loader import load_snapshot
        from src.services.normalizer import normalize_dataframe
        from src.services.reconciler import reconcile

        # snapshot_with_issues.csv uses non-canonical column names
        snapshot_path = fixtures_dir / "snapshot_with_issues.csv"
        df, mapped, missing, _ = load_snapshot(snapshot_path)

        # Should have mapped columns
        assert len(mapped) > 0, "Expected column mapping to occur"
        assert "product_name" in mapped, "Expected product_name to be mapped"

        # After mapping, should have canonical columns
        assert "name" in df.columns
        assert "quantity" in df.columns
        assert "location" in df.columns

    def test_reconciliation_preserves_all_results(self) -> None:
        """Test that reconciliation doesn't lose any items."""
        from src.services.reconciler import reconcile

        df1 = pd.DataFrame({
            "sku": [f"SKU-{i:03d}" for i in range(1, 11)],
            "name": [f"Item {i}" for i in range(1, 11)],
            "quantity": list(range(100, 110)),
            "location": ["Warehouse A"] * 10,
        })
        df2 = pd.DataFrame({
            "sku": [f"SKU-{i:03d}" for i in range(6, 16)],
            "name": [f"Item {i}" for i in range(6, 16)],
            "quantity": list(range(105, 115)),
            "location": ["Warehouse A"] * 10,
        })

        results = reconcile(df1, df2)

        # Should have:
        # - 5 removed (SKU-001 to SKU-005)
        # - 5 items in both (SKU-006 to SKU-010) - some changed, some unchanged
        # - 5 added (SKU-011 to SKU-015)
        removed = [r for r in results if r.status == "removed"]
        added = [r for r in results if r.status == "added"]

        assert len(removed) == 5
        assert len(added) == 5

        # Total unique keys = 15 (5 removed + 5 in both + 5 added)
        assert len(results) == 15

    def test_reconciliation_handles_duplicates(self) -> None:
        """Test that duplicate keys are detected before reconciliation."""
        from src.services.reconciler import find_duplicates

        df_with_dupes = pd.DataFrame({
            "sku": ["SKU-001", "SKU-001", "SKU-002"],
            "name": ["A", "A Updated", "B"],
            "quantity": [100, 150, 50],
            "location": ["Warehouse A", "Warehouse A", "Warehouse B"],
        })

        duplicates = find_duplicates(df_with_dupes, ["sku", "location"])
        assert len(duplicates) == 2, "Should detect both duplicate rows"

        # Filter out duplicates before reconciliation
        dupe_mask = df_with_dupes.duplicated(subset=["sku", "location"], keep=False)
        df_clean = df_with_dupes[~dupe_mask]

        assert len(df_clean) == 1, "Should have 1 non-duplicate row"
        assert df_clean["sku"].iloc[0] == "SKU-002"


class TestJsonOutputGeneration:
    """Integration tests for JSON output generation (User Story 3)."""

    def test_full_flow_generates_valid_json(
        self, sample_snapshot_1: Path, sample_snapshot_2: Path
    ) -> None:
        """Test complete flow generates valid JSON output."""
        from src.models.quality_issue import DataQualityIssue
        from src.services.loader import load_snapshot
        from src.services.normalizer import normalize_dataframe
        from src.services.quality_checker import run_all_checks
        from src.services.reconciler import find_duplicates, reconcile
        from src.services.reporter import build_report, write_json

        # Load and normalize
        df1, mapped1, missing1, float_qty1 = load_snapshot(sample_snapshot_1)
        df2, mapped2, missing2, float_qty2 = load_snapshot(sample_snapshot_2)

        df1_norm, _ = normalize_dataframe(df1)
        df2_norm, _ = normalize_dataframe(df2)

        # Quality checks
        quality_issues = run_all_checks(df1, df2, mapped1, mapped2, missing1, missing2, float_qty1, float_qty2)

        # Filter duplicates
        key_cols = ["sku", "location"]
        dupe_mask1 = df1_norm.duplicated(subset=key_cols, keep=False)
        dupe_mask2 = df2_norm.duplicated(subset=key_cols, keep=False)
        df1_clean = df1_norm[~dupe_mask1]
        df2_clean = df2_norm[~dupe_mask2]

        # Reconcile
        results = reconcile(df1_clean, df2_clean, key_cols)

        # Build report
        report = build_report(
            results=results,
            quality_issues=quality_issues,
            snapshot_1_path=str(sample_snapshot_1),
            snapshot_2_path=str(sample_snapshot_2),
            snapshot_1_rows=len(df1),
            snapshot_2_rows=len(df2),
            snapshot_1_valid_rows=len(df1_clean),
            snapshot_2_valid_rows=len(df2_clean),
        )

        # Write to temp file
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "report.json"
            write_json(report, output_path)

            # Verify file is valid JSON
            with open(output_path) as f:
                loaded = json.load(f)

            # Verify structure
            assert "metadata" in loaded
            assert "summary" in loaded
            assert "results" in loaded
            assert "quality_issues" in loaded

            # Verify counts match
            assert loaded["summary"]["unchanged"] == len(report.results.unchanged)
            assert loaded["summary"]["quantity_changed"] == len(report.results.quantity_changed)
            assert loaded["summary"]["added"] == len(report.results.added)
            assert loaded["summary"]["removed"] == len(report.results.removed)

    def test_json_output_is_deterministic(
        self, sample_snapshot_1: Path, sample_snapshot_2: Path
    ) -> None:
        """Test that running reconciliation twice produces identical JSON output."""
        from src.services.loader import load_snapshot
        from src.services.normalizer import normalize_dataframe
        from src.services.quality_checker import run_all_checks
        from src.services.reconciler import reconcile
        from src.services.reporter import build_report, write_json

        def run_reconciliation() -> str:
            df1, mapped1, missing1, float_qty1 = load_snapshot(sample_snapshot_1)
            df2, mapped2, missing2, float_qty2 = load_snapshot(sample_snapshot_2)

            df1_norm, _ = normalize_dataframe(df1)
            df2_norm, _ = normalize_dataframe(df2)

            quality_issues = run_all_checks(df1, df2, mapped1, mapped2, missing1, missing2, float_qty1, float_qty2)

            key_cols = ["sku", "location"]
            dupe_mask1 = df1_norm.duplicated(subset=key_cols, keep=False)
            dupe_mask2 = df2_norm.duplicated(subset=key_cols, keep=False)
            df1_clean = df1_norm[~dupe_mask1]
            df2_clean = df2_norm[~dupe_mask2]

            results = reconcile(df1_clean, df2_clean, key_cols)

            # Use fixed timestamp for determinism test
            report = build_report(
                results=results,
                quality_issues=quality_issues,
                snapshot_1_path=str(sample_snapshot_1),
                snapshot_2_path=str(sample_snapshot_2),
                snapshot_1_rows=len(df1),
                snapshot_2_rows=len(df2),
                snapshot_1_valid_rows=len(df1_clean),
                snapshot_2_valid_rows=len(df2_clean),
                generated_at="2026-01-02T10:30:00Z",
            )

            with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
                output_path = Path(f.name)

            write_json(report, output_path)
            with open(output_path) as f:
                content = f.read()
            output_path.unlink()
            return content

        output1 = run_reconciliation()
        output2 = run_reconciliation()

        assert output1 == output2, "JSON output should be deterministic"

    def test_json_validates_against_schema(
        self, fixtures_dir: Path, sample_snapshot_1: Path, sample_snapshot_2: Path
    ) -> None:
        """Test that generated JSON validates against the output schema."""
        from src.services.loader import load_snapshot
        from src.services.normalizer import normalize_dataframe
        from src.services.quality_checker import run_all_checks
        from src.services.reconciler import reconcile
        from src.services.reporter import build_report, write_json

        # Load schema
        schema_path = Path(__file__).parent.parent.parent / "specs" / "001-inventory-reconciliation" / "contracts" / "output-schema.json"
        if not schema_path.exists():
            pytest.skip("Schema file not found")

        with open(schema_path) as f:
            schema = json.load(f)

        # Run reconciliation
        df1, mapped1, missing1, float_qty1 = load_snapshot(sample_snapshot_1)
        df2, mapped2, missing2, float_qty2 = load_snapshot(sample_snapshot_2)

        df1_norm, _ = normalize_dataframe(df1)
        df2_norm, _ = normalize_dataframe(df2)

        quality_issues = run_all_checks(df1, df2, mapped1, mapped2, missing1, missing2, float_qty1, float_qty2)

        key_cols = ["sku", "location"]
        dupe_mask1 = df1_norm.duplicated(subset=key_cols, keep=False)
        dupe_mask2 = df2_norm.duplicated(subset=key_cols, keep=False)
        df1_clean = df1_norm[~dupe_mask1]
        df2_clean = df2_norm[~dupe_mask2]

        results = reconcile(df1_clean, df2_clean, key_cols)

        report = build_report(
            results=results,
            quality_issues=quality_issues,
            snapshot_1_path=str(sample_snapshot_1),
            snapshot_2_path=str(sample_snapshot_2),
            snapshot_1_rows=len(df1),
            snapshot_2_rows=len(df2),
            snapshot_1_valid_rows=len(df1_clean),
            snapshot_2_valid_rows=len(df2_clean),
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "report.json"
            write_json(report, output_path)

            with open(output_path) as f:
                report_json = json.load(f)

            # Validate required top-level fields
            for field in ["metadata", "summary", "results", "quality_issues"]:
                assert field in report_json, f"Missing required field: {field}"

            # Validate metadata fields
            for field in schema["properties"]["metadata"]["required"]:
                assert field in report_json["metadata"], f"Missing metadata field: {field}"

            # Validate summary fields
            for field in schema["properties"]["summary"]["required"]:
                assert field in report_json["summary"], f"Missing summary field: {field}"

            # Validate results structure
            for status in ["unchanged", "quantity_changed", "added", "removed"]:
                assert status in report_json["results"], f"Missing results.{status}"
                assert isinstance(report_json["results"][status], list)

    def test_cli_generates_output_file(
        self, sample_snapshot_1: Path, sample_snapshot_2: Path
    ) -> None:
        """Test that CLI generates output file in output/ directory."""
        from src.reconcile import main

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "output"
            output_path = output_dir / "reconciliation_report.json"

            # Run CLI with custom output path
            result = main([
                "--snapshot1", str(sample_snapshot_1),
                "--snapshot2", str(sample_snapshot_2),
                "--output", str(output_path),
                "--quiet",
            ])

            assert result == 0, "CLI should succeed"
            assert output_path.exists(), "Output file should be created"

            # Verify it's valid JSON
            with open(output_path) as f:
                loaded = json.load(f)

            assert "metadata" in loaded
            assert "summary" in loaded
