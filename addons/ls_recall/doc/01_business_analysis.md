# Phase 1 — Business Analysis

Module: `ls_recall` — Recall and Field Action Management
Platform: Odoo 19 Community Edition

---

## 1. Business objectives

| # | Objective |
|---|-----------|
| B1 | Make it possible to start a field action within a defined target time of the decision, at any hour, using a pre-approved arrangement. |
| B2 | Determine, from records already in the ERP, exactly which consignees received which affected lots and in what quantity. |
| B3 | Produce and control the communications issued to consignees and authorities, and retain them as evidence. |
| B4 | Verify that consignees acted on the notice, on a defined sample of them, and record what each said. |
| B5 | Reconcile the quantity distributed against the quantity returned, destroyed or confirmed unrecoverable. |
| B6 | Prevent a field action from being recorded as complete while the evidence for completeness is absent. |
| B7 | Retain a durable, attributable account of the whole action for inspection. |
| B8 | Rehearse the arrangement periodically and record the rehearsal separately from real actions. |

## 2. Business requirements

| # | Requirement | Objective |
|---|-------------|-----------|
| R1 | A recall plan is a versioned document with review, approval and revision. | B1 |
| R2 | An approved plan names a coordinator and a deputy, so cover exists outside office hours. | B1 |
| R3 | A field action can be opened in a single screen carrying the plan defaults. | B1 |
| R4 | Distribution is derived from completed stock movements for the affected lots, not retyped. | B2 |
| R5 | Re-running the trace never overwrites quantities a user has entered. | B2, B5 |
| R6 | Consignees distributed outside the ERP can be added manually. | B2 |
| R7 | A notice cannot be issued until its content has been confirmed against a defined list of elements. | B3 |
| R8 | An issued notice can no longer be reworded or deleted. | B3, B7 |
| R9 | The number of consignees to contact is derived from a declared sampling level. | B4 |
| R10 | A contact that fails can be escalated, and the further attempt is recorded. | B4 |
| R11 | The system computes distributed, returned, destroyed, unrecoverable, accounted and outstanding quantities. | B5 |
| R12 | A line where more is accounted for than was shipped is flagged as a discrepancy. | B5 |
| R13 | Each forward state transition asserts that the evidence for the next phase exists. | B6 |
| R14 | Closure evaluates a set of checks and shows all results at once. | B6 |
| R15 | A failed check can be overridden only by a manager and only with a written justification. | B6 |
| R16 | A closed or cancelled action is read-only. | B7 |
| R17 | Reports freeze the figures they state at the moment of approval. | B7 |
| R18 | An abandoned action is cancelled with a reason, never deleted. | B7 |
| R19 | A rehearsal is recorded as such and excluded from regulatory metrics. | B8 |
| R20 | The system raises a reminder when a rehearsal falls due. | B8 |

## 3. Stakeholders

| Stakeholder | Interest |
|-------------|----------|
| Quality unit / Qualified Person | Owns the decision to act and the decision to close. |
| Recall coordinator | Runs the action day to day. |
| Warehouse and distribution | Must not ship an affected lot; handles returns. |
| Regulatory affairs | Notifies authorities; submits status and final reports. |
| Customer service | Receives consignee responses. |
| Senior management | Accountable for the outcome; needs status at a glance. |
| Inspectors and auditors | Read the record after the fact; need it complete and attributable. |

## 4. User roles

| Role | Group | Rights |
|------|-------|--------|
| Viewer | `group_ls_recall_viewer` | Read everything. Change nothing. |
| Coordinator | `group_ls_recall_coordinator` | Create and run actions, trace, communicate, check, draft reports. No plan authoring, no deletion, no override. |
| Manager | `group_ls_recall_manager` | All of the above, plus plan approval, report approval, deletion, and closure override. |

The roles imply one another: manager implies coordinator implies viewer.

## 5. User stories

| # | As a | I want to | So that |
|---|------|-----------|---------|
| U1 | quality manager | approve a recall plan naming a deputy | someone can act at 02:00 on a Sunday |
| U2 | coordinator | open a recall from the plan in one screen | no time is lost retyping the strategy |
| U3 | coordinator | see every consignee of the affected lots | I know who to contact |
| U4 | coordinator | be stopped from issuing a notice missing a required element | the notice is usable by the recipient |
| U5 | coordinator | record what each consignee replied | reconciliation is based on statements, not assumptions |
| U6 | coordinator | escalate a consignee I cannot reach | the attempts are visible |
| U7 | regulatory affairs | record that the authority was notified and when | the file shows it |
| U8 | quality manager | see why a recall may not be closed | I can act on the gap instead of guessing |
| U9 | quality manager | close with a justification when a check cannot be met | the exception is documented rather than hidden |
| U10 | auditor | read a closed recall and see who did what and when | the record stands on its own |
| U11 | warehouse operator | be warned that a lot is under recall | I do not ship it |
| U12 | quality manager | be reminded when a rehearsal is due | the arrangement stays proven |

## 6. Use cases

