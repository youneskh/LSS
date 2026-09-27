# TEST REPORT — `ls_lab` 19.0.1.0.0

> **THIS IS A FORM TO BE COMPLETED, NOT A RESULTS DOCUMENT.**
>
> The tests below were **written** during the build. They were **not executed**,
> because the build environment had no Odoo runtime and no PostgreSQL server.
> Every result column is therefore blank. Do not read this document as evidence
> that the tests passed.
>
> Execute the suite on a scratch database, complete the columns, and sign below.

---

## 1. Test inventory

**91 tests across 8 suites.**

| Suite | Class | Tests | Covers |
|-------|-------|-------|--------|
| `test_test_method.py` | `TestLsLabTestMethod` | 9 | Method lifecycle, immutability, versioning (BRU-01) |
| `test_specification.py` | `TestLsLabSpecification` | 9 | Specification lifecycle, criteria integrity (BRU-02 to 05, BRU-30) |
| `test_sample_workflow.py` | `TestLsLabSampleWorkflow` | 11 | Sample state machine, segregation of duties (BRU-06, 07, 11 to 15, 26, 29) |
| `test_result_evaluation.py` | `TestLsLabResultEvaluation` | 15 | Evaluation derivation, all criterion types (BRU-08, 09, 10, 16, 28) |
| `test_oos.py` | `TestLsLabOos` | 13 | Two-phase investigation, retest authorisation (BRU-15, 17 to 21) |
| `test_stability.py` | `TestLsLabStability` | 12 | Studies, derived due dates, pull wizard (BRU-24, 25, 27, 29) |
| `test_coa.py` | `TestLsLabCoa` | 10 | Certificate issue, freezing, versioning, signature (BRU-22, 23) |
| `test_security.py` | `TestLsLabSecurity` | 12 | ACL matrix, group hierarchy, record rules, installation integrity |

## 2. Business rule coverage map

Every business rule in `PHASE3-5_SPECIFICATION_AND_ARCHITECTURE.md` §3.4 has at
least one test.

| Rule | Test |
|------|------|
| BRU-01 | `test_approved_method_is_frozen` |
| BRU-02 | `test_approved_specification_lines_are_frozen` |
| BRU-03 | `test_line_cannot_be_added_to_approved_specification` |
| BRU-04 | `test_only_approved_methods_may_be_referenced` |
| BRU-05 | `test_single_approved_version_per_scope` |
| BRU-06 | `test_sample_requires_approved_specification` |
| BRU-07 | `test_registration_generates_result_lines` |
| BRU-08 | `test_evaluation_is_not_user_writable` |
| BRU-09 | `test_entry_refused_when_sample_not_open` |
| BRU-10 | `test_analyst_cannot_review_own_result` |
| BRU-11 | `test_cannot_record_results_with_pending_mandatory_test` |
| BRU-12 | `test_cannot_review_with_unreviewed_result` |
| BRU-13 | `test_analyst_cannot_review_own_sample` |
| BRU-14 | `test_reviewer_cannot_approve_own_review` |
| BRU-15 | `test_sample_cannot_be_approved_with_open_investigation` |
| BRU-16 | `test_value_outside_range_does_not_conform` |
| BRU-17 | `test_retest_result_blocked_without_authorisation` |
| BRU-18 | `test_retest_requires_justification` |
| BRU-19 | `test_close_requires_conclusion_and_disposition` |
| BRU-20 | `test_investigator_cannot_close_own_investigation` |
| BRU-21 | `test_phase2_only_after_no_lab_error` |
| BRU-22 | `test_certificate_requires_approved_sample` |
| BRU-23 | `test_issued_certificate_is_frozen` |
| BRU-24 | `test_pull_refused_when_study_not_ongoing` |
| BRU-25 | `test_scheduled_dates_derive_from_start_date` |
| BRU-26 | `test_cancellation_requires_reason` |
| BRU-27 | `test_missed_timepoint_requires_notes` |
| BRU-28 | `test_oot_requires_justification` |
| BRU-29 | `test_timepoint_cron_does_not_change_state`, `test_overdue_cron_does_not_change_state` |
| BRU-30 | `test_range_minimum_cannot_exceed_maximum` |

