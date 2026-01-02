<!--
SYNC IMPACT REPORT
==================
Version change: 0.0.0 → 1.0.0
Bump rationale: Initial constitution creation (MAJOR)

Modified principles: N/A (initial creation)
Added sections:
  - Core Principles (5 principles)
  - Technology Stack section
  - Development Workflow section
  - Governance section

Removed sections: N/A

Templates requiring updates:
  - .specify/templates/plan-template.md ✅ No changes needed (generic structure)
  - .specify/templates/spec-template.md ✅ No changes needed (generic structure)
  - .specify/templates/tasks-template.md ✅ No changes needed (generic structure)

Follow-up TODOs: None
==================
-->

# Inventory Reconciliations Constitution

## Core Principles

### I. Data Integrity First

All data operations MUST preserve source data integrity. Raw input files are
read-only; transformations produce new outputs. Every reconciliation operation
MUST be reproducible given the same inputs. Pandera schemas MUST validate data
at ingestion boundaries before any business logic executes.

**Rationale**: Inventory reconciliation is only valuable if results are
trustworthy. Corrupted or mutated source data invalidates all downstream
analysis.

### II. Explicit Data Quality Reporting

Data quality issues MUST be explicitly captured and reported, never silently
ignored or auto-corrected. The system MUST distinguish between: (a) validation
errors that block processing, (b) warnings that allow processing but require
documentation, and (c) informational anomalies. All quality findings MUST
appear in structured output alongside reconciliation results.

**Rationale**: Real-world inventory data contains inconsistencies. Users need
visibility into data quality to make informed decisions about reconciliation
results.

### III. Test-First Development (NON-NEGOTIABLE)

Pytest tests MUST be written before implementation code. Test files MUST exist
and fail before the corresponding implementation is written. The red-green-
refactor cycle is strictly enforced: write failing test, implement minimum code
to pass, then refactor. Edge cases for data reconciliation (empty files,
duplicates, type mismatches) MUST have explicit test coverage.

**Rationale**: Reconciliation logic correctness is critical. Test-first ensures
all requirements are captured as executable specifications before
implementation begins.

### IV. Pandas-Centric Operations

All CSV/tabular data operations MUST use pandas. Direct file I/O or manual
parsing is prohibited for structured data. DataFrame operations MUST prefer
vectorized operations over row-by-row iteration. Memory efficiency MUST be
considered for large datasets (use appropriate dtypes, chunked reading if
needed).

**Rationale**: pandas provides a battle-tested, performant foundation for data
manipulation. Consistent use ensures predictable behavior and maintainability.

### V. Clear Output Contracts

Reconciliation outputs MUST follow documented schemas. Output formats (CSV,
JSON) MUST be specified in advance with exact column names, types, and
semantics. The system MUST produce deterministic output given identical inputs
(sorted, consistent formatting). Human-readable summaries MUST accompany
machine-readable outputs.

**Rationale**: Downstream consumers of reconciliation results need reliable
contracts. Deterministic output enables automated validation and comparison.

## Technology Stack

**Language**: Python 3.10+
**Data Processing**: pandas (CSV operations, DataFrame manipulation)
**Data Validation**: pandera (schema definitions, data quality checks)
**Testing**: pytest (unit tests, integration tests, fixtures)
**Output Formats**: CSV (structured data), JSON (metadata/summaries)

All dependencies MUST be pinned to specific versions in requirements.txt or
pyproject.toml. New dependencies require justification against existing stack
capabilities.

## Development Workflow

**Code Organization**:
- Source code in `src/` or project root
- Tests in `tests/` mirroring source structure
- Input data in `data/` (read-only)
- Output results in `output/`
- Documentation in project root (NOTES.md, README.md)

**Quality Gates**:
- All tests MUST pass before merging
- Pandera schemas MUST be defined for all input/output data structures
- Type hints SHOULD be used for function signatures
- Docstrings MUST document public functions with parameters and return types

**Commit Practices**:
- Commit after each logical unit of work
- Commit messages MUST describe the change, not the file modified
- Tests and implementation MAY be committed together when implementing TDD

## Governance

This constitution supersedes all other development practices for this project.
Amendments require:
1. Documentation of the proposed change and rationale
2. Review of impact on existing code and tests
3. Version increment following semantic versioning

**Compliance**: All pull requests and code reviews MUST verify adherence to
these principles. Deviations MUST be documented in code comments with
justification.

**Version**: 1.0.0 | **Ratified**: 2026-01-02 | **Last Amended**: 2026-01-02
