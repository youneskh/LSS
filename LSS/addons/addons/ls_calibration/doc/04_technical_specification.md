# Phase 4 — Technical Specification

Module: `ls_calibration`, version `19.0.1.0.0`, license AGPL-3.0 or later.

## 4.1 Module architecture

```
ls_calibration/
├── __init__.py                     imports models and wizards
├── __manifest__.py
├── README.rst                      and readme/ fragments
├── models/
│   ├── ls_calibration_instrument.py
│   ├── ls_calibration_plan.py
│   ├── ls_calibration_plan_point.py
│   ├── ls_calibration_record.py
│   ├── ls_calibration_record_line.py
│   └── ls_calibration_certificate.py
├── wizards/
│   ├── ls_calibration_record_generate.py   + _views.xml
│   └── ls_calibration_record_reject.py     + _views.xml
├── security/
│   ├── ls_calibration_security.xml         groups and record rules
│   └── ir.model.access.csv                 21 access rules
├── data/
│   ├── ir_sequence_data.xml                4 sequences
│   ├── ir_config_parameter_data.xml        1 parameter
│   └── ir_cron_data.xml                    2 scheduled actions
├── demo/ls_calibration_demo.xml
├── views/                                  4 model view files + menus
├── report/                                 2 report definitions and templates
├── tests/                                  9 modules
├── doc/                                    this documentation set
├── i18n/                                   translation templates
└── static/description/icon.png
```

The module contains **no Python controller, no client-side JavaScript asset
and no SCSS**. Every screen is built with the standard view types of the
Odoo 19 web client. This is a deliberate architectural decision: it removes
the largest source of breakage between Odoo versions and keeps the validation
scope small.

## 4.2 Dependencies

| Dependency | Edition | Reason |
|------------|---------|--------|
| `base` | Community | Core models and ORM. |
| `web` | Community | `web.html_container` and `web.external_layout` used by the two QWeb reports. |
| `mail` | Community | `mail.thread` and `mail.activity.mixin` for the message threads, the tracked fields and the notification activities. |
| `maintenance` | Community | `maintenance.equipment` for the optional link to the equipment on which the instrument is installed, and `maintenance.equipment.category` reused as the instrument taxonomy. |

External Python dependency: `python-dateutil`, used for `relativedelta`. It
is already required by Odoo itself.

**Dependency deliberately not declared:** the suite specification lists
`ls_qms` as a dependency of the calibration module. That module does not
exist. Declaring it would make the module impossible to install. The
dependency is therefore omitted, and the quality management links are listed
in the roadmap as a future bridge module.

## 4.3 Manifest

Keys used: `name`, `summary`, `version`, `category`, `author`, `license`,
`development_status`, `depends`, `external_dependencies`, `data`, `demo`,
`installable`, `application`, `auto_install`. The `data` list is ordered so
that the security groups are loaded before the access rights, the data before
the views, and the menus last, since the menus reference the actions of the
views and of the wizards.

`development_status` is `Beta` and not `Production/Stable`, because the test
suite has not yet been executed against a live Odoo 19 instance. See the
validation report.

## 4.4 Models, fields and database constraints

Eight models are declared: six business models and two transient models. The
following tables are generated from the source code.

### `ls.calibration.certificate` — Calibration Certificate

| Field | Type | Attributes |
|-------|------|------------|
| `name` | Char | required=True, copy=False, default=yes, tracking=True |
| `instrument_id` | Many2one | comodel_name=ls.calibration.instrument, required=True, index=True, check_company=True, tracking=True |
| `record_id` | Many2one | comodel_name=ls.calibration.record, index=True, check_company=True |
| `company_id` | Many2one | comodel_name=res.company, related=instrument_id.company_id, store=True, index=True, readonly=True |
| `issuer_type` | Selection | required=True, default=yes, tracking=True |
| `issuer_partner_id` | Many2one | comodel_name=res.partner |
| `accreditation_reference` | Char | - |
| `issue_date` | Date | required=True, default=yes, tracking=True |
| `valid_until` | Date | tracking=True |
| `certificate_file` | Binary | attachment=True |
| `certificate_filename` | Char | - |
| `note` | Text | - |
| `state` | Selection | required=True, default=yes, tracking=True, copy=False |

