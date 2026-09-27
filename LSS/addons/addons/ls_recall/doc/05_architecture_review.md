# Phase 5 — Architecture Review

Module: `ls_recall`
Reviewer role: Enterprise Software Architect / OCA maintainer perspective

---

## 1. Verdict

**PASS with four recorded deviations from the source specification.**

The deviations are recorded rather than silently applied, because each
changes something the source specification stated.

## 2. Deviations from the Life Sciences Suite Functional Specification v1.0

### D-01 — Dependencies reduced to `mail` and `stock`

*Specification §7.13 states:* dependencies `stock`, `ls_qms`,
`ls_complaint`.

*Implemented:* `mail`, `stock`.

*Reason:* `ls_qms` and `ls_complaint` do not exist. A module that
declares a dependency on a non-existent module cannot be installed, so
following the specification literally would produce something that
cannot run. The functional couplings the specification intended are
preserved as free-text reference fields — `defect_reference` and
`capa_reference` on the recall — which a later glue module can convert
into real relations without a data migration of the recall records
themselves.

*Consequence:* the module carries its own root menu. When a suite-level
quality module exists, a small bridging module should re-parent
`menu_ls_recall_root` and replace the reference fields with many2ones.

### D-02 — A model was added: `ls.recall.line`

*Specification §7.13 lists:* `ls.recall.plan`, `ls.recall.execution`,
`ls.recall.communication`, `ls.recall.report`.

*Implemented:* those four plus `ls.recall.line` and
`ls.recall.effectiveness`.

*Reason:* the specification requires "Recall Tracking — track recall
effectiveness" and an effectiveness check step in its state machine, but
provides no model to hold per-consignee data. Without one there is
nowhere to record who received what, who replied and how much came back
— which is the substance of a recall. The two models are the minimum
needed for the specification's own state machine to mean anything.

### D-03 — `stock.lot`, not `stock.production.lot`

*Specification §5.2.4 names:* `stock.production.lot`.

*Implemented:* `stock.lot`.

*Reason:* the model was renamed in Odoo 16. The specification's name
does not exist on the target platform. This is a correction to the
source document, which should be updated.

### D-04 — A `cancelled` state was added

*Specification §7.13 states:* Planned → Initiated → In Progress →
Communication → Effectiveness Check → Closed.

*Implemented:* the same six states, plus `cancelled`.

*Reason:* the six-state path has no exit for a decision that is
reversed — for instance when a defect is not confirmed on retest.
Without a cancelled state the only ways out are to delete the record,
which destroys evidence of a decision that was genuinely taken, or to
close it, which falsely asserts that a recall was completed. Neither is
acceptable in a regulated record. Cancellation requires a written
reason and leaves the record read-only.

## 3. Assessment against architectural principles

| Principle | Assessment |
|-----------|-----------|
| **Odoo architecture** | Standard module layout; no core modification; extension of `stock.lot` by inheritance only; all restrictions implemented in the ORM layer rather than in the client. |
| **OCA conventions** | AGPL-3, `19.0.1.0.0` version string, one model per file named after the model, `__manifest__.py` key ordering, security in `security/`, `development_status` declared. Departures: no `readme/` fragment directory, no `.pot`, author is a placeholder to be replaced by the implementing organisation. |
| **SOLID — single responsibility** | Each model holds one concept. The largest, `ls.recall.execution`, is the aggregate root; its 36 methods are workflow transitions, computes and helpers, none of which belong to another model. |
| **SOLID — open/closed** | Selections live in `constants.py`; `_workflow_writable_fields`, `_allowed_writes_when_controlled`, `_required_effectiveness_checks` and `_evaluate_closure_gates` are overridable seams for a downstream module. |
| **SOLID — dependency inversion** | The module depends on `stock` in one place only, `_scan_move_lines`. Replacing the source of distribution data means overriding one method. |
| **DRY** | Selections defined once; `_action_open_related` factors the four smart-button actions; `_assert_transition` factors the state guard; `_quantity_precision` factors float comparison. |
| **KISS** | No inheritance hierarchy of abstract models, no JavaScript, no controllers, no external services. The complexity is in the rules, which is where the domain complexity actually is. |
| **Separation of concerns** | Business rules in Python; presentation in XML; access in CSV and XML. No business logic in views. |
| **Upgradeability** | `noupdate="1"` on sequences and crons; no data records that a user is expected to edit; `models.Constraint` used in preference to raw SQL migration scripts. |
| **Extensibility** | The four seams above; reference fields ready for promotion to relations. |
| **Maintainability** | Every module, class and function carries a docstring, verified mechanically. Regulatory provenance is annotated at the point of definition in `constants.py`, so a future maintainer changing a selection value can see what it is derived from. |

