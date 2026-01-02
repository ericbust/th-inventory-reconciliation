"""Reconciliation service for comparing inventory snapshots."""

from typing import Optional

import pandas as pd

from src.models.reconciliation_result import ReconciliationResult


def find_duplicates(df: pd.DataFrame, key_cols: list[str]) -> pd.DataFrame:
    """Find all rows with duplicate composite keys.

    Returns all rows where the key columns have duplicate values,
    including all occurrences (not just second and subsequent).

    Args:
        df: DataFrame to check for duplicates.
        key_cols: List of column names that form the composite key.

    Returns:
        DataFrame containing all rows with duplicate keys.
    """
    # duplicated with keep=False marks ALL occurrences as duplicates
    return df[df.duplicated(subset=key_cols, keep=False)]


def reconcile(
    df1: pd.DataFrame,
    df2: pd.DataFrame,
    key_cols: Optional[list[str]] = None,
) -> list[ReconciliationResult]:
    """Compare two inventory snapshots and categorize differences.

    Performs an outer merge on the composite key (sku, location) and
    categorizes each item as unchanged, quantity_changed, added, or removed.

    Args:
        df1: First snapshot (older) DataFrame with columns:
             sku, name, quantity, location
        df2: Second snapshot (newer) DataFrame with same columns.
        key_cols: List of columns forming the composite key.
                  Defaults to ["sku", "location"].

    Returns:
        List of ReconciliationResult objects, one per unique key.
    """
    if key_cols is None:
        key_cols = ["sku", "location"]

    # Handle empty DataFrames
    if df1.empty and df2.empty:
        return []

    if df1.empty:
        # All items in df2 are "added"
        return [
            ReconciliationResult(
                sku=row["sku"],
                location=row["location"],
                status="added",
                old_quantity=None,
                new_quantity=int(row["quantity"]),
                quantity_delta=None,
                old_name=None,
                new_name=row.get("name"),
            )
            for _, row in df2.iterrows()
        ]

    if df2.empty:
        # All items in df1 are "removed"
        return [
            ReconciliationResult(
                sku=row["sku"],
                location=row["location"],
                status="removed",
                old_quantity=int(row["quantity"]),
                new_quantity=None,
                quantity_delta=None,
                old_name=row.get("name"),
                new_name=None,
            )
            for _, row in df1.iterrows()
        ]

    # Perform outer merge on key columns
    merged = pd.merge(
        df1,
        df2,
        on=key_cols,
        how="outer",
        suffixes=("_old", "_new"),
        indicator=True,
    )

    results: list[ReconciliationResult] = []

    for _, row in merged.iterrows():
        sku = row["sku"]
        location = row["location"]
        merge_status = row["_merge"]

        if merge_status == "left_only":
            # Item only in snapshot_1 -> removed
            results.append(
                ReconciliationResult(
                    sku=sku,
                    location=location,
                    status="removed",
                    old_quantity=_safe_int(row.get("quantity_old")),
                    new_quantity=None,
                    quantity_delta=None,
                    old_name=row.get("name_old"),
                    new_name=None,
                )
            )
        elif merge_status == "right_only":
            # Item only in snapshot_2 -> added
            results.append(
                ReconciliationResult(
                    sku=sku,
                    location=location,
                    status="added",
                    old_quantity=None,
                    new_quantity=_safe_int(row.get("quantity_new")),
                    quantity_delta=None,
                    old_name=None,
                    new_name=row.get("name_new"),
                )
            )
        else:
            # Item in both snapshots
            old_qty = _safe_int(row.get("quantity_old"))
            new_qty = _safe_int(row.get("quantity_new"))

            if old_qty == new_qty:
                status = "unchanged"
                delta = 0
            else:
                status = "quantity_changed"
                delta = new_qty - old_qty if old_qty is not None and new_qty is not None else None

            results.append(
                ReconciliationResult(
                    sku=sku,
                    location=location,
                    status=status,
                    old_quantity=old_qty,
                    new_quantity=new_qty,
                    quantity_delta=delta,
                    old_name=row.get("name_old"),
                    new_name=row.get("name_new"),
                )
            )

    return results


def _safe_int(value) -> Optional[int]:
    """Safely convert value to int, handling NaN and None."""
    if pd.isna(value):
        return None
    try:
        return int(value)
    except (ValueError, TypeError):
        return None
