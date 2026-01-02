# Input Schema: Inventory Snapshots

This document describes the expected format for input CSV files.

## CSV Format

Both `snapshot_1.csv` and `snapshot_2.csv` must be valid CSV files with:
- Header row as first line
- Comma-separated values
- UTF-8 encoding

## Canonical Column Schema

| Column | Type | Required | Description |
|--------|------|----------|-------------|
| sku | string | Yes | Stock keeping unit identifier |
| name | string | Yes | Product name |
| quantity | integer | Yes | Stock count (should be >= 0) |
| location | string | Yes | Warehouse identifier |
| last_counted | string | Yes | Date of last inventory count |

## Known Column Name Variations

The system accepts these alternative column names and maps them to canonical
names:

| Canonical | Accepted Variations |
|-----------|---------------------|
| name | product_name |
| quantity | qty |
| location | warehouse |
| last_counted | updated_at |

When non-canonical names are detected, a `column_name_mismatch` quality issue
is logged (severity: info) and processing continues.

## Data Quality Rules

### Errors (blocking for affected rows)

| Rule | Description |
|------|-------------|
| Duplicate keys | Same SKU + location combination appears multiple times |
| Negative quantity | Quantity value < 0 |
| Missing required column | Required column not found (even after mapping) |
| Empty file | File contains no data rows |

### Warnings (flagged but processed)

| Rule | Description |
|------|-------------|
| SKU format | Non-standard SKU format (missing hyphen, wrong case) |
| Whitespace | Leading/trailing whitespace in text fields |
| Date format | Date not in ISO 8601 format (YYYY-MM-DD) |
| Name drift | Product name changed between snapshots for same SKU |

### Info (logged only)

| Rule | Description |
|------|-------------|
| Column name mismatch | Non-canonical column names used |

## Example Valid Record

```csv
sku,name,quantity,location,last_counted
SKU-001,Widget A,150,Warehouse A,2024-01-08
```

## Example Records with Quality Issues

```csv
# Duplicate key (error)
SKU-001,Widget A,150,Warehouse A,2024-01-08
SKU-001,Widget A Updated,160,Warehouse A,2024-01-08

# Negative quantity (error)
SKU-045,Multimeter Pro,-5,Warehouse B,2024-01-15

# SKU format issue (warning)
SKU005,Connector Cable,480,Warehouse C,2024-01-15
sku-008,Power Supply,42,Warehouse A,2024-01-15

# Whitespace issue (warning)
SKU-002, Widget B,70,Warehouse A,2024-01-15

# Date format issue (warning)
SKU-035,Cable Ties,1420,Warehouse C,01/15/2024
```
