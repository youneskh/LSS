# 05 — Architecture Review

**Phase gate: PASS with two accepted deviations from the suite specification**
(both recorded in `00_VERIFICATION_STATUS.md` section 7).

## 5.1 Odoo architecture conformance

| Criterion | Assessment |
|---|---|
| Standard module layout | Conformant: `models/`, `views/`, `security/`, `data/`, `demo/`, `report/`, `wizards/`, `tests/`, `i18n/`, `static/description/` |
| No core modification | Conformant. `res.company` and `res.config.settings` are extended by `_inherit`; nothing in Odoo core is edited |
| MVC separation | Conformant. Business rules live in Python; XML carries presentation only; no business logic in QWeb beyond formatting selection labels |
| ORM usage | Conformant. No raw SQL anywhere. Grouping uses `_read_group` |
| Manifest completeness | Conformant. Every XML file in the tree is loaded by the manifest, verified programmatically |
| Load order | Security before data before views before wizards before report before menus. Menus load last so every action they reference exists |

## 5.2 SOLID assessment

**Single responsibility.** Each model owns one concept. The transition log is
a separate model rather than fields on the deviation, because its lifecycle
rule (append-only) differs from the parent's.

**Open/closed.** The state machine is data in `STATE_TRANSITIONS`, not
branching logic. Extending the workflow means adding entries to that mapping
and an action method, not editing existing guards. Wizards are separate
transient models, so adding a step does not touch `ls.deviation`.

**Liskov.** Only mixin inheritance is used. `_track_subtype` calls `super()`
for every case it does not handle.

**Interface segregation.** The four groups are separate rather than one
"deviation user" group with conditional behaviour.

**Dependency inversion.** The CAPA linkage is a plain char reference plus a
documented bridge-module pattern, so this module does not depend on a module
that does not exist.

## 5.3 DRY

- The `_apply_transition` helper centralises guard checking, state assignment and logging; no action method repeats that sequence.
- `_deviation_values` and the three `_advance_to_*` helpers in `tests/common.py` remove fixture duplication across eight test modules.
- Closure targets live once on `res.company` and are read through `_ls_deviation_target_days`.

Accepted duplication: `_compute_product_uom_id` appears on both the deviation
and the disposition. Extracting a mixin for four lines would cost more in
indirection than it saves.

## 5.4 KISS

Rejected as unnecessary complexity: a configurable workflow engine; a generic
approval matrix; storing `is_overdue`; auto-generating stock moves from
dispositions. Each was considered and each would have added state to keep
synchronised for no proportionate benefit.

## 5.5 Separation of concerns

| Concern | Location |
|---|---|
| Workflow rules | `ls_deviation.py` transition map and action methods |
| Data integrity | SQL constraints and `@api.constrains` |
| Authorisation | `security/` — ACL and record rules, plus explicit group checks where an action must be restricted regardless of ACL |
| Presentation | `views/` |
| Closure evidence capture | `wizards/` |
| Master data | `data/` |

Disposition approval is guarded **both** by an ACL and by an explicit
`has_group` check in `action_approve`. This is intentional redundancy: the ACL
protects the record, the explicit check protects the business decision, and the
second survives an administrator loosening the first.

## 5.6 Upgradeability

| Risk | Mitigation |
|---|---|
| Six Odoo 19 API changes | Verified against official documentation before use; listed in `00_VERIFICATION_STATUS.md` section 3 |
| Field renames in future versions | No field of a dependency is redefined; only new fields are added |
| Data loss on upgrade | Master data files carry `noupdate="1"`, so site customisation of types and categories survives module upgrade |
| Sequence continuity | The sequence is `noupdate="1"`; reinstalling does not reset numbering |
| Demo data breaking install | Demo records reference no external master data, removing the most common demo-install failure mode |

## 5.7 Extensibility

Documented extension points: add a state by extending `STATE_TRANSITIONS` and
`STATE_SELECTION`; add a disposition decision by extending the selection;
integrate CAPA via a bridge module; add e-signature by overriding
`_apply_transition`; add a regulated audit trail by registering the models
with `ls_audit_trail`.

`_apply_transition` is the single choke point through which every state change
passes, which is what makes the e-signature extension a single override rather
than a change at every action method.

## 5.8 Findings raised during review

| # | Finding | Resolution |
|---|---|---|
| AR-1 | `_sql_constraints` would not apply constraints on Odoo 19 | Rewritten as `models.Constraint` |
| AR-2 | `read_group` deprecated | Rewritten as `_read_group` with tuple unpacking |
| AR-3 | `stock.production.lot` in the suite specification no longer exists | Uses `stock.lot`; recorded as a specification defect |
| AR-4 | Declared dependencies `ls_qms` and `ls_capa` do not exist and would block installation | Dependencies reduced; CAPA hook documented |
| AR-5 | Mail subtypes were declared but never used | `_track_subtype` implemented so they are live |
| AR-6 | `res.groups.category_id` no longer valid | Rewritten using `res.groups.privilege` and `privilege_id` |
| AR-7 | Assigning admin to the manager group at install would create unevidenced access | Removed; documented as a post-install authorisation step |
| AR-8 | Storing `is_overdue` would go stale | Left non-stored with a search method |
| AR-9 | Deleting a deviation would break sequence continuity | Deletion blocked past `reported`; cancellation retains the record |

## 5.9 Known weaknesses

Stated rather than hidden:

1. **No electronic signature.** Approval and closure are ordinary writes by an authenticated user. For Part 11 environments this is insufficient on its own.
2. **Transition log is append-only at application level, not database level.** A user with direct PostgreSQL access can alter it. Database-level protection is an infrastructure control.
3. **Disposition does not move stock.** A "Destroy" decision records the decision; it does not scrap the quant. Deliberate, but it means two systems must agree.
4. **No recurrence detection.** Trending is available through pivot and graph views, but the module does not automatically flag a repeat deviation.
5. **Never executed.** See `00_VERIFICATION_STATUS.md`.
