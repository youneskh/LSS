# Changelog

All notable changes to `ls_document_management`.
Format based on Keep a Changelog; versioning follows Odoo `MAJOR.x.y.z`.

## 19.0.1.0.1 — 2026-09-25

Remediation of the independent audit of 2026-09-25 (report AUDIT_REPORT_FINAL_2026-09-25.md; details in REMEDIATION_REPORT_2026-09-25.md at the project root).

- F-14: folder access rules use `user.all_group_ids`, so groups obtained through an implied group grant access.
- F-24: `_check_company_auto` on documents and folders. F-39: re-submission after a rejection no longer violates the pending-approval index (state changes flushed before the new approvals).
- F-44: demo data loaded with `noupdate="1"`. F-27: the viewer role implies Internal User. F-23: `@api.ondelete` deletion guards.
- Tests ported (F-40): recursion error type, form record comparison.

## [19.0.1.0.0] - 2026-07

### Added
- Initial release for Odoo 19 Community.
- Hierarchical document folders with computed full path and cycle protection.
- Folder-level read/write access control enforced by record rules.
- Controlled document master with lifecycle Draft, Under Review, Approved,
  Published, Archived, and a revision loop preserving the effective version.
- Immutable document versions with mandatory change summary, author, file size
  and SHA-256 checksum; post-hoc integrity verification.
- Parallel approval routing with segregation of authoring and approval roles;
  approver identity enforced server-side.
- Retention policies with configurable duration, trigger and end-of-life action
  (notify or archive); daily retention scheduled action; legal hold.
- Links from a document to any Odoo record.
- Tags.
- Document Control Record QWeb PDF report (version and approval history with
  checksums).
- Four security roles (Viewer, Editor, Approver, Manager), model access rights
  and multi-company record rules.
- Chatter (messages and activities) on documents.
- Two wizards: new version, and reject-with-reason.
- Demo data.
- Test suite (101 methods) and a static self-check harness.

### Known limitations
- Tests written but not executed in the build environment (no Odoo runtime).
- No cryptographic electronic signature (see `ls_electronic_signature`).
- No field-level cross-model audit trail (see `ls_audit_trail`).
- No full-text search of file content.
- No automated destruction of records at end of retention (by design).
