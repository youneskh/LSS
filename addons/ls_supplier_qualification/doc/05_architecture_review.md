# Phase 5 — Architecture Review

Module: `ls_supplier_qualification` · Odoo 19 Community Edition
Reviewers: Solution Architect, Senior Odoo Architect, OCA-style reviewer,
Security Engineer, Performance Engineer, Validation Engineer
Status at end of phase: **PASS with 4 recorded deviations and 3 verification points**

---

## 5.1 Review method

The design was reviewed against six sets of expectations: the Odoo module
architecture, OCA conventions, general software-design principles, security,
performance, and the needs of a regulated environment. Each finding below is
either **closed** (the code was changed during this phase and the change is in
the delivered module) or **accepted** (a conscious deviation, recorded with its
reason and its consequence).

## 5.2 Odoo architecture conformance

| Point | Verdict |
|-------|---------|
| Standard directory layout (`models`, `views`, `security`, `data`, `demo`, `report`, `wizards`, `i18n`, `static/description`, `tests`) | Conforms. |
| One Python module per model, file named after the model | Conforms. |
| One view file per model plus a separate menu file | Conforms. |
| No modification of Odoo core; extension by `_inherit` only (`res.company`, `res.config.settings`, `res.partner`, `purchase.order`) | Conforms. |
| MVC separation: business rules in models, presentation in XML, no logic in views | Conforms. No `<field>` widget carries behaviour that is not also enforced server-side. |
| ORM used throughout; one raw SQL statement in the whole module | Conforms — see §5.6. |
| `<list>` instead of `<tree>`, `<chatter/>` element | Conforms (checked mechanically by `tools/static_check.py`). |
| No Enterprise-only model, view type, widget or asset | Conforms. Views use list, form, search, kanban, calendar, graph and pivot only. |

## 5.3 OCA conventions

| Point | Verdict |
|-------|---------|
| Licence AGPL-3 declared in the manifest and in every file header | Conforms. |
| Version string `19.0.1.0.0` | Conforms. |
| `_sql_constraints` with explicit, translatable messages | Conforms. |
| Field ordering: identification, then relations, then state, then computed | Conforms. |
| `_description` on every model | Conforms, enforced mechanically. |
| Docstrings on every module, class and method | Conforms, enforced mechanically. |
| `README.rst` at module root | Conforms. |
| No `print`, no debugger, no commented-out code, no markers | Conforms, enforced mechanically. |

## 5.4 Design-principle review

**Single responsibility.** Each model owns one concept. The dossier does not
compute assessment scores; the assessment does. The dossier reads results
through stored computed fields, so the coupling is one-directional.

**Don't repeat yourself.** The scoring formula exists once, in
`_compute_scores`. The blocking-prerequisite logic exists once, in
`_get_blocking_reasons`, and is consumed by the computed field, by the
submission action and by the approval wizard — three call sites, one rule.
The purchase check exists once, in
`res.partner.ls_get_qualification_blocking_message`, and is consumed by the
warning field and by the confirmation guard.

**Open/closed.** New criteria, categories and questionnaires are data, not
code. An organisation extends the module by configuring it. Adding a new
material type or a new audit type is a one-line selection extension.

**Keep it simple.** No state-machine engine, no rule engine, no abstraction
layer over the ORM. State transitions are explicit methods with explicit
guards, which is what a validation reviewer can read.

**Separation of concerns.** The signature log knows nothing about
qualification semantics beyond a back-reference; it stores who, when, what and
why. It can be lifted into `ls_electronic_signature` later without touching the
qualification models.

## 5.5 Findings

### F-01 — Stored computed fields on `res.partner` leaked status across companies (**closed**)

*Found.* `ls_qualification_id`, `ls_qualification_state`,
`ls_qualification_expiry_date` and `ls_is_approved_supplier` were declared
`store=True` while their compute reads `self.env.company`. A stored field holds
one value for all companies, so in a multi-company database the last recompute
would have decided what every other company saw.

*Action taken.* The four fields were made non-stored. Searching was preserved
by adding an explicit `_search_ls_is_approved_supplier` method that resolves
the domain through the qualification model in the current company. The
group-by on `ls_qualification_state` was removed from the contact search view,
because a non-stored field cannot be grouped.

