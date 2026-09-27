# 06 — Test Plan and Test Report

**Phase gate: FAIL — tests written, not executed.**

This gate is recorded honestly as a FAIL. The master prompt requires a
minimum of 95% coverage. No test was run and no coverage was measured, because
Odoo is not installed in the build environment. The gate cannot be claimed as
passed on the basis of code that merely exists.

## 6.1 What exists

92 test methods across 8 test modules, plus a shared fixture module.

| Module | Methods | Area |
|---|---|---|
| `test_deviation_workflow.py` | 19 | Sequence, initial state, every transition, every guard, illegal transitions, transition logging, kanban group expansion |
| `test_deviation_constraints.py` | 17 | Chronology, planned justification, quantity/product coupling, SQL check violation, computed fields, overdue search, deletion policy, copy semantics, terminal write protection, company target fallback |
| `test_deviation_wizards.py` | 15 | Closure path, mandatory conclusions and follow-up, CAPA reference rule, closure blockers, wizard defaults, cancellation, send-back, send-back logging, date extension rules, chatter posting, action helper return shapes |
| `test_deviation_security.py` | 13 | Per-role create/read/write/unlink, reporter record rule scoping, state-limited reporter access, manager override, disposition approval segregation, multi-company isolation |
| `test_deviation_investigation.py` | 9 | Lifecycle, company inheritance, completion guards, date constraint, most-probable-cause path, cascade delete |
| `test_deviation_disposition.py` | 8 | Draft state, approval stamping, double approval, lot/product coherence, SQL quantity constraint, UoM mirroring, rejection, all seven decisions |
| `test_deviation_stage_log.py` | 7 | Write blocked, write blocked for superuser, unlink blocked, unlink blocked for superuser, actor recording, cascade removal, ordering |
| `test_deviation_cron.py` | 4 | Selection correctness, follower subscription, idempotence, empty case |

All classes are tagged `post_install, -at_install`, which is correct for tests
that depend on the module's own data records being loaded.

## 6.2 Test design notes

Users are created with `odoo.tests.common.new_test_user`, which accepts group
external identifiers as a string. This was chosen specifically so that the
fixtures never reference the user-to-group relational field by name — that
field is one of the Odoo 19 renames that could not be confirmed. The
uncertainty is therefore isolated inside a helper maintained by Odoo itself.

SQL constraint tests wrap the offending write in `self.cr.savepoint()` and
`mute_logger("odoo.sql_db")`, so an intentional integrity error does not abort
the surrounding transaction or pollute the log.

Access error tests mute `odoo.addons.base.models.ir_model` and `odoo.models`
for the same reason.

## 6.3 Coverage assessment

**Measured coverage: not available.**

By inspection, every public action method on `ls.deviation`
(`action_assess`, `action_start_investigation`, `action_disposition`,
`action_require_capa`, `action_send_back`, `action_open_close_wizard`,
`action_open_cancel_wizard`, `action_open_due_date_wizard`), every
`@api.constrains` method, every compute and search method, both onchange
methods, the cron, and every wizard `action_confirm` has at least one test
that exercises it. That is an argument for coverage, not a measurement of it.

Untested by inspection: `_track_subtype` (requires message flow assertions),
the QWeb report template rendering, and view rendering. These need a running
instance.

## 6.4 How to execute

```bash
odoo --test-enable --test-tags ls_deviation -d <scratch_db> -i ls_deviation --stop-after-init
```

With coverage:

```bash
coverage run --source=/path/to/addons/ls_deviation \
  $(which odoo) --test-enable --test-tags ls_deviation \
  -d <scratch_db> -i ls_deviation --stop-after-init
coverage report -m
```

## 6.5 Additional testing required before release

| Type | Status |
|---|---|
| Installation test | Not performed |
| Upgrade test (`-u ls_deviation`) | Not performed |
| Uninstall test | Not performed |
| Demo data install test | Not performed |
| Multi-company functional test | Automated test written; not executed |
| Report rendering test | Not written |
| Performance test | Not written. The module has no known hot path; `is_overdue` is non-stored, so filtering on it uses the indexed `due_date` and `state` columns via the search method rather than a Python scan |
| User acceptance test | Not performed |
