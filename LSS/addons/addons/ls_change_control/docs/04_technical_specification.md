# Phase 4 - Technical Specification

Module: `ls_change_control` | Odoo 19.0 Community | Version 19.0.1.0.0

## 1. Verified platform facts

The following Odoo 19.0 facts were verified against the official Odoo
documentation before writing the code, because each of them breaks a module
ported from an earlier version.

| Fact | Source |
|------|--------|
| The root element of a list view is `list`; `tree` was the previous name | Odoo 19.0 documentation, View architectures |
| The chatter is inserted with the `<chatter/>` element on a model inheriting `mail.thread` | Odoo 19.0 documentation, Mixins and Useful Classes |
| SQL constraints are declared with `models.Constraint(definition, message)` as a class attribute | Odoo 19.0 documentation, Server framework 101, Constraints |
| The root kanban template is `<t t-name="card">` | Odoo 19.0 documentation, View architectures |
| `attrs` and `states` were removed; visibility uses inline Python expressions | Odoo 17.0 documentation, View architectures |
| `sudo()` keeps the same user on the environment and only sets the superuser flag | Odoo pull request 34297, which introduced the behaviour |

Facts that could **not** be verified and were therefore avoided:

* Whether `numbercall` and `doall` still exist on `ir.cron` in Odoo 19. Both are omitted from the cron records; they are not required to schedule a recurring job.
* The signature of the credential checking API of `res.users` in Odoo 19. No re-authentication is implemented.

## 2. Module architecture

```
ls_change_control/
├── __init__.py
├── __manifest__.py
├── README.md
├── data/
│   ├── ir_cron_data.xml                       3 scheduled actions
│   ├── ir_sequence_data.xml                   request sequence
│   ├── ls_change_control_category_data.xml    10 categories, 29 template lines
│   ├── ls_change_control_impact_area_data.xml 14 impact areas
│   └── mail_template_data.xml                 3 mail templates
├── demo/
│   └── ls_change_control_demo.xml             3 draft requests, 3 actions
├── docs/                                      this documentation set
├── i18n/
│   └── ls_change_control.pot                  403 entries
├── models/
│   ├── __init__.py
│   ├── change_control_approval.py
│   ├── change_control_approval_template.py
│   ├── change_control_assessment.py
│   ├── change_control_category.py
│   ├── change_control_impact_area.py
│   ├── change_control_implementation.py
│   ├── change_control_request.py
│   ├── change_control_verification.py
│   └── res_company.py
├── report/
│   ├── change_control_request_report.xml      ir.actions.report
│   └── change_control_request_templates.xml   QWeb templates
├── security/
│   ├── ir.model.access.csv                    23 lines
│   ├── ls_change_control_groups.xml           1 category, 4 groups
│   └── ls_change_control_rules.xml            7 record rules
├── static/description/
│   ├── icon.png
│   └── index.html
├── tests/                                     12 files
├── views/                                     8 files
└── wizards/
    ├── __init__.py
    ├── change_control_decision_wizard.py
    └── change_control_decision_wizard_views.xml
```

There is **no JavaScript and no Owl component in this module**. None is
required: every screen is built with standard Odoo view types. This is stated
explicitly rather than adding gratuitous front end code.

## 3. Dependencies

| Module | Why |
|--------|-----|
| `base` | Users, companies, sequences, security |
| `mail` | `mail.thread` for the chatter and the tracking, `mail.activity.mixin` for the reminders, `mail.template` for the notifications |
| `hr` | `hr.department` on the request and on the requester lookup |

No Python package beyond the Odoo standard library requirements is used. No
Odoo Enterprise module is referenced.

## 4. Models

### 4.1 `ls.change_control.request`

Inherits `mail.thread` and `mail.activity.mixin`. Ordered by request date
descending.