*Consequence.* Reading a contact list with these fields costs one extra query
per batch. That is acceptable: the fields are not in the default contact list
view, and correctness outranks the saving.

### F-02 — `ir.rule.global` was written from a data file (**closed**)

*Found.* The multi-company rules set `<field name="global" eval="True"/>`.
`global` is a stored computed field derived from `groups`; writing it from data
is wrong regardless of Odoo version.

*Action taken.* The attribute was removed from all thirteen rules. A rule
without `groups` is global by definition, which is exactly the intent. The file
now carries a comment stating this so the next maintainer does not re-add it.

### F-03 — Hard dependency on suite modules that do not exist yet (**accepted deviation**)

The Life Sciences Suite specification places this module downstream of
`ls_qms`, and links it to `ls_audit` and `ls_capa`. None of those modules
exists yet. Declaring them in `depends` would make this module impossible to
install.

*Decision.* Depend only on `base`, `mail`, `product` and `purchase`. The
integration points are designed but not wired:

| Future module | Intended integration | What exists today |
|---------------|----------------------|-------------------|
| `ls_qms` | Link a dossier to the SOP that governs supplier qualification. | Nothing. Add a `Many2one` in a bridge module. |
| `ls_audit` | Reuse the generic audit engine instead of the supplier-specific one. | A self-contained audit model. A bridge would map, not replace, it. |
| `ls_capa` | Escalate a critical finding into a formal CAPA. | The finding carries root cause, corrective action, due date and verification, which is the data a CAPA would need. |
| `ls_electronic_signature` | Replace the login confirmation with real re-authentication. | `ls.supplier.signature` isolates the concern behind `sign()` and `verify_chain()`. |

*Consequence.* When those modules arrive, integration is delivered by bridge
modules (`ls_supplier_qualification_capa` and so on), not by editing this one.
That is the OCA pattern and it keeps this module installable standalone.

### F-04 — Segregation of duties implemented as a constraint, not a fourth group (**accepted deviation**)

The suite specification names three groups. A literal reading would add a
fourth "Approver" group to separate approval from assessment.

*Decision.* Keep three groups and enforce separation with a rule that compares
the approver against the assessors and lead auditors *of that dossier*, toggled
by `res.company.ls_enforce_sod`.

*Reasoning.* A group-based separation is static: it either forbids a manager
from ever assessing, which is unworkable in a small quality department, or it
permits the same person to assess and approve the same dossier, which is the
thing worth preventing. The record-level rule prevents exactly the conflict
that matters and leaves the organisational structure alone. It is also visible:
the refusal message names the person and the dossier, and the approval is
recorded in the signature log either way.

*Consequence.* An organisation that wants a hard group separation adds it in a
bridge module. The default (rule enabled) is the stricter behaviour.

### F-05 — `purchase_stock` field access without a declared dependency (**accepted, guarded**)

`action_compute_delivery_counters` reads `stock.move.purchase_line_id` and
`purchase.order.line.date_planned`. The first belongs to the `purchase_stock`
bridge module.

*Decision.* Do not depend on `purchase_stock`; check the fields at run time
with `'purchase_line_id' in self.env['stock.move']._fields` and raise a
`UserError` naming the missing module when they are absent.

*Reasoning.* The button is optional. Forcing every installation to pull in the
inventory stack for one convenience feature is disproportionate. The guard
means the failure mode is a clear message, not an `AttributeError`.

### F-06 — Assessment ownership rules use the `groups` field of `ir.rule` (**open verification point**)

The four ownership-refinement rules attach to a group through
`<field name="groups" eval="[(4, ref(...))]"/>`. This is the long-standing
field name. It could not be confirmed against the Odoo 19 source in the
preparation of this module: the online documentation pages returned navigation
content only when fetched, and no Odoo 19 source tree was available in the
build environment.

*Mitigation already in place.* The thirteen **security-critical** multi-company
rules do not use `groups` at all, so a rename would not affect data isolation.
Only the four ownership refinements are exposed, and their failure mode at
install time is a clear "invalid field" error, not a silent security hole.

*Required action before production use.* See §5.8.

## 5.6 Security review

