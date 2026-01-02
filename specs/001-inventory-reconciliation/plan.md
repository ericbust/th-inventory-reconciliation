# Implementation Plan: Inventory Reconciliation

**Branch**: `001-inventory-reconciliation` | **Date**: 2026-01-02 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-inventory-reconciliation/spec.md`

## Summary

Build a Python CLI tool that compares two inventory CSV snapshots to identify
changes (quantity differences), additions, and removals while detecting and
reporting data quality issues. Uses pandas for data operations, pandera for
schema validation, and outputs results as JSON with console progress feedback.

## Technical Context

**Language/Version**: Python 3.10+
**Primary Dependencies**: pandas, pandera, tqdm (progress bar)
**Storage**: File-based (CSV input, JSON output)
**Testing**: pytest with pytest-cov for coverage
**Target Platform**: Linux/macOS/Windows CLI
**Project Type**: Single project
**Performance Goals**: Complete reconciliation of sample data in under 5 seconds
**Constraints**: Deterministic output, memory-efficient for reasonable dataset sizes
**Scale/Scope**: ~100-1000 rows per snapshot (sample data has ~75-80 rows)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Evidence |
|-----------|--------|----------|
| I. Data Integrity First | ✅ PASS | Source files read-only, pandera validates at ingestion |
| II. Explicit Data Quality Reporting | ✅ PASS | Quality issues captured with severity levels in output |
| III. Test-First Development | ✅ PASS | pytest required, 90% coverage target in success criteria |
| IV. Pandas-Centric Operations | ✅ PASS | All CSV ops via pandas per constitution |
| V. Clear Output Contracts | ✅ PASS | JSON schema documented, deterministic output required |

**Gate Result**: PASS - All constitution principles satisfied.

## Project Structure

### Documentation (this feature)

```text
specs/001-inventory-reconciliation/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (JSON schema)
└── tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code (repository root)

```text
src/
├── __init__.py
├── models/
│   ├── __init__.py
│   ├── inventory_item.py      # InventoryItem dataclass/schema
│   ├── reconciliation_result.py
│   ├── quality_issue.py
│   └── report.py              # ReconciliationReport
├── services/
│   ├── __init__.py
│   ├── loader.py              # CSV loading with pandera validation
│   ├── normalizer.py          # SKU/name normalization
│   ├── reconciler.py          # Core comparison logic
│   ├── quality_checker.py     # Data quality detection
│   └── reporter.py            # JSON output generation
├── schemas/
│   ├── __init__.py
│   └── inventory_schema.py    # Pandera schemas
└── reconcile.py               # Entry point with progress bar

tests/
├── __init__.py
├── conftest.py                # Shared fixtures
├── unit/
│   ├── test_normalizer.py
│   ├── test_reconciler.py
│   └── test_quality_checker.py
├── integration/
│   └── test_full_reconciliation.py
└── fixtures/
    ├── snapshot_clean.csv
    ├── snapshot_with_issues.csv
    └── expected_output.json

data/                          # Input (read-only)
├── snapshot_1.csv
└── snapshot_2.csv

output/                        # Generated output
└── reconciliation_report.json

requirements.txt               # Pinned dependencies
pyproject.toml                 # Project metadata
NOTES.md                       # Developer notes
```

**Structure Decision**: Single project structure selected. This is a CLI tool
with no frontend/backend split. Source code in `src/` with tests mirroring
the structure in `tests/`.

## Complexity Tracking

No constitution violations requiring justification. The design follows all
principles with minimal complexity:
- Single entry point (cli.py)
- Clear separation of concerns (loader, normalizer, reconciler, reporter)
- No external services or databases
- No web framework overhead
