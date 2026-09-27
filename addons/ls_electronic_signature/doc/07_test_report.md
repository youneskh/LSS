# Phase 7 — Test Report

## 7.1 Execution status — read this first

**The test suite was written but not executed.** The build environment used to
produce this delivery has no Odoo installation, no PostgreSQL server and no
network access. No test result is reported below as passing, because none was
observed.

This document therefore reports **what is tested**, not **what passed**. The
suite must be executed against the target Odoo 19.0 Community build and the
output attached to the validation file before release. A test report claiming
results that were never obtained would be a data integrity failure of exactly
the kind this module exists to prevent.

## 7.2 Suite inventory

140 test methods across 14 files.

| Module | File | Tests |
|---|---|---|
| `ls_electronic_signature` | `test_attempt.py` | 9 |
| `ls_electronic_signature` | `test_credentials_adapter.py` | 7 |
| `ls_electronic_signature` | `test_hashing.py` | 14 |
| `ls_electronic_signature` | `test_install.py` | 8 |
| `ls_electronic_signature` | `test_meaning.py` | 8 |
| `ls_electronic_signature` | `test_session.py` | 10 |
| `ls_electronic_signature_test` | `test_integrity_check.py` | 4 |
| `ls_electronic_signature_test` | `test_log_chain.py` | 10 |
| `ls_electronic_signature_test` | `test_log_immutability.py` | 8 |
| `ls_electronic_signature_test` | `test_mixin.py` | 12 |
| `ls_electronic_signature_test` | `test_policy.py` | 11 |
| `ls_electronic_signature_test` | `test_request.py` | 12 |
| `ls_electronic_signature_test` | `test_security.py` | 11 |
| `ls_electronic_signature_test` | `test_wizard.py` | 16 |
| | **Total** | **140** |

## 7.3 Coverage by test level

| Level | Where | What it covers |
|---|---|---|
| Unit | `test_hashing`, `test_credentials_adapter` | Canonicalisation determinism, type rejection, chain digest algebra, adapter decision logic. No ORM. |
| Integration | `test_log_chain`, `test_mixin`, `test_request` | Chain construction across records, mixin behaviour on a real signable model, request lifecycle. |
| Functional | `test_wizard` | The full control sequence of §3.2.1, both accepted and refused. |
| Security | `test_security`, `test_log_immutability` | Access rights, record rules, privilege escalation, immutability at ORM, sudo and SQL layers. |
| Constraint | `test_policy`, `test_meaning` | Every Python and SQL constraint, positive and negative. |
| Installation | `test_install` | Module state, model presence, ACL invariants, cron activation, trigger presence. |
| Upgrade | `test_install` | Re-runs on `-u`; `noupdate="1"` on all data means an upgrade must not overwrite configuration. |

## 7.4 Requirement traceability

| Requirement | Verified by |
|---|---|
| §11.50(a)(1) printed name | `test_log_chain.test_manifestation_carries_the_three_required_items`, `test_manifestation_fields_are_snapshots` |
| §11.50(a)(2) date and time | same |
| §11.50(a)(3) meaning | same; `test_meaning.*` |
| §11.50(b) human readable form | Report templates — **manual test MT-1**, see §7.6 |
| §11.70 linking, excision | `test_log_chain.test_deleted_entry_is_detected_as_a_gap`, `test_each_entry_links_to_its_predecessor`, `test_sequence_increments_without_gaps` |
| §11.70 linking, falsification | `test_log_chain.test_tampered_payload_is_detected`, `test_is_current_reacts_to_an_edit_in_the_same_transaction`, `test_mixin.test_signature_is_current_until_the_record_changes` |
| §11.70 linking, transfer | `test_mixin.test_payload_binds_signer_and_meaning` |
| §11.100(a) no reassignment | `test_log_immutability.test_signer_account_cannot_be_deleted`, `test_signer_account_can_be_archived` |
| §11.100(c) binding statement shown | `test_wizard.test_binding_statement_is_presented`, `test_consent_is_required` |
| §11.200(a)(1) two components | `test_wizard.test_missing_password_is_refused`, `test_wrong_password_is_refused` |
| §11.200(a)(1)(i) continuous period | `test_session.test_recent_session_is_continuous` |
| §11.200(a)(1)(ii) outside a period | `test_session.test_stale_session_is_not_continuous`, `test_closed_session_is_not_continuous`, `test_wizard.test_password_is_required_without_a_web_session` |
| §11.200(a)(2) genuine owner only | `test_wizard.test_identity_mismatch_is_refused`, `test_security.test_signer_cannot_attribute_a_signature_to_someone_else` |
| §11.300(d) attempts recorded | `test_wizard.test_every_failure_is_logged`, `test_success_is_logged_and_linked` |
| §11.300(d) immediate report | `test_attempt.test_security_unit_recipients_resolve_from_the_group` |
| §11.300(d) transaction safeguard | `test_attempt.test_lockout_after_configured_failures`, `test_below_threshold_does_not_lock_out`, `test_success_clears_the_lockout`, `test_wizard.test_lockout_blocks_further_attempts` |
| BR-4 immutability | `test_log_immutability` (8 tests), `test_install` ACL invariants |
| BR-9 transition blocking | `test_mixin.test_transition_is_blocked_without_signature`, `test_transition_is_allowed_once_signed`, `test_stale_signature_does_not_satisfy_a_policy`, `test_two_signature_policy_requires_two_distinct_signers` |
| BR-13 chain verification | `test_integrity_check` (4 tests), `test_log_chain.test_chain_verifies_end_to_end` |

