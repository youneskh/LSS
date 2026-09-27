# PHASE 4 — TECHNICAL SPECIFICATION

Module: `ls_training` — Life Sciences Training Management
Target: Odoo 19.0 Community Edition, Python 3, PostgreSQL

---

## 1. Directory tree

```
ls_training/
├── __init__.py
├── __manifest__.py
├── README.rst
├── data/
│   ├── ir_config_parameter_data.xml
│   ├── ir_cron_data.xml
│   ├── ir_sequence_data.xml
│   └── mail_template_data.xml
├── demo/
│   └── ls_training_demo.xml
├── doc/
│   ├── administrator_manual.md
│   ├── api_documentation.md
│   ├── architecture_review.md
│   ├── business_analysis.md
│   ├── changelog.md
│   ├── configuration_guide.md
│   ├── developer_manual.md
│   ├── functional_specification.md
│   ├── installation_guide.md
│   ├── regulatory_analysis.md
│   ├── release_notes.md
│   ├── technical_specification.md
│   ├── test_report.md
│   ├── user_manual.md
│   ├── validation_report.md
│   └── verification_notes.md
├── i18n/
│   └── ls_training.pot
├── models/
│   ├── __init__.py
│   ├── hr_employee.py
│   ├── ls_training_attendance.py
│   ├── ls_training_certification.py
│   ├── ls_training_competency.py
│   ├── ls_training_competency_assessment.py
│   ├── ls_training_course.py
│   ├── ls_training_requirement.py
│   └── ls_training_session.py
├── report/
│   ├── ls_training_certificate_template.xml
│   ├── ls_training_employee_record_template.xml
│   └── ls_training_report_actions.xml
├── security/
│   ├── ir.model.access.csv
│   ├── ls_training_groups.xml
│   ├── ls_training_record_rules.xml
│   └── ls_training_record_rules_alt_groups.xml
├── static/description/
│   ├── icon.png
│   └── index.html
├── tests/
│   ├── __init__.py
│   ├── common.py
│   ├── test_certification.py
│   ├── test_competency.py
│   ├── test_course.py
│   ├── test_cron.py
│   ├── test_requirement_matrix.py
│   ├── test_security.py
│   ├── test_session_workflow.py
│   └── test_wizards.py
├── views/
│   ├── hr_employee_views.xml
│   ├── ls_training_attendance_views.xml
│   ├── ls_training_certification_views.xml
│   ├── ls_training_competency_assessment_views.xml
│   ├── ls_training_competency_views.xml
│   ├── ls_training_course_views.xml
│   ├── ls_training_menus.xml
│   ├── ls_training_requirement_views.xml
│   └── ls_training_session_views.xml
└── wizards/
    ├── __init__.py
    ├── ls_training_matrix_wizard.py
    ├── ls_training_matrix_wizard_views.xml
    ├── ls_training_session_register_wizard.py
    └── ls_training_session_register_wizard_views.xml
```

## 2. Manifest

| Key | Value |
|-----|-------|
| `name` | Life Sciences - Training Management |
| `version` | 19.0.1.0.0 |
| `category` | Human Resources/Training |
| `license` | AGPL-3 |
| `depends` | `base`, `mail`, `hr` |
| `external_dependencies` | none (python: [], bin: []) |
| `application` | True |
| `auto_install` | False |
| `installable` | True |

`mail` is declared explicitly even though `hr` pulls it in, because the
module uses `mail.thread`, `mail.activity.mixin` and `mail.template`
directly. Relying on a transitive dependency would be fragile.

**No third-party Python package is required.** `dateutil` is a hard
dependency of Odoo itself and is therefore not listed in
`external_dependencies`.

## 3. Data model

### 3.1 `ls.training.competency`

Inherits: none. Order: `code, name`.

| Field | Type | Notes |
|-------|------|-------|
| `name` | Char | required, translate, index |
| `code` | Char | required, copy=False |
| `active` | Boolean | default True |
| `company_id` | Many2one res.company | required, index |
| `description` | Text | translate |
| `minimum_level` | Selection | developing/proficient/expert, required, default proficient |
| `reassessment_months` | Integer | default 0 (no periodic reassessment) |
| `course_ids` | Many2many ls.training.course | rel `ls_training_course_competency_rel` |
| `assessment_ids` | One2many assessment | inverse `competency_id` |
| `assessment_count` | Integer | computed via `_read_group` |

### 3.2 `ls.training.course`

Inherits: `mail.thread`, `mail.activity.mixin`. Order: `code, name`.

