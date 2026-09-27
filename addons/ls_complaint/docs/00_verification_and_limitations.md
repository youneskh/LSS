# 00 — Verification Status, Limitations and Risk Register

This document exists because the assignment requires that verified facts be
separated from architectural recommendations, and that anything unverifiable be
stated as such. Read it before the other documents.

## 1. What was verified, and how

The module was produced in an offline container with **Python 3.12.3**, no
network access and **no Odoo installation**. The following verifications were
actually executed and passed:

| Verification | Tool | Result |
|---|---|---|
| Python syntax of every `.py` file | `python -m compileall` | PASS |
| XML well-formedness of every `.xml` file | `xml.dom.minidom` / `ElementTree` | PASS |
| CSV structure of `ir.model.access.csv` | `csv.DictReader` | PASS |
| Line length (≤88), tabs, trailing whitespace | custom checker | PASS |
| Absence of `TODO`, `FIXME`, `XXX`, `pdb.set_trace` | custom checker | PASS |
| Manifest: declared files exist, all files declared, required keys present | custom checker | PASS |
| Every `ref=` / `groups=` resolves to a module or dependency identifier | custom checker | PASS |
| Every ACL row targets a declared model and an existing group | custom checker | PASS |
| Every model has at least one ACL row | custom checker | PASS |
| Every `<field name="…">` in a view exists on its model | custom checker | PASS |
| Every `type="object"` button targets an existing method | custom checker | PASS |
| No duplicate XML identifiers | custom checker | PASS |
| Every `t-field` in the report resolves to a real field | custom checker | PASS |
| Absence of APIs removed in Odoo 17/18 (`attrs`, `states`, `<tree>`, `oe_chatter`, `name_get`, `numbercall`, `stock.production.lot`) | custom checker | PASS |

## 2. What could NOT be verified

**This information could not be verified from official documentation.**

The following were **not** performed, and no claim is made about them:

1. **The module was not installed on Odoo 19.** No Odoo runtime exists in this
   environment and the network is disabled, so `-i ls_complaint` was never run.
   *Installation success is therefore unproven.*
2. **No test was executed.** The suite in `tests/` was authored but never run.
   *No coverage figure can be reported.* The 95% coverage target of the
   assignment is **not demonstrated**.
3. **`flake8`, `pylint` and `pylint-odoo` are not installed** and could not be
   installed offline. A substitute checker was written and executed instead
   (section 1). It does not replicate every rule of those tools.
4. **The Odoo 19 API surface could not be checked against official
   documentation.** Section 4 lists every point where a version-sensitive API
   was used.
5. **No regulatory text was consulted.** No deadline, threshold or classification
   in this module is taken from a regulation (see section 3).

## 3. Deliberate refusal to encode regulatory values

The module contains **no hard-coded regulatory timeline**. Specifically:

- acknowledgement, investigation and closure targets, and
- the adverse event reporting deadline

are all `Integer` fields on `ls.complaint.category`, defaulting to `0`
(meaning *not configured*), and no due date is produced while the value is `0`.

Values such as "15 days" or "30 days" circulate widely in life sciences
practice, but their applicability depends on the product, the market, the
authority and the event type. Encoding them as defaults would have amounted to
asserting a regulatory requirement that was not verified here. Regulatory
Affairs must configure them.

The same applies to seriousness and causality vocabularies: the selections are
provided as neutral working vocabularies, not as citations of any standard.

## 4. Odoo 19 API risk register

Each item below is an API whose exact form in Odoo 19 could not be confirmed
offline. Each has a stated fallback. These are the first places to look if the
module fails to load.

