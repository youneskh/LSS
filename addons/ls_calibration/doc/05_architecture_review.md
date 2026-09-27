# Phase 5 — Architecture Review Report

Module: `ls_calibration`. Reviewers: Solution Architect, Senior Odoo
Architect, Security Engineer, Performance Engineer, Validation Engineer.

## 5.1 Conformity to the Odoo architecture

| Criterion | Verdict | Evidence |
|-----------|---------|----------|
| Standard module layout | Pass | `models`, `wizards`, `views`, `security`, `data`, `demo`, `report`, `tests`, `static/description`. |
| No modification of the Odoo core | Pass | No `ir.ui.view` inheritance of a core view, no monkey patch, no change to a core model. |
| Inheritance used where relevant | Pass | `mail.thread` and `mail.activity.mixin` are inherited by four models; `maintenance.equipment.category` is reused instead of a parallel taxonomy. |
| Model, view and controller separation | Pass | Business rules in the models, presentation in the XML, no logic in the templates. |
| ORM used, no raw SQL | Pass | No `self.env.cr.execute` anywhere. |
| Odoo 19 API | Pass | `models.Constraint`, `<list>`, `<chatter/>`, `self.env._`, `_compute_display_name`, `@api.model_create_multi`. |
| Data files ordered and idempotent | Pass | Security before access rights, views before menus, `noupdate="1"` on the configuration data. |

## 5.2 Conformity to the OCA conventions

| Criterion | Verdict | Comment |
|-----------|---------|---------|
| Version string `19.0.x.y.z` | Pass | `19.0.1.0.0`. |
| Licence declared and headers present | Pass | AGPL-3.0 header in every source file. |
| `README.rst` with `readme/` fragments | Pass | Seven fragments. |
| One file per model, named after it | Pass | Six model files. |
| Field ordering and naming | Pass | Relational fields suffixed `_id` and `_ids`, booleans without prefix. |
| Tests in a `tests` package | Pass | Nine modules. |
| `development_status` declared | Pass | `Beta`, justified in the validation report. |
| OCA repository metadata | Not applicable | The module is not published by the OCA; `maintainers` and `website` are deliberately omitted rather than invented. |

## 5.3 Clean architecture and SOLID

| Principle | Assessment |
|-----------|------------|
| Single responsibility | Each model has one reason to change: the instrument holds identity and metrology, the plan holds the schedule, the record holds the event, the line holds one measurement, the certificate holds the document. The two wizards each perform one operation. |
| Open/closed | The locking policy is expressed by `_get_lock_exempt_fields` and `_get_recompute_exempt_fields`, which a bridge module can extend without rewriting `write`. The record values produced by a plan are built by `_prepare_record_values`, which is the documented extension point. |
| Liskov substitution | No inheritance of a business class; only Odoo mixins are inherited, and their contract is respected. |
| Interface segregation | Public methods are small and single purpose: `action_*` for the workflow, `_check_*` for the rules, `_prepare_*` for the values, `_cron_*` for the scheduled actions. |
| Dependency inversion | The models depend on the ORM abstraction, never on the database. The only cross-model coupling is through documented public methods, for instance `plan._add_interval` used by the record. |

## 5.4 DRY, KISS and separation of concerns

| Principle | Assessment |
|-----------|------------|
| DRY | The acceptance limits are computed once, by `ls.calibration.plan.point._get_limits`, and reused by the record line. The interval arithmetic exists once, in `plan._add_interval`. The state checks share `record._check_state`. The instrument status logic exists once, in `_get_calibration_status`, and is used by the compute method, the search method and the two scheduled actions. |
| KISS | No JavaScript, no controller, no custom widget, no dynamic view. The most complex piece of logic is the search method of the status, which is fifteen lines and fully documented. |
| Separation of concerns | Validation rules are in constraints, workflow rules in `action_*`, integrity rules in the ORM overrides, presentation in the views. A rule is never duplicated between a constraint and a view. |

## 5.5 Upgradeability

| Point | Assessment |
|-------|------------|
| No core view inheritance | An Odoo patch that changes a core view cannot break this module. |
| No JavaScript | The most version-sensitive layer is absent. |
| Version-specific API isolated | The only Odoo 19 specific constructs are `models.Constraint`, the view syntax and `self.env._`. They are used uniformly, so a future migration is a mechanical operation. |
| Configuration data protected | `noupdate="1"` prevents an update from resetting the sequences, the parameter and the scheduled actions. |
| Field renames avoided | No field of a core model is renamed or shadowed. |
| Residual risk | The Odoo 19 rename of `res.users.groups_id` could not be verified. It is not used by the module itself, only by the test fixtures, which resolve the field name at run time. |

