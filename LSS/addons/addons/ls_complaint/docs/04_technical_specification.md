# Phase 4 — Technical Specification

## 1. Module architecture

```
ls_complaint/
├── __init__.py
├── __manifest__.py
├── README.md
├── CHANGELOG.md
├── RELEASE_NOTES.md
├── data/
│   ├── ir_cron_data.xml            2 scheduled actions
│   ├── ir_sequence_data.xml        3 sequences
│   └── mail_template_data.xml      2 mail templates
├── demo/
│   └── ls_complaint_demo.xml       2 categories, 1 partner, 1 product, 3 complaints, 1 adverse event
├── docs/                           15 documents, this one included
├── i18n/
│   └── README.md                   how to produce the translation template
├── models/
│   ├── __init__.py
│   ├── ls_complaint.py
│   ├── ls_complaint_adverse_event.py
│   ├── ls_complaint_category.py
│   ├── ls_complaint_investigation.py
│   └── ls_complaint_resolution.py
├── report/
│   ├── ls_complaint_report.xml            report action
│   └── ls_complaint_report_templates.xml  QWeb template
├── security/
│   ├── ir.model.access.csv         21 access rules
│   └── ls_complaint_security.xml   1 category, 4 groups, 7 record rules
├── static/description/
│   ├── icon.png
│   └── index.html
├── tools/                          substitute static analysis scripts
├── tests/
│   ├── __init__.py
│   ├── common.py
│   ├── test_adverse_event.py
│   ├── test_category.py
│   ├── test_complaint_constraints.py
│   ├── test_complaint_security.py
│   ├── test_complaint_workflow.py
│   ├── test_cron_and_reports.py
│   ├── test_investigation.py
│   ├── test_resolution.py
│   └── test_wizards.py
├── views/
│   ├── ls_complaint_adverse_event_views.xml
│   ├── ls_complaint_category_views.xml
│   ├── ls_complaint_investigation_views.xml
│   ├── ls_complaint_menus.xml
│   ├── ls_complaint_resolution_views.xml
│   └── ls_complaint_views.xml
└── wizards/
    ├── __init__.py
    ├── ls_complaint_cancel_wizard.py
    ├── ls_complaint_cancel_wizard_views.xml
    ├── ls_complaint_close_wizard.py
    └── ls_complaint_close_wizard_views.xml
```

Layering inside the module follows the Odoo convention: Python models hold the
behaviour, XML holds the presentation and the data, CSV holds the access matrix,
and no business rule lives only in a view.

## 2. Dependencies

| Module | Why |
|---|---|
| `base` | Users, companies, partners, countries, sequences, groups, record rules |
| `mail` | `mail.thread` for field tracking and messages, `mail.activity.mixin` for the notification activities, `mail.template` |
| `product` | `product.product` and `uom.uom` for the complained item |
| `stock` | `stock.lot` for lot and serial traceability |

No dependency on an Enterprise module. No dependency on `ls_qms` or `ls_capa`,
which do not exist — see deviation D-01 in
`docs/00_verification_and_limitations.md`.

No third-party Python package is required beyond the Odoo runtime itself. The
only imports outside Odoo are `logging` and `datetime.timedelta` from the
standard library.

## 3. Manifest

| Key | Value |
|---|---|
| `name` | Life Sciences - Complaint Management |
| `version` | 19.0.1.0.0 |
| `category` | Life Sciences/Quality |
| `license` | AGPL-3 |
| `development_status` | Beta |
| `depends` | base, mail, product, stock |
| `data` | 15 files, load order given in the manifest |
| `demo` | 1 file |
| `installable` | True |
| `application` | True |
| `auto_install` | False |

`website` and `maintainers` are deliberately absent: inventing a repository URL
or a maintainer handle would be fabricating information. The publishing
organisation must add them.

Data files load in this order, which matters: groups before the access matrix,
the access matrix before any record, model views before the menus that reference
their actions.

## 4. Data model

Five persistent models and two transient models.

```
res.company ──┐
              ├─< ls.complaint >──┬─< ls.complaint.investigation
res.partner ──┤                   ├─< ls.complaint.adverse_event
product.product ──┤               └─< ls.complaint.resolution
stock.lot ────┤
ls.complaint.category ──┘
```

Every child model carries `company_id` as a stored related field of its parent
complaint, so that the multi-company record rules apply uniformly and can use an
index.

### `ls.complaint` — Product Quality Complaint (64 declared fields)

