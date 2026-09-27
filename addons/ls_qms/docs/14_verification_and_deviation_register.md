# 14 — Verification and Deviation Register

This register exists so that a reader can separate what was checked against a
source from what was reasoned, and see every departure from the reference
specification.

## 1. Facts verified against official documentation

| # | Fact | Source consulted | Effect on the code |
|---|---|---|---|
| V-01 | SQL constraints are declared as `models.Constraint` class attributes in Odoo 19 | Official Odoo 19.0 developer tutorial, chapter on constraints | The ten SQL constraints use this form; `_sql_constraints` is not used |
| V-02 | The list view element is `<list>` in Odoo 19 | Official Odoo 19.0 documentation on views | Every list view uses `<list>`; `<tree>` is not used |
| V-03 | The chatter is inserted with the `<chatter/>` element | Official Odoo 19.0 documentation, mixins and useful classes | The seven form views use `<chatter/>`; the legacy `oe_chatter` div is not used |
| V-04 | Conditional display uses direct Python expressions in `invisible` and `readonly` | Official Odoo 19.0 documentation on views | No `attrs` dictionary appears in any view |
| V-05 | Odoo 19 introduces `res.groups.privilege`, and groups carry `privilege_id` while the privilege carries `category_id` | Official Odoo 19.0 tutorial, restricting access to data | `security/ls_qms_security.xml` creates a category, a privilege and four groups in that structure |

## 2. Points that could not be verified

| # | Point | Status | Mitigation applied |
|---|---|---|---|
| U-01 | Whether the many to many field linking users and groups is named `groups_id` or `group_ids` in Odoo 19 | **Could not be verified from official documentation.** Only a non official migration article was found | No code references that field. Record rules are global and use `user.has_group`. Tests create users with `new_test_user` |
| U-02 | ANPP technical requirements for pharmaceutical documentation in Algeria | **Could not be verified from official documentation.** No ANPP publication was retrieved | No ANPP claim is made anywhere in the module. Stated in `02_regulatory_analysis.md`, section 4 |
| U-03 | Whether the review reminder should target the author, the approver or the department head in a given organisation | Not a factual question; no source applies | The author is targeted. Overridable in `_cron_document_review_reminder` |

## 3. Deviations from the reference Functional Specification

| # | Specification says | Delivered | Justification |
|---|---|---|---|
| D-01 | `ls_qms` depends on `document_management` | Depends on `base`, `mail`, `hr` | The named module does not exist. Declaring it makes `ls_qms` impossible to install. Document storage uses `ir.attachment`, with a counter and an attachment action on every document. A future `ls_document_management` can extend it |
| D-02 | Six models are listed for `ls_qms` | Eight stored models and two abstract models | `ls.qms.quality_plan.line` is required because a quality plan is a table of controls, not a text field. `ls.qms.objective.measurement` is required because an objective without a measured series cannot have a computed achievement. The two abstract models carry shared behaviour and create no table |
| D-03 | `hr` is not listed as a dependency | Added | `department_id` targets `hr.department`. Reimplementing a department model would duplicate an existing Odoo model |
| D-04 | Electronic signatures are a separate module of the suite | Not implemented here, extension point provided | Implementing a partial signature here would create a false impression of Part 11 support |

## 4. Statements deliberately **not** made

The following statements are absent from this delivery, and their absence is
intentional. None of them can be supported by evidence available to the
author.

1. That the module is compliant with any regulatory framework.
2. That the module is validated, qualified or certified.
3. That the module installs successfully, since it has never been installed.
4. That the test suite passes, since it has never been executed.
5. That coverage reaches any figure, since coverage was never measured.
6. That the module satisfies any ANPP requirement.
7. That the module passes `flake8` or `pylint-odoo`, since neither was run.
