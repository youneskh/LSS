# Phase 1 — Business Analysis

Module: `ls_supplier_qualification` · Odoo 19 Community Edition
Status at end of phase: **PASS**

---

## 1.1 Business objectives

| # | Objective |
|---|-----------|
| BO-01 | Hold, in one system of record, the evidence that a supplier was evaluated before being used. |
| BO-02 | Make the approval decision explicit: who decided, when, on what basis, for which materials, and until when. |
| BO-03 | Make an approval expire by itself, so that an unnoticed lapse is impossible. |
| BO-04 | Detect an unapproved or out-of-scope supplier at the moment a purchase order is confirmed, not afterwards. |
| BO-05 | Follow audit findings to closure and prevent an audit from being closed while a finding is open. |
| BO-06 | Measure supplier performance on a repeatable, documented formula. |
| BO-07 | Force a periodic re-decision instead of letting an approval drift. |
| BO-08 | Produce, on demand, a printable dossier an auditor or inspector can read without access to Odoo. |

## 1.2 Business requirements

| # | Requirement | Objective |
|---|-------------|-----------|
| BR-01 | One live qualification dossier per supplier per company. | BO-01 |
| BR-02 | The approval scope is an explicit list of materials or services; a dossier without a qualified scope line cannot be approved. | BO-02 |
| BR-03 | Approval prerequisites are derived from the supplier category, not hard-coded. | BO-01 |
| BR-04 | An assessment produces a numeric, weighted, reproducible result. | BO-01 |
| BR-05 | The scoring rules in force at the moment of an assessment are frozen on it. | BO-02 |
| BR-06 | A mandatory criterion scored below the minimum forces a Fail result regardless of the total. | BO-01 |
| BR-07 | An open critical audit finding blocks submission for approval. | BO-05 |
| BR-08 | The approver may not be an assessor or a lead auditor of the same dossier, unless the company disables the rule. | BO-02 |
| BR-09 | Every approval, suspension, reinstatement and disqualification is recorded in an append-only log with the stated meaning and a justification. | BO-02 |
| BR-10 | The end of validity is computed from a category interval and can be overridden by the approver. | BO-03 |
| BR-11 | A daily job moves elapsed approvals to Expired and warns before expiry. | BO-03 |
| BR-12 | Purchase order confirmation is checked against the supplier status, at a level chosen per company: no control, warning, or block. | BO-04 |
| BR-13 | An audit cannot be closed while a finding is open; critical and major findings require a documented corrective action. | BO-05 |
| BR-14 | Performance combines four indicators with company-level weights, frozen on each evaluation. | BO-06 |
| BR-15 | A periodic review consolidates the evidence of a period and writes its decision onto the dossier. | BO-07 |
| BR-16 | Three PDF reports: qualification dossier, assessment, audit. | BO-08 |

## 1.3 Stakeholders

| Stakeholder | Interest in the module |
|-------------|------------------------|
| Quality Assurance | Owns the process, approves, suspends, disqualifies, decides at review. |
| Quality Control / Laboratory | Supplies rejection and non-conformity figures used by the scorecard. |
| Supplier Auditors | Plan and conduct audits, raise and verify findings. |
| Procurement | Buys only from approved suppliers within the qualified scope. |
| Warehouse / Receiving | Sees the consequences of a blocked or warned purchase order. |
| Regulatory Affairs | Uses the dossier report as evidence during inspections. |
| IT / Validation | Installs, configures, validates and maintains the module. |
| Executive Management | Reads the risk and performance indicators. |

## 1.4 User roles

| Role | Group | Can |
|------|-------|-----|
| Supplier Viewer | `group_ls_supplier_viewer` | Read every qualification record. |
| Supplier Assessor | `group_ls_supplier_assessor` | Open dossiers, conduct assessments and audits, record performance. Cannot approve, cannot delete, cannot configure. |
| Supplier Manager | `group_ls_supplier_manager` | Everything, including configuration, approval, status changes and review decisions. |

