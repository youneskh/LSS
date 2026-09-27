# Phase 5 — Architecture Review Report

Reviewer role: Enterprise Software Architect, with input from the Senior Odoo
Architect, the Security Engineer and the Performance Engineer roles.
Scope: the design as implemented in Phase 6, before testing.

## 1. Odoo architecture conformance

| Criterion | Finding |
|---|---|
| Standard module layout | Conformant. `models/`, `views/`, `security/`, `data/`, `demo/`, `report/`, `wizards/`, `tests/`, `static/description/`. |
| No modification of Odoo core | Conformant. No core model is inherited or patched; only mixins are consumed. |
| Inheritance used where extension is needed | Conformant. `mail.thread` and `mail.activity.mixin` are inherited rather than reimplemented. |
| Business logic in Python, not in views | Conformant. Every view condition duplicates a server-side control; no control exists only in a view. |
| Sequences via `ir.sequence` | Conformant, with `with_company` so that a multi-company deployment can override per company. |
| Multi-company | Conformant. `company_id` on every persistent model, stored related on children, global record rules, `_check_company_auto`. |
| Enterprise-only features | None used. |

## 2. OCA conventions

| Criterion | Finding |
|---|---|
| One file per model, named after it | Conformant. |
| Copyright and licence header on every file | Conformant, AGPL-3. |
| Manifest keys | `name`, `summary`, `version`, `category`, `author`, `license`, `development_status`, `depends`, `data`, `demo`, `installable`, `application`, `auto_install` present. `website` and `maintainers` **deliberately absent** — inventing them would be fabricating information. **Minor deviation, accepted, documented.** |
| XML identifier naming | `<model>_view_<type>`, `<model>_action`, `menu_<…>`, `group_<…>`, `rule_<…>`, `access_<…>`. Conformant. |
| Section separators in long models | Conformant. |
| README | Present as `README.md` rather than the OCA `README.rst` fragment structure. **Minor deviation, accepted** — the fragment structure targets the OCA build pipeline, which is not in use here. |

## 3. Clean architecture and SOLID

**Single responsibility.** Each model owns one concept: the complaint owns the
lifecycle, the investigation owns causal analysis, the adverse event owns
vigilance, the resolution owns actions, the category owns configuration. The
wizards own data collection for a transition and nothing else.

**Open/closed.** Extension points exist and are documented: the CAPA linkage is
three fields plus a documented bridge-module contract; the transitions are
individually overridable methods; the guard helpers (`_ensure_state`,
`_require_fields`, `_check_can_close`) can be extended without rewriting the
transitions. Selections are extended by the standard `selection_add` mechanism.

**Liskov substitution.** No model narrows the contract of a model it inherits.
`write()` overrides raise rather than silently ignoring, so a caller cannot be
misled by a no-op.

**Interface segregation.** The four groups expose four distinct capability sets;
a viewer is never forced through an investigator interface.

**Dependency inversion.** The complaint does not depend on a CAPA
implementation, only on a reference string, so any future CAPA module can be
plugged in without touching this one.

## 4. DRY

The state guard, the mandatory-field guard and the smart-button action builder
are factored into helpers reused by every transition. The freeze logic follows
one pattern applied to four models — this is deliberate repetition of a
three-line pattern rather than an abstract base class, on the ground that the
whitelist of still-writable fields differs per model and an abstract mixin would
have to be parameterised until it was longer than the repetition. **Accepted,
with a note**: if a fifth transactional model appears, extract a mixin.

## 5. KISS

No metaprogramming, no dynamic model creation, no custom ORM, no JavaScript, no
controller. The most complex construct is a searchable non-stored compute, which
is a documented Odoo pattern. A reviewer unfamiliar with the module can read any
single model file end to end and understand it.

## 6. Separation of concerns

| Concern | Location |
|---|---|
| Lifecycle rules | model methods |
| Data integrity | SQL and Python constraints |
| Authorisation | ACL and record rules |
| Presentation | views |
| Configuration | `ls.complaint.category`, no code change required |
| Communication | mail templates, not hard-coded strings |
| Time-based reminders | scheduled actions |

The one deliberate crossing: the segregation-of-duties check appears both as a
constraint (data integrity) and as an explicit check inside `action_approve`
(lifecycle), so that the user receives an actionable message rather than a
constraint violation. **Accepted.**

## 7. Upgradeability

