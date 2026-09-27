# Phase 5 - Architecture Review Report

Module: `ls_change_control` | Reviewed version 19.0.1.0.0

## 1. Method

The design was reviewed against the Odoo architecture, the OCA conventions and
the general design principles required by the master specification. Each
criterion below carries a verdict and, where relevant, the evidence or the
accepted trade-off.

## 2. Odoo architecture

| Criterion | Verdict | Evidence |
|-----------|---------|----------|
| Standard module layout | Pass | `models`, `views`, `security`, `data`, `demo`, `report`, `wizards`, `tests`, `i18n`, `static/description` |
| Manifest complete and versioned for the target | Pass | Version `19.0.1.0.0`, five components, verified mechanically |
| No modification of Odoo core | Pass | Only `res.company` is inherited, and only to add four prefixed fields |
| No `xpath` into a standard view | Pass | The module ships its own settings form instead of extending `res.config.settings` |
| Inheritance used where extension is needed | Pass | `_inherit` on `res.company`, `mail.thread`, `mail.activity.mixin` |
| Model, view and controller separation | Pass | Business rules live in the models; views carry no logic beyond visibility; there is no controller because the module exposes no HTTP route |
| ORM used, no raw SQL | Pass | No `self.env.cr.execute` anywhere in the module |
| Odoo 19 syntax throughout | Pass | Verified mechanically: no `tree`, no `attrs`, no `states`, no `oe_chatter`, no `kanban-box`, no `t-esc`, no `_sql_constraints` |

## 3. OCA conventions

| Criterion | Verdict | Comment |
|-----------|---------|---------|
| AGPL-3 licence declared, copyright header on every file | Pass | |
| One model per file, file named after the model | Pass | |
| Model files imported in dependency order | Pass | `res_company`, configuration models, then transactional models |
| Data files loaded with `noupdate="1"` | Pass | All five data files |
| Access rights file covering every model | Pass | Verified mechanically |
| Demo data separated from master data | Pass | `demo/` versus `data/` |
| Tests in a `tests` package with `post_install` tags | Pass | Twelve files |
| Naming of external identifiers prefixed and predictable | Pass | `view_`, `action_`, `menu_`, `group_`, `rule_`, `access_`, `cron_`, `mail_template_`, `seq_` |

## 4. SOLID

| Principle | Assessment |
|-----------|------------|
| Single responsibility | Each model has one reason to change: the request owns the lifecycle, the assessment owns the evaluation of one area, the approval owns one decision, the implementation owns one task, the verification owns one effectiveness check. Configuration is separated from transactional data |
| Open/closed | The module is extended without modification through four documented points: `_apply_signature` for signing, `_get_blocking_reasons` for additional guards, `selection_add` on the approval roles and the action types, and the category configuration which changes behaviour without changing code |
| Liskov substitution | No class hierarchy beyond the Odoo model inheritance, which is used as intended. No override weakens the contract of a parent method: `write`, `unlink` and `create` all call `super()` and only add preconditions |
| Interface segregation | Sub-models expose narrow, purpose-built methods rather than a generic `action_change_state`. A caller of `action_complete` on an assessment cannot accidentally reach approval behaviour |
| Dependency inversion | The request never imports a child model class; it addresses children through `self.env[...]` and through one2many fields, so a downstream module can replace a child model behaviour by inheritance alone |

## 5. DRY

| Duplication risk | Resolution |
|------------------|------------|
| Three decisions requiring a justification | One `decision_wizard` with a `mode`, delegating to the request methods |
| Same guard needed in the transition and in the user interface | One `_get_blocking_reasons` used by the transition guard and by the `blocking_reasons` computed field |
| Approval role list needed in two models | One `APPROVAL_ROLES` constant imported by both |
| Verification delay resolution needed in two places | One `get_verification_delay` method on the category |
| Smart button actions | One `_action_view_related` helper, four thin callers |
| Immutability checks | The same pattern is expressed once per model, deliberately, because the protected field sets differ; factoring it into a mixin would have coupled five models to a shared abstraction for four lines of code each |

