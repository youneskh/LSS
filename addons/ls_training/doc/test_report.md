# TEST REPORT

Module: `ls_training` · Date: July 2026

---

## 1. Headline statement

**The test suite has been written. It has never been executed.**

No Odoo 19 runtime and no PostgreSQL instance were available in the build
environment. Every result below is therefore an inventory of *what exists*,
not a record of *what passed*.

**No pass rate is claimed. No coverage figure is claimed.**

The 95% coverage figure in the project brief is a target defined for this
work. It has not been measured, and stating a measured figure without
running `coverage` would be fabrication.

## 2. Test inventory

146 test methods across 8 test modules plus one shared fixture.

| File | Tests | Scope |
|------|-------|-------|
| `test_course.py` | 22 | Course master data, sequence assignment, constraints, four-state lifecycle, smart-button actions |
| `test_session_workflow.py` | 28 | Session state machine, attendance rules, capacity, certification issuance, immutability after closure |
| `test_certification.py` | 22 | Issuance, frozen course version, expiry derivation and override, status boundaries, warning-window parameter, revocation, delete prohibition, renewal history |
| `test_requirement_matrix.py` | 19 | Requirement targeting and resolution, duplicate rejection, company checks, employee compliance computation |
| `test_wizards.py` | 18 | Bulk registration in four modes, exclusion rules, capacity guard; matrix generation, scope filters, limits |
| `test_competency.py` | 17 | Competency master data, assessment levels, acquisition threshold, self-assessment prohibition, confirmation lock |
| `test_security.py` | 14 | Group installation and hierarchy, record-rule installation, ACL matrix per group, Learner self-scope, multi-company isolation |
| `test_cron.py` | 6 | Status refresh, revoked exclusion, reminder targeting, cron record configuration |
| `common.py` | — | Shared fixture: 2 companies, 3 employees, 2 departments/jobs, 1 competency, 2 approved courses, 1 session |
| **Total** | **146** | |

## 3. Coverage by test level

| Level required by the brief | Present | Where |
|------------------------------|---------|-------|
| Unit tests | Yes | Constraint, compute and derivation tests across all files |
| Integration tests | Yes | `test_session_workflow.py` — full session-to-certification chain |
| Functional tests | Yes | `test_wizards.py` — end-user wizard flows |
| Security tests | Yes | `test_security.py` — 14 tests on ACL and record rules |
| Access-right tests | Yes | `test_security.py` — per-group create/write/unlink assertions |
| Constraint tests | Yes | All 8 SQL and 18 Python constraints have at least one test |
| Workflow tests | Yes | Every transition and every guard in both state machines |
| Installation tests | **No** | Requires a runtime. See §5 |
| Upgrade tests | **No** | Requires a runtime and a prior version. See §5 |
| Performance tests | **No** | Requires a populated running instance. See §5 |

## 4. Constraint coverage

| Constraint | Test |
|-----------|------|
| course code unique per company | `test_code_unique_per_company` |
| competency code unique per company | `test_code_unique_per_company` |
| session name unique per company | covered by sequence assignment test |
| session capacity ≥ 0 | `test_capacity_enforced` |
| attendance unique per session/employee | `test_duplicate_registration_rejected` |
| certification name unique per company | covered by sequence assignment test |
| assessment unique per employee/competency/date | `test_duplicate_assessment_same_day_rejected` |
| requirement grace_days ≥ 0 | `test_negative_grace_period_rejected` |
| course duration > 0 | `test_duration_must_be_positive` |
| course pass score 0–100 | `test_pass_score_bounds` |
| course validity ≥ 0 | `test_validity_months_not_negative` |
| e-learning requires URL | `test_elearning_requires_url` |
| session end > start | `test_end_must_follow_start` |
| session capacity vs attendees | `test_capacity_enforced` |
| single trainer | `test_single_trainer_only` |
| attendance score 0–100 | `test_score_bounds` |
| attendee company matches | `test_attendee_company_must_match` |
| certification expiry ≥ grant | `test_expiry_before_grant_rejected` |
| certification score 0–100 | `test_score_bounds` |
| revocation requires reason | `test_revocation_requires_reason` |
| assessor ≠ subject | `test_self_assessment_forbidden` |
| next assessment ≥ assessment | `test_next_date_cannot_precede_assessment` |
| requirement target defined | `test_requirement_needs_a_target` |
| requirement uniqueness | `test_duplicate_requirement_rejected` |
| requirement target company | `test_employee_company_must_match` |
| competency reassessment ≥ 0 | `test_negative_reassessment_interval_rejected` |