**Database constraints**

| Name | Definition | Message |
|------|------------|---------|
| `_name_company_unique` | `UNIQUE(name, company_id)` | The certificate number must be unique per company. |

### `ls.calibration.instrument` — Calibration Instrument

| Field | Type | Attributes |
|-------|------|------------|
| `name` | Char | required=True, index=True, tracking=True |
| `code` | Char | required=True, copy=False, default=yes, tracking=True |
| `active` | Boolean | default=yes |
| `company_id` | Many2one | comodel_name=res.company, required=True, index=True, default=yes |
| `equipment_id` | Many2one | comodel_name=maintenance.equipment, check_company=True |
| `category_id` | Many2one | comodel_name=maintenance.equipment.category |
| `manufacturer` | Char | - |
| `model_reference` | Char | - |
| `serial_number` | Char | tracking=True |
| `location` | Char | - |
| `responsible_user_id` | Many2one | comodel_name=res.users, tracking=True, default=yes |
| `criticality` | Selection | required=True, default=yes, tracking=True |
| `gxp_impact` | Selection | required=True, default=yes, tracking=True |
| `range_min` | Float | digits=(16, 6) |
| `range_max` | Float | digits=(16, 6) |
| `unit` | Char | - |
| `tolerance_type` | Selection | required=True, default=yes |
| `tolerance_value` | Float | digits=(16, 6) |
| `alert_lead_days` | Integer | required=True, default=yes |
| `state` | Selection | required=True, default=yes, tracking=True, copy=False |
| `plan_ids` | One2many | comodel_name=ls.calibration.plan, inverse_name=instrument_id |
| `record_ids` | One2many | comodel_name=ls.calibration.record, inverse_name=instrument_id |
| `certificate_ids` | One2many | comodel_name=ls.calibration.certificate, inverse_name=instrument_id |
| `plan_count` | Integer | compute=_compute_counts |
| `record_count` | Integer | compute=_compute_counts |
| `certificate_count` | Integer | compute=_compute_counts |
| `last_calibration_date` | Date | compute=_compute_calibration_dates, store=True |
| `next_calibration_date` | Date | compute=_compute_calibration_dates, store=True, index=True |
| `calibration_status` | Selection | compute=_compute_calibration_status, search=_search_calibration_status |
| `note` | Html | sanitize=True |

**Database constraints**

| Name | Definition | Message |
|------|------------|---------|
| `_code_company_unique` | `UNIQUE(code, company_id)` | The instrument reference must be unique per company. |
| `_range_consistent` | `CHECK(range_max >= range_min)` | The maximum of the measuring range must be greater than or equal to the minimum of the measuring range. |
| `_alert_lead_days_positive` | `CHECK(alert_lead_days >= 0)` | The alert lead time must be greater than or equal to zero days. |
| `_tolerance_value_positive` | `CHECK(tolerance_value >= 0)` | The maximum permissible error must be greater than or equal to zero. |

### `ls.calibration.plan` — Calibration Plan

| Field | Type | Attributes |
|-------|------|------------|
| `name` | Char | required=True, copy=False, default=yes, tracking=True |
| `active` | Boolean | default=yes |
| `instrument_id` | Many2one | comodel_name=ls.calibration.instrument, required=True, index=True, check_company=True, tracking=True |
| `company_id` | Many2one | comodel_name=res.company, related=instrument_id.company_id, store=True, index=True, readonly=True |
| `description` | Char | - |
| `procedure_reference` | Char | - |
| `method_description` | Text | - |
| `interval_number` | Integer | required=True, default=yes, tracking=True |
| `interval_uom` | Selection | required=True, default=yes, tracking=True |
| `start_date` | Date | required=True, default=yes, tracking=True |
| `responsible_user_id` | Many2one | comodel_name=res.users, default=yes, tracking=True |
| `performed_externally` | Boolean | - |
| `provider_id` | Many2one | comodel_name=res.partner |
| `point_ids` | One2many | comodel_name=ls.calibration.plan.point, inverse_name=plan_id, copy=True |
| `record_ids` | One2many | comodel_name=ls.calibration.record, inverse_name=plan_id |
| `record_count` | Integer | compute=_compute_record_count |
| `last_calibration_date` | Date | compute=_compute_schedule_dates, store=True |
| `next_due_date` | Date | compute=_compute_schedule_dates, store=True, index=True |
| `state` | Selection | required=True, default=yes, tracking=True, copy=False |

