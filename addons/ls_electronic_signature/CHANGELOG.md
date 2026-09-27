# Changelog

All notable changes to `ls_electronic_signature`.
Format based on Keep a Changelog; versioning follows the OCA convention
`<odoo series>.<major>.<minor>.<patch>`.

## 19.0.1.1.0 — 2026-09-25

Remediation of the independent audit of 2026-09-25 (report AUDIT_REPORT_FINAL_2026-09-25.md; details in REMEDIATION_REPORT_2026-09-25.md at the project root).

- F-02: authorisation uses `res.users.all_group_ids` (the removed `groups_id` crashed the wizard; demo users use `group_ids`).
- F-11: the password is never stored: a non-stored field is verified on save and only the outcome is kept (restricted to Settings); migration 19.0.1.1.0 drops the old clear-text column.
- F-10: the signature chain tail is also read through a fresh cursor after the lock (concurrent signatures no longer collide).
- F-12: the immutability trigger is installed inside a savepoint instead of calling `cr.rollback()`; the DDL uses `odoo.tools.SQL` identifiers.
- The security unit alert reads `res.groups.all_user_ids` (`users` was removed in Odoo 19). Lockout ordering has an `id` tie-breaker.
- F-27: the signer role implies Internal User. F-23: `@api.ondelete` deletion guards.

## [19.0.1.0.0] — 2026-07-28

### Added
- Append-only signature log with per-company SHA-256 hash chain (21 CFR 11.70).
- Signature manifestation fields stored as snapshots: printed name, instant of
  signing, meaning (21 CFR 11.50(a)).
- Reusable QWeb manifestation block and standalone signature certificate PDF
  (21 CFR 11.50(b)).
- Signature meanings as configurable, group-restricted master data; seven
  supplied, covering the four examples named in §11.50(a)(3).
- Signature policies: manual and field-transition triggers, multi-signature with
  distinct signers, applicability domain, authorised signer groups.
- `ls.signature.mixin`, making any model signable.
- Signing wizard enforcing lockout, identity, components, password,
  authorisation and mandatory reason, in that order.
- Continuous-session tracking with configurable idle timeout
  (21 CFR 11.200(a)(1)(i) and (ii)).
- Attempt log written on an independent cursor so refused attempts survive
  transaction rollback; immediate notification to a Security Unit group;
  configurable lockout (21 CFR 11.300(d)).
- Chain verification, manual and scheduled daily, with stored dated results.
- Signature requests with expected signers, deadline, decline-with-reason, and
  automatic expiry.
- Four-layer immutability: ACL, ORM, PostgreSQL trigger, cryptographic chain.
- Five roles with escalating visibility and no write right over evidence.
- Companion test-fixture module `ls_electronic_signature_test` with a signable
  model and 89 integration tests.
- 140 automated tests in total; `static_check.py` for offline static analysis.
- Fourteen documents covering phases 1–10 and the manuals.

### Security
- `ls.signature.log.create` overwrites the signer identity and timestamp with
  server-side values for any non-elevated call, so a crafted RPC cannot
  attribute a signature to another person (architecture review finding AR-1).
- `user_id` uses `ondelete="restrict"`, preventing deletion of a signer and
  therefore recycling of an identification code (21 CFR 11.100(a)).
- The raw web session identifier is never stored; only a digest keyed with the
  database secret.
- Passwords are never written to any log, record or trace.
- A credential API fault is reported as `system_error` and never as a wrong
  password, so a system defect cannot masquerade as user error or drive a
  spurious lockout (AR-6).

### Fixed
- `is_current` is a non-stored compute whose cached value did not react to an
  edit of the signed record within the same transaction; a stale signature could
  therefore have satisfied a policy. The cache is now invalidated before every
  evaluation (AR-2).
- The signing session is registered before the signature row is inserted, so
  `session_id` is part of the insert. The earlier post-insert `UPDATE` would have
  been rejected by the module's own immutability trigger (AR-3).
- Policy model-signability is tested through an explicit `_ls_signature_enabled`
  marker instead of registry internals (AR-5).

### Known limitations
- The `res.users` password verification API is private and its Odoo 19.0
  signature could not be verified from official documentation. Isolated in
  `tools/credentials.py`; qualification test OQ-CRED-001 refers.
- `<chatter/>` and the settings `<app>`/`<block>`/`<setting>` elements could not
  be verified against 19.0 documentation. Qualification test OQ-VIEW-001 refers.
- The test suite was written but not executed; flake8 and pylint-odoo were not
  run. See `doc/07_test_report.md` and `doc/08_static_analysis.md`.
- No `.pot` translation template is shipped; the generation command is in
  `i18n/README.md`.
