"""Unit tests for reconciler service."""

import pandas as pd
import pytest


class TestFindDuplicates:
    """Tests for find_duplicates() function."""

    def test_no_duplicates_returns_empty(self) -> None:
        """No duplicates should return empty DataFrame."""
        from src.services.reconciler import find_duplicates

        df = pd.DataFrame({
            "sku": ["SKU-001", "SKU-002", "SKU-003"],
            "location": ["Warehouse A", "Warehouse A", "Warehouse B"],
            "quantity": [100, 50, 200],
        })
        result = find_duplicates(df, ["sku", "location"])
        assert len(result) == 0

    def test_single_duplicate_returns_both_rows(self) -> None:
        """Single duplicate key should return both occurrences."""
        from src.services.reconciler import find_duplicates

        df = pd.DataFrame({
            "sku": ["SKU-001", "SKU-001", "SKU-002"],
            "location": ["Warehouse A", "Warehouse A", "Warehouse B"],
            "quantity": [100, 150, 200],
        })
        result = find_duplicates(df, ["sku", "location"])
        assert len(result) == 2
        assert all(result["sku"] == "SKU-001")

    def test_multiple_duplicates_returns_all(self) -> None:
        """Multiple duplicate keys should return all occurrences."""
        from src.services.reconciler import find_duplicates

        df = pd.DataFrame({
            "sku": ["SKU-001", "SKU-001", "SKU-002", "SKU-002", "SKU-002"],
            "location": ["Warehouse A", "Warehouse A", "Warehouse B", "Warehouse B", "Warehouse B"],
            "quantity": [100, 150, 200, 250, 300],
        })
        result = find_duplicates(df, ["sku", "location"])
        assert len(result) == 5

    def test_same_sku_different_location_not_duplicate(self) -> None:
        """Same SKU in different locations is not a duplicate."""
        from src.services.reconciler import find_duplicates

        df = pd.DataFrame({
            "sku": ["SKU-001", "SKU-001"],
            "location": ["Warehouse A", "Warehouse B"],
            "quantity": [100, 150],
        })
        result = find_duplicates(df, ["sku", "location"])
        assert len(result) == 0