**Database constraints**

| Name | Definition | Message |
|------|------------|---------|
| `_name_company_unique` | `UNIQUE(name, company_id)` | The calibration plan reference must be unique per company. |
| `_interval_number_positive` | `CHECK(interval_number > 0)` | The calibration interval must be strictly greater than zero. |

### `ls.calibration.plan.point` — Calibration Plan Test Point

| Field | Type | Attributes |
|-------|------|------------|
| `sequence` | Integer | default=yes |
| `plan_id` | Many2one | comodel_name=ls.calibration.plan, required=True, index=True, check_company=True |
| `company_id` | Many2one | comodel_name=res.company, related=plan_id.company_id, store=True, index=True, readonly=True |
| `name` | Char | required=True |
| `nominal_value` | Float | required=True, digits=(16, 6) |
| `unit` | Char | - |
| `tolerance_type` | Selection | required=True, default=yes |
| `tolerance_value` | Float | required=True, digits=(16, 6) |
| `limit_min` | Float | compute=_compute_limits, store=True, digits=(16, 6) |
| `limit_max` | Float | compute=_compute_limits, store=True, digits=(16, 6) |

**Database constraints**

| Name | Definition | Message |
|------|------------|---------|
| `_tolerance_value_positive` | `CHECK(tolerance_value >= 0)` | The tolerance of a test point must be greater than or equal to zero. |

### `ls.calibration.record` — Calibration Record

| Field | Type | Attributes |
|-------|------|------------|
| `name` | Char | required=True, copy=False, default=yes, tracking=True |
| `instrument_id` | Many2one | comodel_name=ls.calibration.instrument, required=True, index=True, check_company=True, tracking=True |
| `plan_id` | Many2one | comodel_name=ls.calibration.plan, index=True, check_company=True, tracking=True |
| `company_id` | Many2one | comodel_name=res.company, related=instrument_id.company_id, store=True, index=True, readonly=True |
| `calibration_type` | Selection | required=True, default=yes, tracking=True |
| `scheduled_date` | Date | - |
| `calibration_date` | Datetime | tracking=True |
| `performed_by_id` | Many2one | comodel_name=res.users, tracking=True |
| `performed_externally` | Boolean | - |
| `provider_id` | Many2one | comodel_name=res.partner |
| `standard_ids` | Many2many | comodel_name=ls.calibration.instrument, relation=ls_calibration_record_standard_rel, check_company=True |
| `external_standard_reference` | Char | - |
| `ambient_temperature` | Float | digits=(16, 2) |
| `ambient_humidity` | Float | digits=(16, 2) |
| `line_ids` | One2many | comodel_name=ls.calibration.record.line, inverse_name=record_id, copy=True |
| `line_count` | Integer | compute=_compute_line_count, store=True |
| `as_found_status` | Selection | compute=_compute_tolerance_status, store=True, tracking=True |
| `as_left_status` | Selection | compute=_compute_tolerance_status, store=True, tracking=True |
| `result` | Selection | compute=_compute_tolerance_status, store=True, tracking=True |
| `adjustment_performed` | Boolean | - |
| `oot_impact_assessment` | Text | - |
| `oot_action_reference` | Char | - |
| `conclusion` | Text | - |
| `next_due_date` | Date | compute=_compute_next_due_date, store=True |
| `certificate_ids` | One2many | comodel_name=ls.calibration.certificate, inverse_name=record_id |
| `certificate_count` | Integer | compute=_compute_certificate_count |
| `submitted_by_id` | Many2one | comodel_name=res.users, readonly=True, copy=False, tracking=True |
| `submission_date` | Datetime | readonly=True, copy=False |
| `approved_by_id` | Many2one | comodel_name=res.users, readonly=True, copy=False, tracking=True |
| `approval_date` | Datetime | readonly=True, copy=False |
| `rejection_reason` | Text | readonly=True, copy=False |
| `state` | Selection | required=True, default=yes, tracking=True, copy=False |

