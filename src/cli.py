"""Command-line interface for inventory reconciliation."""

import argparse
import sys
from pathlib import Path

from tqdm import tqdm

from src.models.quality_issue import DataQualityIssue
from src.models.reconciliation_result import ReconciliationResult
from src.services.loader import load_snapshot
from src.services.normalizer import normalize_dataframe
from src.services.quality_checker import run_all_checks
from src.services.reconciler import find_duplicates, reconcile
from src.services.reporter import build_report, write_json


def parse_args(args: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments.

    Args:
        args: Command-line arguments. If None, uses sys.argv.

    Returns:
        Parsed arguments namespace.
    """
    parser = argparse.ArgumentParser(
        description="Compare two inventory CSV snapshots and identify changes.",
        prog="python -m src.cli",
    )
    parser.add_argument(
        "--snapshot1",
        "-s1",
        type=str,
        default="data/snapshot_1.csv",
        help="Path to first (older) snapshot CSV file (default: data/snapshot_1.csv)",
    )
    parser.add_argument(
        "--snapshot2",
        "-s2",
        type=str,
        default="data/snapshot_2.csv",
        help="Path to second (newer) snapshot CSV file (default: data/snapshot_2.csv)",
    )
    parser.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        help="Suppress progress bar output",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        default="output/reconciliation_report.json",
        help="Path to output JSON file (default: output/reconciliation_report.json)",
    )

    return parser.parse_args(args)


def print_summary(
    results: list[ReconciliationResult],
    quality_issues: list[DataQualityIssue],
    snapshot1_path: str,
    snapshot2_path: str,
    snapshot1_rows: int,
    snapshot2_rows: int,
) -> None:
    """Print reconciliation summary to console.

    Args:
        results: List of reconciliation results.
        quality_issues: List of data quality issues.
        snapshot1_path: Path to first snapshot file.
        snapshot2_path: Path to second snapshot file.
        snapshot1_rows: Number of rows in first snapshot.
        snapshot2_rows: Number of rows in second snapshot.
    """
    # Count by status
    unchanged = sum(1 for r in results if r.status == "unchanged")
    changed = sum(1 for r in results if r.status == "quantity_changed")
    added = sum(1 for r in results if r.status == "added")
    removed = sum(1 for r in results if r.status == "removed")

    # Count quality issues by severity
    errors = sum(1 for i in quality_issues if i.severity == "error")
    warnings = sum(1 for i in quality_issues if i.severity == "warning")
    infos = sum(1 for i in quality_issues if i.severity == "info")

    print()
    print("=== Reconciliation Summary ===")
    print(f"Snapshot 1: {snapshot1_path} ({snapshot1_rows} rows)")
    print(f"Snapshot 2: {snapshot2_path} ({snapshot2_rows} rows)")
    print()
    print("Results:")
    print(f"  Unchanged:        {unchanged:>5}")
    print(f"  Quantity Changed: {changed:>5}")
    print(f"  Added:            {added:>5}")
    print(f"  Removed:          {removed:>5}")
    print()
    print(f"Quality Issues: {len(quality_issues)} ({errors} errors, {warnings} warnings, {infos} info)")


def main(args: list[str] | None = None) -> int:
    """Main entry point for CLI.

    Args:
        args: Command-line arguments. If None, uses sys.argv.

    Returns:
        Exit code (0 for success, non-zero for errors).
    """
    parsed_args = parse_args(args)
    snapshot1_path = parsed_args.snapshot1
    snapshot2_path = parsed_args.snapshot2
    quiet = parsed_args.quiet
    output_path = Path(parsed_args.output)

    # Check that files exist
    if not Path(snapshot1_path).exists():
        print(f"Error: Snapshot 1 not found: {snapshot1_path}", file=sys.stderr)
        return 1

    if not Path(snapshot2_path).exists():
        print(f"Error: Snapshot 2 not found: {snapshot2_path}", file=sys.stderr)
        return 1

    # Progress bar with 7 steps (added JSON output)
    steps = [
        "Loading snapshot 1",
        "Loading snapshot 2",
        "Normalizing data",
        "Checking quality",
        "Detecting duplicates",
        "Reconciling",
        "Writing output",
    ]

    if quiet:
        pbar = None
    else:
        pbar = tqdm(total=len(steps), desc="Reconciling", unit="step")

    def update_progress(description: str) -> None:
        if pbar:
            pbar.set_description(description)
            pbar.update(1)

    try:
        # Step 1: Load snapshot 1
        update_progress("Loading snapshot 1")
        df1, mapped1, missing1 = load_snapshot(snapshot1_path)
        snapshot1_rows = len(df1)

        if missing1:
            print(f"Error: Missing columns in {snapshot1_path}: {missing1}", file=sys.stderr)
            return 1

        # Step 2: Load snapshot 2
        update_progress("Loading snapshot 2")
        df2, mapped2, missing2 = load_snapshot(snapshot2_path)
        snapshot2_rows = len(df2)

        if missing2:
            print(f"Error: Missing columns in {snapshot2_path}: {missing2}", file=sys.stderr)
            return 1

        # Step 3: Normalize data
        update_progress("Normalizing data")
        df1_norm, normalizations1 = normalize_dataframe(df1)
        df2_norm, normalizations2 = normalize_dataframe(df2)

        # Step 4: Check quality (on raw data before normalization for accurate reporting)
        update_progress("Checking quality")
        quality_issues = run_all_checks(
            df1, df2,
            mapped1, mapped2,
            missing1, missing2,
        )

        # Step 5: Detect and filter duplicates
        update_progress("Detecting duplicates")
        key_cols = ["sku", "location"]
        dupes1 = find_duplicates(df1_norm, key_cols)
        dupes2 = find_duplicates(df2_norm, key_cols)

        # Filter out duplicates for reconciliation
        if not dupes1.empty:
            dupe_mask1 = df1_norm.duplicated(subset=key_cols, keep=False)
            df1_clean = df1_norm[~dupe_mask1]
        else:
            df1_clean = df1_norm

        if not dupes2.empty:
            dupe_mask2 = df2_norm.duplicated(subset=key_cols, keep=False)
            df2_clean = df2_norm[~dupe_mask2]
        else:
            df2_clean = df2_norm

        # Step 6: Reconcile
        update_progress("Reconciling")
        results = reconcile(df1_clean, df2_clean, key_cols)

        # Step 7: Write JSON output
        update_progress("Writing output")
        report = build_report(
            results=results,
            quality_issues=quality_issues,
            snapshot_1_path=snapshot1_path,
            snapshot_2_path=snapshot2_path,
            snapshot_1_rows=snapshot1_rows,
            snapshot_2_rows=snapshot2_rows,
            snapshot_1_valid_rows=len(df1_clean),
            snapshot_2_valid_rows=len(df2_clean),
        )
        write_json(report, output_path)

    finally:
        if pbar:
            pbar.close()

    # Print summary
    print_summary(
        results,
        quality_issues,
        snapshot1_path,
        snapshot2_path,
        snapshot1_rows,
        snapshot2_rows,
    )
    print()
    print(f"Output written to: {output_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