Segregation of duties is not expressed as a fourth group. It is enforced by a
rule that compares the approver with the people who produced the evidence, so
that a small organisation can still operate with two people while a large one
keeps a full separation. See §1.8, risk R-03.

## 1.5 User stories

| # | Story |
|---|-------|
| US-01 | As a **QA officer**, I register a new supplier so that the evaluation has a home before any purchase is made. |
| US-02 | As an **assessor**, I load a questionnaire and score it with evidence so that the evaluation is reproducible. |
| US-03 | As an **assessor**, I must justify in writing any criterion scored below the minimum so that a low score is never silent. |
| US-04 | As a **second assessor**, I review a completed assessment so that no evaluation is self-certified. |
| US-05 | As a **lead auditor**, I plan an audit, record findings, issue a report and set a response deadline. |
| US-06 | As a **lead auditor**, I follow each finding through response, agreed action, implementation, verification and closure. |
| US-07 | As a **QA manager**, I see why a dossier is not ready for approval before I open the approval dialog. |
| US-08 | As a **QA manager**, I approve a supplier for a defined scope and a defined period, and I sign that decision. |
| US-09 | As a **QA manager**, I approve with conditions when the evidence is acceptable but incomplete. |
| US-10 | As a **QA manager**, I suspend a supplier immediately when a serious issue appears. |
| US-11 | As a **buyer**, I am stopped or warned when I confirm an order for a supplier that is not approved. |
| US-12 | As a **QA officer**, I record a quarterly scorecard and the system rates the supplier for me. |
| US-13 | As a **QA manager**, I run the annual review, see the collected evidence and record a decision that updates the dossier. |
| US-14 | As a **responsible**, I receive a reminder before an approval expires so that requalification starts in time. |
| US-15 | As a **regulatory affairs officer**, I print the full dossier for an inspection. |
| US-16 | As an **administrator**, I verify that the signature log has not been altered. |

## 1.6 Use cases

| # | Use case | Actor | Main flow | Exceptions |
|---|----------|-------|-----------|------------|
| UC-01 | Register supplier | Assessor | Create dossier, pick category, start assessment. | A live dossier already exists for that supplier. |
| UC-02 | Conduct assessment | Assessor | Create, load template, start, score, conclude, complete. | No criteria loaded; low score without comment; no conclusion. |
| UC-03 | Review assessment | Second assessor | Open completed assessment, review. | The reviewer is the assessor and the rule is enabled. |
| UC-04 | Define scope | Assessor | Add scope lines, qualify them. | Qualified line without a date; duplicate product. |
| UC-05 | Conduct audit | Lead auditor | Plan, start, draft report, set outcome, issue report. | Outcome or conclusion missing; critical finding with an Acceptable outcome. |
| UC-06 | Close finding | Lead auditor | Response, agree action, implement, verify, close. | Missing response, action, due date or verification method. |
| UC-07 | Submit for approval | Assessor | Submit; the system re-checks the prerequisites. | Any prerequisite unmet. |
| UC-08 | Approve | Manager | Open wizard, pick decision, set validity, justify, confirm login. | Wrong login; past expiry date; segregation-of-duties conflict. |
| UC-09 | Change status | Manager | Open wizard, suspend, reinstate or disqualify with a reason. | Reinstating an expired approval. |
| UC-10 | Confirm purchase order | Buyer | Confirm the order. | Supplier not approved, expired, or product outside scope. |
| UC-11 | Record performance | Assessor | Enter counters, confirm; score and rating computed. | Overlapping confirmed periods; inconsistent counters. |
| UC-12 | Periodic review | Manager | Collect evidence, decide, complete. | Conditional decision without conditions; adverse decision without justification. |
| UC-13 | Expiry handling | System | Daily job expires and warns. | None. |
| UC-14 | Print dossier | Regulatory affairs | Print the PDF. | None. |

## 1.7 Functional scope

**In scope**

