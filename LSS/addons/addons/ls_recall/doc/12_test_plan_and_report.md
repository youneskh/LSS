# Test Plan and Test Report

Module: `ls_recall`

---

## 1. Statement to read before anything else

**No test in this suite has been executed.**

The environment in which this module was written has no Odoo runtime and
no network access with which to install one. `flake8`, `pylint` and
`pylint-odoo` were likewise unavailable and could not be installed.

Therefore:

* **No coverage figure is reported.** The source specification asks for
  95%. That number is not claimed, estimated or implied. Coverage is
  **unmeasured**.
* **No test is reported as passing.** The tests are written and
  syntactically valid; whether they pass is unknown.
* The static analysis in §5 **was** executed, and its results are real.

Anything in this document stated as a result was produced by a command
that actually ran. Anything not yet run is labelled as such.

## 2. Test plan

### 2.1 Levels

| Level | Where | Status |
|-------|-------|--------|
| Static analysis | `static_checks.py` | **Executed — passes** |
| Unit | `tests/test_*.py` | Written, not executed |
| Integration (stock) | `tests/test_traceability.py` | Written, not executed |
| Security | `tests/test_security.py` | Written, not executed |
| Installation | Manual | Not performed |
| Upgrade | Manual | Not performed |
| Performance | Manual | Not performed |
| User acceptance | Manual | Not performed |

### 2.2 Written tests

| File | Test methods |
|------|--------------|
| `test_communication.py` | 12 |
| `test_cron.py` | 6 |
| `test_effectiveness.py` | 10 |
| `test_execution_workflow.py` | 23 |
| `test_line_reconciliation.py` | 9 |
| `test_plan_lifecycle.py` | 10 |
| `test_report_immutability.py` | 10 |
| `test_security.py` | 12 |
| `test_traceability.py` | 7 |
| **Total** | **99** |

Counted from the source by AST, not by hand.

### 2.3 Requirement coverage of the written tests

Every requirement in `01_business_analysis.md` §2 is addressed by at
least one written test.

| Requirement | Test |
|-------------|------|
| R1 plan versioning | `test_plan_lifecycle::test_new_revision_supersedes_previous` |
| R2 deputy required | `test_plan_lifecycle::test_cannot_approve_without_deputy` |
| R4 tracing from stock | `test_traceability::test_trace_creates_one_line_per_consignee_and_lot` |
| R5 trace preserves user data | `test_traceability::test_retracing_preserves_user_entered_returns` |
| R7 content confirmation | `test_communication::test_approval_requires_content_confirmations` |
| R8 sent notice immutable | `test_communication::test_sent_communication_is_frozen` |
| R9 sampling levels | `test_execution_workflow::test_required_checks_follow_the_level` |
| R10 escalation | `test_effectiveness::test_escalation_plans_a_further_attempt` |
| R11 quantity arithmetic | `test_line_reconciliation::test_accounted_and_outstanding` |
| R12 discrepancy flag | `test_line_reconciliation::test_status_discrepancy` |
| R13 transition gates | `test_execution_workflow::test_cannot_skip_a_state` and six others |
| R14 closure gates surfaced | `test_execution_workflow::test_closure_gates_reported` |
| R15 manager-only override | `test_security::test_closure_override_is_manager_only` |
| R16 closed record read-only | `test_execution_workflow::test_closed_recall_is_immutable` |
| R17 frozen report figures | `test_report_immutability::test_approval_freezes_the_figures` |
| R18 cancel not delete | `test_execution_workflow::test_cancellation_records_the_reason` |
| R19 rehearsals excluded | `test_cron::test_mock_recall_not_monitored` |
| R20 rehearsal reminder | `test_cron::test_overdue_mock_recall_raises_an_activity` |

**Coverage of requirements by written tests is not the same as code
coverage, and neither has been measured by execution.**

## 3. Environment constraints, verified

Commands run in the build environment:

| Check | Result |
|-------|--------|
| `python3 --version` | 3.12.3 |
| `python3 -c "import lxml"` | available |
| `which flake8 pylint black` | **absent** |
| Odoo importable | **no** |
| Network from shell | **disabled**, so nothing could be installed |

## 4. What was executed

### 4.1 Python compilation

`python3 -m compileall` over the module: **all 25 Python files compile.**

### 4.2 XML well-formedness

All 17 XML files parsed with `lxml`: **all well-formed.**

### 4.3 Static analysis

`python3 static_checks.py ls_recall` → **PASS, no blocking finding.**

Reported inventory:

```
Models declared: 9
  ls.recall.close.wizard: 7 fields, 2 methods
  ls.recall.communication: 25 fields, 12 methods
  ls.recall.effectiveness: 14 fields, 6 methods
  ls.recall.execution: 59 fields, 36 methods
  ls.recall.initiate.wizard: 12 fields, 3 methods
  ls.recall.line: 19 fields, 8 methods
  ls.recall.plan: 24 fields, 17 methods
  ls.recall.report: 33 fields, 9 methods
  stock.lot: 3 fields, 2 methods
XML ids declared: 162
```

Checks performed: Python syntax; XML well-formedness; manifest and disk
agreement in both directions; every `<field>` in every view architecture
resolved against the target model's declared fields, following
relational fields into sub-views; every `<button type="object">`
resolved against the model's methods; every `ref=`, `groups=`, `parent=`
and `action=` resolved against declared or known-external ids; the
access rights CSV for duplicate ids, unknown models, unknown groups and
uncovered models; Python line length, trailing whitespace, tabs and
placeholder markers; docstrings on every module, class and function.

### 4.4 Negative control on the static analyser

A checker that reports PASS is worthless unless it can fail. Four faults
were injected into a copy and the analyser was re-run:

| Injected fault | Detected |
|----------------|----------|
| View field renamed to `verzion` | Yes — "references unknown field 'verzion'" |
| Button method renamed to `action_initiate_typo` | Yes — "calls unknown method" |
| ACL group changed to `group_ls_recall_ghost` | Yes — "names unknown group" |
| Cron `ref` changed to `model_ls_recall_ghost` | Yes — "points at undeclared id" |

Four faults, four detections, no false negatives. The copy was then
discarded and the real module re-verified as passing.

### 4.5 Findings fixed as a result

Eight, listed in `05_architecture_review.md` §6. Two would have prevented
installation (`web_icon` with no icon file; `ir.ui.view.groups_id`
renamed in Odoo 19) and one would have displayed every rate a hundred
times too large.

## 5. What was not executed

| Activity | Why | What to do |
|----------|-----|-----------|
| The 99 tests | No Odoo runtime | Run `--test-tags /ls_recall`; start with `test_traceability.py` |
| Coverage measurement | Same | Run under `coverage.py`; report the real figure |
| `flake8`, `pylint-odoo` | Not installed, no network | Run both; expect findings this analyser does not model |
| Installation and upgrade | No runtime | Install on a clean 19.0 database, then upgrade |
| Performance | No runtime | Exercise tracing against a realistic movement volume |

## 6. Result

| Phase | Result |
|-------|--------|
| Static analysis | **PASS** (executed) |
| Dynamic testing | **NOT PERFORMED** |

The module is **not** qualified. It is ready to enter qualification. The
open items are enumerated in `14_verification_register.md`.
