"""Integration tests for full reconciliation flow."""

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
        df1, mapped1, missing1 = load_snapshot(sample_snapshot_1)
        df2, mapped2, missing2 = load_snapshot(sample_snapshot_2)

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
        df, mapped, missing = load_snapshot(snapshot_path)

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
