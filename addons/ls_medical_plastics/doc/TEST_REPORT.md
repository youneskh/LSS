# Test Report

**Module:** `ls_medical_plastics` · **Version:** 19.0.1.0.0
**Date of preparation:** August 2026

---

## 1. Execution status — read this before anything else

> **The tests described in this document have never been executed.**
>
> The preparation environment contained no Odoo runtime and no PostgreSQL
> server. It was therefore impossible to run a single test.
>
> Consequently, and without exception:
>
> - **No pass rate exists.** Any number presented as one would be fabricated.
> - **No coverage percentage exists.** The 95% coverage target set by the
>   development framework has **not been demonstrated** and is not claimed.
> - **No test is known to pass.** Tests are written to the documented Odoo API,
>   but a test that has never run may itself contain defects.
>
> This document is therefore an **inventory of written tests and their intent**,
> not a record of results. Executing them is the first task of the receiving
> team.

---

## 2. Test inventory

139 test methods across 11 test classes in 9 test modules, plus one shared
fixture module. Counts below were extracted from the source with the Python
`ast` module, not compiled by hand.

| Module | Class | Tests | Area covered |
|---|---|---:|---|
| `test_material_grade.py` | `TestMaterialGrade` | 10 | Qualification workflow, uniqueness, date coherence |
| `test_component.py` | `TestComponent` | 10 | Categorisation, sterility, release gating |
| `test_tool.py` | `TestTool` | 17 | Cavity register, shot counting, maintenance status |
| `test_tool.py` | `TestToolMaintenance` | 7 | Maintenance events and their effect on the tool |
| `test_molding_parameter.py` | `TestMoldingParameter` | 19 | Versioning, approval, segregation of duties |
| `test_injection_molding.py` | `TestInjectionMolding` | 28 | Run state machine, gating, computed quantities |
| `test_readings.py` | `TestReadings` | 14 | Append-only behaviour, criteria freezing, corrections |
| `test_traceability.py` | `TestTraceability` | 10 | Genealogy resolution in four directions |
| `test_wizards.py` | `TestReadingWizard` | 6 | Bulk reading capture |
| `test_wizards.py` | `TestToolServiceWizard` | 6 | Controlled return of a tool to service |
| `test_security.py` | `TestSecurity` | 12 | Access rights, role implication, company isolation |
| **Total** | **11 classes** | **139** | |

---

## 3. Coverage by requirement, as designed

The table states what each area is *intended* to demonstrate once executed.

### 3.1 Data integrity controls

| Control | Test |
|---|---|
| A reading cannot be modified | `test_reading_cannot_be_modified` |
| Not even its comment can be modified | `test_reading_comment_cannot_be_modified` |
| A reading cannot be deleted | `test_reading_cannot_be_deleted` |
| A correction requires a stated reason | `test_correction_requires_reason` |
| The original value survives correction | `test_correction_creates_chain` |
| Acceptance criteria are frozen at capture | `test_criteria_frozen_at_capture` |
| Revising the specification does not alter history | `test_later_specification_change_does_not_alter_history` |
| Superseded readings leave the deviation count | `test_superseded_reading_excluded_from_statistics` |
| A closed run rejects new readings | `test_reading_rejected_on_closed_run` |
| A closed run cannot be modified | `test_close_freezes_record` |
| A closed run cannot be deleted | `test_closed_run_cannot_be_deleted` |

### 3.2 Segregation of duties

| Control | Test |
|---|---|
| Author cannot review a specification | `test_author_cannot_review` |
| Author cannot approve a specification | `test_author_cannot_approve` |
| Reviewer cannot approve a specification | `test_reviewer_cannot_approve` |
| Approval requires a prior review | `test_approval_requires_prior_review` |
| Operator cannot review their own run | `test_operator_cannot_review_own_run` |
| Setter cannot review their own run | `test_setter_cannot_review_own_run` |

### 3.3 Production gating

