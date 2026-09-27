# Phase 4 — Technical Specification

Module: `ls_recall` — Odoo 19 Community Edition

---

## 1. Module layout

```
ls_recall/
├── __init__.py
├── __manifest__.py
├── data/
│   ├── ir_cron_data.xml            2 scheduled actions
│   └── ir_sequence_data.xml        4 sequences
├── demo/
│   └── ls_recall_demo.xml
├── doc/                            this documentation set
├── models/
│   ├── __init__.py
│   ├── constants.py                selections, with provenance annotations
│   ├── ls_recall_plan.py
│   ├── ls_recall_execution.py
│   ├── ls_recall_line.py
│   ├── ls_recall_communication.py
│   ├── ls_recall_effectiveness.py
│   ├── ls_recall_report.py
│   └── stock_lot.py
├── report/
│   ├── ls_recall_report_actions.xml
│   ├── ls_recall_notice_template.xml
│   └── ls_recall_summary_template.xml
├── security/
│   ├── ir.model.access.csv         22 rules
│   └── ls_recall_security.xml      category, privilege, 3 groups, 6 rules
├── static/description/icon.png
├── tests/                          10 files
├── views/                          8 files
└── wizards/
    ├── __init__.py
    ├── ls_recall_initiate_wizard.py
    ├── ls_recall_close_wizard.py
    └── *_views.xml
```

## 2. Dependencies

```python
"depends": ["mail", "stock"]
```

| Dependency | Why |
|------------|-----|
| `mail` | `mail.thread` and `mail.activity.mixin` provide the chatter used as the change history and the activities used by the scheduled actions. |
| `stock` | `stock.lot`, `stock.move.line` and `stock.picking` are the source of distribution tracing. |

`stock` pulls in `product` and `base` transitively. No dependency on
`ls_qms`, `ls_capa` or `ls_complaint`: see deviation D-01 in
`05_architecture_review.md`.

No third-party Python package is required. `dateutil` is already an Odoo
runtime dependency and is used for `relativedelta`.

## 3. Models

| Model | Type | Purpose | Fields | Methods |
|-------|------|---------|--------|---------|
| `ls.recall.plan` | regular | Standing arrangement | 24 | 17 |
| `ls.recall.execution` | regular | One field action | 59 | 36 |
| `ls.recall.line` | regular | Consignee/lot reconciliation | 19 | 8 |
| `ls.recall.communication` | regular | One issued message | 25 | 12 |
| `ls.recall.effectiveness` | regular | One documented contact | 14 | 6 |
| `ls.recall.report` | regular | Status or final report | 33 | 9 |
| `stock.lot` | inherit | Recall visibility on lots | 3 added | 2 added |
| `ls.recall.initiate.wizard` | transient | Opening a field action | 12 | 3 |
| `ls.recall.close.wizard` | transient | Closing or cancelling | 7 | 2 |

Counts are produced by `static_checks.py` from the source, not by hand.

### 3.1 Relationships

```
ls.recall.plan 1 ──────< ls.recall.execution
                              │
                              ├──< ls.recall.line >──── res.partner
                              │         └──────────────  stock.lot
                              ├──< ls.recall.communication >── res.partner
                              ├──< ls.recall.effectiveness ──> ls.recall.line
                              └──< ls.recall.report
ls.recall.execution >──── product.product
ls.recall.execution >──< stock.lot   (ls_recall_execution_lot_rel)
```

`ls.recall.report` uses `ondelete="restrict"` on its recall: an approved
report must not disappear because its parent was removed. All other
children cascade.

### 3.2 Constraints

SQL constraints are declared with `models.Constraint`, which replaced
`_sql_constraints` in Odoo 19.

| Model | Constraint | Rule |
|-------|-----------|------|
| plan | `_code_company_uniq` | UNIQUE(code, company_id) |
| plan | `_reconciliation_rate_range` | 0 ≤ target ≤ 100 |
| plan | `_mock_interval_positive` | interval ≥ 0 |
| plan | `_initiation_target_positive` | target ≥ 0 |
| execution | `_name_uniq` | UNIQUE(name) |
| execution | `_sample_pct_range` | 0 ≤ sample ≤ 100 |
| line | `_partner_lot_uniq` | UNIQUE(execution_id, partner_id, lot_id) |
| line | `_quantities_positive` | all four quantities ≥ 0 |
| effectiveness | `_attempt_positive` | attempt > 0 |
| communication | `_name_uniq` | UNIQUE(name) |
| report | `_name_uniq` | UNIQUE(name) |

Python constraints (`@api.constrains`): plan scope completeness, plan
approval completeness, level B bounds, lot/product agreement, date
ordering, communication recipients, effectiveness line ownership,
effectiveness completeness, report period ordering, single final report.

### 3.3 Write restrictions

Implemented in `write()` overrides rather than only as view readonly, so
they hold for RPC callers too.

| Model | Restriction |
|-------|-------------|
| plan | Approved or obsolete: only workflow and bookkeeping fields writable. |
| execution | Closed or cancelled: only `active` and mail fields writable. Fields in `EXECUTION_LOCKED_AFTER_INITIATION` frozen once the state leaves `planned`. |
| line | No writes when the parent recall is closed or cancelled; quantity changes are posted to the chatter. |
| communication | Sent or acknowledged: only acknowledgement and mail fields writable. |
| effectiveness | No writes when the parent recall is closed or cancelled. |
| report | Approved or submitted: only submission and mail fields writable. |

