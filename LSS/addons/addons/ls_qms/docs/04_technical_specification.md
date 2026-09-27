# 04 — Technical Specification

Phase 4 deliverable. Status: **PASS**.

## 1. Directory tree

```
ls_qms/
├── __init__.py
├── __manifest__.py
├── README.md
├── CHANGELOG.md
├── RELEASE_NOTES.md
├── data/          4 files
├── demo/          1 file
├── docs/          14 files
├── i18n/          1 file, see section 9
├── models/        10 files
├── report/        5 files
├── security/      2 files
├── static/description/icon.png
├── tests/         13 files
├── views/         9 files
└── wizards/       4 files
```

## 2. Dependencies

`base`, `mail`, `hr`. No Python package outside the Odoo runtime is required.
`dateutil` is used and is already a dependency of Odoo itself.

The Functional Specification lists `document_management` as a dependency of
`ls_qms`. That module does not exist. Declaring it would make `ls_qms`
impossible to install. See `14_verification_and_deviation_register.md`,
deviation D-01.

## 3. Models and fields

### 3.1 `ls.qms.parameter.mixin` (abstract)

Two helpers, `_get_int_parameter` and `_get_bool_parameter`, read
`ir.config_parameter` and fall back to a documented default when the stored
value is absent, not a number, or negative.

### 3.2 `ls.qms.document.mixin` (abstract)

Inherits `mail.thread`, `mail.activity.mixin`, `ls.qms.parameter.mixin`.

Fields: `name`, `reference`, `version`, `state`, `active`, `company_id`,
`author_id`, `reviewer_ids`, `approver_id`, `department_id`,
`date_submitted`, `date_approved`, `date_effective`, `date_obsolete`,
`review_period_months`, `date_next_review`, `review_state`,
`reason_for_change`, `attachment_count`.

`date_next_review` is computed and stored, and remains writable so that a
review can be brought forward. `review_state` is computed and not stored.

### 3.3 Concrete models

| Model | Own fields |
|---|---|
| `ls.qms.policy` | `policy_statement`, `scope`, `commitment`, `communication_method`, `previous_revision_id`, `next_revision_ids`, `objective_ids`, `objective_count` |
| `ls.qms.sop` | `purpose`, `scope`, `definitions`, `responsibilities`, `procedure`, `reference_documents`, `training_required`, `previous_revision_id`, `next_revision_ids`, `work_instruction_ids`, `work_instruction_count` |
| `ls.qms.work_instruction` | `sop_id`, `instruction_body`, `equipment_reference`, `safety_precautions`, `estimated_duration_minutes`, `previous_revision_id`, `next_revision_ids` |
| `ls.qms.quality_plan` | `subject`, `scope`, `objective_summary`, `line_ids`, `line_count`, `sop_ids` |
| `ls.qms.quality_plan.line` | `sequence`, `quality_plan_id`, `company_id`, `stage`, `characteristic`, `specification`, `control_method`, `frequency`, `sample_size`, `responsible_id`, `sop_id`, `record_reference` |
| `ls.qms.objective` | `name`, `reference`, `active`, `company_id`, `policy_id`, `department_id`, `responsible_id`, `description`, `state`, `date_start`, `date_target`, `direction`, `uom_name`, `baseline_value`, `target_value`, `tolerance`, `measurement_ids`, `measurement_count`, `current_value`, `last_measurement_date`, `achievement_rate`, `performance_status` |
| `ls.qms.objective.measurement` | `objective_id`, `company_id`, `date`, `value`, `comment`, `recorded_by_id` |
| `ls.qms.quality_record` | `name`, `reference`, `active`, `company_id`, `record_type`, `state`, `date_record`, `author_id`, `department_id`, `description`, `conclusion`, `policy_id`, `sop_id`, `quality_plan_id`, `objective_id`, `retention_period_months`, `date_retention_until`, `retention_expired`, `attachment_count` |