| Control | Test |
|---|---|
| Component must be released | `test_setup_requires_released_component` |
| Tool must be in service | `test_setup_requires_tool_in_service` |
| An approved specification must exist | `test_setup_requires_approved_specification` |
| Required start-up readings must be present | `test_startup_blocked_by_missing_readings` |
| Material consumption must be recorded | `test_startup_blocked_by_missing_material` |
| A failing critical parameter blocks production | `test_startup_blocked_by_failing_critical_parameter` |
| An out-of-tolerance run needs a deviation reference | `test_review_requires_deviation_reference` |

### 3.4 Access control

| Control | Test |
|---|---|
| Roles imply one another correctly | `test_role_hierarchy_implied` |
| Viewer cannot create a run | `test_viewer_cannot_create_run` |
| Operator cannot delete a run | `test_operator_cannot_delete_run` |
| Operator cannot create master data | `test_operator_cannot_create_component` |
| **No role holds write or delete on readings** | `test_reading_write_denied_to_every_role` |
| Company isolation holds even for a manager | `test_multi_company_isolation` |
| Isolation rules carry no group link | `test_record_rules_carry_no_group_link` |

### 3.5 Not covered by automated tests

Stated explicitly rather than left to inference.

| Area | Why not covered | How to qualify it |
|---|---|---|
| QWeb report rendering | Requires a rendering engine | Print each report during OQ |
| View rendering and the chatter question | Requires a browser | Visual inspection during OQ |
| Scheduled action behaviour under the real scheduler | Requires a running instance | Observe over several days during PQ |
| Performance at volume | Requires a populated database | Load testing during PQ |
| Upgrade from a previous version | No previous version exists | Applies from 19.0.1.0.1 onwards |
| The `mrp.production` view inheritance | Requires the real Odoo view arch | Confirm at installation |

---

## 4. Static analysis results

Static analysis **was** performed and **did** execute.

| Check | Result |
|---|---|
| Python syntax, all files | PASS |
| XML well-formedness, all files | PASS |
| Manifest completeness and load order | PASS |
| View field references resolve | PASS |
| XML `ref` resolution | PASS |
| ACL model coverage and group references | PASS |
| Button methods exist | PASS |
| PEP 8 subset | PASS |
| No placeholder tokens | PASS |
| No raw SQL | PASS |
| Report templates resolve | PASS |
| **Errors** | **0** |
| **Warnings** | **0** |

### 4.1 The checker was itself validated

A static checker reporting PASS is worthless unless it can report FAIL. Sixteen
deliberate faults were injected into copies of the module and the checker was
required to detect each one.

| Injected fault | Detected |
|---|---|
| Python syntax error | Yes |
| Malformed XML | Yes |
| Manifest declares a missing file | Yes |
| File on disk not declared in the manifest | Yes |
| View references a non-existent field | Yes |
| Unresolvable XML reference | Yes |
| Model with no access control line | Yes |
| ACL references an unknown group | Yes |
| ACL permission value not 0 or 1 | Yes |
| Line over 100 characters | Yes |
| Placeholder token | Yes |
| Raw SQL execution | Yes |
| Model file not imported | Yes |
| Malformed manifest version | Yes |
| Button calls a missing method | Yes |
| Report action points at a missing template | Yes |
| **Detection rate** | **16 of 16** |

This exercise was not a formality. The first run detected only 13 of 15: the
view-field check was silently skipping every model that inherits a mixin — that
is, every model in the module — and one control was itself faulty. Both were
repaired and re-validated. Without fault injection, a broken check would have
been reported as a clean pass.

### 4.2 Tools that were not run

| Tool | Reason |
|---|---|
| `flake8` | Not installed; no network access to install it |
| `pylint` | Same |
| `pylint-odoo` | Same |
| `coverage.py` | Requires test execution, which was impossible |

The custom checker covers a PEP 8 subset only. It is **not** a substitute for
`flake8` or `pylint-odoo`, and both should be run by the receiving team.

---

## 5. Conclusion

Static analysis: **PASS**, with the checker itself validated.

Dynamic testing: **NOT PERFORMED**. 139 tests are written and none has run.

The correct characterisation of this module is *statically verified, dynamically
unverified*. The next action is to install it on an Odoo 19 instance and run the
test suite.