| Field | Type | Attributes |
|---|---|---|
| `name` | Char | required, readonly, copy=False, index, default=…, tracking |
| `active` | Boolean | default |
| `company_id` | Many2one → `res.company` | required, index, default=… |
| `priority` | Selection | default=0, tracking |
| `state` | Selection | default=received, required, copy=False, index, tracking |
| `receipt_date` | Datetime | required, copy=False, default=…, tracking |
| `occurrence_date` | Date | — |
| `channel` | Selection | required, default=email, tracking |
| `channel_other_description` | Char | — |
| `received_by_id` | Many2one → `res.users` | required, default=…, tracking |
| `owner_id` | Many2one → `res.users` | tracking |
| `reviewer_id` | Many2one → `res.users` | copy=False, tracking |
| `partner_id` | Many2one → `res.partner` | tracking |
| `complainant_type` | Selection | tracking |
| `contact_name` | Char | — |
| `contact_email` | Char | — |
| `contact_phone` | Char | — |
| `product_related` | Boolean | default, tracking |
| `product_id` | Many2one → `product.product` | check_company, tracking |
| `lot_id` | Many2one → `stock.lot` | check_company, tracking |
| `lot_name` | Char | — |
| `quantity_complained` | Float | digits=Product Unit of Measure |
| `product_uom_id` | Many2one → `uom.uom` | — |
| `manufacturing_date` | Date | — |
| `expiry_date` | Date | — |
| `market_country_id` | Many2one → `res.country` | — |
| `sample_available` | Boolean | — |
| `sample_reference` | Char | — |
| `sample_received_date` | Date | — |
| `summary` | Char | required, tracking |
| `description` | Text | required |
| `category_id` | Many2one → `ls.complaint.category` | check_company, tracking |
| `complaint_type` | Selection | tracking |
| `complaint_type_other_description` | Char | — |
| `severity` | Selection | tracking |
| `assessment_date` | Datetime | copy=False, readonly |
| `assessed_by_id` | Many2one → `res.users` | copy=False, readonly |
| `assessment_summary` | Text | — |
| `potential_safety_impact` | Boolean | tracking |
| `potential_regulatory_impact` | Boolean | tracking |
| `investigation_waiver_reason` | Text | copy=False |
| `investigation_ids` | One2many → `ls.complaint.investigation` | copy=False |
| `resolution_ids` | One2many → `ls.complaint.resolution` | copy=False |
| `adverse_event_ids` | One2many → `ls.complaint.adverse_event` | copy=False |
| `investigation_count` | Integer | compute=_compute_related_counts |
| `resolution_count` | Integer | compute=_compute_related_counts |
| `adverse_event_count` | Integer | compute=_compute_related_counts |
| `has_adverse_event` | Boolean | compute=_compute_regulatory_flags, store |
| `regulatory_reportable` | Boolean | compute=_compute_regulatory_flags, store, tracking |
| `root_cause_summary` | Text | compute=_compute_root_cause_summary |
| `capa_required` | Boolean | copy=False, tracking |
| `capa_justification` | Text | copy=False |
| `capa_reference` | Char | copy=False, tracking |
| `acknowledgement_due_date` | Date | compute=_compute_due_dates, store |
| `investigation_due_date` | Date | compute=_compute_due_dates, store |
| `closure_due_date` | Date | compute=_compute_due_dates, store |
| `customer_notified` | Boolean | copy=False, tracking |
| `customer_notification_date` | Date | copy=False |
| `date_closed` | Datetime | readonly, copy=False, tracking |
| `closed_by_id` | Many2one → `res.users` | readonly, copy=False |
| `closure_summary` | Text | copy=False |
| `cancellation_reason` | Text | copy=False |
| `closure_duration_days` | Float | compute=_compute_closure_duration_days, store |
| `is_overdue` | Boolean | compute=_compute_is_overdue, search=_search_is_overdue |

### `ls.complaint.category` — Complaint Category (14 declared fields)

| Field | Type | Attributes |
|---|---|---|
| `name` | Char | required, index |
| `code` | Char | required |
| `sequence` | Integer | default=10 |
| `active` | Boolean | default |
| `company_id` | Many2one → `res.company` | required, default=…, index |
| `description` | Text | — |
| `default_severity` | Selection | — |
| `requires_investigation` | Boolean | default |
| `acknowledgement_target_days` | Integer | default=0 |
| `investigation_target_days` | Integer | default=0 |
| `closure_target_days` | Integer | default=0 |
| `ae_reporting_deadline_days` | Integer | default=0 |
| `complaint_ids` | One2many → `ls.complaint` | — |
| `complaint_count` | Integer | compute=_compute_complaint_count |

### `ls.complaint.investigation` — Complaint Investigation (20 declared fields)

