# Phase 3 - Functional Specification

Module: `ls_change_control` | Odoo 19.0 Community

## 1. Functional description

The module manages a controlled change from its request to its closure. A
change request is classified in a category. The category determines which
areas of the quality system must be assessed, which functions must approve,
and which deadlines apply. Each area produces one assessment record and each
function produces one approval record, so that the coverage of the evaluation
and of the decision is deterministic and auditable.

Once every mandatory assessment is completed and every mandatory approval is
granted, the request becomes approved. Implementation actions are then
executed, each requiring an evidence reference before it can be closed. When
every action is closed, the actual implementation date is derived from the
actions and the planned verification date is computed. The effectiveness of
the change is verified against acceptance criteria defined in advance. The
change control manager then declares the change verified and closes it with a
closure statement.

## 2. Menus and navigation

```
Change Control
├── Change Requests
│   ├── All Change Requests        action_ls_change_control_request
│   ├── My Change Requests         action_ls_change_control_my_requests
│   └── Impact Assessments         action_ls_change_control_assessment
├── Approvals
│   ├── My Approvals               action_ls_change_control_my_approvals
│   └── All Approvals              action_ls_change_control_approval
├── Execution
│   ├── Implementation Actions     action_ls_change_control_implementation
│   └── Effectiveness Verifications action_ls_change_control_verification
├── Reporting
│   └── Change Request Analysis    action_ls_change_control_request_analysis
└── Configuration  (Change Control Manager only)
    ├── Change Categories          action_ls_change_control_category
    ├── Impact Areas               action_ls_change_control_impact_area
    └── Settings                   action_ls_change_control_settings
```

The root menu is visible to the Viewer group and above. The Configuration
menu is visible to the Change Control Manager group only.

The suite specification places these menus under a `Quality` root menu owned by
`ls_qms`. That module does not exist, so the module creates its own root menu.
Re-parenting requires a single `menuitem` override in a bridge module.

## 3. State machine

### 3.1 States

| Technical value | Label | Meaning |
|-----------------|-------|---------|
| `draft` | Draft | The requester is composing the request |
| `under_review` | Under Review | The quality unit screens the request and builds the matrix |
| `impact_assessment` | Impact Assessment | Assessments are performed and approvals are decided |
| `approved` | Approved | Every mandatory assessment and approval is cleared |
| `implementation` | Implementation | Actions are being executed and verification is performed |
| `verified` | Verified | Implementation and effectiveness are confirmed |
| `closed` | Closed | Final, successful outcome |
| `rejected` | Rejected | Final, refused outcome |
| `cancelled` | Cancelled | Final, withdrawn outcome |

### 3.2 Transitions

| From | To | Method | Who | Guards |
|------|----|--------|-----|--------|
| draft | under_review | `action_submit_review` | Requester of the record, or manager | Mandatory content filled; content fields become frozen |
| under_review | draft | `action_reset_draft` | Manager | None |
| under_review | impact_assessment | `action_start_assessment` | Manager | Manager assigned, at least one impact area, at least one approval, every approval has an approver |
| under_review | rejected | `action_reject` | Manager or an assigned approver | Reason mandatory |
| impact_assessment | approved | `_try_approve`, triggered by the last approval | System | Every mandatory assessment completed and every mandatory approval granted |
| impact_assessment | rejected | `action_reject`, or an approval rejection | Manager or an assigned approver | Reason mandatory; a rejecting approver must have written a comment |
| approved | implementation | `action_start_implementation` | Manager | At least one implementation action exists |
| implementation | verified | `action_verify` | Manager | No open action when the company blocks on open actions; at least one completed verification with an Effective result when verification is required; no verification concluded Not Effective |
| verified | closed | `action_close` | Manager | Closure statement mandatory |
| draft, under_review, impact_assessment, approved | cancelled | `action_cancel` | Manager | Reason mandatory |

### 3.3 Transitions that do not exist, by design

* No transition out of `closed`, `rejected` or `cancelled`. These states are final. A change that is still required after a rejection requires a new request.
* No transition from `impact_assessment` back to `under_review`. The matrix is fixed once the assessment has started.
* No transition from `implementation` back to `approved`.

### 3.4 Deviation from the specification, stated explicitly

Section 7.6 of the suite specification lists the states as
`Draft, Under Review, Impact Assessment, Approved, Implementation, Verified,
Closed`. It lists no separate state for a pending approval. The module
implements exactly that list. Approvals are therefore collected **within** the
`impact_assessment` state, and the transition to `approved` is automatic when
the last mandatory approval is granted. Adding an eighth state would have
deviated from the specification.

## 4. Approval workflow

1. The category carries an ordered approval template of roles, each optionally with a default approver and a mandatory flag.
2. When the change control manager starts the impact assessment, one approval record is created per template line that does not already exist.
3. Every approval without an assigned approver blocks the start of the assessment.
4. Each assigned approver, and nobody else, records their own decision.
5. The `sequence` field orders the display. It does **not** impose a sequential order: approvals may be granted in any order. This is a deliberate decision, so that the process is not blocked by one absent approver while others could progress.
6. A favourable decision writes the state, the author, the date and time in UTC and the meaning of the signature, then attempts to approve the request.
7. An unfavourable decision requires a comment, and rejects the whole request.
8. A decided approval is immutable and undeletable.