## 6. KISS

| Decision | Simpler alternative rejected, and why |
|----------|--------------------------------------|
| Selection field for the state rather than a stage model | A configurable stage model would let an administrator alter a regulated workflow at run time. A fixed selection makes the state machine deterministic and testable |
| Approvals collected inside the assessment state | Adding an eighth state would have deviated from the specification |
| Configuration on `res.company` rather than `res.config.settings` | Fewer moving parts, no dependency on the layout of the standard settings screen, and correct behaviour in a multi-site organisation |
| Text references for risk, follow-up and documents | Avoids fabricating dependencies on modules that do not exist |

## 7. Separation of concerns

| Concern | Where it lives |
|---------|---------------|
| Lifecycle rules | `change_control_request.py` transition methods |
| Field level integrity | `_check_system_fields`, `_check_content_fields`, `_check_writer` |
| Record level access | `security/ls_change_control_rules.xml` |
| Operation level access | `security/ir.model.access.csv` |
| Configuration | Category, impact area, approval template, `res.company` |
| Presentation | `views/`, no business logic |
| Rendering | `report/`, no business logic |
| Notification | Mail templates and the `_send_mail_template` helper |

## 8. Upgradeability

| Criterion | Verdict | Comment |
|-----------|---------|---------|
| No standard view is modified | Pass | Nothing to repair when Odoo changes its own layouts |
| No standard field is modified | Pass | Only additive fields, all prefixed `ls_cc_` |
| Data files are `noupdate` | Pass | A module upgrade does not overwrite the site configuration |
| Sequence is not reset by an upgrade | Pass | `noupdate="1"` on the sequence record |
| No deprecated Odoo 19 API is used | Pass | Verified mechanically |
| Model names follow the specification | Pass | `ls.change_control.*` as required by section 15.3 |
| No renaming of a field between minor versions is anticipated | Accepted risk | A future rename would require a migration script; none is needed for the initial release |

## 9. Extensibility

Four documented extension points, listed in `docs/developer_manual.md`:
`_apply_signature`, `_get_blocking_reasons`, `selection_add` on the closed
selection lists, and the category configuration.

## 10. Maintainability

| Indicator | Value |
|-----------|-------|
| Python files in the module, excluding tests | 12 |
| Longest model file | `change_control_request.py` |
| Maximum line length | 88 characters, enforced mechanically |
| Docstring coverage of modules, classes and public methods | 100 percent, enforced mechanically |
| Dead code, commented out code, placeholders | None, enforced mechanically |
| Test files | 12 |

## 11. Findings and residual risks

| # | Finding | Severity | Disposition |
|---|---------|----------|-------------|
| F-1 | The module was never installed, upgraded or executed in the build environment | High | Accepted and disclosed. The receiving organisation must perform installation and operational qualification. See `docs/validation_report.md` |
| F-2 | The automated test suite was written but never run | High | Accepted and disclosed. Same as F-1 |
| F-3 | `copy_data` returning a list is a version sensitive contract | Medium | Correct for Odoo 17 and above; a change would be caught immediately by `test_copy_resets_the_lifecycle` |
| F-4 | `_render_qweb_html` signature is version sensitive | Low | Only used in tests, never in production code |
| F-5 | An assessor must hold the Requester group | Low | Deliberate, to keep the four groups of the specification. Documented in the configuration guide |
| F-6 | No re-authentication at the moment of signing | Medium for an organisation subject to FDA 21 CFR Part 11 | Deliberate and disclosed. Assigned to `ls_electronic_signature` |
| F-7 | The suite dependencies `ls_qms` and `ls_validation` are not declared | Medium | Unavoidable: the modules do not exist. Integration points are documented |

## 12. Verdict

**PASS**, with the seven findings above recorded and disclosed. Findings F-1
and F-2 are not defects of the design; they are limitations of the environment
in which the module was built, and they define the work the receiving
organisation must perform before the module can be considered qualified.
