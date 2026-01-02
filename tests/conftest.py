"""Shared pytest fixtures for inventory reconciliation tests."""

from pathlib import Path

import pandas as pd
import pytest


@pytest.fixture
def fixtures_dir() -> Path:
    """Return the path to the test fixtures directory."""
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def sample_snapshot_1(fixtures_dir: Path) -> Path:
    """Return path to sample snapshot 1 fixture."""
    return fixtures_dir / "snapshot_clean.csv"


@pytest.fixture
def sample_snapshot_2(fixtures_dir: Path) -> Path:
    """Return path to sample snapshot 2 fixture."""
    return fixtures_dir / "snapshot_with_changes.csv"


@pytest.fixture
def snapshot_with_issues(fixtures_dir: Path) -> Path:
    """Return path to snapshot with quality issues fixture."""
    return fixtures_dir / "snapshot_with_issues.csv"


@pytest.fixture
def clean_dataframe() -> pd.DataFrame:
    """Return a clean DataFrame for testing."""
    return pd.DataFrame({
        "sku": ["SKU-001", "SKU-002", "SKU-003"],
        "name": ["Widget A", "Widget B", "Gadget Pro"],
        "quantity": [100, 50, 200],
        "location": ["Warehouse A", "Warehouse A", "Warehouse B"],
        "last_counted": ["2024-01-08", "2024-01-08", "2024-01-08"],
    })


@pytest.fixture
def dataframe_with_issues() -> pd.DataFrame:
    """Return a DataFrame with quality issues for testing."""
    return pd.DataFrame({
        "sku": ["SKU-001", "SKU001", "sku-002", "SKU-003", "SKU-003"],
        "name": [" Widget A ", "Widget B", "Gadget Pro", "Item X", "Item X"],
        "quantity": [100, -5, 50, 200, 150],
        "location": ["Warehouse A", "Warehouse A", "Warehouse B", "Warehouse C", "Warehouse C"],
        "last_counted": ["2024-01-08", "01/08/2024", "2024-01-08", "2024-01-08", "2024-01-08"],
    })