All 26 constraints have at least one test.

## 5. What was NOT executed

| Activity | Status | Reason |
|----------|--------|--------|
| Installation on Odoo 19 | **Not performed** | No Odoo 19 runtime available |
| Upgrade test | **Not performed** | Same |
| Execution of the 146 tests | **Not performed** | Same |
| Coverage measurement | **Not performed** | Requires executing the suite |
| Performance test | **Not performed** | Requires a populated instance |
| `flake8` | **Not performed** | Not installed; network egress disabled |
| `pylint` / `pylint-odoo` | **Not performed** | Same |

## 6. Static analysis actually performed

These checks were run in the build environment and their results are real.

| Check | Method | Result |
|-------|--------|--------|
| Python syntax, 24 files | `ast.parse` | **PASS** |
| XML well-formedness, 22 files | `lxml.etree.parse` | **PASS** |
| Manifest lists only existing files | custom script | **PASS** |
| Every XML file referenced by the manifest (except the documented alternate) | custom script | **PASS** |
| Internal `ref=""` resolution | custom script | **PASS — 0 unresolved of all refs checked** |
| `ir.model.access.csv` model references | custom script | **PASS — 31 lines, all resolve** |
| `ir.model.access.csv` group references | custom script | **PASS** |
| Line length ≤ 79 | custom script | **PASS — 0 violations** (1 found and fixed) |
| Trailing whitespace / tabs | custom script | **PASS — 0** |
| Docstring on every module, class, function | `ast` | **PASS — 264/264** |
| No TODO/FIXME/XXX/HACK | regex | **PASS — 0** |

These cover a subset of what `flake8` and `pylint-odoo` would report. They
are not a substitute for those tools.

## 7. Defects found and fixed during the build

| # | Defect | Found by | Fix |
|---|--------|----------|-----|
| D-01 | `test_cron.py` line exceeded 79 characters | Style check | Reflowed |
| D-02 | `test_refresh_skips_revoked` asserted through convoluted set logic that did not actually test the intended behaviour | Manual review | Rewritten to assert that a revoked, past-expiry certification stays `revoked` after the refresh |
| D-03 | `mail` was only a transitive dependency | Architecture review | Declared explicitly in the manifest |
| D-04 | Certification `unlink` was initially permitted for Managers | Architecture review | Changed to always raise |

## 8. Required actions before release

| # | Action | Owner |
|---|--------|-------|
| 1 | Install on a clean Odoo 19 database | Implementer |
| 2 | Apply the `ir.rule` field-name fix if installation fails (`verification_notes.md` §2) | Implementer |
| 3 | Execute all 146 tests | Implementer |
| 4 | Investigate and fix every failure; add a regression test per defect | Developer |
| 5 | Measure coverage with `coverage`; record the real figure | Developer |
| 6 | Run `flake8` and `pylint-odoo`; resolve blocking findings | Developer |
| 7 | Perform an installation and an upgrade test | Implementer |
| 8 | Performance-test matrix generation at production scale | Performance Engineer |
| 9 | Re-issue this report with measured results | QA |

## 9. Phase gate

| Phase | Outcome |
|-------|---------|
| Phase 7 — Testing | **CONDITIONAL PASS** — artefacts complete (146 tests, all constraints and transitions covered); execution outstanding |
| Phase 8 — Static Analysis | **CONDITIONAL PASS** — 11 checks executed and passed; `flake8` and `pylint-odoo` could not be run offline |

Neither phase can be closed to a full PASS without a runtime.