## 5. Business rules

| # | Rule |
|---|------|
| BRU-1 | The reference is allocated from a sequence at creation and is never modified |
| BRU-2 | A temporary change must declare an end date; a permanent change must not |
| BRU-3 | A planning date cannot precede the request date |
| BRU-4 | The requester and the change control manager must be internal users |
| BRU-5 | Only a Draft request may be archived |
| BRU-6 | Only a Draft request may be deleted, and only by a manager |
| BRU-7 | Content fields are frozen once the request leaves Draft, for every user |
| BRU-8 | After Draft, only a change control manager may modify a request |
| BRU-9 | Workflow fields are never writable from a client session |
| BRU-10 | An assessment requires a written rationale before completion |
| BRU-11 | An assessment declaring an impact requires the actions to be described |
| BRU-12 | Only the assigned assessor or a manager may complete an assessment |
| BRU-13 | Only the assigned approver may record their decision |
| BRU-14 | A rejection requires a comment on the approval |
| BRU-15 | An implementation action requires an evidence reference before closure |
| BRU-16 | Only the responsible person or a manager may execute an action |
| BRU-17 | Only a manager may cancel an action, and a reason must be recorded first |
| BRU-18 | The actual implementation date is computed, never entered |
| BRU-19 | A verification requires a conclusion before completion |
| BRU-20 | A Not Effective verification requires a follow-up to be requested |
| BRU-21 | An impact area can be assessed only once per request |
| BRU-22 | An approval role can appear only once per request |
| BRU-23 | The closure requires a closure statement |

## 6. Notifications

Three mail templates, sent with `force_send=False` so that delivery goes
through the standard Odoo mail queue.

| Template | Model | Trigger | Recipient |
|----------|-------|---------|-----------|
| `mail_template_approval_requested` | approval | Start of the impact assessment, and each reminder | The assigned approver |
| `mail_template_change_approved` | request | Transition to Approved | The requester |
| `mail_template_change_rejected` | request | Transition to Rejected | The requester |

In addition, the module posts a note in the chatter of the request for each
of the following: submission, return to draft, completion of an assessment,
each approval decision, completion or cancellation of an action, completion
of a verification.

## 7. Scheduled actions

| Name | Frequency | Method | Behaviour |
|------|-----------|--------|-----------|
| Change Control: remind pending approvals | Daily | `_cron_remind_pending_approvals` | For each company with a reminder delay greater than zero, sends the approval mail and schedules a to-do to approvers whose approval has been pending longer than the delay, at most once per day per approval |
| Change Control: remind overdue implementations | Daily | `_cron_remind_overdue_implementations` | Schedules a to-do on requests in Approved or Implementation whose planned implementation date has passed and which are not implemented |
| Change Control: remind due effectiveness verifications | Daily | `_cron_remind_due_verifications` | Schedules a to-do on requests in Implementation whose planned verification date has been reached and which have no completed verification |

All three avoid creating a duplicate activity for the same user and the same
summary.

## 8. Reports

One report: **Change Control Record**, `qweb-pdf`, bound to the change request
model so that it appears in the Print menu.

Sections: header, description of the change, impact declaration, impact
assessments, approvals with signature metadata, implementation actions with
evidence, effectiveness verifications with acceptance criteria and
conclusions, outcome with all dates and the closure, rejection or cancellation
statement.

The footer carries the notice that the document is uncontrolled when printed,
the name of the person who printed it and the date and time of printing.

## 9. Analysis and indicators

No Enterprise dashboard view is used. Analysis relies on the `graph` and
`pivot` views, which are part of Odoo Community.

Indicators available as fields on the request: number of assessments and of
completed assessments, number of approvals and of granted approvals, number of
actions and of closed actions, number of verifications, and the list of
outstanding items blocking the next transition.

## 10. Search, filters and grouping

### 10.1 Change request

Search fields: reference or title combined, category, requester, change
control manager, impact areas.

Filters: My Requests, Managed by Me, Open, one filter per state, GMP Impact,
Regulatory Action Required, Critical, Implementation Late, Verification Due,
Archived.

Group by: Status, Category, Classification, Requester, Change Control Manager,
Department, Regulatory Impact, Request Date.

### 10.2 Other models

Assessments, approvals, implementation actions and verifications each have
their own search view with an ownership filter, status filters, a lateness
filter where relevant, and grouping by parent request and by status.

## 11. Wizards

One wizard, `ls.change_control.decision_wizard`, serving the three decisions
that require a justification: closure, rejection and cancellation. A single
wizard is used because the data collected and the confirmation pattern are
identical; the decision itself is always delegated to the corresponding method
of the request, so the workflow rules exist in one place only.

## 12. Configuration

Configuration is held on `res.company`, exposed through a dedicated form
opened from Configuration, Settings. Four parameters: approval reminder delay,
default verification delay, whether effectiveness verification is mandatory,
and whether open actions block the transition out of Implementation.

The standard `res.config.settings` view is deliberately not extended, so that
the module carries no risk from a change of layout of the standard settings
screen in a future Odoo version.
