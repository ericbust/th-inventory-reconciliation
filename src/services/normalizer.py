"""Data normalization service for inventory records."""

import re

import pandas as pd


def normalize_sku(sku: str) -> str:
    """Normalize SKU to uppercase with hyphen format: SKU-NNN.

    Handles variations like:
    - SKU001 -> SKU-001 (missing hyphen)
    - sku-001 -> SKU-001 (lowercase)
    - sku001 -> SKU-001 (both)

    Args:
        sku: Raw SKU string.

    Returns:
        Normalized SKU in format SKU-NNN.
    """
    if pd.isna(sku):
        return ""

    # Strip whitespace and convert to uppercase
    clean = str(sku).strip().upper()

    # Insert hyphen if missing: SKU001 -> SKU-001
    if re.match(r"^SKU\d{3}$", clean):
        clean = f"{clean[:3]}-{clean[3:]}"

    return clean


def normalize_name(name: str) -> str:
    """Normalize product name by trimming whitespace.

    Args:
        name: Raw product name string.

    Returns:
        Name with leading/trailing whitespace removed.
    """
    if pd.isna(name):
        return ""

    return str(name).strip()


def normalize_location(location: str) -> str:
    """Normalize location by trimming whitespace.

    Args:
        location: Raw location string.

    Returns:
        Location with leading/trailing whitespace removed.
    """
    if pd.isna(location):
        return ""

    return str(location).strip()


def normalize_dataframe(df: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, list[int]]]:
    """Apply all normalization rules to DataFrame.

    Normalizes SKU, name, and location columns. Tracks which rows required
    normalization for quality reporting.

    Args:
        df: DataFrame with columns: sku, name, quantity, location, last_counted.

    Returns:
        Tuple containing:
        - DataFrame with normalized values
        - Dict mapping normalization types to row indices that required it
          Keys: 'sku_normalized', 'name_trimmed', 'location_trimmed'
    """
    result = df.copy()
    normalizations: dict[str, list[int]] = {
        "sku_normalized": [],
        "name_trimmed": [],
        "location_trimmed": [],
    }

    # Normalize SKU column
    if "sku" in result.columns:
        original_skus = result["sku"].astype(str)
        result["sku"] = result["sku"].apply(normalize_sku)

        # Track rows where SKU changed
        for idx in result.index:
            orig = str(original_skus.loc[idx]).strip()
            normalized = result.loc[idx, "sku"]
            if orig.upper() != normalized or orig != normalized:
                normalizations["sku_normalized"].append(int(idx))

    # Normalize name column
    if "name" in result.columns:
        original_names = result["name"].astype(str)
        result["name"] = result["name"].apply(normalize_name)

        # Track rows where name changed (whitespace trimmed)
        for idx in result.index:
            orig = str(original_names.loc[idx])
            normalized = result.loc[idx, "name"]
            if orig != normalized:
                normalizations["name_trimmed"].append(int(idx))

    # Normalize location column
    if "location" in result.columns:
        original_locations = result["location"].astype(str)
        result["location"] = result["location"].apply(normalize_location)

        # Track rows where location changed
        for idx in result.index:
            orig = str(original_locations.loc[idx])
            normalized = result.loc[idx, "location"]
            if orig != normalized:
                normalizations["location_trimmed"].append(int(idx))

    # Coerce quantity to int
    if "quantity" in result.columns:
        result["quantity"] = pd.to_numeric(result["quantity"], errors="coerce").fillna(0).astype(int)

    return result, normalizations
