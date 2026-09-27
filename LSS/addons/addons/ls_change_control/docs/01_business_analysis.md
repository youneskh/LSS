# Phase 1 - Business Analysis

Module: `ls_change_control` | Suite: Life Sciences Suite | Platform: Odoo 19.0 Community

## 1. Business objectives

| # | Objective |
|---|-----------|
| BO-1 | Ensure that no change affecting product quality, patient safety or regulatory status is made without a documented evaluation and a documented decision |
| BO-2 | Make the evaluation coverage deterministic: every change is assessed against a defined list of impact areas, not against the memory of the assessor |
| BO-3 | Make every approval attributable to a named person, at a recorded date and time, with a recorded meaning |
| BO-4 | Ensure that an approved change is actually implemented, with retained evidence, within a planned deadline |
| BO-5 | Ensure that an implemented change is verified for effectiveness against criteria defined in advance |
| BO-6 | Produce, at any moment, a complete printable record of a change for an inspection or an audit |
| BO-7 | Prevent retrospective modification of the description of a change or of a decision already taken |

## 2. Business requirements

| # | Requirement | Objective |
|---|-------------|-----------|
| BR-1 | A change request describes the situation before the change, the situation after the change and the justification | BO-1 |
| BR-2 | The description of the change is frozen once the request is submitted | BO-7 |
| BR-3 | A change is classified in a category which determines the impact areas, the approvers and the deadlines | BO-2 |
| BR-4 | Each impact area produces one assessment record with a written rationale | BO-2 |
| BR-5 | An assessment declaring an impact must describe the actions required | BO-2, BO-4 |
| BR-6 | A change reaches the approved state only when every mandatory approval is granted and every mandatory assessment is completed | BO-1, BO-3 |
| BR-7 | Only the assigned approver may record their own decision | BO-3 |
| BR-8 | A recorded decision can never be modified or deleted | BO-7 |
| BR-9 | An implementation action cannot be closed without an evidence reference | BO-4 |
| BR-10 | The actual implementation date is derived from the actions, never entered by hand | BO-4 |
| BR-11 | Acceptance criteria of a verification are recorded before the verification is completed | BO-5 |
| BR-12 | A verification concluding that the change is not effective blocks the closure and requires a follow-up | BO-5 |
| BR-13 | A submitted change request can never be deleted | BO-7 |
| BR-14 | A complete record of the change can be printed at any time | BO-6 |
| BR-15 | Approvers, implementers and verifiers are reminded automatically when they are late | BO-4, BO-5 |

## 3. Stakeholders

| Stakeholder | Interest in the process |
|-------------|------------------------|
| Quality Assurance | Owns the process, reviews every request, approves, closes |
| Requesting departments (Production, Engineering, QC, IT, Supply Chain) | Raise requests and execute implementation actions |
| Subject matter experts | Perform the impact assessments of their area |
| Regulatory Affairs | Determine whether the change triggers a notification, a variation or a prior approval |
| Qualified Person or Pharmacist Responsible | Approves changes affecting the product |
| Validation | Determines whether requalification or revalidation is required |
| Site management | Approves organisational changes, arbitrates resources |
| Internal and external auditors, inspectors | Read the records, verify the traceability of decisions |
| System administrator | Maintains users, groups, scheduled actions and the configuration |

## 4. User roles

The specification of the suite defines four security groups. They are
implemented exactly as specified, in a cumulative hierarchy.

| Role | Group | Rights |
|------|-------|--------|
| Viewer | `group_ls_change_control_viewer` | Read everything within their companies |
| Requester | `group_ls_change_control_requester` | Create requests, edit their own drafts, complete the assessments assigned to them, execute the actions and verifications they are responsible for |
| Approver | `group_ls_change_control_approver` | Rights of a requester, plus record the approval decisions assigned to them |
| Change Control Manager | `group_ls_change_control_manager` | Drive the whole process and maintain the configuration |

A subject matter expert who performs assessments must hold at least the
Requester group. This is a deliberate design decision taken so as not to add a
fifth group beyond the four defined by the specification. It is documented in
`docs/configuration_guide.md`.

## 5. User stories

| # | As a | I want to | So that |
|---|------|-----------|---------|
| US-1 | Requester | describe a change and submit it | the change is evaluated before it is made |
| US-2 | Requester | see what is blocking my request | I know who is waiting for what |
| US-3 | Change control manager | assign the impact areas and the approvers | the evaluation covers the right areas and the right functions |
| US-4 | Change control manager | generate the assessment and approval matrix from the category | I do not rebuild the same matrix for every request of the same type |
| US-5 | Subject matter expert | record my assessment of my area | my evaluation is traceable to me |
| US-6 | Approver | record my decision with a comment | my decision is attributable and justified |
| US-7 | Approver | reject a change and state why | an insufficiently evaluated change is not made |
| US-8 | Change control manager | plan implementation actions with a responsible person and a date | the change is actually implemented |
| US-9 | Implementer | close my action with an evidence reference | the completion of the action is traceable to a record |
| US-10 | Verifier | conclude on the effectiveness of the change | an ineffective change is detected and corrected |
| US-11 | Change control manager | close the change with a conclusion | the record is complete and final |
| US-12 | Auditor | print the complete record of a change | I can review the change during an inspection |
| US-13 | Change control manager | be reminded of late items | the process does not stall silently |
| US-14 | Quality manager | analyse changes by category, status and classification | I can report on the performance of the process |

## 6. Use cases