1. Supplier categories with their own qualification rules.
2. Criterion library and weighted questionnaire templates.
3. Qualification dossier with a nine-state lifecycle.
4. Explicit qualified scope of materials and services, with its own validity.
5. Assessments with frozen scoring rules, weighted scoring and mandatory-criterion logic.
6. Audits with findings, severities, response deadlines and a closure workflow.
7. Performance scorecards with four weighted indicators and an A–D rating.
8. Periodic reviews that write their decision onto the dossier.
9. Append-only signature log with a SHA-256 chain and a verification action.
10. Three scheduled actions: expiry, audit and review due dates, scope validity.
11. Purchase order control at three levels, with an optional scope check.
12. Three QWeb PDF reports.
13. Three security groups, model access rights and record rules, including multi-company rules.
14. Company-level configuration exposed in the settings screen.

**Out of scope** (and the reason)

| Item | Reason |
|------|--------|
| CAPA management | Belongs to `ls_capa`. This module records audit findings and their corrective actions inside the audit; it does not implement a general CAPA lifecycle. |
| General document management with versioning | Belongs to `ls_document_management`. Evidence is attached through the standard Odoo attachment mechanism. |
| Electronic signature with re-authentication | Belongs to `ls_electronic_signature`. See Phase 2, §2.4. |
| General audit trail on every model and field | Belongs to `ls_audit_trail`. This module logs decisions, not every field change. |
| Internal audits | This module audits suppliers. Internal audits belong to `ls_audit`. |
| Supplier portal | Suppliers do not log in; the audit report is sent by e-mail. |
| Automatic import of complaint and non-conformity counts | No source module exists yet; the counters are entered manually. |
| Automatic delivery counters without `purchase_stock` | The link between stock moves and purchase order lines lives in a module this one does not depend on. The button refuses to guess and states the missing dependency. |

## 1.8 Risks

| # | Risk | Impact | Mitigation implemented |
|---|------|--------|------------------------|
| R-01 | An approval lapses without anyone noticing. | Purchases from an unqualified supplier. | Daily expiry job, reminder activities, e-mail template, dedicated "Expiring Approvals" menu. |
| R-02 | The signature log is altered in the database. | Loss of evidential value. | Append-only ORM guard plus SHA-256 chain and a verification action that detects direct SQL edits. |
| R-03 | One person both produces and approves the evidence. | Weak decision. | Segregation-of-duties rule on approval and on assessment review, switchable per company and recorded in the log. |
| R-04 | Changing a questionnaire retroactively changes past results. | Loss of traceability. | Scale, thresholds and minimum mandatory score are copied onto each assessment at creation. |
| R-05 | Blocking purchase orders paralyses procurement at go-live. | Business disruption. | Default control level is "warn"; blocking is opt-in per company. |
| R-06 | Performance figures are entered inconsistently. | Meaningless ratings. | Counters drive the indicators, constraints reject impossible values, and weights are frozen on the record. |
| R-07 | The module is mistaken for a compliance certificate. | Regulatory exposure. | Explicit wording in the manifest, in the dossier report footer and in Phase 2. |
| R-08 | Two companies share one supplier status. | Data leakage between companies. | Partner-level status fields are deliberately not stored; global multi-company record rules on every model. |

## 1.9 Success criteria

| # | Criterion | How it is demonstrated |
|---|-----------|------------------------|
| SC-01 | The module installs and uninstalls on a clean Odoo 19 Community database. | Installation test, Phase 10. |
| SC-02 | No dossier can reach Approved without an assessment, a qualified scope and no open critical finding. | `test_qualification_workflow`, `test_constraints`. |
| SC-03 | Every approval produces exactly one chained signature entry. | `test_signature`, `test_qualification_workflow`. |
| SC-04 | A tampered log entry is detected. | `test_signature.test_chain_verification_detects_tampering`. |
| SC-05 | The three purchase control levels behave as specified. | `test_purchase_control`. |
| SC-06 | Each group is limited to its intended operations. | `test_security`. |
| SC-07 | The three reports render. | `test_reports`. |
| SC-08 | The offline static check reports no finding. | Phase 8. |

---

**Phase 1 gate: PASS.** No open issue. Phase 2 may start.