## 4. Security review

### 4.1 The `sudo` in `stock.lot._compute_ls_recall_state`

This is the module's only privilege escalation and is deliberate.

*What it exposes:* whether a lot is named in a real, non-finalised field
action, and how many real actions have named it. Two attributes are
read: `action_type` and `state`.

*To whom:* any user who can already read the lot record.

*Why:* a warehouse operator picking stock generally holds no quality
role. If the indicator required a recall role, the person physically
handling the goods would be the one person not warned. The risk of a
recalled lot being shipped outweighs the disclosure of the fact that a
recall exists.

*What it does not expose:* the reason, the classification, the hazard
evaluation, the consignees, the communications. The smart button that
opens the recall records is restricted at arch level to
`group_ls_recall_viewer`.

*Residual risk:* accepted and documented. An organisation that treats
the existence of a recall as confidential from warehouse staff should
override the compute and restrict the field.

### 4.2 Other checks

| Concern | Finding |
|---------|---------|
| SQL injection | No raw SQL, no `self.env.cr.execute`. All access through the ORM. |
| XSS | HTML fields declare `sanitize=True`. The closure gate report is HTML built from module-controlled strings and integers only; no user text is interpolated into it. |
| Access rights | Every model has a rule for every group that needs it; verified mechanically by `static_checks.py`. |
| Record rules | Global multi-company rules on all six persistent models. |
| Privilege escalation via wizards | The close wizard checks `has_group` for the override path rather than relying on the view's `groups=` attribute, so an RPC caller cannot bypass it. |
| Mass-assignment through `write` | The finalisation and change-control restrictions are in `write()`, so they apply to RPC as well as to the UI. |

## 5. Performance review

| Concern | Assessment |
|---------|-----------|
| Tracing | One `search` on `stock.move.line` bounded by the lots named. `picking_id.partner_id` is read per move line, which Odoo prefetches in batch. Acceptable for the volumes a recall involves. |
| Computes | Stored computes on quantities and rates depend only on the child lines, so the recomputation set is bounded by one recall. |
| `_compute_execution_count` | Uses `_read_group` rather than a loop of `search_count`. |
| Counts on the form | `_compute_related_counts` is not stored and iterates one2many caches already loaded by the form. |
| Indexes | `index=True` on every foreign key used in a domain or grouping, and on the state and reference fields. |
| N+1 risk | `_compute_rates` iterates checks and lines already in cache; no query inside the loop. |

## 6. Findings raised during review and their resolution

| # | Finding | Resolution |
|---|---------|-----------|
| A1 | `widget="percentage"` was applied to fields storing 0–100, which would have displayed 90% as 9000%. | Widget removed from four fields. |
| A2 | `decoration-danger` was placed on a `<field>` inside a list; decorations are list-level attributes. | Moved to the `<list>` element. |
| A3 | `ir.ui.view.groups_id` was used to restrict an inherited view; the field is renamed in Odoo 19. | Field removed; restriction moved to the arch-level `groups=` attribute on the button. |
| A4 | `web_icon` referenced an icon file that did not exist, which fails at install. | Icon generated and shipped. |
| A5 | A redundant computed field existed only to make a constraint depend on a type. | Field removed; the constraint depends on the type directly. |
| A6 | An unused import remained in the close wizard. | Removed. |
| A7 | The close wizard used `sudo()` to cancel, which would have bypassed multi-company rules. | Removed; the coordinator has the necessary rights. |
| A8 | Package `__init__.py` files had no docstring. | Docstrings added. |

All eight were found and fixed before the static analysis run recorded
in `12_test_plan_and_report.md`.

## 7. Known architectural limitations

1. **No field-level audit trail.** Change history is Odoo's chatter over
   the fields marked `tracking=True`. A general audit trail belongs to a
   dedicated module.
2. **No electronic signature.** See `02_regulatory_analysis.md` §4.
3. **Tracing sees only what Odoo recorded.** Distribution outside the
   ERP must be entered manually.
4. **Lot-level granularity.** Serial-level or aggregation-level tracing
   is not modelled.
5. **One product per field action.** A defect spanning several products
   requires one record per product. This keeps reconciliation
   arithmetic unambiguous; a campaign-level grouping model could be
   added later without changing these records.