**Database constraints**

| Name | Definition | Message |
|------|------------|---------|
| `_name_company_unique` | `UNIQUE(name, company_id)` | The calibration record reference must be unique per company. |

### `ls.calibration.record.line` — Calibration Record Test Point Result

| Field | Type | Attributes |
|-------|------|------------|
| `sequence` | Integer | default=yes |
| `record_id` | Many2one | comodel_name=ls.calibration.record, required=True, index=True, check_company=True |
| `company_id` | Many2one | comodel_name=res.company, related=record_id.company_id, store=True, index=True, readonly=True |
| `plan_point_id` | Many2one | comodel_name=ls.calibration.plan.point, check_company=True |
| `name` | Char | required=True |
| `nominal_value` | Float | required=True, digits=(16, 6) |
| `unit` | Char | - |
| `tolerance_type` | Selection | required=True, default=yes |
| `tolerance_value` | Float | required=True, digits=(16, 6) |
| `limit_min` | Float | compute=_compute_limits, store=True, digits=(16, 6) |
| `limit_max` | Float | compute=_compute_limits, store=True, digits=(16, 6) |
| `as_found_value` | Float | digits=(16, 6) |
| `as_left_value` | Float | digits=(16, 6) |
| `as_found_deviation` | Float | compute=_compute_deviations, store=True, digits=(16, 6) |
| `as_left_deviation` | Float | compute=_compute_deviations, store=True, digits=(16, 6) |
| `as_found_in_tolerance` | Boolean | compute=_compute_in_tolerance, store=True |
| `as_left_in_tolerance` | Boolean | compute=_compute_in_tolerance, store=True |

**Database constraints**

| Name | Definition | Message |
|------|------------|---------|
| `_tolerance_value_positive` | `CHECK(tolerance_value >= 0)` | The tolerance of a test point must be greater than or equal to zero. |

### `ls.calibration.record.generate` — Generate Calibration Records

| Field | Type | Attributes |
|-------|------|------------|
| `date_to` | Date | required=True, default=yes |
| `plan_ids` | Many2many | comodel_name=ls.calibration.plan |
| `company_id` | Many2one | comodel_name=res.company, required=True, default=yes |

### `ls.calibration.record.reject` — Reject Calibration Record

| Field | Type | Attributes |
|-------|------|------------|
| `record_id` | Many2one | comodel_name=ls.calibration.record, required=True |
| `reason` | Text | required=True |

## 4.5 Python constraints

| Model | Method | Rule |
|-------|--------|------|
| `ls.calibration.record` | `_check_plan_instrument` | The plan belongs to the instrument of the record. |
| `ls.calibration.record` | `_check_standard_not_self` | The instrument is not its own reference standard. |
| `ls.calibration.certificate` | `_check_validity_dates` | The validity end date is not earlier than the issue date. |
| `ls.calibration.certificate` | `_check_record_instrument` | The record belongs to the instrument of the certificate. |

## 4.6 Compute methods

| Model | Method | Fields | Stored |
|-------|--------|--------|--------|
| instrument | `_compute_display_name` | `display_name` | no |
| instrument | `_compute_counts` | `plan_count`, `record_count`, `certificate_count` | no |
| instrument | `_compute_calibration_dates` | `last_calibration_date`, `next_calibration_date` | yes |
| instrument | `_compute_calibration_status` | `calibration_status` | no, with a search method |
| plan | `_compute_display_name` | `display_name` | no |
| plan | `_compute_record_count` | `record_count` | no |
| plan | `_compute_schedule_dates` | `last_calibration_date`, `next_due_date` | yes |
| plan point | `_compute_display_name` | `display_name` | no |
| plan point | `_compute_limits` | `limit_min`, `limit_max` | yes |
| record | `_compute_display_name` | `display_name` | no |
| record | `_compute_line_count` | `line_count` | yes |
| record | `_compute_certificate_count` | `certificate_count` | no |
| record | `_compute_tolerance_status` | `as_found_status`, `as_left_status`, `result` | yes |
| record | `_compute_next_due_date` | `next_due_date` | yes |
| record line | `_compute_display_name` | `display_name` | no |
| record line | `_compute_limits` | `limit_min`, `limit_max` | yes |
| record line | `_compute_deviations` | `as_found_deviation`, `as_left_deviation` | yes |
| record line | `_compute_in_tolerance` | `as_found_in_tolerance`, `as_left_in_tolerance` | yes |
| certificate | `_compute_display_name` | `display_name` | no |

