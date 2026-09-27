# PHASE 5 — ARCHITECTURE REVIEW REPORT

Module: `ls_training` — Life Sciences Training Management
Reviewers: Enterprise Software Architect, Senior Odoo Architect,
Senior OCA Maintainer, Security Engineer, Performance Engineer,
Validation Engineer

---

## 1. Verdict

**PASS with three accepted limitations** (§6). No blocking finding.

## 2. Odoo architecture conformance

| Check | Result | Evidence |
|-------|--------|----------|
| Standard module layout | PASS | models/, views/, security/, data/, demo/, report/, wizards/, tests/, i18n/, static/description/ |
| One model per Python file, named after the model | PASS | 8 model files |
| No modification of Odoo core | PASS | Only `_inherit = "hr.employee"` |
| Inheritance used instead of replacement | PASS | `hr.employee` extended with prefixed fields |
| Field prefixing on inherited models | PASS | All added fields use `ls_training_` prefix, avoiding collisions |
| Business logic in models, not views | PASS | Views contain no expressions beyond visibility/readonly |
| Wizards as TransientModel | PASS | 3 transient models |
| Sequences via `ir.sequence` | PASS | 3 sequences, no manual counters |
| Reports as QWeb templates | PASS | 2 reports using `web.external_layout` |
| `@api.model_create_multi` on create overrides | PASS | 3 overrides |
| Computed counters use `_read_group` | PASS | 5 counter computes |
| `ondelete` declared on every Many2one to a business model | PASS | restrict where evidence must survive, cascade where the child is meaningless alone |

## 3. OCA conformance

| Check | Result | Note |
|-------|--------|------|
| AGPL-3 licence declared and in every file header | PASS | |
| Version string `19.0.1.0.0` | PASS | |
| `development_status` declared | PASS | Beta — correct, since the suite has never been executed |
| No `external_dependencies` beyond Odoo core | PASS | Keeps deployment simple in validated environments |
| `README.rst` present | PASS | |
| Tests in `tests/` with a shared `common.py` | PASS | |
| `@tagged("post_install", "-at_install")` on test classes | PASS | Correct for tests requiring a fully loaded registry |
| Translatable user-facing strings wrapped in `_()` | PASS | All `UserError` and `ValidationError` messages |
| No commented-out code, no TODO/FIXME | PASS | Verified by static check, 0 occurrences |

## 4. Design principles

### SOLID

| Principle | Assessment |
|-----------|-----------|
| Single responsibility | **PASS.** Each model owns one concept. Certification issuance logic lives on the certification model (`_prepare_from_attendance`), not in the session, so the session orchestrates but does not know how to build a certification. |
| Open/closed | **PASS.** Extension points documented; state machines are method-based and overridable; no monolithic dispatch to modify. |
| Liskov substitution | **PASS.** `hr.employee` extension adds fields and methods only; it overrides nothing and changes no existing contract. |
| Interface segregation | **PASS.** Learners are not granted access to models they cannot use; the ACL is per-model rather than blanket. |
| Dependency inversion | **PARTIAL.** Models reference each other by `self.env["..."]` string, which is Odoo's idiom rather than injected dependencies. Accepted as framework convention. |

### DRY

- Outcome derivation exists in exactly one place (`_compute_result`), and
  the session, wizard and matrix all read it rather than recomputing.
- Requirement resolution exists in exactly one place
  (`_get_requirements_for_employee`), used by the matrix wizard, the
  registration wizard and the employee compliance compute.
- Certification value construction exists once
  (`_prepare_from_attendance`).
- The expiry warning window is read through one accessor
  (`_get_expiry_warning_days`) rather than parsed at each call site.

### KISS

- No metaclasses, no dynamic model generation, no monkey-patching.
- No JavaScript. The module adds zero front-end assets; every view uses
  stock Odoo widgets. This materially reduces upgrade risk, which matters
  more in a validated environment than UI polish.
- No raw SQL in the shipped code (see §5).

### Separation of concerns

| Concern | Location |
|---------|----------|
| Master data lifecycle | course, competency models |
| Operational workflow | session model |
| Evidence capture | attendance, assessment models |
| Evidence retention | certification model |
| Policy definition | requirement model |
| Reporting | matrix wizard, QWeb templates |
| Notification | mail template + cron methods |
| Authorisation | security/ directory |

## 5. Rejected design: PostgreSQL view for the training matrix

The first design modelled `ls.training.matrix` as a read-only model with
`_auto = False` over a PostgreSQL view joining `ls_training_requirement`,
`hr_employee` and a `LATERAL` sub-select for the latest certification.
That design is the conventional Odoo pattern for analysis models
(`sale.report`, `stock.report`) and would have been substantially faster.

**It was rejected**, for reasons recorded here so the decision is
auditable:

1. **Unverifiable physical schema.** Odoo 19 restructured HR
   substantially — `hr.contract` became `hr.version`, among other changes.
   Whether `job_id` and `department_id` remain columns of `hr_employee`
   could not be verified from official documentation. A SQL view hard-codes
   that assumption; a wrong guess produces either an installation failure
   or, worse, a silently wrong population.
