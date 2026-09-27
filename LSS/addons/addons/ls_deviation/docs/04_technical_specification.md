# 04 — Technical Specification

**Phase gate: PASS**

## 4.1 Module identity

| Attribute | Value |
|---|---|
| Technical name | `ls_deviation` |
| Version | `19.0.1.0.0` |
| Licence | AGPL-3 |
| Category | Life Sciences/Quality |
| Application | Yes (owns a root menu) |
| Depends | `base`, `mail`, `hr`, `stock`, `mrp`, `maintenance` |
| External Python packages | None beyond the Odoo runtime |

Dependency rationale: `mail` for chatter, tracking and activities; `hr` for
department; `stock` for `stock.lot` and `stock.location`; `mrp` for
`mrp.production`; `maintenance` for `maintenance.equipment`. All five are
Layer 1 modules of the suite architecture and will be present in any regulated
manufacturing deployment.

## 4.2 Directory tree

```
ls_deviation/
├── __init__.py
├── __manifest__.py
├── README.md
├── data/
│   ├── ir_cron_data.xml
│   ├── ir_sequence_data.xml
│   ├── ls_deviation_category_data.xml
│   ├── ls_deviation_rca_method_data.xml
│   ├── ls_deviation_type_data.xml
│   ├── mail_message_subtype_data.xml
│   └── mail_template_data.xml
├── demo/
│   └── ls_deviation_demo.xml
├── docs/
│   ├── 00_VERIFICATION_STATUS.md
│   ├── 01_business_analysis.md
│   ├── 02_regulatory_analysis.md
│   ├── 03_functional_specification.md
│   ├── 04_technical_specification.md
│   ├── 05_architecture_review.md
│   ├── 06_test_plan.md
│   ├── 07_static_analysis_report.md
│   ├── 08_installation_and_configuration.md
│   ├── 09_user_and_admin_manual.md
│   ├── 10_validation_checklist.md
│   └── CHANGELOG.md
├── i18n/
│   └── ls_deviation.pot
├── models/
│   ├── __init__.py
│   ├── ls_deviation.py
│   ├── ls_deviation_action.py
│   ├── ls_deviation_category.py
│   ├── ls_deviation_disposition.py
│   ├── ls_deviation_investigation.py
│   ├── ls_deviation_rca_method.py
│   ├── ls_deviation_stage_log.py
│   ├── ls_deviation_tag.py
│   ├── ls_deviation_type.py
│   ├── res_company.py
│   └── res_config_settings.py
├── report/
│   ├── ls_deviation_report.xml
│   └── ls_deviation_report_templates.xml
├── security/
│   ├── ir.model.access.csv
│   └── ls_deviation_security.xml
├── static/description/
│   └── icon.png
├── tests/
│   ├── __init__.py
│   ├── common.py
│   ├── test_deviation_constraints.py
│   ├── test_deviation_cron.py
│   ├── test_deviation_disposition.py
│   ├── test_deviation_investigation.py
│   ├── test_deviation_security.py
│   ├── test_deviation_stage_log.py
│   ├── test_deviation_wizards.py
│   └── test_deviation_workflow.py
├── views/
│   ├── ls_deviation_action_views.xml
│   ├── ls_deviation_category_views.xml
│   ├── ls_deviation_disposition_views.xml
│   ├── ls_deviation_investigation_views.xml
│   ├── ls_deviation_menus.xml
│   ├── ls_deviation_rca_method_views.xml
│   ├── ls_deviation_stage_log_views.xml
│   ├── ls_deviation_tag_views.xml
│   ├── ls_deviation_type_views.xml
│   ├── ls_deviation_views.xml
│   └── res_config_settings_views.xml
└── wizards/
    ├── __init__.py
    ├── ls_deviation_cancel_wizard.py
    ├── ls_deviation_cancel_wizard_views.xml
    ├── ls_deviation_close_wizard.py
    ├── ls_deviation_close_wizard_views.xml
    ├── ls_deviation_due_date_wizard.py
    └── ls_deviation_due_date_wizard_views.xml
```

## 4.3 Models