| # | Use case | Primary actor | Precondition | Outcome |
|---|----------|---------------|--------------|---------|
| UC-1 | Raise a change request | Requester | None | Request in Draft |
| UC-2 | Submit for review | Requester | Request in Draft, all mandatory content filled | Request in Under Review, content frozen |
| UC-3 | Review and open the assessment | Change control manager | Request Under Review, manager, impact areas and approvers assigned | Request in Impact Assessment, assessments and approvals generated |
| UC-4 | Return an incomplete request | Change control manager | Request Under Review | Request back in Draft |
| UC-5 | Complete an impact assessment | Subject matter expert | Request in Impact Assessment, user is the assessor | Assessment completed and immutable |
| UC-6 | Approve | Approver | Request in Impact Assessment, user is the assigned approver | Decision recorded; request approved when it was the last mandatory one |
| UC-7 | Reject | Approver or manager | Request Under Review or in Impact Assessment | Request Rejected, final |
| UC-8 | Plan and start the implementation | Change control manager | Request Approved, at least one action planned | Request in Implementation |
| UC-9 | Execute an action | Responsible person | Request Approved or in Implementation | Action Done with evidence |
| UC-10 | Cancel an action | Change control manager | Action not closed, reason recorded | Action Cancelled |
| UC-11 | Complete a verification | Verifier | Request in Implementation, conclusion written | Verification Completed, result recorded |
| UC-12 | Declare verified | Change control manager | No open action, verification effective when required | Request Verified |
| UC-13 | Close | Change control manager | Request Verified, closure statement written | Request Closed, final |
| UC-14 | Cancel a request | Change control manager | Request not yet in Implementation | Request Cancelled, final |
| UC-15 | Print the change control record | Any reader | None | PDF of the complete record |

## 7. Functional scope

In scope:

* Change request lifecycle from Draft to Closed, Rejected or Cancelled.
* Configuration of categories, impact areas and approval templates.
* Impact assessment per area.
* Approval matrix and decision capture.
* Implementation actions and their evidence.
* Effectiveness verification with acceptance criteria.
* Company level parameters, per manufacturing site.
* Change control record report in PDF.
* Three scheduled reminders.
* Analysis views: graph and pivot.
* Access rights and record rules for the four groups, with multi-company isolation.

## 8. Out of scope

The following items are deliberately excluded. Each is excluded for a stated
reason, not by omission.

| Item | Reason |
|------|--------|
| Binding electronic signature with re-authentication of the signer | Assigned to `ls_electronic_signature` by the suite architecture. This module provides the `_apply_signature` extension point |
| Generic field level audit trail on every model | Assigned to `ls_audit_trail` by the suite architecture. This module relies on the Odoo message tracking of the chatter for its own records |
| Document management and controlled document versioning | Assigned to `ls_document_management`. This module stores a document reference as text |
| Corrective and preventive action management | Assigned to `ls_capa`. This module stores a follow-up reference as text |
| Risk assessment methodology such as failure mode and effects analysis | Assigned to `ls_risk_management`. This module stores a risk assessment reference as text |
| Validation protocols and qualification records | Assigned to `ls_validation`. This module records that revalidation is required and tracks it as an implementation action |
| Training record management | Assigned to `ls_training`. This module records that training is required and tracks it as an implementation action |
| Direct link to products, equipment, lots or bills of material | Would require dependencies on `stock`, `mrp` or `maintenance`, which the specification does not list for this module |
| Deviation and complaint linkage | Assigned to `ls_deviation` and `ls_complaint` |
| Customer portal access to change requests | Change control is an internal process; portal users are explicitly rejected by constraints |

## 9. Risks

| # | Risk | Impact | Mitigation implemented |
|---|------|--------|------------------------|
| R-1 | A user modifies the description of a change after approval | Loss of record integrity, inspection finding | Content fields frozen at submission for every user |
| R-2 | A user forges a state or a decision through the external API | Loss of record integrity | Workflow fields refused outside superuser mode, which an RPC context cannot reach |
| R-3 | An approval is recorded by somebody other than the approver | Loss of attribution | The decision methods verify that the current user is the assigned approver |
| R-4 | A change is closed without evidence of implementation | Undocumented change | Evidence reference mandatory before closing an action |
| R-5 | Effectiveness verification is skipped | Ineffective change left in place | Verification enforced by category and company parameters, and blocked when a verification concluded that the change is not effective |
| R-6 | A change stalls without anybody noticing | Late implementation, uncontrolled situation | Three daily scheduled reminders and dedicated search filters |
| R-7 | Records of one manufacturing site are visible to another | Confidentiality, data integrity | Global multi-company record rules on all five transactional models |
| R-8 | Deleting a request destroys a quality record | Loss of records | Deletion refused for every request that is not in Draft |
| R-9 | The suite modules this module should depend on do not exist | Broken installation | Dependencies limited to `base`, `mail` and `hr`; integration points documented |
| R-10 | The module was not installed or tested in the build environment | Undetected defect at install time | Documented in the validation report; installation qualification remains to be performed by the receiving organisation |

## 10. Success criteria

| # | Criterion | How it is demonstrated |
|---|-----------|------------------------|
| SC-1 | The module installs on a clean Odoo 19.0 Community database | To be executed by the receiving organisation, see `docs/validation_report.md` |
| SC-2 | The seven states of the specification are implemented, no more and no less | `tests/test_request_workflow.py`, model `STATES` constant |
| SC-3 | The four security groups of the specification are implemented | `tests/test_install.py`, `tests/test_security.py` |
| SC-4 | No record of a taken decision can be modified | `tests/test_approval.py`, `tests/test_assessment.py`, `tests/test_verification.py` |
| SC-5 | No Odoo Enterprise dependency | Manifest declares `base`, `mail`, `hr` only; no Enterprise view type is used |
| SC-6 | Static analysis passes without error | `static_check.py`: 170 checks, 0 error |
| SC-7 | Every model is covered by access rights | Verified by `static_check.py` |
| SC-8 | The complete record can be printed | `tests/test_reports.py` |