| Field | Type | Attributes |
|---|---|---|
| `name` | Char | required, readonly, copy=False, index, default=… |
| `sequence` | Integer | default=10 |
| `complaint_id` | Many2one → `ls.complaint` | required, index, check_company |
| `company_id` | Many2one → `res.company` | related=complaint_id.company_id, store, index, readonly |
| `state` | Selection | default=draft, required, copy=False, index, tracking |
| `investigator_id` | Many2one → `res.users` | required, default=…, tracking |
| `date_started` | Datetime | copy=False, readonly |
| `date_completed` | Datetime | copy=False, readonly |
| `methodology` | Selection | tracking |
| `methodology_other_description` | Char | — |
| `investigation_plan` | Text | — |
| `investigation_summary` | Text | — |
| `root_cause_category` | Selection | tracking |
| `root_cause_description` | Text | — |
| `conclusion` | Selection | tracking |
| `batch_impact_assessment` | Text | — |
| `other_batches_impacted` | Boolean | tracking |
| `approved_by_id` | Many2one → `res.users` | readonly, copy=False, tracking |
| `approval_date` | Datetime | readonly, copy=False |
| `rejection_reason` | Text | copy=False |

### `ls.complaint.adverse_event` — Complaint Adverse Event (26 declared fields)

| Field | Type | Attributes |
|---|---|---|
| `name` | Char | required, readonly, copy=False, index, default=… |
| `complaint_id` | Many2one → `ls.complaint` | required, index, check_company |
| `company_id` | Many2one → `res.company` | related=complaint_id.company_id, store, index, readonly |
| `state` | Selection | default=draft, required, copy=False, index, tracking |
| `event_date` | Date | — |
| `awareness_date` | Date | required, default=…, tracking |
| `event_description` | Text | required |
| `seriousness` | Selection | default=undetermined, required, tracking |
| `seriousness_criteria` | Text | — |
| `outcome` | Selection | default=unknown, required, tracking |
| `causality_assessment` | Selection | tracking |
| `causality_rationale` | Text | — |
| `patient_reference` | Char | — |
| `patient_age_range` | Selection | default=unknown |
| `patient_sex` | Selection | default=not_disclosed |
| `reportable` | Boolean | copy=False, tracking |
| `reportability_rationale` | Text | — |
| `authority_id` | Many2one → `res.partner` | — |
| `report_due_date` | Date | compute=_compute_report_due_date, store |
| `report_submitted_date` | Date | readonly, copy=False |
| `report_reference` | Char | copy=False |
| `submitted_by_id` | Many2one → `res.users` | readonly, copy=False |
| `follow_up_required` | Boolean | tracking |
| `follow_up_notes` | Text | — |
| `closure_notes` | Text | copy=False |
| `is_report_overdue` | Boolean | compute=_compute_is_report_overdue, search=_search_is_report_overdue |

### `ls.complaint.resolution` — Complaint Resolution (10 declared fields)

| Field | Type | Attributes |
|---|---|---|
| `complaint_id` | Many2one → `ls.complaint` | required, index, check_company |
| `company_id` | Many2one → `res.company` | related=complaint_id.company_id, store, index, readonly |
| `resolution_type` | Selection | required, tracking |
| `description` | Text | required |
| `owner_id` | Many2one → `res.users` | required, default=…, tracking |
| `due_date` | Date | tracking |
| `completion_date` | Date | readonly, copy=False |
| `state` | Selection | default=draft, required, copy=False, index, tracking |
| `completion_evidence` | Text | — |
| `cancellation_reason` | Text | copy=False |

### `ls.complaint.close.wizard` — Close Complaint Wizard (7 declared fields)

| Field | Type | Attributes |
|---|---|---|
| `complaint_id` | Many2one → `ls.complaint` | required |
| `complaint_state` | Selection | related=complaint_id.state, readonly |
| `owner_id` | Many2one | related=complaint_id.owner_id, readonly |
| `closure_summary` | Text | required |
| `reviewer_id` | Many2one → `res.users` | required |
| `effectiveness_confirmed` | Boolean | — |
| `customer_notified` | Boolean | — |

### `ls.complaint.cancel.wizard` — Cancel Complaint Wizard (2 declared fields)

| Field | Type | Attributes |
|---|---|---|
| `complaint_id` | Many2one → `ls.complaint` | required |
| `reason` | Text | required |

Total declared fields across the seven models: **143**.
## 5. Constraints

### 5.1 SQL constraints