| Field | Type | Notes |
|-------|------|-------|
| `name` | Char | required, translate, tracking |
| `code` | Char | required, copy=False, sequence-assigned, tracking |
| `version` | Char | required, default "1.0", tracking |
| `active` | Boolean | default True |
| `company_id` | Many2one res.company | required, index |
| `state` | Selection | draft/review/approved/obsolete, tracking, index |
| `course_type` | Selection | induction/gmp/sop/technical/safety/quality/regulatory |
| `delivery_mode` | Selection | classroom/on_the_job/self_study/external_elearning |
| `elearning_url` | Char | required by constraint when mode is external_elearning |
| `description` | Html | translate |
| `objective` | Text | translate |
| `duration_hours` | Float | required, > 0 |
| `validity_months` | Integer | 0 = no expiry |
| `requires_assessment` | Boolean | tracking |
| `pass_score` | Float | 0…100 |
| `competency_ids` | Many2many competency | |
| `session_ids` / `session_count` | One2many / Integer | |
| `certification_ids` / `certification_count` | One2many / Integer | |
| `requirement_ids` | One2many requirement | |

### 3.3 `ls.training.session`

Inherits: `mail.thread`, `mail.activity.mixin`. Order: `date_start desc, id desc`.

| Field | Type | Notes |
|-------|------|-------|
| `name` | Char | required, readonly, sequence-assigned |
| `course_id` | Many2one course | required, ondelete restrict, domain state=approved |
| `company_id` | Many2one res.company | required, index |
| `state` | Selection | draft/confirmed/in_progress/done/cancelled |
| `date_start` / `date_end` | Datetime | required, end > start |
| `trainer_employee_id` | Many2one hr.employee | ondelete restrict |
| `trainer_external` | Char | mutually exclusive with the above |
| `location` | Char | |
| `capacity` | Integer | 0 = unlimited, CHECK ≥ 0 |
| `attendance_ids` | One2many attendance | |
| `attendee_count`, `passed_count`, `failed_count` | Integer | computed, **stored** |
| `certification_ids` / `certification_count` | One2many / Integer | |
| `note` | Text | |

### 3.4 `ls.training.attendance`

Order: `session_id desc, employee_id`.

| Field | Type | Notes |
|-------|------|-------|
| `session_id` | Many2one session | required, ondelete cascade, index |
| `employee_id` | Many2one hr.employee | required, ondelete restrict, index |
| `course_id` | Many2one course | related session_id.course_id, **stored** |
| `company_id` | Many2one res.company | related, stored |
| `session_state` | Selection | related, stored |
| `date_start` | Datetime | related, stored |
| `attended` | Boolean | default False |
| `score` | Float | 0…100 |
| `requires_assessment`, `pass_score` | related (non-stored) | |
| `result` | Selection | computed, **stored**, index |
| `comment` | Text | |

`course_id`, `company_id` and `date_start` are stored related fields so
that grouping and filtering do not require a join at query time.

### 3.5 `ls.training.certification`

Inherits: `mail.thread`. Order: `date_granted desc, id desc`.

| Field | Type | Notes |
|-------|------|-------|
| `name` | Char | required, readonly, sequence-assigned |
| `employee_id`, `course_id` | Many2one | required, ondelete restrict, index, tracking |
| `session_id` | Many2one session | optional (empty for external training) |
| `company_id` | Many2one res.company | required, index |
| `course_version` | Char | required, frozen at creation |
| `date_granted` | Date | required, index, tracking |
| `date_expiry` | Date | computed, **store=True, readonly=False** (overridable) |
| `score` | Float | 0…100 |
| `revoked` | Boolean | copy=False, tracking |
| `revocation_reason` | Text | required by constraint when revoked |
| `state` | Selection | computed, **stored**, index |
| `days_to_expiry` | Integer | computed, non-stored |
| `competency_ids` | Many2many competency | |

### 3.6 `ls.training.competency.assessment`

Inherits: `mail.thread`. Order: `date_assessment desc, id desc`.

| Field | Type | Notes |
|-------|------|-------|
| `employee_id`, `competency_id`, `assessor_id` | Many2one | required, ondelete restrict |
| `company_id` | Many2one res.company | required |
| `date_assessment` | Date | required, index |
| `date_next` | Date | computed, store, readonly=False |
| `level` | Selection | not_demonstrated/developing/proficient/expert |
| `is_acquired` | Boolean | computed, stored, compares level to competency minimum |
| `state` | Selection | draft/confirmed |
| `evidence` | Text | required to confirm |

Level ordering is held in the module constant `LEVEL_ORDER`.

### 3.7 `ls.training.requirement`