**UC1 — Approve a recall plan.** Manager drafts, submits, approves. System refuses approval without a documented procedure and a named deputy.

**UC2 — Open and initiate a field action.** Coordinator opens the wizard, selects product and lots, states the reason, and initiates. System refuses initiation of a real action without a hazard evaluation, a classification and a depth.

**UC3 — Trace distribution.** System scans completed movements of the affected lots to customer locations and builds one line per consignee and lot. Quantities that cannot be attributed to a consignee are reported in the chatter for manual handling.

**UC4 — Issue a recall notice.** Coordinator drafts, confirms the content elements, approves, records as sent. System marks the recipients' lines as notified and stamps the first-communication metrics.

**UC5 — Notify the authority.** Same flow with the authority notification type; the recall header records the fact and the date.

**UC6 — Perform effectiveness checks.** System plans one check per consignee. Coordinator records the outcome of each contact. An unreachable consignee is escalated and a further attempt is planned.

**UC7 — Reconcile.** Coordinator enters returned, destroyed and unrecoverable quantities per line. System computes the rates and flags discrepancies.

**UC8 — Report.** Coordinator drafts a status or final report; a second person reviews; a manager approves, which freezes the figures; submission is recorded against named recipients.

**UC9 — Close.** Manager opens the closure wizard, reads the check results, and either resolves the gaps or overrides them with a justification.

**UC10 — Cancel.** A decision that is reversed is cancelled with a reason. The record remains.

**UC11 — Rehearse.** A mock recall runs the same flow, is flagged as a rehearsal, is excluded from metrics, and resets the plan's next-due date on closure.

## 7. Functional scope

In scope: recall plans; field actions of five types; distribution tracing from stock; consignee reconciliation; communications with content control; effectiveness checks with sampling levels; status and final reports with frozen figures; closure gating; cancellation; scheduled monitoring; role-based access; multi-company isolation; two printable documents.

## 8. Out of scope

The following are deliberately excluded, each for a stated reason.

| Item | Reason |
|------|--------|
| Sending e-mail to consignees from the module | The module records what was issued. Making it also the sending channel would mean an outage in the mail queue becomes a gap in the regulatory record. Issue by the organisation's normal channel and record it here. |
| Automatic stock quarantine of affected lots | Moving stock to quarantine is a warehouse decision with operational consequences, so the module does not move goods. Since the 2026-09-25 remediation (audit F-06) it does, however, refuse the validation of a customer delivery of a lot named in an open recall (rehearsals excluded). |
| Electronic signature under 21 CFR Part 11 Subpart C | Requires identity proofing, credential controls, and a signature manifestation bound to the record, which are organisational and infrastructural matters beyond one module. See §9 R3. |
| CAPA investigation and root cause workflow | Belongs to a CAPA module. The recall records a reference to it. |
| Complaint intake | Belongs to a complaint module. The recall records a defect reference. |
| Authority portal submission (e.g. electronic gateways) | Interfaces differ per jurisdiction and change independently of this module. |
| Serialisation-level tracing below the lot | Would require an aggregation model; the lot is the granularity Odoo's stock module tracks natively. |

## 9. Risks

| # | Risk | Impact | Mitigation in this module |
|---|------|--------|---------------------------|
| R1 | Distribution recorded outside Odoo is missed by tracing. | Consignees not contacted. | Tracing reports unattributable quantities; lines can be added manually; the user manual states the limitation. |
| R2 | A user believes the closure attestation is a compliant electronic signature. | False confidence in an inspection. | The field is labelled and documented as not an electronic signature, in the model, the view and the manuals. |
| R3 | Content confirmations are ticked without reading the notice. | A notice missing a required element is issued. | The confirmations are attributable and timestamped, which makes the check auditable; the module cannot inspect prose, and this is stated. |
| R4 | Closure override becomes routine. | Gates lose meaning. | Override is manager-only, requires free-text justification, and is written to the chatter and to the closed record. |
| R5 | Traced quantities overwrite user-entered responses on re-trace. | Loss of evidence. | Trace refreshes only shipped quantities and source transfers; covered by an automated test. |
| R6 | Lot recall status is invisible to warehouse staff who lack a recall role. | An affected lot is shipped. | The lot indicator is computed through `sudo` and is deliberately readable without a recall role. |

## 10. Success criteria

| # | Criterion | How it is evidenced |
|---|-----------|---------------------|
| S1 | The module installs on a clean Odoo 19 Community database. | Installation test — **not executed in this environment**, see `14_verification_register.md`. |
| S2 | No forward transition succeeds without its evidence. | `tests/test_execution_workflow.py`. |
| S3 | Re-tracing never destroys user-entered reconciliation data. | `tests/test_traceability.py::test_retracing_preserves_user_entered_returns`. |
| S4 | A sent notice and an approved report cannot be altered. | `tests/test_communication.py`, `tests/test_report_immutability.py`. |
| S5 | Only a manager can close a recall with failed checks. | `tests/test_security.py::test_closure_override_is_manager_only`. |
| S6 | Every model is covered by an access rule and multi-company rule. | `static_checks.py` — executed, passes. |