| Model | Name | Definition |
|---|---|---|
| `ls.complaint` | `name_company_uniq` | `UNIQUE(name, company_id)` |
| `ls.complaint` | `quantity_complained_positive` | `CHECK(quantity_complained >= 0)` |
| `ls.complaint.category` | `code_company_uniq` | `UNIQUE(code, company_id)` |
| `ls.complaint.investigation` | `name_company_uniq` | `UNIQUE(name, company_id)` |
| `ls.complaint.adverse_event` | `name_company_uniq` | `UNIQUE(name, company_id)` |

### 5.2 Python constraints

| Model | Method | Enforces |
|---|---|---|
| `ls.complaint` | `_check_dates` | receipt not in the future, occurrence not after receipt |
| `ls.complaint` | `_check_product_dates` | expiry not before manufacturing |
| `ls.complaint` | `_check_channel_other` | description present for "Other Channel" |
| `ls.complaint` | `_check_complaint_type_other` | description present for "Other Type" |
| `ls.complaint` | `_check_product_required` | product identified once past Received |
| `ls.complaint` | `_check_lot_product` | lot belongs to the product |
| `ls.complaint` | `_check_segregation_of_duties` | reviewer ≠ responsible |
| `ls.complaint.category` | `_check_targets_positive` | no negative day target |
| `ls.complaint.category` | `_check_target_consistency` | acknowledgement target ≤ closure target |
| `ls.complaint.investigation` | `_check_dates` | completion not before start |
| `ls.complaint.investigation` | `_check_methodology_other` | description present for "Other Methodology" |
| `ls.complaint.investigation` | `_check_segregation_of_duties` | approver ≠ investigator |
| `ls.complaint.adverse_event` | `_check_dates` | awareness not in the future, event not after awareness |
| `ls.complaint.adverse_event` | `_check_reportability_rationale` | rationale present once assessed |
| `ls.complaint.resolution` | `_check_dates` | completion not before creation |
| `ls.complaint.close.wizard` | `_check_reviewer` | reviewer ≠ responsible |

## 6. Compute, search and onchange methods

| Model | Method | Kind | Notes |
|---|---|---|---|
| `ls.complaint` | `_compute_display_name` | compute | reference and subject |
| `ls.complaint` | `_compute_related_counts` | compute | three stat-button counters |
| `ls.complaint` | `_compute_regulatory_flags` | compute, **stored** | `has_adverse_event`, `regulatory_reportable` |
| `ls.complaint` | `_compute_root_cause_summary` | compute | concatenates approved investigations |
| `ls.complaint` | `_compute_due_dates` | compute, **stored** | three target dates from the category |
| `ls.complaint` | `_compute_closure_duration_days` | compute, **stored** | KPI measure |
| `ls.complaint` | `_compute_is_overdue` / `_search_is_overdue` | compute + search | non-stored, searchable, `=` and `!=` only |
| `ls.complaint` | `_onchange_product_id` | onchange | aligns the unit of measure, clears an inconsistent lot |
| `ls.complaint` | `_onchange_category_id` | onchange | proposes the default severity |
| `ls.complaint` | `_onchange_partner_id` | onchange | copies the contact details |
| `ls.complaint.category` | `_compute_complaint_count` | compute | single `_read_group`, no query per record |
| `ls.complaint.investigation` | `_compute_display_name` | compute | qualified by the complaint |
| `ls.complaint.adverse_event` | `_compute_display_name` | compute | qualified by the complaint |
| `ls.complaint.adverse_event` | `_compute_report_due_date` | compute, **stored** | awareness date + configured deadline |
| `ls.complaint.adverse_event` | `_compute_is_report_overdue` / `_search_is_report_overdue` | compute + search | non-stored, searchable |
| `ls.complaint.resolution` | `_compute_display_name` | compute | complaint plus resolution type |

Stored computes are used where the value must be searchable, groupable or
indexed. Non-stored computes with an explicit `search` method are used where the
value depends on the current date, because a stored value would be wrong the day
after it was computed.

## 7. ORM overrides

| Model | Override | Purpose |
|---|---|---|
| `ls.complaint` | `create` (`@api.model_create_multi`) | assigns the sequence per company |
| `ls.complaint` | `write` | refuses any change on closed or cancelled records, except a whitelist |
| `ls.complaint` | `copy_data` | resets the reference and the status on duplication |
| `ls.complaint` | `_unlink_except_progressed` (`@api.ondelete`) | forbids deletion past Received |
| `ls.complaint.investigation` | `create`, `write`, `_unlink_except_started` | sequence, freeze after approval or rejection, deletion only in draft |
| `ls.complaint.adverse_event` | `create`, `write`, `_unlink_except_assessed` | sequence, freeze after closure, deletion only in draft |
| `ls.complaint.resolution` | `write`, `_unlink_except_started` | freeze after done or cancelled, deletion only in draft |