`previous_revision_id` is declared on each concrete model and not on the
abstract mixin, because a relational field cannot target an abstract model.

## 4. Database constraints

Ten SQL constraints, declared as `models.Constraint` class attributes, which
is the Odoo 19 form.

| Model | Constraint | Rule |
|---|---|---|
| `ls.qms.policy` | `_reference_version_uniq` | unique(reference, version, company_id) |
| `ls.qms.sop` | `_reference_version_uniq` | unique(reference, version, company_id) |
| `ls.qms.work_instruction` | `_reference_version_uniq` | unique(reference, version, company_id) |
| `ls.qms.work_instruction` | `_duration_positive` | check(estimated_duration_minutes >= 0) |
| `ls.qms.quality_plan` | `_reference_version_uniq` | unique(reference, version, company_id) |
| `ls.qms.objective` | `_reference_uniq` | unique(reference, company_id) |
| `ls.qms.objective` | `_dates_consistent` | check(date_target >= date_start) |
| `ls.qms.objective` | `_tolerance_positive` | check(tolerance >= 0) |
| `ls.qms.quality_record` | `_reference_uniq` | unique(reference, company_id) |
| `ls.qms.quality_record` | `_retention_positive` | check(retention_period_months >= 0) |

Python constraints complement them where the rule needs the ORM:
`_check_single_published_revision`, `_check_review_period_months`,
`_check_effective_after_approval`, `_check_sop_company`,
`_check_target_direction`, `_check_date_within_objective`.

## 5. Security

### 5.1 Structure

Odoo 19 places `res.groups.privilege` between `ir.module.category` and
`res.groups`. The module therefore creates one category **Life Sciences**,
one privilege **Quality Management**, and four groups carrying `privilege_id`.

### 5.2 Access control lists

26 rows in `security/ir.model.access.csv`, three per stored model plus one
per wizard. Viewer rows grant read only. User rows grant read, write and
create. Manager rows add unlink.

### 5.3 Record rules

Eight global rules, one per stored model. Document rules combine, with a
logical AND, the multi company isolation and the restriction of viewers to
published revisions:

```
[('company_id', 'in', company_ids)] + ([] if user.has_group('ls_qms.group_ls_qms_user') else [('state', '=', 'published')])
```

A global rule is used because group rules are combined with a logical OR: a
user holding two groups obtains the union of their domains, which makes a
narrowing rule ineffective. This construction also avoids referencing the
many to many field of `ir.rule`, whose name differs between versions.

## 6. Data files

| File | Content |
|---|---|
| `data/ir_sequence_data.xml` | Six sequences: POL, SOP, WI, QPL, OBJ padded to four digits, QR padded to five |
| `data/mail_activity_type_data.xml` | Three activity types: document review, objective monitoring, retention review |
| `data/ir_config_parameter_data.xml` | Four parameters, listed in `07_configuration_guide.md` |
| `data/ir_cron_data.xml` | Three scheduled actions |

All four are loaded with `noupdate="1"` so that a module upgrade never
overwrites a value changed by the operating organisation.

## 7. Demonstration data

`demo/ls_qms_demo.xml` creates one department, one published policy, two
objectives with two measurements, one published procedure, one published work
instruction, one draft quality plan with two control lines, and one confirmed
quality record. It references only `base.user_admin`, so it does not depend
on the demonstration data of any other module.

## 8. Reports

`report/ls_qms_common_templates.xml` defines two shared templates used by the
three document templates. It is loaded before the report actions, because a
QWeb template must exist before a template that calls it is registered.

## 9. Translations

`i18n/` is empty and ships no `.pot` file. A translation template must be
produced by the Odoo export, from an installed database:

```bash
odoo-bin -d <database> --modules=ls_qms --i18n-export=ls_qms.pot --stop-after-init
```

Writing a `.pot` by hand would produce line references that do not correspond
to the source, which is fabricated data.