| ID | Location | Used form | If it fails |
|---|---|---|---|
| R-01 | all list views | `<list>` | Revert to `<tree>` (pre-18 name) |
| R-02 | form views | `<chatter/>` | Revert to the `<div class="oe_chatter">` block with `message_follower_ids`, `activity_ids`, `message_ids` |
| R-03 | all models | `_sql_constraints = [(name, definition, message)]` | Convert to the declarative `models.Constraint` form if the list form was dropped |
| R-04 | `ls_complaint_category._compute_complaint_count` | `_read_group(domain, groupby, aggregates)` returning tuples | Adapt to the signature of the installed version |
| R-05 | `tests/common.py` | user↔group link written through `res.groups.users` | Deliberately avoids `res.users.groups_id` / `group_ids`, whose name is version-sensitive |
| R-06 | `data/ir_cron_data.xml` | no `numbercall`, no `doall`, no `nextcall` | Add `nextcall` if the field has no default in the installed version |
| R-07 | `ls_complaint.closure_duration_days` | no aggregator attribute | Add `aggregator="avg"` (18+) or `group_operator="avg"` (≤17) to average the KPI in group-by |
| R-08 | `tests/test_cron_and_reports.py` | `report._render_qweb_html(report_name, ids)[0]` | Adapt to the signature of the installed version |
| R-09 | views | **no kanban view is delivered** | The Odoo 18+ kanban `<t t-name="card">` template could not be confirmed; a candidate snippet is in `docs/developer_manual.md` and must be validated before use |
| R-10 | `ls_complaint.copy_data` | mutates `default` then delegates to `super()` | Version-neutral by construction (works whether `copy_data` returns a dict or a list) |
| R-11 | `tests/common.py` | `_make_lot_trackable` inspects `_fields` before writing `is_storable` / `type` / `tracking` | Version-neutral by construction |
| R-12 | `demo/ls_complaint_demo.xml` | products created with `name` and `default_code` only; no `stock.lot` created | Avoids the `type` / `is_storable` change of Odoo 18 |
| R-13 | `tests/common.py` | `from odoo import Command` | Available since Odoo 15 |
| R-14 | all models | `@api.ondelete(at_uninstall=False)` | Available since Odoo 15 |
| R-15 | form views | `bg_color="text-bg-danger"` on `web_ribbon` | Bootstrap 5 class naming; use `bg-danger` on older themes |

## 5. Deviations from the source functional specification

The source document (*Life Sciences Suite — Functional Specification, v1.0*)
specifies `ls_complaint` in section 7.12. The following deviations were made
deliberately; each is justified.

| ID | Specification | Delivered | Justification |
|---|---|---|---|
| D-01 | `depends: ls_qms, ls_capa` | `depends: base, mail, product, stock` | `ls_qms` and `ls_capa` do not exist. Declaring them would make the module non-installable, contradicting the requirement that the module install successfully. CAPA linkage is delivered as an extension point (`capa_required`, `capa_justification`, `capa_reference`) to be replaced by a bridge module. |
| D-02 | 4 models | 5 models + 2 wizards | `ls.complaint.category` was added so that classification and all time targets are configuration rather than code. The two wizards enforce that closure and cancellation cannot happen without a recorded justification. |
| D-03 | states: Received → Assessment → Investigation → CAPA Required → Resolution → Closed | same six states plus `cancelled` | Without a cancellation state, an erroneous or duplicate complaint could only be deleted, which destroys the record. Cancellation preserves it with a documented reason. |
| D-04 | menus under `Quality → Complaints` | root menu `Complaints` | The `Quality` root menu belongs to `ls_qms`, which does not exist. Re-parenting instructions are in `docs/administrator_manual.md`. |
| D-05 | "Adverse Event Reporting — support for regulatory reporting" | reporting deadline is configuration, defaulting to *not configured* | See section 3. |
| D-06 | "Complaint Trends — trend analysis and reporting" | list, graph, pivot and search group-by; no kanban | See R-09. |

## 6. What must happen before this module is used in a regulated environment

This module is **not** validated software and is **not** compliant with any
regulation on its own. Before use in a GxP context the deploying organisation
must, at minimum:

1. Install it on a controlled Odoo 19 Community instance and confirm it loads.
2. Execute the delivered test suite, record the results and the coverage.
3. Perform its own computer system validation (URS, risk assessment, IQ, OQ, PQ)
   against its own intended use.
4. Configure the categories, targets and deadlines from its own procedures.
5. Assess whether the audit trail provided here (Odoo `mail.thread` field
   tracking) satisfies its own data integrity requirements — see
   `docs/02_regulatory_analysis.md`, section 4, which explains why it likely
   does not on its own.
