# 12 — Test Report

Phase 7 deliverable. Status: **CONDITIONAL PASS**. The condition is in
section 5.

## 1. Execution status

**The test suite has not been executed.** No Odoo runtime and no PostgreSQL
server are present in the environment where this module was written. What was
verified is stated in section 3.

Consequently:

* No coverage figure is reported. The target of 95 percent stated in the
  master prompt **is not demonstrated** and must not be quoted as achieved.
* No test is reported as passing. Every test below is written, syntactically
  valid, and unrun.

## 2. Test inventory

| Test module | Test methods | Scope |
|---|---|---|
| `test_document_lifecycle` | 28 | State machine, revisions, periodic review, freezing, deletion guards, parameter fallbacks |
| `test_policy` | 5 | Policy content, link to objectives |
| `test_sop` | 5 | Mandatory sections, link to work instructions |
| `test_work_instruction` | 5 | Subordination to the parent procedure |
| `test_quality_plan` | 6 | Control lines, freezing, copy on revision |
| `test_objective` | 16 | Achievement formulas, measurements, lifecycle, constraints |
| `test_quality_record` | 16 | Lifecycle, locking, retention, disposal |
| `test_security` | 11 | Access lists, record rules, group hierarchy |
| `test_wizards` | 6 | Context handling and effects of both wizards |
| `test_cron` | 7 | The three scheduled actions and their idempotence |
| `test_installation` | 10 | Sequences, parameters, rules, activity types, reports, menus |
| **Total** | **115** | 11 test modules and one fixture module |

The fixture module `tests/common.py` creates one user per role using
`new_test_user`, one department, and five record factories.

## 3. What was actually verified

| Verification | Tool | Result |
|---|---|---|
| Python syntax of every source and test file | `python3 -m py_compile` | Passed |
| Well formedness of every XML file | `xmllint --noout` | Passed |
| Structure of the access control list, eight columns on every row | Column count check | Passed |
| Presence of a sequence code for every document model | Cross read of the model and the data file | Passed |

## 4. What was **not** verified, and why

| Not verified | Reason |
|---|---|
| Installation on Odoo 19 | No Odoo runtime in the environment |
| Execution of the tests | Same |
| Coverage | Same |
| `flake8`, `pylint`, `pylint-odoo` | Not installed, and the environment has no network access, so they could not be installed |
| Validity of the view architectures against the ORM | Requires a running registry |
| Behaviour of `res.groups.privilege` | Written from the official Odoo 19 tutorial, never executed |
| Behaviour of `models.Constraint` | Written from the official Odoo 19 tutorial, never executed |

## 5. Condition attached to the PASS

The phase passes on the condition that the operating organisation executes:

```bash
odoo-bin -d <database> -i ls_qms --test-enable --stop-after-init
flake8 ls_qms/
pylint --load-plugins=pylint_odoo -d all -e odoolint ls_qms/
```

and records the outcome. Until then the delivery is a syntactically valid,
untested source package.

## 6. Known limitation of the test design

The ten SQL constraints of the technical specification are not exercised by a
dedicated test. Triggering a PostgreSQL check violation inside a test requires
a savepoint and a flush, and the resulting test verifies PostgreSQL rather
than the module. The equivalent Python constraints are tested instead. This is
a deliberate choice, stated here so that a reader does not assume the SQL
constraints were exercised.
