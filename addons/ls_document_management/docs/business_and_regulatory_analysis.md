# Business and Regulatory Analysis

Module: `ls_document_management` — Life Sciences Suite, Odoo 19 Community.

This document covers Phase 1 (Business Analysis) and Phase 2 (Regulatory
Analysis) of the development framework.

---

## Part 1 — Business Analysis

### 1.1 Business objectives

- Provide a controlled document management capability on Odoo 19 Community,
  which does not include the Enterprise Documents application.
- Enforce a formal document lifecycle with review, approval and versioning
  suitable for regulated Life Sciences operations.
- Preserve the integrity and traceability of controlled documents (who did
  what, when, and to which version).
- Support retention management without ever performing unattended destruction
  of records.

### 1.2 Business requirements

| Ref | Requirement |
|-----|-------------|
| BR-01 | Documents are organised in a folder hierarchy of arbitrary depth. |
| BR-02 | Access to documents can be restricted per folder to defined groups. |
| BR-03 | Each document carries a complete, ordered version history. |
| BR-04 | Once created, a version's controlled content cannot be altered. |
| BR-05 | The integrity of a stored file can be verified after the fact. |
| BR-06 | A document follows Draft, Under Review, Approved, Published, Archived. |
| BR-07 | Publication requires the approval of every designated approver. |
| BR-08 | Authoring and approval are performed by segregated roles. |
| BR-09 | A published document can be revised without losing the version in force. |
| BR-10 | Retention periods are configurable and monitored automatically. |
| BR-11 | No automated process deletes controlled records. |
| BR-12 | A document can be linked to any other business record. |
| BR-13 | A control record (versions and approvals) can be produced as a PDF. |
| BR-14 | All changes to a document are traceable (message and activity log). |

### 1.3 Stakeholders

- **Quality Assurance** — owns the document control process and the SOP set.
- **Document authors** — draft and revise documents.
- **Approvers / subject-matter experts** — review and approve documents.
- **Document controllers / QA managers** — publish, archive, configure.
- **Auditors and inspectors** — consult history and control records.
- **System administrators** — install, configure roles, maintain the system.

### 1.4 User roles

Viewer, Editor, Approver, Manager. See the README for the capability matrix.
The design keeps Approver separate from Editor so that a person cannot both
author and approve the same document by virtue of a single role.

### 1.5 User stories

- As an **author**, I create a document in a folder, upload a file, describe
  the change, and submit it for review, so that it can be approved.
- As an **author**, I revise a published document, upload a new version, and
  resubmit it, while users keep access to the version currently in force.
- As an **approver**, I see the documents awaiting my decision, review the
  file, and approve or reject with a comment.
- As a **QA manager**, I publish an approved document so that it becomes the
  effective version, and I archive a document that is no longer in use.
- As a **QA manager**, I configure a retention policy and attach it to a
  folder so that documents inherit it.
- As an **auditor**, I open a document, read its full version and approval
  history, verify a file's checksum, and print the control record.
- As an **administrator**, I restrict a folder to a group so that only
  authorised users can read its documents.

### 1.6 Use cases

1. Create and issue a new controlled document.
2. Revise a published document (new version through the revision loop).
3. Reject a document under review with a reason and return it to draft.
4. Restrict and grant folder-level access.
5. Evaluate retention and act at end of retention (notify or archive).
6. Place and observe a legal hold.
7. Link a document to another record and navigate to it.
8. Produce a Document Control Record PDF.
9. Verify the integrity of a stored version.

### 1.7 Functional scope (in scope)

- Folder hierarchy with computed path and access groups.
- Document lifecycle state machine and revision loop.
- Immutable versioning with SHA-256 checksum and integrity verification.
- Parallel approval routing with segregation of authoring and approval.
- Retention policies and a daily retention scheduled action.
- Legal hold.
- Links to arbitrary Odoo records.
- Document Control Record PDF.
- Multi-company isolation.
- Message and activity history (chatter).
- Four security roles, model access rights and record rules.

### 1.8 Out of scope

The following are deliberately **not** implemented and must not be assumed:

- **Cryptographic electronic signatures** in the sense of FDA 21 CFR Part 11
  subpart C. The approval records who decided and when; they are not a
  compliant electronic signature. Signatures belong to the separate
  `ls_electronic_signature` module of the suite.
- **A cross-model, database-wide audit trail** with field-level before/after
  values. This module relies on Odoo's per-record message log (chatter). A
  dedicated audit trail belongs to the separate `ls_audit_trail` module.