| Field | Type | Notes |
|-------|------|-------|
| `name` | Char | Required, read only, unique, from the sequence |
| `title` | Char | Required, tracked, frozen after Draft |
| `company_id` | Many2one res.company | Required, indexed |
| `active` | Boolean | Only a Draft request may be archived |
| `category_id` | Many2one category | Required, tracked, frozen after Draft |
| `change_type` | Selection permanent/temporary | Required, tracked, frozen after Draft |
| `temporary_end_date` | Date | Required when temporary, forbidden otherwise |
| `classification` | Selection minor/major/critical | Required, tracked |
| `priority` | Selection 0/1 | Kanban and list highlighting |
| `requester_id` | Many2one res.users | Required, tracked, internal user only |
| `department_id` | Many2one hr.department | Proposed from the employee of the requester |
| `manager_id` | Many2one res.users | Tracked, internal user only |
| `current_situation`, `proposed_change`, `justification` | Text | Required, frozen after Draft |
| `impact_area_ids` | Many2many impact_area | Drives the generated assessments |
| `gmp_impact` | Boolean | Tracked |
| `product_quality_impact` | Selection none/low/medium/high | Tracked |
| `regulatory_impact` | Selection none/notification/variation/prior_approval | Tracked |
| `validation_impact`, `training_impact`, `documentation_impact`, `customer_notification_required` | Boolean | Consequence declarations |
| `risk_assessment_reference` | Char | Integration point |
| `state` | Selection, 9 values | Required, read only, tracked, indexed |
| `date_request` | Datetime | Required, read only, default now |
| `date_required`, `date_planned_implementation` | Date | Planning |
| `date_actual_implementation` | Date | Computed, stored |
| `date_verification_planned` | Date | Computed, stored |
| `date_approved`, `date_rejected`, `date_cancelled`, `date_closed` | Datetime | Read only, workflow |
| `rejection_reason`, `cancellation_reason`, `closure_statement` | Text | Read only, workflow |
| `assessment_ids`, `approval_ids`, `implementation_ids`, `verification_ids` | One2many | Related records |
| `assessment_count`, `assessment_done_count`, `approval_count`, `approval_done_count`, `implementation_count`, `implementation_done_count`, `verification_count` | Integer | Computed, not stored |
| `blocking_reasons` | Text | Computed, not stored |

SQL constraint: `_name_unique`, `UNIQUE(name)`.

Python constraints: `_check_temporary_end_date`, `_check_dates_after_request`,
`_check_users_are_internal`, `_check_archive_only_draft`.

Compute methods: `_compute_display_name`, `_compute_assessment_count`,
`_compute_approval_count`, `_compute_implementation_count`,
`_compute_verification_count`, `_compute_date_actual_implementation`,
`_compute_date_verification_planned`, `_compute_blocking_reasons`.

Onchange methods: `_onchange_category_id`, `_onchange_change_type`,
`_onchange_requester_id`.

ORM overrides: `create` with `@api.model_create_multi`, `write`, `unlink`,
`copy_data`.

### 4.2 `ls.change_control.assessment`

One assessment per impact area per request. SQL constraint
`UNIQUE(request_id, impact_area_id)`. States Draft and Completed. A completed
assessment is immutable and undeletable. Stores `completed_by_id` and
`date_completed`.

### 4.3 `ls.change_control.approval`

One approval per role per request. SQL constraint
`UNIQUE(request_id, approval_role)`. States Pending, Approved, Rejected.
Stores `decided_by_id`, `date_decision`, `signature_meaning`,
`date_requested`, `date_reminder`. A decided approval is immutable and
undeletable. `_apply_signature` is the extension point for a stronger signing
procedure.

### 4.4 `ls.change_control.implementation`

Twelve explicit action types. States Pending, In Progress, Done, Cancelled.
`evidence_reference` mandatory before closing. `cancellation_reason` mandatory
before cancelling, and cancellation is reserved to managers. Stores
`done_by_id` and `date_done`.

### 4.5 `ls.change_control.verification`

Seven explicit verification methods. `acceptance_criteria` required at
creation. Results Pending, Effective, Not Effective. A Not Effective result
requires `follow_up_required`. A completed verification is immutable and
undeletable.

### 4.6 Configuration models

`ls.change_control.category` holds the impact areas, the approval template, the
implementation deadline, the verification delay and whether verification is
required. `ls.change_control.impact_area` holds the areas.
`ls.change_control.approval_template` holds the ordered roles of a category.
All three carry a unique code and an `active` flag.

