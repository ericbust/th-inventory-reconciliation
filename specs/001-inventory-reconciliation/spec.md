# Feature Specification: Inventory Reconciliation

**Feature Branch**: `001-inventory-reconciliation`
**Created**: 2026-01-02
**Status**: Draft
**Input**: User description: "Compare two warehouse inventory snapshots to identify changes, additions, removals, and data quality issues"

## User Scenarios & Testing _(mandatory)_

### User Story 1 - Basic Reconciliation Report (Priority: P1)

As an inventory analyst, I want to compare two inventory snapshots and receive a
report showing what items changed, were added, or were removed, so I can
understand inventory movement over the week.

**Why this priority**: Core functionality - without this, the tool has no value.
This delivers the primary business need of understanding inventory changes.

**Independent Test**: Run the reconciliation script with two CSV snapshots and
verify the output report correctly categorizes items as unchanged, changed,
added, or removed.

**Acceptance Scenarios**:

1. **Given** two valid snapshot files with matching items at different
   quantities, **When** reconciliation runs, **Then** those items appear in the
   "quantity changed" section with old and new values.
2. **Given** two snapshots where snapshot_1 has items not in snapshot_2,
   **When** reconciliation runs, **Then** those items appear in the "removed"
   section.
3. **Given** two snapshots where snapshot_2 has items not in snapshot_1,
   **When** reconciliation runs, **Then** those items appear in the "added"
   section.
4. **Given** two snapshots with items at identical quantities, **When**
   reconciliation runs, **Then** those items appear in the "unchanged" section.

---

### User Story 2 - Data Quality Flagging (Priority: P2)

As an inventory analyst, I want data quality issues to be detected and reported
separately from reconciliation results, so I can assess data reliability and
take corrective action on source systems.

**Why this priority**: Data quality issues affect the trustworthiness of
reconciliation results. Users need visibility into problems even if they can
still see the reconciliation output.

**Independent Test**: Run the reconciliation script with intentionally malformed
data (duplicates, format issues, negative values) and verify all quality issues
appear in a dedicated quality report section.

**Acceptance Scenarios**:

1. **Given** a snapshot with duplicate keys (same SKU+Warehouse), **When**
   reconciliation runs, **Then** duplicates are flagged in the quality report
   with row numbers.
2. **Given** a snapshot with negative quantity values, **When** reconciliation
   runs, **Then** the invalid quantities are flagged as errors.
3. **Given** snapshots with inconsistent column names, **When** reconciliation
   runs, **Then** column name differences are flagged as quality issues,
   mapping is applied, and processing continues.
4. **Given** a snapshot with inconsistent SKU formats (missing hyphens, case
   differences), **When** reconciliation runs, **Then** format issues are
   flagged and normalized values are used for matching.
5. **Given** a snapshot with whitespace issues in product names, **When**
   reconciliation runs, **Then** issues are flagged and normalized for matching.
6. **Given** a snapshot with inconsistent date formats, **When** reconciliation
   runs, **Then** format inconsistencies are flagged.

---

### User Story 3 - Structured Output Generation (Priority: P3)

As an inventory analyst, I want reconciliation results in structured JSON format,
so I can import them into other systems or generate further reports.

**Why this priority**: Enables integration with downstream processes. The
reconciliation is useful on its own but becomes more valuable when outputs can
be consumed programmatically.

**Independent Test**: Run reconciliation and verify a JSON output file is
generated in the `output/` directory matching the documented schema.

**Acceptance Scenarios**:

1. **Given** a completed reconciliation, **When** output generation runs,
   **Then** a JSON file is created containing reconciliation results,
   quality findings, counts, and metadata.
2. **Given** identical input files run twice, **When** comparing outputs,
   **Then** the JSON results are byte-for-byte identical (deterministic).

---

### Edge Cases

- What happens when one or both snapshot files are empty?
  - System reports "empty file" as a data quality error and produces minimal
    output.
- What happens when snapshot files have completely different columns?
  - System fails with clear error message listing expected vs actual columns.
- What happens when the same SKU appears in multiple warehouses?
  - The natural key is SKU + Warehouse, so these are treated as distinct items.
- What happens when a SKU exists in both snapshots but at different warehouses?
  - Treated as a removal from one warehouse and addition to another.