**Design note on `calibration_status`.** The status depends on the current
date. A stored value would become stale at midnight. The field is therefore
computed at read time and made searchable through `_search_calibration_status`,
which resolves the domain in Python because the comparison uses the per
instrument alert lead time and cannot be expressed in SQL. The consequence is
that the field cannot be used as a group-by axis. The trade-off is accepted:
an always-correct status matters more than a groupable one for a control that
decides whether an instrument may be used.

## 4.7 Onchange methods

| Model | Method | Effect |
|-------|--------|--------|
| plan point | `_onchange_plan_id` | Proposes the unit and the default tolerance of the instrument. |
| record | `_onchange_instrument_id` | Clears the plan when it belongs to another instrument. |
| record | `_onchange_plan_id` | Aligns the instrument, the externalisation and the provider, and loads the test points of the plan when the record has no line. |
| record line | `_onchange_as_found_value` | Proposes the as-found reading as the as-left reading. |
| certificate | `_onchange_record_id` | Aligns the instrument with the selected record. |

## 4.8 Overridden ORM methods

| Model | Method | Purpose |
|-------|--------|---------|
| instrument, plan, record, certificate | `create` | Assigns the reference from the sequence when it is `/` or empty. |
| instrument, plan, record, certificate | `copy_data` | Resets the reference, and the state where applicable. |
| record | `write` | Refuses any change on an approved or cancelled record, except the exempt technical fields. |
| record | `unlink` | Refuses the deletion of a record that left the draft state. |
| record line | `create` | Refuses a line on a record that is no longer editable. |
| record line | `write` | Same, except for the fields written by the recomputation engine. |
| record line | `unlink` | Same. |
| certificate | `write` | Refuses any change on an issued or superseded certificate, except state and notes. |
| certificate | `unlink` | Refuses the deletion of a certificate that left the draft state. |

The exempt field sets are returned by `_get_lock_exempt_fields` and
`_get_recompute_exempt_fields`, so that they are visible, testable and
extensible by a bridge module.

## 4.9 Security model

Three groups, in a hierarchy built with `implied_ids`:

```
base.group_user
   └── group_ls_calibration_viewer
          └── group_ls_calibration_technician
                 └── group_ls_calibration_manager
```

The groups carry no category. The Odoo 19 refactoring of the `res.groups`
categories into privileges could not be verified from official documentation,
and an unverified field name would prevent the installation.

### Access rights matrix

| Model | Viewer | Technician | Manager |
|-------|--------|------------|---------|
| `ls.calibration.instrument` | R | R | RWCU |
| `ls.calibration.plan` | R | R | RWCU |
| `ls.calibration.plan.point` | R | R | RWCU |
| `ls.calibration.record` | R | RWC | RWCU |
| `ls.calibration.record.line` | R | RWCU | RWCU |
| `ls.calibration.certificate` | R | RWC | RWCU |
| `ls.calibration.record.generate` | none | RWCU | RWCU |
| `ls.calibration.record.reject` | none | none | RWCU |

R read, W write, C create, U unlink. The technician can delete a record line
while the record is still editable, which the line `unlink` override
restricts to the draft and in-progress states; the technician cannot delete a
calibration record and must cancel it instead.

### Record rules

Six global multi-company rules, one per business model, with the domain
`[('company_id', 'in', company_ids)]`. A rule attached to no group is global
by construction in modern Odoo; the `global` flag is a computed field and is
therefore not set in the data file.

