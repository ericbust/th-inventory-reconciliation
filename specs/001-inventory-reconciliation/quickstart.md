# Quickstart: Inventory Reconciliation

## Prerequisites

- Python 3.10 or higher
- pip (Python package installer)

## Installation

```bash
# Clone the repository (if not already done)
cd inventory-reconciliations

# Create and activate virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install development dependencies (for testing)
pip install -r requirements-dev.txt
```

## Quick Usage

```bash
# Run reconciliation on sample data
python -m src.cli

# Or specify custom paths
python -m src.cli --snapshot1 data/snapshot_1.csv --snapshot2 data/snapshot_2.csv
```

## Expected Output

The script will:
1. Display a progress bar during processing
2. Print a summary to console
3. Generate `output/reconciliation_report.json`

### Console Output Example

```
Reconciling: 100%|████████████████████| 5/5 [00:00<00:00, 25.3it/s]

=== Reconciliation Summary ===
Snapshot 1: data/snapshot_1.csv (75 rows)
Snapshot 2: data/snapshot_2.csv (80 rows)

Results:
  Unchanged:        50
  Quantity Changed: 15
  Added:             5
  Removed:           2

Quality Issues: 8 (3 errors, 4 warnings, 1 info)

Output written to: output/reconciliation_report.json
```

## Running Tests

```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=src --cov-report=term-missing

# Run specific test file
pytest tests/unit/test_reconciler.py

# Run tests matching pattern
pytest -k "test_duplicate"
```

## Project Structure

```
inventory-reconciliations/
├── src/                    # Source code
│   ├── cli.py              # Entry point
│   ├── models/             # Data classes
│   ├── services/           # Business logic
│   └── schemas/            # Pandera schemas
├── tests/                  # Test suite
│   ├── unit/               # Unit tests
│   ├── integration/        # Integration tests
│   └── fixtures/           # Test data
├── data/                   # Input files (read-only)
│   ├── snapshot_1.csv
│   └── snapshot_2.csv
├── output/                 # Generated output
├── specs/                  # Specifications
└── requirements.txt        # Dependencies
```

## Common Tasks

### Verify Installation

```bash
python -c "import pandas; import pandera; import tqdm; print('All dependencies OK')"
```

### Check Output Schema Compliance

```bash
# Using jsonschema (install with: pip install jsonschema)
python -c "
import json
from jsonschema import validate

with open('specs/001-inventory-reconciliation/contracts/output-schema.json') as f:
    schema = json.load(f)
with open('output/reconciliation_report.json') as f:
    report = json.load(f)
validate(report, schema)
print('Output validates against schema')
"
```

### View Specific Results

```bash
# View quantity changes only
python -c "
import json
with open('output/reconciliation_report.json') as f:
    report = json.load(f)
for item in report['results']['quantity_changed']:
    print(f\"{item['sku']} @ {item['location']}: {item['old_quantity']} -> {item['new_quantity']} ({item['quantity_delta']:+d})\")
"
```

## Troubleshooting

### "ModuleNotFoundError: No module named 'src'"

Ensure you're running from the repository root directory.

### "FileNotFoundError: data/snapshot_1.csv"

The input files must exist at the specified paths. Default paths are
`data/snapshot_1.csv` and `data/snapshot_2.csv`.

### "pandera.errors.SchemaError"

The input data failed validation. Check the quality issues section of the
output for details on what went wrong.