| Criterion | Finding |
|---|---|
| Version string | `19.0.1.0.0`, semantic, Odoo-prefixed. |
| `noupdate` on operational data | Sequences, crons and templates are `noupdate="1"`, so administrator changes survive an update. |
| Security data updatable | Groups, rules and the ACL are updatable so that a security fix propagates. |
| No stored data written by a data file into a transactional model | Conformant; only demo data creates transactional records. |
| Field renames | None; the module is at its first version. |
| Version-sensitive API | Isolated and listed in the risk register, each with a fallback. **This is the principal upgrade risk and it is documented rather than hidden.** |

## 8. Extensibility

Documented extension points: the CAPA bridge contract, selection extension,
transition method override, guard helper override, additional resolution types,
additional root cause categories, re-parenting of the root menu under a future
`ls_qms` Quality menu, and the candidate kanban view.

## 9. Maintainability

143 declared fields across seven models, no method longer than roughly 40 lines,
docstrings on every class and every public method with `:param:` and `:raises:`
where relevant, no dead code, no commented-out code, no `TODO` or `FIXME`
(enforced by the static checker), consistent naming, and a test file per model.

## 10. Security review

| Vector | Assessment |
|---|---|
| SQL injection | No raw SQL anywhere; only ORM calls. |
| XSS | No custom QWeb rendering of user input outside `t-field`, which escapes; no `t-raw`; no JavaScript. |
| Access control | Every model has an ACL row for every group that must reach it, and no more. Verified by static check. |
| Record isolation | Global multi-company rules on all five persistent models. Verified by test. |
| Privilege escalation through a wizard | The wizards call model methods that re-verify every precondition; a user cannot reach a transition through a wizard that he could not reach directly. |
| `sudo()` usage | Only in test fixtures, never in production code. |
| Data protection | Adverse events carry a pseudonym, an age range and a sex, and no free-text identity field; a warning is displayed. |
| Deletion of evidence | Blocked by ACL and by `@api.ondelete`. |
| Post-closure tampering | Blocked by `write()` at ORM level. **A database administrator is not blocked** — stated explicitly, because pretending otherwise would be the dangerous claim. |

## 11. Performance review

| Aspect | Assessment |
|---|---|
| N+1 queries | `_compute_complaint_count` uses one `_read_group`. Other computes iterate over already-loaded one2many recordsets. |
| Indexes | `name`, `state`, `company_id` on the complaint; `complaint_id` and `company_id` on every child; `code`/`name` on the category. |
| Stored versus computed | Values needed for grouping and filtering are stored; date-relative values are not stored and carry a search method, which avoids a daily mass recomputation. |
| Scheduled action cost | Both crons search on indexed, stored columns and are bounded by `limit=200` per run. |
| Report cost | One record per print; the tables iterate over already-loaded one2many sets. |
| Expected volume | Designed for tens of thousands of complaints. Beyond that, the pivot on `closure_duration_days` is the first thing to watch. |

## 12. Findings and corrective actions

| # | Severity | Finding | Action |
|---|---|---|---|
| F-01 | Major | The specified dependencies `ls_qms` and `ls_capa` do not exist; declaring them makes the module non-installable. | Replaced by native dependencies plus a documented CAPA extension point. Applied, documented as D-01. |
| F-02 | Major | The specified state list has no cancellation state, forcing deletion of erroneous records. | `cancelled` state added with a mandatory reason. Applied, documented as D-03. |
| F-03 | Major | Encoding reporting deadlines as defaults would assert unverified regulatory requirements. | All targets moved to configuration, defaulting to *not configured*. Applied, documented as D-05. |
| F-04 | Major | The Odoo 19 kanban template API could not be confirmed; a wrong kanban arch prevents installation. | Kanban omitted; candidate snippet moved to the developer manual. Applied, documented as R-09. |
| F-05 | Minor | `group_operator` / `aggregator` naming on the KPI measure is version-sensitive. | Attribute removed; the measure still works, only the default aggregation differs. Applied, documented as R-07. |
| F-06 | Minor | The rejection and cancellation reasons were originally readonly, leaving no way to enter them before the action. | Fields made writable, actions read them, buttons carry a confirmation. Applied. |
| F-07 | Minor | The freeze pattern is repeated on four models. | Accepted as-is; extract a mixin if a fifth model appears. Deferred with justification. |
| F-08 | Informational | `website` and `maintainers` are absent from the manifest. | Left absent deliberately; the publishing organisation must add them. |

All Major findings are closed. No open blocking finding remains.

## Phase 5 gate

**PASS** — Odoo architecture, OCA conventions, clean architecture, SOLID, DRY,
KISS, separation of concerns, upgradeability, extensibility and maintainability
reviewed; eight findings raised, four Major findings corrected, one Minor
deferred with justification, one informational accepted.