## 5.6 Extensibility

Documented extension points: `_prepare_record_values`, `_prepare_record_line_values`,
`_get_limits`, `_get_calibration_status`, `_get_lock_exempt_fields`,
`_get_recompute_exempt_fields`, `_check_ready_for_review`,
`_check_standards_validity`, `_get_open_records`. A bridge module can add a
deviation link on an out-of-tolerance record, block a laboratory result
produced by an overdue instrument, or add a second review step, without
modifying this module.

## 5.7 Maintainability

| Indicator | Value |
|-----------|-------|
| Python files, excluding tests | 13 |
| Longest model file | `ls_calibration_record.py` |
| Longest method | `_check_ready_for_review`, one check per business rule, each with its own message |
| Methods without docstring | 0, enforced by the static analysis |
| Commented-out code | 0, enforced by the static analysis |
| Placeholders, TODO or FIXME | 0, enforced by the static analysis |
| Cyclomatic complexity hot spots | `_check_ready_for_review` and `_search_calibration_status`; both are linear sequences of guarded conditions, not nested logic |

## 5.8 Security review

| Threat | Control |
|--------|---------|
| SQL injection | No raw SQL; every query goes through the ORM. |
| Cross-site scripting | No `t-raw` in the QWeb templates; the rich text field uses the sanitising `Html` field. |
| Privilege escalation | `sudo()` is used only to read the system parameter in the scheduled action, never to write business data. |
| Unauthorised approval | Group check plus segregation of duties check, both server side. |
| Falsification of evidence | `write` and `unlink` overrides on the record, its lines and the certificate. |
| Cross-company data leakage | Six global record rules, plus `check_company=True` on the relational fields and `_check_company_auto = True` on the models. |
| Uncontrolled mass edit | The list view allows multi-edit on the instruments only, which are manager-writable. |

**Finding SEC-01, accepted.** The approval does not re-authenticate the
signer. This is a functional gap against FDA 21 CFR Part 11, declared in the
regulatory analysis and in the README. It is not a defect of the
implementation but a scope decision.

## 5.9 Performance review

| Point | Assessment |
|-------|------------|
| Indexes | `company_id`, `instrument_id`, `plan_id`, `record_id`, `next_calibration_date`, `next_due_date` and the instrument name are indexed. |
| Stored versus computed | The date fields that drive the searches and the scheduled actions are stored; only the volatile status is computed at read time. |
| N+1 queries | The compute methods iterate over the recordset and traverse pre-fetched relations; no query inside a loop. |
| Scheduled action cost | Both actions run one search followed by a bounded iteration. |
| `_search_calibration_status` | Reads the instrument register and filters in Python. Cost is linear in the number of instruments visible to the user. |

**Finding PERF-01, accepted with a documented threshold.** The status search
is not delegated to PostgreSQL. For a register of a few thousand instruments
the cost is negligible. An organisation operating a substantially larger
register should replace the per-instrument alert lead time by a global
parameter, which would make the filter expressible as a plain SQL domain. The
mitigation is recorded in the roadmap.

## 5.10 Validation readiness review

| Point | Assessment |
|-------|------------|
| Requirements traceable to tests | Each business rule of Phase 3 has at least one automated test. |
| Deterministic behaviour | No random value, no dependence on the wall clock except the status, which is derived from the business date. |
| Evidence retention | Approved records and issued certificates cannot be deleted. |
| Attributability | Performer, submitter and approver are recorded with their timestamps. |
| Documented gaps | Five regulatory gaps declared in Phase 2, two findings accepted in this review. |

## 5.11 Findings summary

| # | Finding | Severity | Status |
|---|---------|----------|--------|
| SEC-01 | No re-authentication at signature | Major, functional scope | Accepted and declared |
| PERF-01 | Status search resolved in Python | Minor | Accepted with a documented threshold |
| ARCH-01 | `ls_qms` dependency omitted | Major, deviation from the suite specification | Accepted; declaring a non-existent dependency would prevent installation. Bridge module in the roadmap. |
| ARCH-02 | Security groups without category | Minor | Accepted; the Odoo 19 privilege model could not be verified. |
| ARCH-03 | No kanban view | Informational | Accepted; the Odoo 18 kanban template rewrite could not be verified for 19, and the list views with status badges cover the need. |

No blocking finding.

## Gate

**Phase 5: PASS.** Three major findings are accepted and declared, two minor
and one informational finding are documented. No corrective action is
required before development, which was already completed under these
constraints.