| Aspect | Finding |
|--------|---------|
| SQL injection | One raw SQL statement exists, in `tests/test_signature.py`, and it is parameterised. No raw SQL in the module code. All searches go through the ORM. |
| XSS | No `t-raw` in any QWeb template. The only HTML field, `ls.supplier.qualification.notes`, is declared `sanitize=True`. |
| Access rights | 44 ACL lines, three per model. The signature log grants no write, create or unlink to any group. |
| Record rules | 13 global multi-company rules plus 4 ownership refinements. |
| Privilege escalation through `sudo()` | Two uses, both inside `ls.supplier.signature`: creating an entry, and reading the chain for verification. Both operate on a model no user can write to, so `sudo()` cannot be turned into a write primitive by a caller. |
| Input validation | Every numeric input is bounded by a Python constraint, an SQL check, or both. Dates are checked for chronology. |
| Mass-mailing risk from demo data | Demo addresses use the reserved `.invalid` TLD. |
| Information disclosure between companies | Addressed by F-01 and the multi-company rules. |

## 5.7 Performance review

| Aspect | Finding |
|--------|---------|
| N+1 queries | `_compute_qualification_count` uses `_read_group` rather than iterating. Other counters read already-prefetched one2many fields. |
| Index coverage | `index=True` on every field used in a stored search filter: dossier `name`, `state`, `expiry_date`, `next_audit_date`, `next_review_date`, `partner_id`, `company_id`; assessment and audit `state` and `company_id`; finding `severity` and `state`; signature `sequence_number`, `res_model`, `res_id`. |
| Stored versus computed | Indicators used in list decorations and search filters are stored. Fields used only on an open form (`days_to_expiry`, `blocking_reasons`, `is_expired`) are not, so they never cost a write on unrelated updates. |
| Scheduled-action cost | The three crons search on indexed fields with narrow domains and iterate over the result, not over the whole table. Activity creation is guarded by a duplicate check so a daily run over a stable dataset performs no writes. |
| Signature chain verification | `verify_chain` is O(n) over a company's log and is triggered manually, never in a request path. On a very large log this is a long-running action; it is exposed as an explicit button so the operator chooses when to pay the cost. |
| Report rendering | The dossier report iterates six one2many collections of one record. No sub-query per row. |

## 5.8 Verification required against the target Odoo 19 build

These three items could not be verified in the build environment, which had no
Odoo installation and no network access. They are listed here, in the
installation guide and in the compliance checklist so that they are checked
before the module is used.

| # | Item | How to verify | If it fails |
|---|------|---------------|-------------|
| V-01 | The `ir.rule` field holding the groups is named `groups`. | Install the module on a scratch database. A rename surfaces as a load error on `security/ls_supplier_qualification_security.xml`. | Rename the field in the four ownership rules. The thirteen multi-company rules are unaffected. |
| V-02 | Assigning security groups to a user. | Add a test user to Supplier Manager through the Settings interface. | None expected; the module ships no data record that writes user groups, precisely to avoid depending on that field name. |
| V-03 | `stock.move.purchase_line_id` and `purchase.order.line.date_planned` exist when `purchase_stock` is installed. | Press **Recompute Delivery Counters** on a draft performance evaluation. | The button raises a clear `UserError`. Counters stay manual; nothing else is affected. |

## 5.9 Upgradeability, extensibility, maintainability

**Upgrade safety.** Configuration, security and infrastructure data carry
`noupdate="1"`, so a module upgrade never overwrites an organisation's
categories, criteria, thresholds or record rules. View files are updatable so
that layout fixes ship normally. No field is removed or renamed relative to a
previous version, because this is version 1.0.0.

**Extension points.** Every state transition is a public method that can be
overridden. `_get_blocking_reasons` is the single hook for adding a
prerequisite. `ls_get_qualification_blocking_message` is the single hook for
changing the purchase policy. `sign()` is the single hook for replacing the
signature mechanism.

**Maintainability.** 18 model classes, 308 field declarations, no JavaScript,
no controller, one raw SQL statement in a test. The offline checker in
`tools/` runs in under a second and enforces the conventions that a reviewer
would otherwise check by hand.

---

**Phase 5 gate: PASS.**
Two findings closed in code (F-01, F-02). Three deviations accepted and
recorded with their reasoning (F-03, F-04, F-05). One verification point open
and carried forward (F-06 / V-01), with its blast radius limited by design.
Phase 6 may start.