| Model | Type | Fields | Purpose |
|---|---|---|---|
| `ls.deviation` | Model | 56 | The deviation record |
| `ls.deviation.investigation` | Model | 12 | Root cause investigation |
| `ls.deviation.disposition` | Model | 11 | Product disposition decision |
| `ls.deviation.action` | Model | 10 | Immediate/containment/correction action |
| `ls.deviation.stage.log` | Model | 6 | Append-only transition log |
| `ls.deviation.type` | Model | 7 | Configurable nature of deviation |
| `ls.deviation.category` | Model | 7 | Configurable functional area |
| `ls.deviation.rca.method` | Model | 5 | Configurable RCA technique |
| `ls.deviation.tag` | Model | 3 | Trending label |
| `ls.deviation.close.wizard` | TransientModel | 7 | Closure evidence capture |
| `ls.deviation.cancel.wizard` | TransientModel | 3 | Cancellation / send-back |
| `ls.deviation.due.date.wizard` | TransientModel | 4 | Justified date extension |
| `res.company` | Inherit | +3 | Closure targets per severity |
| `res.config.settings` | Inherit | +3 | Settings exposure |

`ls.deviation` inherits `mail.thread` and `mail.activity.mixin`.
`ls.deviation.investigation` and `ls.deviation.disposition` inherit
`mail.thread`.

## 4.4 Constraints

**SQL (Odoo 19 `models.Constraint` declarative form):**

| Model | Attribute | Definition |
|---|---|---|
| `ls.deviation` | `_name_company_uniq` | `UNIQUE(name, company_id)` |
| `ls.deviation` | `_quantity_affected_positive` | `CHECK(quantity_affected >= 0)` |
| `ls.deviation.disposition` | `_quantity_positive` | `CHECK(quantity > 0)` |
| `ls.deviation.type` | `_code_company_uniq` | `UNIQUE(code, company_id)` |
| `ls.deviation.category` | `_code_company_uniq` | `UNIQUE(code, company_id)` |
| `ls.deviation.rca.method` | `_code_uniq` | `UNIQUE(code)` |
| `ls.deviation.tag` | `_name_uniq` | `UNIQUE(name)` |

**Python (`@api.constrains`):** `_check_chronology`,
`_check_planned_justification`, `_check_quantity_requires_product`,
`_check_completion_evidence`, `_check_dates`, `_check_lot_product`.

## 4.5 Compute, search and onchange

| Method | Model | Notes |
|---|---|---|
| `_compute_product_uom_id` | deviation, disposition | Stored, depends on product |
| `_compute_has_impact` | deviation | Stored, depends on five flags |
| `_compute_days_open` | deviation | Non-stored |
| `_compute_is_overdue` | deviation | Non-stored, paired with `_search_is_overdue` |
| `_search_is_overdue` | deviation | Supports `=` and `!=` only; raises otherwise |
| `_compute_related_counts` | deviation | Smart-button counters |
| `_compute_deviation_count` | category | Uses `_read_group` (Odoo 19 API) |
| `_group_expand_state` | deviation | Renders all kanban columns |
| `_onchange_severity_set_due_date` | deviation | Proposes target date from company settings |
| `_onchange_production_id` | deviation | Defaults product from the MO |

`is_overdue` is deliberately **not stored**: a stored computed field would not
recompute merely because the date changed, so it would silently go stale. The
paired search method keeps it filterable.

## 4.6 Security model

Four hierarchical groups under a `res.groups.privilege` record.
29 ACL rows covering all 12 module-owned models. 11 record rules: 7 global
multi-company rules and 4 group rules on `ls.deviation` whose OR-combination
yields the intended privilege ladder.

No user is assigned to any group at installation. This is deliberate: role
assignment is an authorisation activity requiring per-user evidence.

## 4.7 CAPA integration hook

`ls_capa` does not exist, so no dependency is declared. The integration
surface is:

- `capa_required` (boolean), `capa_reference` (char), `capa_decision_rationale` (text) on `ls.deviation`.
- The `capa_required` state.

When `ls_capa` is implemented, create a bridge module `ls_deviation_capa`
depending on both, which adds a `capa_id` many2one, makes `capa_reference` a
related stored field of it, and extends `action_require_capa` to create the
CAPA record. No change to this module is required. Keeping the linkage in a
bridge module is the standard OCA pattern and keeps `ls_deviation` installable
on its own.

## 4.8 Translation

`i18n/ls_deviation.pot` is provided as a template. All user-facing strings use
`_()` with named `%(placeholder)s` interpolation, which is the form that
survives reordering during translation.
