# Phase 5 — Architecture Review Report

Reviewers: Enterprise Software Architect, Senior Odoo Architect, Senior OCA
Maintainer, Security Engineer, Performance Engineer, Validation Engineer.

## 5.1 Odoo architecture conformance

| Criterion | Finding |
|---|---|
| Standard module layout | Conforms. `models/`, `wizards/`, `security/`, `data/`, `views/`, `report/`, `tests/`, `i18n/`, `static/description/`. |
| Odoo core untouched | Conforms. Only `res.config.settings` is extended, by `_inherit`. No core file is modified, monkey-patched or copied. |
| Inheritance over modification | Conforms. Capability is delivered by an `AbstractModel` mixin, the idiomatic Odoo mechanism. |
| MVC separation | Conforms. Business rules live in models; views carry no logic; `tools/` holds pure functions with no ORM coupling. |
| ORM practice | Conforms. `@api.model_create_multi`; batched search in the mixin compute; parameterised SQL only where the ORM cannot express an advisory lock or a chain-head read. |
| 19.0 API currency | Conforms. `models.Constraint` replaces `_sql_constraints` (verified against the official 19.0 tutorial). `<list>` replaces `<tree>`. No `attrs`/`states`. `t-out` rather than `t-esc`/`t-raw`. |
| Enterprise independence | Conforms. Dependencies are `base` and `mail`, both LGPLv3 Community. |

## 5.2 OCA practice conformance

| Criterion | Finding |
|---|---|
| Version string | `19.0.1.0.0`. Conforms. |
| Licence coherence | AGPL-3 over LGPLv3 dependencies. Permissible. |
| One model per file, file named after the model | Conforms. |
| Test fixtures isolated from the production module | Conforms — `ls_electronic_signature_test` follows the pattern Odoo itself uses for `test_*` addons. |
| Complete `README` | Conforms, including an explicit non-compliance-claim notice. |
| No committed `.pot` that misstates source references | Conforms, with the generation command documented. |

## 5.3 SOLID, DRY, KISS, Separation of Concerns

**Single responsibility.** Each model has exactly one: meaning is vocabulary;
policy is configuration; log is evidence; attempt is the security log; session
is continuity; request is routing; integrity check is verification results. The
wizard orchestrates and owns no data.

**Open/closed.** A new signable model requires no change to this module: it
inherits the mixin and declares its payload. A new meaning or policy is data.
The payload composition is overridable via `_ls_signature_fields` and
`_ls_signature_field_value` without touching the digest algorithm.

**Liskov.** The mixin overrides only `write`, and only to add a precondition
that can be bypassed by an explicit context flag. It changes no return type and
weakens no postcondition.

**Interface segregation.** A model that only needs to display signatures uses
the computed fields; a model that needs enforcement additionally configures a
transition policy. Neither is obliged to take the other.

**Dependency inversion.** The one volatile external dependency — the private
`res.users` password API — is inverted behind `tools/credentials.py`. Callers
depend on `verify_password(user, password) -> bool`, not on the Odoo internal.

**DRY.** Canonicalisation exists once, in `tools/hashing.py`, and is used by the
wizard, the log and the mixin. The manifestation block exists once and is
`t-call`ed. Integer parameter reading is factored into `_int_parameter`.

**KISS.** No state machine on signatures. No sequential approval. No custom
JavaScript. No HTTP controller. Each absence is a deliberate reduction in
validated surface.

**Separation of concerns.** `tools/` is ORM-free and unit-testable in
isolation; models hold rules; views hold presentation; the wizard holds
orchestration.

## 5.4 Findings raised during review, and their resolution