Order: `course_id, job_id, department_id`.

| Field | Type | Notes |
|-------|------|-------|
| `course_id` | Many2one course | required, ondelete cascade |
| `company_id` | Many2one res.company | required |
| `active` | Boolean | default True |
| `job_id`, `department_id`, `employee_id` | Many2one | all optional, at least one required by constraint |
| `mandatory` | Boolean | default True |
| `grace_days` | Integer | default 30, CHECK ≥ 0 |
| `note` | Text | |
| `target_employee_count` | Integer | computed, non-stored |

### 3.8 `hr.employee` (inherited)

| Field | Type | Notes |
|-------|------|-------|
| `ls_training_certification_ids` | One2many | |
| `ls_training_certification_count` | Integer | computed |
| `ls_training_attendance_ids` | One2many | |
| `ls_training_assessment_ids` | One2many | |
| `ls_training_required_count` | Integer | computed, non-stored |
| `ls_training_compliant_count` | Integer | computed, non-stored |
| `ls_training_compliance_rate` | Float | computed, non-stored |

Compliance fields are deliberately **not stored**: they depend on the
current date through certification status and would otherwise be stale
between scheduled recomputations. The cost is that they cannot be searched
or grouped; the matrix wizard covers that need.

### 3.9 Transient models

| Model | Purpose |
|-------|---------|
| `ls.training.session.register.wizard` | Bulk registration |
| `ls.training.matrix.wizard` | Matrix scope and generation |
| `ls.training.matrix.line` | One generated matrix cell |

Transient models rely on Odoo's built-in per-user isolation and vacuum; no
record rules are declared for them.

## 4. Compute, onchange and CRUD overrides

### 4.1 Compute methods

| Model | Method | Depends | Stored |
|-------|--------|---------|--------|
| competency | `_compute_assessment_count` | assessment_ids | no |
| competency | `_compute_display_name` | code, name | no |
| course | `_compute_session_count` | session_ids | no |
| course | `_compute_certification_count` | certification_ids | no |
| course | `_compute_display_name` | code, name, version | no |
| session | `_compute_attendance_statistics` | attendance_ids, attendance_ids.result | **yes** |
| session | `_compute_certification_count` | certification_ids | no |
| session | `_compute_display_name` | name, course_id | no |
| attendance | `_compute_result` | attended, score, course requires_assessment, course pass_score | **yes** |
| attendance | `_compute_display_name` | employee_id, session_id | no |
| certification | `_compute_date_expiry` | date_granted, course validity_months | **yes**, readonly=False |
| certification | `_compute_state` | date_expiry, revoked | **yes** |
| certification | `_compute_days_to_expiry` | date_expiry | no |
| certification | `_compute_display_name` | name, employee_id, course_id | no |
| assessment | `_compute_date_next` | date_assessment, competency reassessment_months | **yes**, readonly=False |
| assessment | `_compute_is_acquired` | level, competency minimum_level | **yes** |
| assessment | `_compute_display_name` | employee_id, competency_id, date_assessment | no |
| requirement | `_compute_target_employee_count` | job_id, department_id, employee_id, company_id | no |
| requirement | `_compute_display_name` | course_id, job_id, department_id, employee_id | no |
| hr.employee | `_compute_ls_training_counters` | certification_ids | no |
| hr.employee | `_compute_ls_training_compliance` | (no depends — date-sensitive) | no |

Counter computes use `_read_group` with `__count` rather than iterating
`len(record.x_ids)` per record, to avoid N+1 queries on list views.

### 4.2 Onchange methods

| Model | Method | Effect |
|-------|--------|--------|
| course | `_onchange_requires_assessment` | clears pass score when assessment disabled; proposes 80 when enabled |
| session | `_onchange_course_id` | proposes `date_end` from `date_start` + course duration |
| register wizard | `_onchange_selection_mode` | clears criteria belonging to other modes |

### 4.3 CRUD overrides

| Model | Override | Purpose |
|-------|----------|---------|
| course | `create` (`@api.model_create_multi`) | assign code from sequence when default |
| session | `create` | assign reference from sequence |
| session | `write` | block header changes when done |
| session | `unlink` | allow only draft/cancelled |
| attendance | `create` | block on done/cancelled sessions |
| attendance | `write` | block evidence changes when session done |
| attendance | `unlink` | block when session done |
| certification | `create` | assign reference; freeze course version |
| certification | `unlink` | always raises |
| assessment | `write` | block content changes when confirmed |
| assessment | `unlink` | block when confirmed |

### 4.4 Public model methods