`res.company` is extended with four configuration fields prefixed `ls_cc_`.

### 4.7 `ls.change_control.decision_wizard`

Transient model with `request_id`, `mode`, `reason`. Delegates to
`action_close`, `action_reject` or `action_cancel`.

## 5. Security model

### 5.1 Groups

Cumulative hierarchy, each group implying the previous one:
`base.group_user` to Viewer to Requester to Approver to Change Control Manager.

### 5.2 Access rights

Twenty-three lines in `security/ir.model.access.csv`. Every model declared by
the module is covered; this is verified mechanically by `static_check.py`.

Summary: Viewer reads everything. Requester creates and writes requests, and
writes assessments, actions and verifications. Approver adds write on
approvals. Manager holds create and delete on everything, including the
configuration.

### 5.3 Record rules

| Rule | Scope | Effect |
|------|-------|--------|
| Five multi-company rules | Global, on request, assessment, approval, implementation, verification | A user only sees records of their allowed companies |
| Ownership rule | Requester group, write and create only | A requester only modifies the requests they raised or manage |
| Manager rule | Manager group, write, create and delete | Unrestricted within the allowed companies |

Record rules of different groups combine with a logical OR, so the manager
rule neutralises the ownership restriction for managers.

### 5.4 Defence in depth in `write`

Record rules answer "which records". Three checks in `write` answer "which
fields, in which state, by whom".

| Check | Effect |
|-------|--------|
| `_check_system_fields` | Refuses any write on a workflow field unless `env.su` is set. `env.su` is only set by a server side `sudo()` call and cannot be forged through an RPC context |
| `_check_content_fields` | Refuses any write on a content field of a submitted request, for every user |
| `_check_writer` | Refuses any business write on a submitted request by a user who is not a change control manager. Messaging and activity fields are excluded, so the chatter keeps working |

## 6. Data files

| File | Contents | `noupdate` |
|------|----------|------------|
| `ir_sequence_data.xml` | One global sequence, prefix `CC/%(year)s/`, padding 5 | 1 |
| `ls_change_control_impact_area_data.xml` | 14 impact areas | 1 |
| `ls_change_control_category_data.xml` | 10 categories and 29 approval template lines | 1 |
| `mail_template_data.xml` | 3 mail templates | 1 |
| `ir_cron_data.xml` | 3 scheduled actions | 1 |

`noupdate="1"` throughout, so that a module upgrade never overwrites a local
modification of the configuration, which is a quality record in its own right.

## 7. Demo data

Three change requests in Draft and three implementation actions. Demo records
are never created directly in an advanced state: that would bypass the
workflow and produce records that could not exist in reality.

## 8. Views

| Model | Views |
|-------|-------|
| request | form, list, kanban, search, graph, pivot, activity |
| assessment | form, list, search |
| approval | form, list, search |
| implementation | form, list, search |
| verification | form, list, search |
| category | form, list, search |
| impact area | form, list, search |
| res.company | dedicated settings form |
| decision wizard | form |

Only view types available in Odoo Community are used. No gantt, cohort, map or
dashboard view is declared.

## 9. Translation

`i18n/ls_change_control.pot`, 403 entries, generated by static extraction of
the `_()` calls, the field labels and help texts, the selection labels and the
translatable XML attributes.

**This POT is a starting template.** It must be regenerated with the Odoo
export command on a running instance before a translation campaign, because
only the running instance knows the complete set of translatable terms:

```bash
odoo-bin -d <database> --i18n-export=ls_change_control.pot \
         --modules=ls_change_control --stop-after-init
```

## 10. Performance considerations

* `company_id`, `state`, `request_id` and `request_state` are indexed, because every record rule and every search filter uses them.
* `request_state` is a stored related field on the four child models, so that the scheduled actions filter on the state of the parent without a join through the ORM.
* Counters are computed and not stored: they are only needed when a form is displayed, and storing them would add write amplification on every child change.
* `date_actual_implementation` and `date_verification_planned` are stored, because the scheduled actions search on them.
* No `read_group` call: the method is deprecated in Odoo 19 in favour of `_read_group` and `formatted_read_group`. The module uses `search` and `filtered` only.
