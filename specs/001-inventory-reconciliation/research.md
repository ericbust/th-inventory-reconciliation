# Research: Inventory Reconciliation

**Date**: 2026-01-02
**Branch**: 001-inventory-reconciliation

## Technology Decisions

### 1. Pandera Schema Validation Strategy

**Decision**: Use pandera DataFrameSchema with column-level validators at CSV
load time, with lazy validation to collect all errors before failing.

**Rationale**:

- Pandera integrates natively with pandas DataFrames
- Lazy validation (`lazy=True`) collects all schema violations in one pass
- Custom checks can be defined for domain-specific rules (SKU format, etc.)
- Supports coercion for type normalization (e.g., quantity to int)

**Alternatives Considered**:

- Great Expectations: More powerful but overkill for single-file validation
- Cerberus: Dict-based, doesn't integrate with pandas
- Manual validation: Error-prone, not declarative

**Implementation Pattern**:

```python
import pandera as pa

class InventorySchema(pa.DataFrameModel):
    sku: str = pa.Field(str_matches=r'^SKU-\d{3}$')
    product_name: str = pa.Field(str_length={'min_value': 1})
    quantity: int = pa.Field(ge=0, coerce=True)
    warehouse: str = pa.Field(isin=['Warehouse A', 'Warehouse B', 'Warehouse C'])
    last_updated: str  # Validate format separately for flexibility

    class Config:
        strict = False  # Allow extra columns (will flag as quality issue)
        coerce = True
```

### 2. SKU Normalization Approach

**Decision**: Normalize SKUs to uppercase with standard hyphen format (SKU-NNN)
using regex replacement, applied before comparison.

**Rationale**:

- Sample data shows variations: `SKU005`, `sku-008`, `SKU018`
- Standard format enables reliable matching
- Original value preserved for quality reporting

**Alternatives Considered**:

- Case-insensitive comparison only: Doesn't handle missing hyphens
- Fuzzy matching: Overkill when format is predictable
- Strict rejection: Too brittle for real-world data

**Implementation Pattern**:

```python
import re

def normalize_sku(sku: str) -> str:
    """Normalize SKU to uppercase with hyphen: SKU-NNN"""
    clean = sku.strip().upper()
    # Insert hyphen if missing: SKU001 -> SKU-001
    if re.match(r'^SKU\d{3}$', clean):
        clean = f"{clean[:3]}-{clean[3:]}"
    return clean
```

### 3. Duplicate Detection Strategy

**Decision**: Detect duplicates using pandas `duplicated()` on composite key
(normalized SKU + Warehouse), exclude ALL occurrences from reconciliation.

**Rationale**:

- Per clarification: duplicates are flagged but excluded entirely
- Using `keep=False` in `duplicated()` marks all occurrences, not just second+
- Enables clear reporting of which rows are problematic

**Alternatives Considered**:

- Keep first: Arbitrary choice, per clarification should exclude all
- Keep last: Same issue
- Aggregate: Not appropriate for inventory snapshots

**Implementation Pattern**:

```python
def find_duplicates(df: pd.DataFrame, key_cols: list[str]) -> pd.DataFrame:
    """Return all rows that have duplicate keys."""
    return df[df.duplicated(subset=key_cols, keep=False)]
```

### 4. Progress Bar Implementation

**Decision**: Use tqdm for progress display with discrete steps for each
processing phase.

**Rationale**:

- tqdm is lightweight and well-maintained
- Works in terminals, notebooks, and CI environments
- Can wrap iterators or use manual updates for phase tracking

**Alternatives Considered**:

- Rich: More features but heavier dependency
- Click progress bars: Tied to Click framework
- Custom print statements: Not as polished

**Implementation Pattern**:

```python
from tqdm import tqdm

def reconcile_with_progress(snapshot1_path, snapshot2_path):
    with tqdm(total=5, desc="Reconciling") as pbar:
        pbar.set_description("Loading snapshot 1")
        df1 = load_snapshot(snapshot1_path)
        pbar.update(1)

        pbar.set_description("Loading snapshot 2")
        df2 = load_snapshot(snapshot2_path)
        pbar.update(1)

        # ... etc
```

### 5. JSON Output Structure

**Decision**: Single JSON file with nested structure containing metadata,
summary, reconciliation results (grouped by status), and quality issues.

**Rationale**:

- Single file simplifies consumption
- Grouped results enable quick access to specific categories
- Metadata enables traceability and debugging
- Deterministic key ordering via `sort_keys=True`

**Alternatives Considered**:

- Multiple files (one per category): Harder to consume atomically
- CSV output: Loses nested structure, less expressive for quality issues
- JSONL (one record per line): Good for streaming but not needed here

**Implementation Pattern**:

```python
{
    "metadata": {
        "generated_at": "2026-01-02T10:30:00Z",
        "snapshot_1": "data/snapshot_1.csv",
        "snapshot_2": "data/snapshot_2.csv",
        "snapshot_1_rows": 75,
        "snapshot_2_rows": 80
    },
    "summary": {
        "unchanged": 50,
        "quantity_changed": 15,
        "added": 5,
        "removed": 2,
        "quality_issues": 8
    },
    "results": {
        "unchanged": [...],
        "quantity_changed": [...],
        "added": [...],
        "removed": [...]
    },
    "quality_issues": [...]
}
```

### 6. Column Mapping Strategy

**Decision**: Use a static dictionary mapping for known column name variations,
applied at load time with quality issue flagging.

**Rationale**:

- Column differences between snapshots are predictable from sample data
- Static mapping is simpler and more predictable than inference
- Quality report captures which mappings were applied

**Known Mappings** (from sample data analysis):

```python
COLUMN_MAPPING = {
    'product_name': 'name',
    'qty': 'quantity',
    'warehouse': 'location',
    'updated_at': 'last_counted'
}
# Canonical names: sku, name, quantity, location, last_counted
```

### 7. Date Format Handling

**Decision**: Detect date format inconsistencies, flag as quality issues, but
do not attempt to normalize dates (they are informational only).

**Rationale**:

- Dates are not used in reconciliation logic (SKU+Warehouse is the key)
- Multiple formats in sample data: `2024-01-15`, `01/15/2024`
- Flagging helps users identify source system inconsistencies

**Alternatives Considered**:

- Parse and normalize all dates: Adds complexity for minimal benefit
- Strict format rejection: Too brittle
- Ignore dates entirely: Misses useful quality information

## Dependencies

### Production Dependencies

| Package | Version | Purpose                       |
| ------- | ------- | ----------------------------- |
| pandas  | ^2.3.3  | DataFrame operations, CSV I/O |
| pandera | ^0.27.1 | Schema validation             |
| tqdm    | ^4.67.1 | Progress bar                  |

### Development Dependencies

| Package    | Version | Purpose            |
| ---------- | ------- | ------------------ |
| pytest     | ^9.0.2  | Test framework     |
| pytest-cov | ^7.0.0  | Coverage reporting |

## Open Questions Resolved

All technical context items from the plan template have been resolved:

- Language: Python 3.10+ (from constitution)
- Dependencies: pandas, pandera, tqdm (researched above)
- Testing: pytest (from constitution)
- No external services or storage required
- Performance: 5 second target easily achievable for ~100 rows