## 8. Security model

### 8.1 Groups

| Group | Implies | Purpose |
|---|---|---|
| `group_ls_complaint_viewer` | — | read-only |
| `group_ls_complaint_investigator` | viewer | intake, assessment, investigation, resolution, adverse event |
| `group_ls_complaint_reviewer` | investigator | approval, waiver, closure |
| `group_ls_complaint_manager` | reviewer | cancellation, reset, deletion, configuration |

### 8.2 Access rights

21 rows in `ir.model.access.csv`. Summary:

| Model | Viewer | Investigator | Reviewer | Manager |
|---|---|---|---|---|
| `ls.complaint` | R | RWC | RWC | RWCU |
| `ls.complaint.category` | R | R | R | RWCU |
| `ls.complaint.investigation` | R | RWC | RWC | RWCU |
| `ls.complaint.resolution` | R | RWC | RWC | RWCU |
| `ls.complaint.adverse_event` | R | RWC | RWC | RWCU |
| `ls.complaint.close.wizard` | — | — | RWCU | RWCU |
| `ls.complaint.cancel.wizard` | — | — | — | RWCU |

R read, W write, C create, U unlink. **No group has unlink on the
transactional models except the manager**, and even the manager is blocked by
`@api.ondelete` once a record left its initial state.

### 8.3 Record rules

| Rule | Model | Scope | Domain |
|---|---|---|---|
| multi-company (×5) | each persistent model | global | `company_id` false or in `company_ids` |
| investigator writes own complaints | `ls.complaint` | investigator group, write only | responsible or receiving user is the current user |
| reviewer writes all complaints | `ls.complaint` | reviewer group, write only | always true |

Because non-global rules of the groups a user belongs to are combined with a
logical OR, a reviewer or a manager — who also belongs to the investigator group
through the implication chain — is not restricted by the ownership rule.

## 9. Views

| Model | Views |
|---|---|
| `ls.complaint` | list, form, search, graph, pivot |
| `ls.complaint.category` | list, form, search |
| `ls.complaint.investigation` | list, form, search, pivot |
| `ls.complaint.adverse_event` | list, form, search, graph |
| `ls.complaint.resolution` | list (editable), form, search |
| both wizards | form |

No kanban view is delivered — see R-09 in
`docs/00_verification_and_limitations.md`.

Conditional display uses the Odoo 17+ syntax (`invisible="…"`, `readonly="…"`,
`required="…"` with Python expressions). The obsolete `attrs` and `states`
attributes are not used anywhere, and a static check enforces their absence.

## 10. Controllers, services and public API

The module declares **no HTTP controller** and **no web service**. Integration
happens through the standard Odoo external API (XML-RPC / JSON-RPC) against the
seven models and their public methods, which are listed in
`docs/api_documentation.md`.

## 11. Scheduled jobs

Described in `docs/03_functional_specification.md` section 7. Both are declared
`noupdate="1"` so that an administrator can disable or retune them without a
module update overwriting the change.

## 12. Data files

| File | `noupdate` | Content |
|---|---|---|
| `ir_sequence_data.xml` | yes | 3 sequences, company-independent, prefixes `CMP/`, `CMP/INV/`, `CMP/AE/`, padding 5, year variable |
| `mail_template_data.xml` | yes | 2 templates on `ls.complaint` |
| `ir_cron_data.xml` | yes | 2 scheduled actions |
| `ls_complaint_security.xml` | no | module category, 4 groups, 7 record rules |
| `ir.model.access.csv` | no | 21 access rules |

**No complaint category is delivered as production data.** A category carries
time targets; delivering one would mean delivering a target the deploying
organisation did not choose.

## 13. Demo data

`demo/ls_complaint_demo.xml` creates two categories, one partner, one product,
three complaints and one adverse event. Every target value in it is marked as
illustrative in the record description and in an XML comment. No `stock.lot` is
created, to stay independent of the product type changes across Odoo versions.

## 14. Translation structure

All user-facing strings are wrapped in `_()` in Python and are translatable
attributes in XML. `name` and `description` on the category model carry
`translate=True`. No `.pot` file is delivered because generating it requires a
running Odoo instance; `i18n/README.md` gives the exact command.

## Phase 4 gate

**PASS** — architecture, dependencies, manifest, models, fields, constraints,
compute and onchange methods, security model, access rights, record rules, XML
structure, views, reports, controllers, scheduled jobs, data files, demo data
and translation structure are specified and implemented.
