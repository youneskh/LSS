# 01 — Business Analysis

Phase 1 deliverable. Status: **PASS**.

## 1. Business objectives

| Identifier | Objective |
|---|---|
| BO-01 | Hold every quality document in one controlled repository whose current revision is unambiguous |
| BO-02 | Guarantee that no document reaches the shop floor without review and approval by a person other than its author |
| BO-03 | Make the periodic review of documents an automatic prompt instead of a manual watch |
| BO-04 | Express quality objectives as measurable series and compute their achievement from recorded measurements |
| BO-05 | Retain quality records for a defined period and prevent their silent alteration or premature destruction |
| BO-06 | Produce, on demand, a printable document carrying its own control block for an audit or an inspection |

## 2. Stakeholders

| Stakeholder | Interest in the system |
|---|---|
| Quality Assurance manager | Owns the QMS, withdraws documents, disposes of records past retention |
| Quality Assurance officer | Drafts and revises documents, records measurements and quality records |
| Head of department | Approves documents applicable to their department |
| Production and laboratory operator | Consults the applicable published revision |
| Internal auditor | Reads the history, the revision chain and the review status |
| External auditor or inspector | Receives printed documents carrying a control block |
| System administrator | Configures parameters, groups and scheduled actions |

## 3. User roles

Four roles are implemented as Odoo groups: **Viewer**, **User**, **Approver**,
**Manager**. Their privileges are tabulated in the README, section 3.

## 4. User stories

| Identifier | As | I want | So that | Implemented by |
|---|---|---|---|---|
| US-01 | QA officer | to draft a procedure and submit it for review | it is checked before use | `action_submit_for_review` |
| US-02 | Approver | to approve a document I did not write | segregation of duties is respected | `action_approve` |
| US-03 | Approver | to reject a document with a written reason | the author knows what to correct | `ls.qms.reject.wizard` |
| US-04 | Approver | to publish a document with an effective date | its entry into force is dated | `action_publish` |
| US-05 | QA officer | to open a new revision giving a reason for change | the change history is legible | `ls.qms.new.revision.wizard` |
| US-06 | Operator | to see only published documents | I never apply a draft | record rules |
| US-07 | QA manager | to be prompted before a document reaches its review date | the review is not missed | `_cron_document_review_reminder` |
| US-08 | QA manager | to withdraw a document | it stops being applicable | `action_set_obsolete` |
| US-09 | QA manager | to define an objective with a baseline and a target | progress is measurable | `ls.qms.objective` |
| US-10 | QA officer | to record a dated measurement | achievement is computed and not estimated | `ls.qms.objective.measurement` |
| US-11 | QA manager | to be prompted for an objective that is late | corrective action is taken in time | `_cron_objective_monitoring` |
| US-12 | QA officer | to record evidence of a management review | it can be produced at an audit | `ls.qms.quality_record` |
| US-13 | QA officer | to be prevented from editing confirmed evidence | its integrity is preserved | `write` guard |
| US-14 | QA manager | to correct a confirmed record, with a trace | a genuine error is correctable | `write` guard, manager path |
| US-15 | QA manager | to dispose of a record only after its retention | destruction is controlled | `action_dispose` |
| US-16 | Auditor | to print a document with its control block | the printed copy is identifiable | three PDF reports |

## 5. Functional scope

In scope: quality policy, procedures, work instructions, quality plans,
quality objectives with their measurements, quality records, revision control,
approval workflow, periodic review, retention control, three printable
documents, four security roles, three scheduled actions.

## 6. Out of scope

The following are outside this module. Each is stated so that no reader
assumes a capability that does not exist.

| Excluded | Reason |
|---|---|
| Authenticated electronic signature | Delegated to `ls_electronic_signature`; extension point provided |
| Field level audit trail with hash chain | Delegated to `ls_audit_trail` |
| Corrective and preventive actions | Delegated to `ls_capa` |
| Internal and supplier audits | Delegated to `ls_audit` |
| Deviations | Delegated to `ls_deviation` |
| Change control | Delegated to `ls_change_control` |
| Training records and training matrix | Delegated to `ls_training` |
| Hierarchical folders and full text document search | Delegated to `ls_document_management` |
| Distribution and acknowledgement of read receipts | Not specified in section 7.2 of the Functional Specification |
| Import of legacy documents | Not specified |
| Electronic batch records | Delegated to `ls_pharma` |

## 7. Risks

| Identifier | Risk | Treatment applied |
|---|---|---|
| R-01 | A user applies a superseded revision | Viewers see published revisions only; the previous revision becomes obsolete automatically on publication |
| R-02 | Self approval of a document | Blocked by default, controlled by a system parameter |
| R-03 | Silent modification of published content | Content fields are frozen by the `write` guard |
| R-04 | Loss of evidence by deletion | Deletion restricted to drafts; disposal restricted to the manager after retention |
| R-05 | Missed periodic review | Daily scheduled action creating one activity per document, without duplication |
| R-06 | The module is taken as proof of compliance | Stated in the README, in `02_regulatory_analysis.md` and in `13_validation_report.md` |
| R-07 | Approval without an authenticated signature | Documented as out of scope, with an extension point |

## 8. Success criteria

| Identifier | Criterion | Verification |
|---|---|---|
| SC-01 | The module installs on Odoo 19 Community with no error | To be executed by the operating organisation |
| SC-02 | Every transition rule of section 2 of the README is enforced | `tests/test_document_lifecycle.py` |
| SC-03 | A viewer cannot read a draft | `tests/test_security.py` |
| SC-04 | Achievement is computed by the documented formulas | `tests/test_objective.py` |
| SC-05 | Confirmed evidence is protected from a QMS user | `tests/test_quality_record.py` |
| SC-06 | The three scheduled actions are idempotent | `tests/test_cron.py` |