Every requirement in Phase 1 §1.2 and every implemented paragraph in Phase 2
§2.3 has at least one automated test, except §11.50(b), which is manual (MT-1).

## 7.5 Coverage target

The Phase 7 brief sets a **95 % minimum**. Coverage cannot be measured without
executing the suite, so **no coverage figure is stated here.** Measure it with:

```bash
coverage run --source=addons/ls_electronic_signature \
  odoo-bin -c odoo.conf -d <db> -i ls_electronic_signature_test \
  --test-enable --test-tags ls_signature --stop-after-init
coverage report -m
coverage html
```

Lines expected to remain uncovered, with reasons, so that a shortfall can be
assessed rather than merely observed:

| Location | Reason |
|---|---|
| `ls_signature_log.init()` exception branch | Only reached on a database role without trigger privileges. |
| `ls_signature_session._current_token_hash` ImportError branch | Defensive; `odoo.http` is always importable in a running server. |
| `credentials._detect_mode` inspection failure branch | Requires a non-introspectable builtin as `_check_credentials`. |
| `_notify_security_unit` no-template branch | Requires the module's own data to be absent. |

If measured coverage falls below 95 %, the gap must be closed or justified
line by line before release.

## 7.6 Manual and environment tests

These cannot be automated in a headless test run and must be executed and
recorded during qualification.

| # | Test | Method | Acceptance |
|---|---|---|---|
| **OQ-CRED-001** | Password verification against the real `res.users` API | Sign with the correct password; sign with an incorrect one | Correct accepted; incorrect refused **as `invalid_password`, not `system_error`**. A `system_error` result means the credential API convention must be pinned in Settings. |
| **OQ-VIEW-001** | View element compatibility | Open the request form, the settings page and every list view | All render; no view-parse error in the log. Covers `<chatter/>`, `<list>`, and the settings `<app>`/`<block>`/`<setting>` elements. |
| **MT-1** | §11.50(b) manifestation in printed output | Print the signature certificate; print a report embedding the manifestation block | Printed name, date and time, and meaning are all legible on paper. |
| **MT-2** | §11.300(d) immediate notification end to end | Trigger an identity mismatch with a configured mail server | Alert e-mail arrives at the Security Unit; the attempt row exists even though the transaction was rolled back. |
| **MT-3** | Concurrency of the chain | Two simultaneous signatures in one company from two sessions | Both succeed; sequences contiguous; chain verifies. |
| **PT-1** | Performance at volume | 100 000 signature rows, then run chain verification | Verification completes within the maintenance window; record the time. |
| **PT-2** | Signing latency | Measure `action_sign` under normal load | Record the figure; no acceptance limit is asserted here because it depends on hardware not known to this document. |

## 7.7 Running the suite

```bash
odoo-bin -c odoo.conf -d <db> \
  -i ls_electronic_signature_test \
  --test-enable --test-tags ls_signature --stop-after-init
```

Note that `test_attempt` and the integration fixtures set
`ls_electronic_signature.attempt_isolated_cursor = 0`, so that attempt rows are
written on the test cursor and are visible inside the test transaction. **This
parameter must be `1` in production**, or a refused attempt will be rolled back
with its transaction and the §11.300(d) evidence lost. Verify it after any
restore from a validation database.

## Gate

**CONDITIONAL PASS.** A complete, traceable suite of 140 automated tests plus
7 manual and environment tests is delivered, and every implemented regulatory
requirement is traced to at least one test. Execution and coverage measurement
require the target environment and are outstanding. The gate cannot be closed
as an unconditional PASS on written-but-unexecuted tests.