## 3. Execution record — TO BE COMPLETED

```bash
odoo -d <scratch_db> -i ls_lab --test-enable --test-tags /ls_lab \
     --stop-after-init --log-level=test
```

| Item | Value |
|------|-------|
| Executed by | ________________________ |
| Date | ________________________ |
| Odoo version | ________________________ |
| PostgreSQL version | ________________________ |
| Database name | ________________________ |
| Tests run | ________ |
| Passed | ________ |
| Failed | ________ |
| Errors | ________ |
| Duration | ________ |

### Failures

| Test | Error | Root cause | Resolution |
|------|-------|------------|------------|
| | | | |

## 4. Coverage — TO BE MEASURED

**Target: 95% statement coverage. Coverage has NOT been measured.** The figure
below is a target, not a result.

```bash
coverage run --source=ls_lab $(which odoo) -d <db> -i ls_lab \
    --test-enable --test-tags /ls_lab --stop-after-init
coverage report -m
```

| Module | Statements | Missed | Coverage |
|--------|-----------|--------|----------|
| `models/` | | | |
| `wizard/` | | | |
| **Total** | | | **________%** |

## 5. Static analysis — PARTIALLY COMPLETED

| Check | Status | Result |
|-------|--------|--------|
| Python compilation | **DONE** | All files compile |
| XML well-formedness | **DONE** | All files well-formed |
| Odoo 19 RNG validation of view archs | **DONE** | All validated archs pass |
| Custom static checker | **DONE** | 0 findings |
| Negative control (25 seeded faults) | **DONE** | 25/25 detected |
| `flake8` | **NOT RUN** | Not installed in the build environment |
| `pylint` | **NOT RUN** | Not installed in the build environment |
| `pylint-odoo` | **NOT RUN** | Not installed in the build environment |

`flake8`, `pylint` and `pylint-odoo` must be run before the module is considered
to have passed Phase 8 in full.

## 6. Manual test scenarios — TO BE COMPLETED

Requires three distinct users (analyst, reviewer, manager).

| # | Scenario | Expected | Result |
|---|----------|----------|--------|
| M-01 | Install on a clean Odoo 19 CE database | Installs without error | |
| M-02 | Upgrade the module | Upgrades without error | |
| M-03 | Create and approve a method | Frozen once approved | |
| M-04 | Attempt to edit the approved method | Refused with a clear message | |
| M-05 | Create and approve a specification | Frozen; lines locked | |
| M-06 | Register a sample | Result lines generated automatically | |
| M-07 | Record a conforming result | Evaluation shows Conforms | |
| M-08 | Record a failing result | Investigation raised automatically | |
| M-09 | Attempt to review own result | Refused | |
| M-10 | Review as a second user | Accepted | |
| M-11 | Attempt to approve as the reviewer | Refused | |
| M-12 | Approve as a third user via signature wizard | Approved; intent recorded | |
| M-13 | Attempt approval with an open investigation | Refused | |
| M-14 | Attempt a retest before authorisation | Refused | |
| M-15 | Authorise the retest, then record it | Accepted | |
| M-16 | Close the investigation as the investigator | Refused | |
| M-17 | Close as a different quality user | Closed | |
| M-18 | Issue a Certificate of Analysis | Issued and frozen | |
| M-19 | Print the CoA PDF | Renders, including the Part 11 notice | |
| M-20 | Print the OOS investigation PDF | Renders correctly | |
| M-21 | Create a stability study and pull a sample | Stability sample created and linked | |
| M-22 | Run each of the three crons manually | Messages posted; no state changed | |
| M-23 | Log in as Viewer | Read-only; no write buttons effective | |
| M-24 | Uninstall the module | Uninstalls cleanly | |

## 7. Sign-off — TO BE COMPLETED

| Role | Name | Signature | Date |
|------|------|-----------|------|
| Test executor | | | |
| Reviewer | | | |
| Quality approver | | | |

Until this section is completed, the module remains at **CONDITIONAL PASS** and
must not be used in a regulated production environment.
