# Data Model: Inventory Reconciliation

**Date**: 2026-01-02
**Branch**: 001-inventory-reconciliation

## Entities

### InventoryItem

Represents a single inventory record from a snapshot CSV file.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| sku | str | Required, format `SKU-NNN` after normalization | Stock keeping unit identifier |
| name | str | Required, non-empty after trim | Product name |
| quantity | int | Required, >= 0 (negative flagged as error) | Stock count |
| location | str | Required, one of known warehouses | Warehouse identifier |
| last_counted | str | Required | Date of last inventory count |

**Natural Key**: `(sku, location)` - composite key for matching between snapshots

**Normalization Rules**:
- `sku`: Uppercase, insert hyphen if missing (SKU001 → SKU-001)
- `name`: Strip leading/trailing whitespace
- `quantity`: Coerce to int (floats like 70.0 → 70)
- `location`: Strip whitespace

### ReconciliationResult

Represents the comparison outcome for a single inventory item.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| sku | str | Required | Normalized SKU |
| location | str | Required | Warehouse |
| status | str | Enum: unchanged, quantity_changed, added, removed | Reconciliation category |
| old_quantity | int | None | Quantity in snapshot_1 (null if added) |
| new_quantity | int | None | Quantity in snapshot_2 (null if removed) |
| quantity_delta | int | None | new_quantity - old_quantity (null if added/removed) |
| old_name | str | None | Product name in snapshot_1 |
| new_name | str | None | Product name in snapshot_2 |

**Status Definitions**:
- `unchanged`: Item exists in both snapshots with identical quantity
- `quantity_changed`: Item exists in both snapshots with different quantity
- `added`: Item exists only in snapshot_2
- `removed`: Item exists only in snapshot_1

### DataQualityIssue

Represents a detected data quality problem.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| issue_type | str | Enum (see below) | Category of quality issue |
| severity | str | Enum: error, warning, info | Impact level |
| source_file | str | Required | Which snapshot file (1 or 2) |
| row_number | int | None | CSV row number (1-indexed, excluding header) |
| field | str | None | Affected column name |
| original_value | str | None | Value as it appeared in source |
| normalized_value | str | None | Value after normalization (if applicable) |
| description | str | Required | Human-readable explanation |

**Issue Types**:

| Type | Severity | Description |
|------|----------|-------------|
| `duplicate_key` | error | Same SKU+Warehouse appears multiple times |
| `negative_quantity` | error | Quantity < 0 |
| `column_name_mismatch` | info | Column names differ from canonical names |
| `sku_format_normalized` | warning | SKU required normalization (case, hyphen) |
| `whitespace_trimmed` | warning | Leading/trailing whitespace removed |
| `date_format_inconsistent` | warning | Date format differs from ISO standard |
| `name_drift` | warning | Product name changed between snapshots for same SKU |
| `empty_file` | error | Snapshot file contains no data rows |
| `missing_required_column` | error | Required column not found (even after mapping) |

### ReconciliationReport

Aggregate output structure containing all results and metadata.

| Field | Type | Description |
|-------|------|-------------|
| metadata | ReportMetadata | Execution context |
| summary | ReportSummary | Aggregate counts |
| results | ResultsByStatus | Reconciliation results grouped by status |
| quality_issues | list[DataQualityIssue] | All detected quality issues |

### ReportMetadata (nested)

| Field | Type | Description |
|-------|------|-------------|
| generated_at | str | ISO 8601 timestamp of report generation |
| snapshot_1_path | str | Path to first snapshot file |
| snapshot_2_path | str | Path to second snapshot file |
| snapshot_1_rows | int | Total rows in snapshot_1 (before filtering) |
| snapshot_2_rows | int | Total rows in snapshot_2 (before filtering) |
| snapshot_1_valid_rows | int | Rows after excluding duplicates |
| snapshot_2_valid_rows | int | Rows after excluding duplicates |

### ReportSummary (nested)

| Field | Type | Description |
|-------|------|-------------|
| total_items_compared | int | Count of unique keys across both snapshots |
| unchanged | int | Count of items with no quantity change |
| quantity_changed | int | Count of items with quantity change |
| added | int | Count of items only in snapshot_2 |
| removed | int | Count of items only in snapshot_1 |
| quality_issues_count | int | Total quality issues detected |
| quality_issues_by_severity | dict[str, int] | Breakdown by error/warning/info |

### ResultsByStatus (nested)

| Field | Type | Description |
|-------|------|-------------|
| unchanged | list[ReconciliationResult] | Items with identical quantities |
| quantity_changed | list[ReconciliationResult] | Items with different quantities |
| added | list[ReconciliationResult] | Items only in snapshot_2 |
| removed | list[ReconciliationResult] | Items only in snapshot_1 |

## Relationships

```text
┌─────────────────────┐
│ ReconciliationReport│
└─────────┬───────────┘
          │
          ├──────────────────┬────────────────────┐
          ▼                  ▼                    ▼
┌─────────────────┐  ┌─────────────────┐  ┌──────────────────┐
│ ReportMetadata  │  │ ReportSummary   │  │ ResultsByStatus  │
└─────────────────┘  └─────────────────┘  └────────┬─────────┘
                                                   │
                                                   ▼
                                          ┌────────────────────┐
                                          │ReconciliationResult│ (many)
                                          └────────────────────┘

┌─────────────────────┐
│ ReconciliationReport│
└─────────┬───────────┘
          │
          ▼
┌──────────────────┐
│ DataQualityIssue │ (many)
└──────────────────┘
```

## State Transitions

### Item Reconciliation State

```text
                  ┌─────────────┐
                  │ Input CSVs  │
                  └──────┬──────┘
                         │
                         ▼
                  ┌─────────────┐
                  │ Load & Parse│
                  └──────┬──────┘
                         │
            ┌────────────┼────────────┐
            ▼            ▼            ▼
     ┌──────────┐ ┌───────────┐ ┌──────────┐
     │ Valid    │ │ Duplicate │ │ Invalid  │
     │ (unique) │ │ (flagged) │ │ (flagged)│
     └────┬─────┘ └───────────┘ └──────────┘
          │           │              │
          │           └──────────────┘
          │                 │
          │                 ▼
          │         ┌─────────────────┐
          │         │ Quality Issues  │
          │         └─────────────────┘
          │
          ▼
   ┌─────────────┐
   │ Reconcile   │
   └──────┬──────┘
          │
   ┌──────┴──────┬──────────────┬──────────────┐
   ▼             ▼              ▼              ▼
┌─────────┐ ┌──────────┐ ┌─────────┐ ┌─────────┐
│unchanged│ │qty_changed│ │ added   │ │ removed │
└─────────┘ └──────────┘ └─────────┘ └─────────┘
```

## Column Mapping

Canonical column names and their known variations:

| Canonical | Variations | Notes |
|-----------|------------|-------|
| sku | sku | Always lowercase in source |
| name | name, product_name | snapshot_2 uses product_name |
| quantity | quantity, qty | snapshot_2 uses qty |
| location | location, warehouse | snapshot_2 uses warehouse |
| last_counted | last_counted, updated_at | snapshot_2 uses updated_at |

Mapping is applied at load time with quality issue flagged if non-canonical
names are detected.