| Model | Method | Contract |
|-------|--------|----------|
| certification | `_get_expiry_warning_days()` | returns int; falls back to 30 on missing, non-numeric or negative parameter |
| certification | `_prepare_from_attendance(attendance)` | returns a values dict for one passing attendance |
| certification | `_cron_refresh_certification_state()` | returns count of refreshed records |
| certification | `_cron_send_expiry_reminders()` | returns count of queued emails |
| requirement | `_get_target_employees()` | single record; returns hr.employee recordset |
| requirement | `_get_requirements_for_employee(employee)` | model method; returns requirement recordset |
| matrix wizard | `_get_scope_employees()` | returns hr.employee recordset in scope |
| matrix wizard | `_prepare_matrix_lines(employees)` | returns list of line value dicts |
| register wizard | `_get_candidate_employees()` | returns hr.employee recordset before exclusions |

## 5. Security model

### 5.1 Groups

Four groups under one `res.groups.privilege` record
(`res_groups_privilege_ls_training`), itself under the
`module_category_ls_training` module category:

`group_ls_training_learner` ← `group_ls_training_viewer` ←
`group_ls_training_trainer` ← `group_ls_training_manager`

Each group's `implied_ids` links the one below.

### 5.2 Access control list

31 lines in `security/ir.model.access.csv`, covering 8 persistent models
and 3 transient models across 4 groups. See the functional specification
§11 for the resulting matrix.

### 5.3 Record rules

13 rules in total:

- **7 global** multi-company rules, one per persistent model with a
  `company_id`, domain
  `['|', ('company_id','=',False), ('company_id','in',company_ids)]`.
  Global rules intersect, so they always restrict.
- **3 Learner** rules on certification, attendance and assessment, domain
  `[('employee_id.user_id','=',user.id)]`, read-only.
- **3 Viewer** rules on the same three models, domain `[(1,'=',1)]`.
  Group rules unify, so a Viewer (and by implication Trainer and Manager)
  is not restricted by the Learner rule.

**API caveat.** The `ir.rule` many2many to `res.groups` is written as
`group_ids`. This name could not be verified for Odoo 19; see
`verification_notes.md` §2 and the shipped alternate file.

## 6. Data files

| File | noupdate | Content |
|------|----------|---------|
| `ir_sequence_data.xml` | 1 | 3 sequences: TRN/CRS/, TRN/SES/yyyy/, TRN/CER/yyyy/ |
| `ir_config_parameter_data.xml` | 1 | `ls_training.expiry_warning_days` = 30 |
| `ir_cron_data.xml` | 1 | 2 daily scheduled actions |
| `mail_template_data.xml` | 1 | expiry reminder template |
| `demo/ls_training_demo.xml` | 0 | 2 competencies, 3 courses (driven through the approval workflow with `<function>`), 2 requirements, 1 session, 1 attendance |

Sequences are created with `company_id` unset so a single sequence serves
all companies; `next_by_code` is called with `with_company()` so that a
company-specific sequence can be added later without code changes.

## 7. Translation

`i18n/ls_training.pot` is provided. It was produced by a helper extraction
script, **not** by Odoo's `--i18n-export`, because no Odoo runtime was
available. It should be regenerated with

```
odoo-bin --i18n-export=ls_training.pot --modules=ls_training -d <db>
```

before translation work begins.

## 8. Performance considerations

| Concern | Mitigation |
|---------|-----------|
| Counter fields on list views | `_read_group` aggregation instead of per-record `len()` |
| Attendance filtering and grouping | `course_id`, `company_id`, `date_start`, `result` stored and indexed |
| Certification status filtering | `state` stored and indexed; refreshed by cron rather than computed per read |
| Matrix generation | One `search` per employee/course pair for the latest certification. O(employees × courses) queries. Bounded by a 20 000-line guard with an actionable error. Acknowledged as the main performance limitation — see the architecture review. |
| Compliance rate on employee lists | Non-stored compute; adding this field to a large list view will be slow. It is placed on the form only. |

## 9. Extension points

| Extension | Approach |
|-----------|----------|
| Link training to controlled SOPs | Bridge module adding `document_id` to `ls.training.course` |
| Part 11 signature on session closure | Override `action_close`; call the signature service before `super()` |
| Field-level audit trail | Bridge module registering the models with `ls_audit_trail` |
| Odoo eLearning integration | Bridge module mapping `delivery_mode = external_elearning` to `slide.channel` |
| Manager escalation on overdue training | New cron method on `ls.training.certification` |
| Trainer qualification enforcement | Constraint on `ls.training.session.trainer_employee_id` checking a certification for a trainer course |
