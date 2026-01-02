# Tasks: Inventory Reconciliation

**Input**: Design documents from `/specs/001-inventory-reconciliation/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: Required per FR-014 (test coverage in `tests/`) and SC-004 (90% coverage target).

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story?] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root (per plan.md)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [x] T001 Create project structure with src/, tests/, output/ directories
- [x] T002 Create pyproject.toml with Python 3.10+ and project metadata
- [x] T003 Create requirements.txt with pandas==2.3.3, pandera==0.27.1, tqdm==4.67.1
- [x] T004 [P] Create requirements-dev.txt with pytest==9.0.2, pytest-cov==7.0.0
- [x] T005 [P] Create src/__init__.py, src/models/__init__.py, src/services/__init__.py, src/schemas/__init__.py
- [x] T006 [P] Create tests/__init__.py, tests/conftest.py with shared fixtures
- [x] T007 [P] Create tests/fixtures/ directory with sample test data files

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T008 Create InventoryItem dataclass in src/models/inventory_item.py with sku, name, quantity, location, last_counted fields
- [x] T009 Create pandera schema in src/schemas/inventory_schema.py with column validators and coercion rules
- [x] T010 [P] Create column mapping constants in src/services/loader.py (COLUMN_MAPPING dict)
- [x] T011 Implement load_snapshot() in src/services/loader.py using pandas read_csv with column mapping
- [x] T012 [P] Implement normalize_sku() in src/services/normalizer.py (uppercase, hyphen insertion)
- [x] T013 [P] Implement normalize_name() in src/services/normalizer.py (whitespace trimming)
- [x] T014 Implement normalize_dataframe() in src/services/normalizer.py combining SKU and name normalization

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 - Basic Reconciliation Report (Priority: P1) 🎯 MVP

**Goal**: Compare two inventory snapshots and categorize items as unchanged, changed, added, or removed

**Independent Test**: Run `python -m src.cli` with sample data and verify items are correctly categorized by status

### Tests for User Story 1

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [x] T015 [P] [US1] Create test_reconciler.py in tests/unit/ with test cases for unchanged, changed, added, removed categorization
- [x] T016 [P] [US1] Create test_normalizer.py in tests/unit/ with SKU and name normalization test cases
- [x] T017 [P] [US1] Create integration test in tests/integration/test_full_reconciliation.py for basic reconciliation flow

### Implementation for User Story 1

- [x] T018 [P] [US1] Create ReconciliationResult dataclass in src/models/reconciliation_result.py with status, quantities, delta
- [x] T019 [US1] Implement find_duplicates() in src/services/reconciler.py using pandas duplicated(keep=False)
- [x] T020 [US1] Implement reconcile() in src/services/reconciler.py with outer merge and status categorization
- [x] T021 [US1] Create basic CLI entry point in src/cli.py with argument parsing for snapshot paths
- [x] T022 [US1] Add tqdm progress bar to CLI in src/cli.py with 5 discrete steps
- [x] T023 [US1] Print console summary (counts per status) in src/cli.py

**Checkpoint**: At this point, User Story 1 should be fully functional - reconciliation works but no quality issues or JSON output

---

## Phase 4: User Story 2 - Data Quality Flagging (Priority: P2)

**Goal**: Detect and report data quality issues (duplicates, negative quantities, format issues, name drift)

**Independent Test**: Run with snapshot containing known issues and verify all quality issues appear in output with correct severity

### Tests for User Story 2

- [ ] T024 [P] [US2] Create test_quality_checker.py in tests/unit/ with test cases for each issue type (duplicate_key, negative_quantity, etc.)
- [ ] T025 [P] [US2] Create snapshot_with_issues.csv in tests/fixtures/ with all quality issue types
- [ ] T026 [P] [US2] Add quality issue test cases to tests/integration/test_full_reconciliation.py

### Implementation for User Story 2

- [ ] T027 [P] [US2] Create DataQualityIssue dataclass in src/models/quality_issue.py with issue_type, severity, source_file, row_number, field, values, description
- [ ] T028 [US2] Implement check_duplicates() in src/services/quality_checker.py returning DataQualityIssue list
- [ ] T029 [US2] Implement check_negative_quantities() in src/services/quality_checker.py
- [ ] T030 [US2] Implement check_sku_format() in src/services/quality_checker.py for normalization detection
- [ ] T031 [US2] Implement check_whitespace() in src/services/quality_checker.py for text field issues
- [ ] T032 [US2] Implement check_date_format() in src/services/quality_checker.py for ISO format validation
- [ ] T033 [US2] Implement check_column_names() in src/services/quality_checker.py for mapping detection
- [ ] T034 [US2] Implement check_name_drift() in src/services/quality_checker.py comparing names across snapshots
- [ ] T035 [US2] Implement run_all_checks() in src/services/quality_checker.py aggregating all quality checks
- [ ] T036 [US2] Integrate quality checking into CLI flow in src/cli.py
- [ ] T037 [US2] Update console summary to include quality issue counts by severity in src/cli.py

**Checkpoint**: At this point, User Stories 1 AND 2 should both work - reconciliation with quality issues detected

---

## Phase 5: User Story 3 - Structured Output Generation (Priority: P3)

**Goal**: Generate JSON output file with results, quality issues, summary, and metadata

**Independent Test**: Run reconciliation and verify output/reconciliation_report.json matches the JSON schema in contracts/output-schema.json

### Tests for User Story 3

- [ ] T038 [P] [US3] Create test_reporter.py in tests/unit/ with JSON structure and determinism test cases
- [ ] T039 [P] [US3] Create expected_output.json in tests/fixtures/ for schema validation
- [ ] T040 [P] [US3] Add JSON output validation to tests/integration/test_full_reconciliation.py

### Implementation for User Story 3

- [ ] T041 [P] [US3] Create ReconciliationReport dataclass in src/models/report.py with metadata, summary, results, quality_issues
- [ ] T042 [P] [US3] Create ReportMetadata and ReportSummary nested dataclasses in src/models/report.py
- [ ] T043 [US3] Implement build_report() in src/services/reporter.py assembling all components
- [ ] T044 [US3] Implement write_json() in src/services/reporter.py with sort_keys=True for determinism
- [ ] T045 [US3] Integrate JSON output into CLI flow in src/cli.py
- [ ] T046 [US3] Ensure output/ directory is created if missing in src/cli.py

**Checkpoint**: All user stories should now be independently functional - complete reconciliation with quality issues and JSON output

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Final validation, documentation, and cleanup

- [ ] T047 [P] Create NOTES.md documenting key decisions, assumptions, and approach
- [ ] T048 Run pytest --cov=src --cov-report=term-missing and verify 90% coverage target (SC-004)
- [ ] T049 Validate JSON output against contracts/output-schema.json using jsonschema
- [ ] T050 Run full reconciliation on sample data and verify <5 second completion (SC-001)
- [ ] T051 Verify deterministic output by running twice and comparing (SC-005)
- [ ] T052 [P] Run quickstart.md validation - follow all steps and verify they work

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Foundational phase completion
- **User Story 2 (Phase 4)**: Depends on Foundational phase completion (can run parallel to US1 but integrates with it)
- **User Story 3 (Phase 5)**: Depends on US1 and US2 (needs reconciliation results and quality issues)
- **Polish (Phase 6)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Integrates with US1 reconciler but independently testable
- **User Story 3 (P3)**: Depends on US1 results and US2 quality issues - combines both into final output

### Within Each User Story

- Tests MUST be written and FAIL before implementation (TDD per constitution)
- Models before services
- Services before CLI integration
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- T004, T005, T006, T007 can run in parallel (Setup phase)
- T010, T012, T013 can run in parallel (Foundational phase)
- T015, T016, T017 can run in parallel (US1 tests)
- T024, T025, T026 can run in parallel (US2 tests)
- T038, T039, T040 can run in parallel (US3 tests)
- T041, T042 can run in parallel (US3 models)
- T047, T052 can run in parallel (Polish phase)

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together:
Task: T015 "Create test_reconciler.py in tests/unit/"
Task: T016 "Create test_normalizer.py in tests/unit/"
Task: T017 "Create integration test in tests/integration/test_full_reconciliation.py"

# After tests written, models can be parallel:
Task: T018 "Create ReconciliationResult dataclass in src/models/reconciliation_result.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001-T007)
2. Complete Phase 2: Foundational (T008-T014)
3. Complete Phase 3: User Story 1 (T015-T023)
4. **STOP and VALIDATE**: Run `python -m src.cli` and verify basic reconciliation works
5. Output shows unchanged/changed/added/removed counts in console

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → **MVP: Basic reconciliation works**
3. Add User Story 2 → Test independently → **Quality issues now detected**
4. Add User Story 3 → Test independently → **JSON output generated**
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (reconciliation)
   - Developer B: User Story 2 tests + DataQualityIssue model (can start before US1 complete)
3. User Story 3 requires both US1 and US2, so sequence: US1 → US2 → US3

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing (TDD per constitution Principle III)
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- All quality issues from sample data must be detected (SC-002)