- **Full-text search of file content.** Search covers metadata (number, title,
  description, tags, folder), not the text inside the stored files.
- **Automated destruction of records** at end of retention. By design, no path
  deletes a controlled record automatically.
- **Online document editing / co-authoring / rendering.** Files are stored and
  downloaded as uploaded.
- **Periodic-review scheduling** (next-review-date reminders). Not implemented
  in this version.

### 1.9 Risks

| Risk | Mitigation in this module |
|------|---------------------------|
| A user bypasses folder restrictions via RPC | Access enforced by record rules, not only the UI. |
| An approver's decision is forged by another user | Identity checked in `write`, not only in the action button. |
| A version's content is silently altered in the database | SHA-256 checksum stored at creation; `verify_integrity()` detects mismatch. |
| Unattended process destroys records | No deletion path in the scheduled action; end-of-life actions limited to notify/archive. |
| Author approves their own document | Approver role does not imply Editor; roles are separable. |
| Code fails to install on Odoo 19 | Built against verified Odoo 19 APIs; see validation report for the residual, runtime-only risks. |

### 1.10 Success criteria

- The module installs on a clean Odoo 19 Community instance.
- The lifecycle, versioning, approval, retention and access-control behaviours
  operate as described and pass the provided test suite.
- No controlled record can be deleted by an automated process.
- Static self-check passes with no blocking issue.

**Phase 1 result: PASS** (analysis complete; residual runtime verification is
tracked in the validation report).

---

## Part 2 — Regulatory Analysis

### 2.1 Approach

This section identifies frameworks whose **document-control** expectations are
relevant to this module and describes **how the module supports** their
implementation. It makes **no claim of compliance or certification**. Where a
framework requires capabilities outside this module's scope, that is stated
explicitly.

### 2.2 Applicable frameworks and how the module supports them

| Framework | Relevant expectation (document control) | How this module supports it | Not covered here |
|-----------|------------------------------------------|------------------------------|------------------|
| ISO 9001:2015, cl. 7.5 | Control of documented information: approval, review, version, access, retention. | Lifecycle with approval; immutable versions; folder access groups; retention policies. | Organisational procedure and its execution. |
| ISO 13485:2016, cl. 4.2.4 / 4.2.5 | Document control and control of records; identify changes and current revision status; prevent unintended use of obsolete documents. | Version numbering, effective-version tracking, superseding of prior versions, archiving. | Signature meaning; SOPs; validation. |
| EU GMP Annex 11 | Data integrity, access control, audit trail, retention for computerised systems. | Access control by record rules; SHA-256 integrity check; chatter change log; retention monitoring. | System validation; a dedicated field-level audit trail (`ls_audit_trail`). |
| FDA 21 CFR Part 11 | Electronic records: access limitation, record protection and retention. | Role-based access; immutable versions with checksum; retention without deletion. | **Electronic signatures (subpart C) are NOT provided here** — see `ls_electronic_signature`. |
| WHO GMP; EU GMP Chapter 4 | Documentation lifecycle and retention. | Lifecycle, versioning, retention. | Organisational documentation system. |

### 2.3 Data integrity (ALCOA+) support and limits

| Principle | How the module supports it | Limit |
|-----------|-----------------------------|-------|
| Attributable | Author on each version; approver on each decision; chatter records the user. | Depends on correct user account management. |
| Legible | Structured records and PDF control record. | — |
| Contemporaneous | Creation and decision timestamps set by the system. | Relies on server time. |
| Original | Versions are immutable; content cannot be rewritten. | — |
| Accurate | SHA-256 checksum and `verify_integrity()`. | Detects alteration; does not prevent a DBA with direct SQL access from also rewriting the stored checksum — a full audit trail and database controls are external. |
| Complete | Full version and approval history retained. | — |
| Consistent | Enforced state machine and constraints. | — |
| Enduring | Retention never deletes; archived records persist. | — |
| Available | Records remain queryable and printable. | — |

### 2.4 Explicit non-claims

- The module is **not certified** against any standard.
- The approval feature is **not** a 21 CFR Part 11 electronic signature.
- Installing this module does **not** validate the system; computer system
  validation remains the organisation's responsibility.
- This analysis is an architectural mapping, not legal or regulatory advice.

**Phase 2 result: PASS** (applicable expectations mapped; non-claims stated).