- What happens when quantity changes to zero?
  - Reported as a quantity change (not as removal); zero is a valid quantity.

## Requirements _(mandatory)_

### Functional Requirements

- **FR-001**: System MUST read CSV files from `data/snapshot_1.csv` and
  `data/snapshot_2.csv`.
- **FR-002**: System MUST use SKU + Warehouse as the composite natural key for
  matching items between snapshots.
- **FR-003**: System MUST categorize each item as: unchanged, quantity_changed,
  added (new in snapshot_2), or removed (only in snapshot_1).
- **FR-004**: System MUST normalize SKU values before comparison (uppercase,
  hyphen format).
- **FR-005**: System MUST normalize product names before comparison (trim
  whitespace).
- **FR-006**: System MUST validate data against defined schemas at load time
  using pandera.
- **FR-007**: System MUST detect and report duplicate key entries within a
  single snapshot; duplicates MUST be excluded from reconciliation (neither
  occurrence participates in comparison).
- **FR-008**: System MUST detect and report negative quantity values.
- **FR-009**: System MUST detect and report inconsistent date formats.
- **FR-010**: System MUST detect and report whitespace anomalies in text fields.
- **FR-011**: System MUST detect and report product name differences between
  snapshots for the same SKU as warnings (name drift detection).
- **FR-012**: System MUST produce a reconciliation report in JSON format in the
  `output/` directory, including reconciliation results, quality findings,
  counts, and metadata.
- **FR-013**: System MUST detect and report column name differences between
  snapshots as quality issues; processing MUST continue using configurable
  column mapping.
- **FR-014**: System MUST include all test coverage in the `tests/` directory
  using pytest.
- **FR-015**: System MUST produce deterministic output given identical inputs.
- **FR-016**: System MUST display progress status during processing and print a
  summary (counts of changed/added/removed items and quality issues) upon
  completion.

### Key Entities

- **InventoryItem**: Represents a single item in a snapshot. Key attributes:
  SKU, Product Name, Quantity, Warehouse, Last Updated Date. Natural key is
  SKU + Warehouse.
- **ReconciliationResult**: Represents the comparison outcome for one item.
  Contains: natural key, status (unchanged/changed/added/removed), old quantity,
  new quantity, quantity delta.
- **DataQualityIssue**: Represents a detected quality problem. Contains: issue
  type, severity (error/warning/info), affected field, row number, description,
  original value, suggested correction.
- **ReconciliationReport**: Aggregate output containing: list of results grouped
  by status, list of quality issues, summary statistics, metadata (file paths,
  timestamps, row counts).

## Clarifications

### Session 2026-01-02

- Q: How should duplicate keys be handled after flagging? → A: Exclude duplicates from reconciliation entirely; flag as quality issue and continue processing non-duplicate rows.
- Q: What should be printed to console during execution? → A: Progress bar/status during processing, then summary of results.
- Q: Should product name differences for the same SKU be detected? → A: Yes, flag as a warning (informational quality issue) when product name changes between snapshots for the same SKU.
- Q: What output format should be used? → A: JSON only (no CSV output).
- Q: How should column name differences be handled? → A: Flag as quality issue but continue processing using column mapping.

## Assumptions

- SKU + Warehouse is confirmed as the composite natural key per user decision.
- Column mapping between snapshots is static and known (name↔product_name,
  quantity↔qty, location↔warehouse, last_counted↔updated_at).
- Quality issues are flagged AND data is normalized for reconciliation (per user
  decision to do both).
- The system runs as a command-line script, not a web service.
- Input files are always CSV format (not Excel, JSON, etc.).
- Output directory `output/` will be created if it doesn't exist.

## Success Criteria _(mandatory)_

### Measurable Outcomes

- **SC-001**: Users can run reconciliation on the provided sample data and
  receive complete results in under 5 seconds.
- **SC-002**: 100% of known data quality issues in the sample data are detected
  and reported.
- **SC-003**: All items are correctly categorized (unchanged/changed/added/
  removed) with zero false positives or negatives on test data.
- **SC-004**: Test suite achieves minimum 90% code coverage of reconciliation
  logic.
- **SC-005**: Running the same reconciliation twice produces identical output
  files.
- **SC-006**: Users can understand the output reports without additional
  documentation (clear column headers, descriptive status values).