Deletion is blocked by `@api.ondelete(at_uninstall=False)` on plan
(non-draft), execution (non-planned), communication (non-draft) and
report (non-draft).

## 4. Security model

### 4.1 Groups

Odoo 19 replaced `res.groups.category_id` with `privilege_id`, pointing
at the new `res.groups.privilege` model. The security file follows that
structure: one `ir.module.category`, one `res.groups.privilege`, three
`res.groups` chained by `implied_ids`.

### 4.2 Access rights

22 rules across 8 models and 3 groups. Viewer is read-only everywhere;
coordinator gains create and write but never unlink and never write on
plans; manager gains everything including unlink.

### 4.3 Record rules

Six **global** multi-company rules, one per persistent model with a
company, each using the standard pattern:

```
['|', ('company_id', '=', False), ('company_id', 'in', company_ids)]
```

Global rules are used rather than group-scoped rules because a global
rule intersects with every other rule and cannot be escaped by adding a
user to a further group. No other record rule exists: within a company,
every holder of a recall role sees every recall, which is the point of
the record.

### 4.4 The one deliberate `sudo`

`stock.lot._compute_ls_recall_state` reads through `sudo`, limited to
`action_type` and `state`. Rationale and risk assessment in
`05_architecture_review.md` §4.

## 5. Distribution tracing algorithm

```
for each execution:
    move_lines := stock.move.line where
        lot_id ∈ execution.lot_ids
        and state = 'done'
        and location_dest_id.usage = 'customer'
        and company_id = execution.company_id
    for each move_line:
        partner := move_line.picking_id.partner_id
        if not partner: accumulate into unassigned_qty; continue
        traced[(partner, lot)].quantity += move_line.quantity
        traced[(partner, lot)].picking_ids ∪= {move_line.picking_id}
    for each (key, data) in traced:
        if a line exists for key: write qty_shipped and picking_ids
        else: create the line
    post a chatter summary including unassigned_qty
```

Properties:

* **Idempotent for user data.** Only `qty_shipped` and `picking_ids` are
  written. `qty_returned`, `qty_destroyed`, `qty_not_recovered`,
  `notified` and `response_received` are never touched.
* **Additive.** A line created manually for a consignee outside the ERP
  survives re-tracing.
* **Reported, not silent.** Quantity that cannot be attributed to a
  consignee is stated in the chatter rather than dropped.
* **Refused after finalisation.** Tracing raises on a closed or
  cancelled recall.

`search()` with Python accumulation is used in preference to
`_read_group`, because the grouping key spans a relation
(`picking_id.partner_id`) and the volume in a recall is bounded by the
lots involved.

## 6. XML structure

| File | Contents |
|------|----------|
| `security/ls_recall_security.xml` | 1 category, 1 privilege, 3 groups, 6 global rules |
| `data/ir_sequence_data.xml` | 4 sequences, `noupdate="1"`, `no_gap` implementation, company-independent |
| `data/ir_cron_data.xml` | 2 crons, `noupdate="1"`, `state="code"` |
| `views/*.xml` | 6 forms, 6 lists, 6 searches, 1 graph, 1 pivot, 7 window actions, 1 inherited stock view |
| `wizards/*_views.xml` | 2 forms, 1 window action (8 window actions in total across the module) |
| `report/*.xml` | 2 report actions, 2 QWeb templates |
| `views/ls_recall_menus.xml` | 12 menu items: 1 root, 3 sections, 8 leaves |

Sequences use `noupdate="1"` so that a module upgrade cannot reset a
counter that has already issued references to real records.

## 7. Odoo 19 API usage

| Construct | Note |
|-----------|------|
| `models.Constraint(definition, message)` | Replaces `_sql_constraints`; the attribute name becomes the constraint name. |
| `res.groups.privilege_id` | Replaces `category_id`. |
| `<list>` | Replaces `<tree>`. |
| `invisible="expr"` / `readonly="expr"` | Replaces the removed `attrs`. |
| `<chatter/>` | Replaces the manual `oe_chatter` div. |
| `_compute_display_name` | Replaces `name_get`. |
| `self.env._()` | Used instead of importing `_`. |
| `@api.model_create_multi` | Used on every `create` override. |
| `Command.link` | Used in XML `eval` for x2many writes. |

## 8. Fields the module does not use, and why

| Not used | Reason |
|----------|--------|
| `widget="percentage"` | It renders a 0–1 ratio as a percentage. The rate fields here store 0–100, so the widget would multiply them by a hundred. Plain float display is used. |
| `ir.ui.view.groups_id` | Renamed in Odoo 19. View-level restriction is done with the arch-level `groups=` attribute on the element instead, which is unaffected. |
| `digits=` on Float | Would require naming a decimal-precision record whose exact name was not verified. Default precision is used. |
| `numbercall` / `doall` on `ir.cron` | Removed in Odoo 17. |
| `stock.production.lot` | Renamed to `stock.lot` in Odoo 16. The source specification names the old model; see D-03. |

## 9. Translation

No `.pot` file is shipped. A translation template must be generated from
a running instance:

```
odoo-bin -d <db> --i18n-export=ls_recall.pot --modules=ls_recall --stop-after-init
```

Hand-writing a `.pot` would mean asserting line numbers and message
extraction that were never produced by the extractor. See
`14_verification_register.md` item 12.