class TestReconcile:
    """Tests for reconcile() function."""

    def test_unchanged_items(self) -> None:
        """Items with same quantity in both snapshots are unchanged."""
        from src.services.reconciler import reconcile

        df1 = pd.DataFrame({
            "sku": ["SKU-001"],
            "name": ["Widget A"],
            "quantity": [100],
            "location": ["Warehouse A"],
        })
        df2 = pd.DataFrame({
            "sku": ["SKU-001"],
            "name": ["Widget A"],
            "quantity": [100],
            "location": ["Warehouse A"],
        })
        results = reconcile(df1, df2)

        unchanged = [r for r in results if r.status == "unchanged"]
        assert len(unchanged) == 1
        assert unchanged[0].sku == "SKU-001"
        assert unchanged[0].old_quantity == 100
        assert unchanged[0].new_quantity == 100
        assert unchanged[0].quantity_delta == 0

    def test_quantity_changed_items(self) -> None:
        """Items with different quantities are marked as changed."""
        from src.services.reconciler import reconcile

        df1 = pd.DataFrame({
            "sku": ["SKU-001"],
            "name": ["Widget A"],
            "quantity": [100],
            "location": ["Warehouse A"],
        })
        df2 = pd.DataFrame({
            "sku": ["SKU-001"],
            "name": ["Widget A"],
            "quantity": [80],
            "location": ["Warehouse A"],
        })
        results = reconcile(df1, df2)

        changed = [r for r in results if r.status == "quantity_changed"]
        assert len(changed) == 1
        assert changed[0].sku == "SKU-001"
        assert changed[0].old_quantity == 100
        assert changed[0].new_quantity == 80
        assert changed[0].quantity_delta == -20

    def test_added_items(self) -> None:
        """Items only in snapshot_2 are marked as added."""
        from src.services.reconciler import reconcile

        df1 = pd.DataFrame({
            "sku": ["SKU-001"],
            "name": ["Widget A"],
            "quantity": [100],
            "location": ["Warehouse A"],
        })
        df2 = pd.DataFrame({
            "sku": ["SKU-001", "SKU-002"],
            "name": ["Widget A", "Widget B"],
            "quantity": [100, 50],
            "location": ["Warehouse A", "Warehouse B"],
        })
        results = reconcile(df1, df2)

        added = [r for r in results if r.status == "added"]
        assert len(added) == 1
        assert added[0].sku == "SKU-002"
        assert added[0].old_quantity is None
        assert added[0].new_quantity == 50
        assert added[0].quantity_delta is None

    def test_removed_items(self) -> None:
        """Items only in snapshot_1 are marked as removed."""
        from src.services.reconciler import reconcile

        df1 = pd.DataFrame({
            "sku": ["SKU-001", "SKU-002"],
            "name": ["Widget A", "Widget B"],
            "quantity": [100, 50],
            "location": ["Warehouse A", "Warehouse B"],
        })
        df2 = pd.DataFrame({
            "sku": ["SKU-001"],
            "name": ["Widget A"],
            "quantity": [100],
            "location": ["Warehouse A"],
        })
        results = reconcile(df1, df2)

        removed = [r for r in results if r.status == "removed"]
        assert len(removed) == 1
        assert removed[0].sku == "SKU-002"
        assert removed[0].old_quantity == 50
        assert removed[0].new_quantity is None
        assert removed[0].quantity_delta is None

    def test_mixed_reconciliation(self) -> None:
        """Test a mix of unchanged, changed, added, and removed items."""
        from src.services.reconciler import reconcile

        df1 = pd.DataFrame({
            "sku": ["SKU-001", "SKU-002", "SKU-003"],
            "name": ["Widget A", "Widget B", "Gadget Pro"],
            "quantity": [100, 50, 200],
            "location": ["Warehouse A", "Warehouse A", "Warehouse B"],
        })
        df2 = pd.DataFrame({
            "sku": ["SKU-001", "SKU-002", "SKU-004"],
            "name": ["Widget A", "Widget B Updated", "Power Supply"],
            "quantity": [100, 75, 40],
            "location": ["Warehouse A", "Warehouse A", "Warehouse C"],
        })
        results = reconcile(df1, df2)

        unchanged = [r for r in results if r.status == "unchanged"]
        changed = [r for r in results if r.status == "quantity_changed"]
        added = [r for r in results if r.status == "added"]
        removed = [r for r in results if r.status == "removed"]

        assert len(unchanged) == 1
        assert len(changed) == 1
        assert len(added) == 1
        assert len(removed) == 1

        # Verify specific items
        assert unchanged[0].sku == "SKU-001"
        assert changed[0].sku == "SKU-002"
        assert changed[0].quantity_delta == 25
        assert added[0].sku == "SKU-004"
        assert removed[0].sku == "SKU-003"

    def test_name_tracking(self) -> None:
        """Test that old_name and new_name are tracked correctly."""
        from src.services.reconciler import reconcile

        df1 = pd.DataFrame({
            "sku": ["SKU-001"],
            "name": ["Old Name"],
            "quantity": [100],
            "location": ["Warehouse A"],
        })
        df2 = pd.DataFrame({
            "sku": ["SKU-001"],
            "name": ["New Name"],
            "quantity": [100],
            "location": ["Warehouse A"],
        })
        results = reconcile(df1, df2)

        assert len(results) == 1
        assert results[0].old_name == "Old Name"
        assert results[0].new_name == "New Name"

    def test_empty_dataframes(self) -> None:
        """Test reconciliation with empty DataFrames."""
        from src.services.reconciler import reconcile

        df_empty = pd.DataFrame(columns=["sku", "name", "quantity", "location"])
        df_with_data = pd.DataFrame({
            "sku": ["SKU-001"],
            "name": ["Widget A"],
            "quantity": [100],
            "location": ["Warehouse A"],
        })

        # Empty snapshot_1 - all items should be "added"
        results1 = reconcile(df_empty, df_with_data)
        assert len(results1) == 1
        assert results1[0].status == "added"

        # Empty snapshot_2 - all items should be "removed"
        results2 = reconcile(df_with_data, df_empty)
        assert len(results2) == 1
        assert results2[0].status == "removed"