2. **Silent-wrongness asymmetry.** An ORM query against a field that has
   moved to a related model generally still resolves. A SQL join against a
   column that has moved fails loudly at install — or, if a same-named
   column exists with different semantics, returns wrong answers. For a
   training-gap report used to decide who may work in a cleanroom, a
   silently wrong answer is the worst possible failure mode.
3. **Record rules.** The ORM path applies record rules and multi-company
   scoping automatically. A SQL view requires re-implementing that
   filtering in the view definition, duplicating security logic in a second
   language — a recurring source of leakage.
4. **Raw SQL surface.** Avoiding raw SQL entirely removes a class of
   injection review from the security assessment. There is no dynamic SQL
   anywhere in the shipped module.

**Cost accepted:** matrix generation issues O(employees × courses) queries
instead of one. Mitigated by a hard 20 000-line guard with an actionable
message. Recorded as accepted limitation L-1.

**Reversal condition:** once the module has been installed and the Odoo 19
`hr` schema confirmed, a SQL-view variant may be introduced behind the
same public interface (`ls.training.matrix.line`) without changing any
caller.

## 6. Accepted limitations

| ID | Limitation | Impact | Why accepted |
|----|-----------|--------|--------------|
| L-1 | Matrix generation is O(employees × courses) queries | Slow on very large populations | Correctness under an unverifiable schema was ranked above speed. Bounded and documented. |
| L-2 | `ls_training_compliance_rate` is not stored | Cannot be searched, grouped or used in a list view efficiently | Storing a date-dependent value guarantees staleness between cron runs. A wrong-but-fast compliance number is worse than one that must be computed on demand. The matrix wizard covers bulk reporting. |
| L-3 | Session closure is performed by a single Trainer with no counter-approval | Weak segregation of duties for GxP | Implementing a second approval here would duplicate `ls_electronic_signature`. Documented as an integration point rather than solved twice. |

## 7. Security review

| Check | Result |
|-------|--------|
| Raw SQL / injection surface | **PASS.** No raw SQL in shipped code. The single `cr.execute` in the test suite is parameterised. |
| XSS surface | **PASS.** No custom JavaScript, no `t-raw`. The one Html field (`course.description`) is rendered through standard Odoo widgets which sanitise. |
| Input validation | **PASS.** 8 SQL constraints and 18 Python constraints; all numeric ranges bounded. |
| Access rights completeness | **PASS.** Every model has an ACL line for every group that should reach it; no model is left ACL-less (which would deny all non-superuser access). |
| Record rules present on every model carrying `company_id` | **PASS.** 7 global rules. |
| Privilege escalation via inherited fields | **PASS.** `hr.employee` additions are read-only computes or One2many to models with their own ACL. |
| Sensitive data exposure to Learners | **PASS by rule**, contingent on the `ir.rule` field name resolving (see `verification_notes.md` §2). `test_security.py` asserts the rules loaded. |
| `sudo()` usage | **PASS.** Used only in `_get_expiry_warning_days` to read a system parameter, and in the reminder cron. Both are read-only, no user data crosses a boundary. |

## 8. Upgradeability

| Risk | Assessment |
|------|-----------|
| Core modification | None |
| View inheritance fragility | Two xpath-free inherits on `hr.view_employee_form` using element and `position="inside"` locators, which are more robust than deep xpaths |
| Field name collisions on `hr.employee` | Avoided by `ls_training_` prefix |
| Front-end asset breakage | None — no assets |
| Data migration on future versions | State selections and model names are stable; no field is planned for rename |
| Reliance on unverified APIs | 5 items, all catalogued in `verification_notes.md` with remediation; the highest-risk one ships with a working alternate file |

## 9. Findings and actions

| # | Finding | Severity | Action | Status |
|---|---------|----------|--------|--------|
| F-01 | `ir.rule` group field name unverified for Odoo 19 | High | Ship both variants; minimise blast radius by making all multi-company rules global; assert rule presence in tests | **Closed** |
| F-02 | Original SQL-view matrix hard-codes HR schema | High | Redesigned to ORM-only resolution | **Closed** |
| F-03 | Absent attendees block session closure | Medium | Confirmed as intended; documented in user manual and risk R-07 | **Closed** |
| F-04 | Compliance rate not searchable | Medium | Accepted as L-2; matrix wizard provides bulk reporting | **Closed** |
| F-05 | Test line exceeded 79 characters; one test assertion was convoluted | Low | Line reflowed; assertion rewritten to test the actual behaviour (revoked status is terminal) | **Closed** |
| F-06 | `mail` was a transitive dependency only | Low | Declared explicitly in the manifest | **Closed** |
| F-07 | Certification `unlink` originally allowed for Managers | Medium | Changed to always raise; revocation is the only withdrawal path | **Closed** |
| F-08 | Test suite never executed | High | Cannot be closed in this environment. Stated in `test_report.md`; execution is a release precondition | **Open — accepted, disclosed** |

## 10. Gate decision

| Phase | Outcome |
|-------|---------|
| Phase 5 — Architecture Review | **PASS** |

Proceed to Phase 6 (Development). Finding F-08 remains open by necessity
and is carried forward to Phase 7 and Phase 10, where it constrains the
overall release recommendation.