## 4.10 XML structure

| File | Content |
|------|---------|
| `security/ls_calibration_security.xml` | 3 `res.groups`, 6 `ir.rule` |
| `security/ir.model.access.csv` | 21 `ir.model.access` |
| `data/ir_sequence_data.xml` | 4 `ir.sequence`, `noupdate="1"` |
| `data/ir_config_parameter_data.xml` | 1 `ir.config_parameter`, `noupdate="1"` |
| `data/ir_cron_data.xml` | 2 `ir.cron`, `noupdate="1"` |
| `views/*_views.xml` | list, form and search views, plus the window actions |
| `views/ls_calibration_menus.xml` | 1 root menu and 8 menu items |
| `wizards/*_views.xml` | 2 form views and 2 window actions |
| `report/*_report.xml` | 2 `ir.actions.report` and 4 QWeb templates |
| `demo/ls_calibration_demo.xml` | 3 instruments, 2 plans, 5 test points, 1 record, 1 certificate, 4 `<function>` calls |

The `ir.cron` records do not set `numbercall` or `doall`; the module relies on
the interval fields only.

The demonstration data drives the record through the real workflow with
`<function>` calls rather than writing the final state directly, so that the
demonstration database contains a record with a genuine history.

## 4.11 Views

| Model | Views |
|-------|-------|
| instrument | list with status badge and decorations, form with three stat buttons and five notebook pages, search with nine filters and six group-by axes |
| plan | list, form with an editable test point list, search |
| record | list with decorations on the result, form with five notebook pages, search, pivot, graph |
| certificate | list, form, search |
| wizards | two dialog forms |

The Odoo 19 view syntax is used throughout: `<list>` instead of `<tree>`,
`<chatter/>` instead of the chatter div, direct `invisible`, `readonly` and
`required` attributes instead of `attrs`, `column_invisible` for the list
columns, and `list,form` in `view_mode`.

## 4.12 Reports, controllers, services and APIs

Two QWeb PDF reports, described in the functional specification. They use
`t-field` and `t-out` only; `t-raw` is not used anywhere, which removes the
cross-site scripting risk in the rendered documents.

The module exposes **no HTTP controller and no custom web service**. Every
model, field and method is reachable through the standard Odoo external API,
XML-RPC and JSON-RPC, subject to the access rights and record rules described
above. The methods intended for integration are documented in the API
documentation.

## 4.13 Scheduled jobs

| XML identifier | Model | Method |
|----------------|-------|--------|
| `ls_calibration_cron_notify_due` | `ls.calibration.instrument` | `_cron_notify_due_calibrations` |
| `ls_calibration_cron_generate_records` | `ls.calibration.plan` | `_cron_generate_calibration_records` |

Both run daily as OdooBot and return a count, so that the execution can be
monitored from the scheduled action log.

## 4.14 Data and demonstration data

Four sequences: `INS/`, `CP/`, `CAL/%(year)s/`, `CERT/%(year)s/`, padding 5,
standard implementation, no company restriction. One system parameter:
`ls_calibration.generation_horizon_days`, default `30`. All data files are
declared `noupdate="1"` so that a module update never overwrites a value
adjusted by the customer.

## 4.15 Translation structure

Every user-facing string is either a field label, a selection label, a help
text, a view string, or a message wrapped in `self.env._()`, which is the
translation API required by the Odoo 19 coding guidelines. No string is
concatenated before translation and no variable is passed to the translation
function.

The `i18n/` directory is present and empty. The translation template is
produced from the installed module rather than written by hand, because a
hand-written template would be incomplete and would silently drift from the
source:

```
odoo-bin -d <database> --i18n-export=ls_calibration.pot --modules=ls_calibration
```

The resulting file is placed in `i18n/ls_calibration.pot`.

## Gate

**Phase 4: PASS.** Architecture, dependencies, manifest, eight models with
their fields, database and Python constraints, compute and onchange methods,
ORM overrides, security model, XML structure, views, reports, scheduled jobs,
data, demonstration data and translation structure are specified and match
the source code, from which the field tables were generated.