| # | Severity | Finding | Resolution |
|---|---|---|---|
| AR-1 | **High** | Signers hold `perm_create` on the log, so a crafted RPC could record a signature attributed to another person, defeating §11.200(a)(2). | `_force_signer_identity` overwrites signer identity and timestamp server-side for every non-elevated call. Regression test `test_signer_cannot_attribute_a_signature_to_someone_else`. **Closed.** |
| AR-2 | **High** | `is_current` is a non-stored compute, so the ORM served a value cached earlier in the transaction and did not react to a later edit of the signed record. A stale signature could have satisfied a policy. | Explicit `invalidate_recordset(["is_current"])` before every evaluation in the mixin, both when surfacing signatures and when counting them against a policy. Regression test `test_is_current_reacts_to_an_edit_in_the_same_transaction`. **Closed.** |
| AR-3 | **High** | The first draft set `session_id` with a post-insert `UPDATE`, which the module's own immutability trigger would have rejected — the module would not have installed and run correctly. | The signing session is registered before the log row is created, so `session_id` is part of the insert. No `UPDATE` is ever issued against the table. **Closed.** |
| AR-4 | Medium | A failed attempt raises, rolling back the transaction and destroying the very §11.300(d) evidence that must be kept. | Attempts are written on an independent cursor committed before the exception is raised, with a documented switch for the test transaction. **Closed.** |
| AR-5 | Medium | Policy model-signability was probed through registry internals (`_inherit_module`), which is fragile and would have raised `TypeError`. | Replaced with an explicit `_ls_signature_enabled` class marker set by the mixin. **Closed.** |
| AR-6 | Medium | A credential API fault would have been reported to the signer as a wrong password, hiding a system defect behind a routine user error and, worse, contributing to a spurious lockout. | `CredentialApiError` is a distinct exception, logged as `system_error`, never as `invalid_password`. **Closed.** |
| AR-7 | Medium | Deleting a signer would orphan historical signatures and permit login recycling, contrary to §11.100(a). | `ondelete="restrict"` on `user_id`; archiving is the supported route; both behaviours tested. **Closed.** |
| AR-8 | Low | `verify_chain` could stop at the first divergence, hiding later ones. | The walk continues past a divergence, re-anchoring expectations, and reports every message while recording the first divergence separately. **Closed.** |
| AR-9 | Low | Trigger creation could fail on a restricted database role and block installation. | Wrapped; outcome recorded in a system parameter, surfaced in settings, and honoured by the tests, which skip rather than falsely pass. **Closed.** |
| AR-10 | Low | The `.pot` file, if hand-authored, would carry source references that do not match the real extraction. | Not shipped; generation command documented. **Closed by documented decision.** |
| AR-11 | **Open** | The private `res.users` password API signature for 19.0 could not be verified from official documentation. | Mitigated by the adapter, not eliminated. Carried into Phase 10 as verification obligation **OQ-CRED-001**. **Open — mitigated.** |
| AR-12 | **Open** | `<chatter/>` and the settings `<app>`/`<block>`/`<setting>` elements could not be verified against 19.0 documentation. | Carried into Phase 10 as **OQ-VIEW-001**. Failure mode is a view that does not render, detected on first install, with no effect on evidence integrity. **Open — mitigated.** |

## 5.5 Upgradeability

Version-sensitive surfaces, in descending order of risk: view XML element names;
the private credential API; `models.Constraint`; ORM method signatures. The
first two are the subject of AR-11 and AR-12. All data files carry
`noupdate="1"`, so a module upgrade never overwrites site configuration. The
canonicalisation rules are versioned by the `schema` key inside the payload
itself, so a future change can be introduced without invalidating past
signatures: old entries keep `schema: 1` and continue to verify under the rules
that produced them.

## 5.6 Extensibility

Documented extension points: `_ls_signature_field_whitelist`;
`_ls_signature_fields()`; `_ls_signature_field_value()`;
`_ls_signature_payload()`; the `signature_manifestation` template; the
`ls_signature_bypass` context flag for code that has already verified policy
satisfaction. Sibling suite modules (`ls_qms`, `ls_capa`, `ls_deviation`,
`ls_change_control`, `ls_validation`, `ls_lab`) consume the mixin without
modifying this module.

## 5.7 Maintainability

Every module, class, method and function carries a docstring stating purpose,
parameters, return value and raised exceptions. Regulatory rationale is recorded
next to the code that implements it, so a future maintainer cannot remove a
control without seeing why it exists. Static analysis reports zero findings.
There are no `TODO`, `FIXME` or `XXX` markers, no commented-out code and no
dead code — all checked mechanically.

## Gate

**PASS with two open, mitigated items.** AR-1 through AR-10 are closed in code
with regression tests. AR-11 and AR-12 are environment-verification obligations
that cannot be discharged without the target Odoo 19.0 build; both are carried
forward to Phase 10 as named qualification tests, and neither can compromise
the integrity of signature evidence.
