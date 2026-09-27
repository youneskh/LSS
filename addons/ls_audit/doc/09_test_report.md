# 09 — Test Report

**Status: NOT EXECUTED.**

This document describes a test suite that has been **written but never run**.
Odoo 19 was not available in the build environment and network access was
disabled, so no test in this suite has ever been executed against a database.

Nothing below may be cited as evidence of correct behaviour. It is evidence
that tests exist.

---

## 1. Inventory

| Module | Tests | Covers |
|---|---|---|
| `test_audit_configuration.py` | 17 | Type code uniqueness, area hierarchy and cycles, qualification status and scope, category rules |
| `test_audit_program.py` | 11 | Reference allocation, date validity, statistics, lifecycle, cancellation |
| `test_audit_workflow.py` | 23 | Full lifecycle, qualification gating, conformity rate, locking, deletion, overdue search |
| `test_audit_independence.py` | 8 | Every impartiality and segregation-of-duties control |
| `test_checklist.py` | 16 | Approval, immutability, versioning, load wizard, copy-on-load |
| `test_finding_workflow.py` | 21 | Lifecycle, deadlines, mandatory root cause and CAPA, verification, evidence |
| `test_audit_report.py` | 12 | Prepare, review, approve, issue, locking, PDF actions |
| `test_security.py` | 13 | Group hierarchy, ACLs, record rules, model coverage |
| `test_cron.py` | 6 | All three scheduled actions, idempotency |
| `test_installation.py` | 8 | Module state, model registration, XML ids, sequences, menus, no legacy tags |
| **Total** | **135** | |

Source size for context: 4,037 lines of Python outside tests, 1,831 lines of
test Python, 2,642 lines of XML.

---

## 2. Controls with a dedicated negative test

Every control below has a test that asserts the module **refuses** the
invalid case. A test that only exercises the happy path does not test a
control.

| Control | Test |
|---|---|
| Team member cannot be an auditee | `test_lead_auditor_cannot_be_auditee`, `test_team_member_cannot_be_auditee` |
| Team member cannot own an audited area | `test_auditor_cannot_own_the_audited_area` |
| Finding auditee cannot be the raiser | `test_finding_auditee_cannot_be_the_raiser` |
| Auditee cannot verify their own finding | `test_finding_cannot_be_verified_by_the_auditee` |
| Preparer cannot review their report | `test_report_preparer_cannot_review` |
| Preparer cannot approve their report | `test_report_preparer_cannot_approve` |
| Unqualified lead auditor blocks scheduling | `test_schedule_requires_qualified_lead_auditor` |
| Expired qualification blocks scheduling | `test_schedule_refuses_expired_qualification` |
| Out-of-scope auditor blocks scheduling | `test_schedule_refuses_out_of_scope_auditor` |
| Adverse result requires evidence | `test_adverse_response_requires_evidence` |
| Mandatory question blocks completion | `test_cannot_complete_with_pending_mandatory_question` |
| Closure requires documented verification | `test_close_requires_documented_verification` |
| Approved checklist is immutable | `test_approved_checklist_questions_are_immutable`, `_cannot_be_deleted`, `_cannot_receive_new_questions` |
| Template change cannot alter a past audit | `test_template_change_does_not_alter_executed_audit` |
| Closed records are read-only | `test_closed_audit_is_read_only`, `test_closed_finding_is_read_only`, `test_issued_report_is_read_only` |
| Auditee row-level isolation | `test_auditee_sees_only_their_own_findings`, `_sees_only_audits_they_take_part_in`, `_does_not_see_a_draft_report` |
| Every model has an ACL | `test_every_model_has_an_access_rule` |

---

## 3. Coverage

**No coverage figure is reported, because none was measured.**

The Phase 7 target was 95%. Whether it is met is unknown and will remain
unknown until the suite runs under `coverage`:

```bash
coverage run --source=addons/ls_audit $(which odoo-bin) \
    -d test_ls_audit -i ls_audit --test-enable --test-tags /ls_audit \
    --stop-after-init
coverage report -m
```

Quoting a number here without measuring it would be fabrication.

### 3.1 Known gaps in the written suite

Even once executed, the following are **not** covered:

| Area | Why |
|---|---|
| QWeb PDF rendering | Only the report *actions* are asserted, not rendered output. Rendering requires wkhtmltopdf |
| Mail template rendering | Templates are asserted to exist, not to render |
| Multi-company record rules | One test creates a second company for an area constraint; full cross-company isolation is untested |
| Upgrade path | There is no prior version to upgrade from |
| Performance | No load or volume testing |
| Concurrency | No test of simultaneous edits |
| UI behaviour | No tour tests; `invisible` and `readonly` expressions are unverified at runtime |

---

## 4. What *was* verified

Static analysis only, via `validate_module.py`. Result: **PASS**.

| Check | Result |
|---|---|
| Python syntax, 30 files | PASS |
| Docstring coverage, 254 functions | PASS — 254/254 |
| Forbidden markers (TODO, FIXME, XXX) | PASS — none |
| XML well-formedness, 24 files, 130 records | PASS |
| Manifest coherence, 25 declared files | PASS |
| XML identifier resolution | PASS |
| ACL integrity, 37 rules, 14 models | PASS — every model covered |
| PEP 8 subset | PASS |
| Odoo 19 regressions | PASS |

This proves the module is **structurally coherent**. It does not prove it
works.

### 4.1 Defects the harness actually caught

| Defect | Consequence had it shipped |
|---|---|
| Explicit writes to `ir.rule.global` (18 occurrences) | Install failure — the field is computed from `groups` |
| Three lines over 79 characters | Style gate failure |
| Four dead fields (`closure_statement`, two `color`, `audit_state`) | Dead code |
| `_order` on the `severity` Selection | Findings sorted alphabetically, not by severity |

---

## 5. Verdict

| Phase 7 requirement | Status |
|---|---|
| Unit tests | Written |
| Integration tests | Written |
| Functional tests | Written |
| Security tests | Written |
| Installation tests | Written |
| Access-right tests | Written |
| Constraint tests | Written |
| Workflow tests | Written |
| Upgrade tests | **Not written** — no prior version exists |
| Performance tests | **Not written** |
| ≥95% coverage | **Unmeasured** |
| **Suite executed** | **NO** |

**Phase 7 verdict: FAIL.**

Corrective action: execute the suite on Odoo 19 Community with `coverage`,
fix every failure, measure coverage, add performance tests, and reissue this
report with real numbers.
