# Changelog — `ls_audit_trail`

All notable changes to this module are recorded here. The format follows the
spirit of Keep a Changelog; versions follow the Odoo `19.0.x.y.z` convention.

## 19.0.1.0.1 — 2026-09-25

Remediation of the independent audit of 2026-09-25 (report AUDIT_REPORT_FINAL_2026-09-25.md; details in REMEDIATION_REPORT_2026-09-25.md at the project root).

- F-09: the audit rule applied to a record is the rule of the company that owns the record, not of the active company; mixed recordsets are split by company.
- F-10: the chain tail is also read through a fresh cursor after the chain lock, so concurrent sealers no longer collide on the chain position (REPEATABLE READ).
- F-38: one rule per model and company, including rules without company (`UNIQUE NULLS NOT DISTINCT`, PostgreSQL 15 or later).
- F-27: the viewer role implies Internal User. F-23: `@api.ondelete` deletion guards.
- Tests ported (F-40): valid PNG fixture, entries aged with `freezegun` instead of SQL, tampering through the database column.

## [19.0.1.0.0] — 2026-07-30

### Added
- Initial release.
- Per-company, per-model, per-field audit rules (`ls.audit_trail.rule`) with a
  documented justification field and an all-fields-except-excluded mode.
- Automatic capture of create, write and delete via an extension of the
  abstract `base` model, with a registry-cached configuration lookup that
  issues no query for unaudited models.
- Immutable audit entries (`ls.audit_trail.log`) and field-change lines
  (`ls.audit_trail.log.line`), with a per-company SHA-256 hash chain sealed
  under a PostgreSQL transaction advisory lock.
- Deterministic canonical-JSON serialisation and dual technical/display value
  representation, with binary values fingerprinted rather than copied.
- On-demand and scheduled integrity verification, recorded in an immutable
  verification model (`ls.audit_trail.verification`), including head-of-chain
  reconciliation against retention anchors.
- Sealed evidence packs (`ls.audit_trail.evidence_pack`) producing a ZIP of
  JSON, CSV and a digest manifest, with an archive self-check and a PDF cover
  sheet.
- Controlled retention run wizard that removes aged entries only under explicit
  preconditions and replaces the removed range with a tamper-evident anchor.
- Three-tier security model (Viewer, Auditor, Administrator) with ORM-level
  segregation of duties and global multi-company record rules.
- Company-level retention configuration on `res.company`.
- QWeb PDF reports for evidence packs and verifications.
- Ninety-seven automated tests across eleven modules.
- Offline static checker with cross-reference validation and negative controls.

### Known limitations
- Not executed against a live Odoo 19 instance in the build environment;
  delivered as CONDITIONAL PASS pending the receiving team's IQ/OQ/PQ.
- No electronic-signature functionality (separate concern).
- ANPP/BPF-specific requirements not claimed; official sources unavailable.
