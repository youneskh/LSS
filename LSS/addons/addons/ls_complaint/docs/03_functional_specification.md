# Phase 3 — Functional Specification

## 1. Functional description

`ls_complaint` adds a complaint handling process to Odoo 19 Community. A
complaint is a statement received from outside (or from inside) the organisation
alleging a deficiency in a product or a service. The module carries it from
reception to a reviewed, frozen closure, and records everything decided on the
way: the classification, the impact assessment, any adverse event and its
reportability, the root cause investigation and its independent approval, the
actions taken, and the closure review.

Four object families are involved:

- **Complaint** (`ls.complaint`) — the master record and the state machine.
- **Investigation** (`ls.complaint.investigation`) — root cause analysis, one or
  more per complaint, each independently approved.
- **Adverse event** (`ls.complaint.adverse_event`) — a safety event associated
  with the complaint, with its own reportability lifecycle.
- **Resolution** (`ls.complaint.resolution`) — an action taken towards the
  complainant or the product.

A fifth model, **Category** (`ls.complaint.category`), is configuration: it
carries the classification and every configurable time target.

## 2. Menus and navigation

```
Complaints (root, visible to Complaint Viewer and above)
├── Complaint Handling
│   ├── All Complaints          → ls.complaint, open complaints by default
│   ├── My Complaints           → ls.complaint filtered on the responsible user
│   ├── Investigations          → ls.complaint.investigation
│   └── Resolutions             → ls.complaint.resolution
├── Vigilance
│   └── Adverse Events          → ls.complaint.adverse_event
├── Reporting
│   └── Complaint Analysis      → ls.complaint, pivot first
└── Configuration               (Complaint Manager only)
    └── Complaint Categories    → ls.complaint.category
```

Child records are also reachable from the complaint form, through three stat
buttons (Investigations, Resolutions, Adverse Events) and through three notebook
pages holding editable embedded lists.

## 3. State machines

### 3.1 Complaint

```
                    ┌──────────────────────────────┐
                    ▼                              │ Reset to Received
  ┌──────────┐  Start Assessment  ┌────────────┐   │ (Manager)
  │ Received │ ─────────────────► │ Assessment │   │
  └──────────┘                    └────────────┘   │
        │                          │        │      │
        │                          │        │ Waive Investigation
        │        Start Investigation        │ (Reviewer, category permitting)
        │                          ▼        │
        │                 ┌───────────────┐ │
        │                 │ Investigation │ │
        │                 └───────────────┘ │
        │                   │          │    │
        │      CAPA Required│          │    │
        │                   ▼          │    │
        │           ┌───────────────┐  │    │
        │           │ CAPA Required │  │    │
        │           └───────────────┘  │    │
        │                   │          │    │
        │      Start Resolution        │    │
        │                   ▼          ▼    ▼
        │                 ┌────────────────────┐
        │                 │     Resolution     │
        │                 └────────────────────┘
        │                            │ Close (wizard)
        │                            ▼
        │                      ┌──────────┐
        │                      │  Closed  │  frozen
        │                      └──────────┘
        │ Cancel (wizard, Manager, from any open state)
        ▼
  ┌───────────┐
  │ Cancelled │  frozen, reversible by Reset to Received
  └───────────┘
```

Transition preconditions:

| Transition | Preconditions |
|---|---|
| Received → Assessment | responsible user and category set; a product is identified if the complaint is product related |
| Assessment → Investigation | severity, complaint type and assessment summary set; a draft investigation is created automatically if none exists |
| Assessment → Resolution (waiver) | the category does not require an investigation; no adverse event exists; severity, complaint type and waiver justification set |
| Investigation → CAPA Required | every investigation is approved or rejected, at least one approved if the category requires it; CAPA justification set |
| Investigation → Resolution | same investigation conditions |
| CAPA Required → Resolution | same, plus a CAPA reference |
| Resolution → Closed | at least one resolution exists; no resolution in draft or in progress; no adverse event outside the closed state; a CAPA reference when a CAPA was declared; closure summary, effectiveness confirmation and a reviewer distinct from the responsible user |
| any open state → Cancelled | a cancellation reason |
| Cancelled → Received | manager only |

There is **no transition out of Closed**. A closed complaint is corrected by
raising a new one.

### 3.2 Investigation

`Draft → In Progress → Completed → Approved` or `→ Rejected`.

- *Complete* requires methodology, investigation summary, root cause category
  and conclusion; a root cause description is additionally required unless the
  category is "Not Determined"; "Other Methodology" requires its description.
- *Approve* is refused when the acting user is the investigator of that record.
- *Reject* requires a rejection reason recorded on the Rejection tab.
- Approved and rejected investigations are frozen.

### 3.3 Adverse event

`Draft → Assessed → Submitted → Closed`, with `Assessed → Closed` when the event
is not reportable.

- *Assess* requires a reportability rationale and a causality assessment; a
  reportable event additionally requires the competent authority.
- *Record Submission* is available only for reportable events and requires the
  authority acknowledgement reference.
- *Close* is refused for a reportable event that was not submitted, and requires
  follow-up notes when a follow-up was declared.
- Closed events are frozen.

### 3.4 Resolution

`Draft → In Progress → Done`, or `→ Cancelled` from draft or in progress.

- *Mark as Done* requires completion evidence and stamps the completion date.
- *Cancel* requires a cancellation reason.
- Done and cancelled resolutions are frozen.

## 4. Approval workflow

Two approvals exist and both are enforced server-side, per record:

1. **Investigation approval** — performed by a Complaint Reviewer, refused when
   the acting user is the investigator of that investigation. The approver and
   the approval date are stamped and a message is posted.
2. **Closure review** — performed through the closure wizard by a Complaint
   Reviewer, refused when the chosen reviewer is the responsible user of that
   complaint. The reviewer, the closing user, the closure date and the closure
   summary are stamped and the record is frozen.

## 5. Business rules

| # | Rule | Enforcement |
|---|---|---|
| R-01 | The complaint reference is unique per company and generated by a sequence. | SQL constraint + `create()` |
| R-02 | The receipt date cannot be in the future. | Python constraint |
| R-03 | The occurrence date cannot be later than the receipt date. | Python constraint |
| R-04 | The expiry date cannot precede the manufacturing date. | Python constraint |
| R-05 | "Other Channel" and "Other Type" require a description. | Python constraints + `required` in the view |
| R-06 | A product related complaint identifies a product before leaving Received. | Python constraint |
| R-07 | The lot belongs to the selected product. | Python constraint + domain |
| R-08 | The reviewer differs from the responsible user. | Python constraint on the complaint and on the wizard |
| R-09 | The approver of an investigation differs from its investigator. | Python constraint + check in `action_approve` |
| R-10 | Quantities are not negative. | SQL check constraint |
| R-11 | Category day targets are not negative, and the acknowledgement target does not exceed the closure target. | Python constraints |
| R-12 | Final records are read-only. | `write()` override on the four transactional models |
| R-13 | Records that left their initial state cannot be deleted. | `@api.ondelete` on the four transactional models |
| R-14 | Duplicating a complaint resets its reference and status. | `copy_data()` |
| R-15 | The awareness date of an adverse event is not in the future and not earlier than the event date. | Python constraint |
| R-16 | The reportability rationale cannot be removed after assessment. | Python constraint |
| R-17 | Records are isolated per company. | Global record rules |
| R-18 | An investigator writes only the complaints he owns or received. | Record rule, overridden for reviewers |

## 6. Notifications

| Trigger | Mechanism | Recipient |
|---|---|---|
| Every state transition | Message posted on the record, plus field tracking on `state`, `severity`, `owner_id`, `capa_required`, `regulatory_reportable` and others | Followers |
| Closure target passed, complaint still open | To-do activity created daily by a scheduled action, one per complaint, not duplicated | Responsible user, or the receiving user if none |
| Adverse event reporting deadline reached, event not submitted | To-do activity created daily by a scheduled action | Responsible user of the complaint |
| Acknowledgement to the complainant | Mail template `Complaint: Acknowledgement of Receipt`, sent manually | Complainant |
| Outcome to the complainant | Mail template `Complaint: Closure Notification`, sent manually | Complainant |

The two mail templates are delivered but are **not** sent automatically: sending
a communication to a complainant is a decision, not an automation.

## 7. Scheduled actions

| Name | Model | Method | Interval |
|---|---|---|---|
| Life Sciences: Overdue Complaint Notification | `ls.complaint` | `_cron_notify_overdue_complaints` | 1 day |
| Life Sciences: Adverse Event Reporting Deadline Notification | `ls.complaint.adverse_event` | `_cron_notify_due_adverse_event_reports` | 1 day |

Both process at most 200 records per run, are idempotent, and log the number of
activities created.

## 8. Reports

| Report | Type | Content |
|---|---|---|
| Complaint Record | QWeb PDF, bound to `ls.complaint` | Identification, reception, complainant, product and lot, description, assessment, table of investigations with root causes, table of adverse events with reporting status, table of resolutions, CAPA fields, closure or cancellation |

The print file name is `Complaint - <reference>`.

## 9. Dashboards and KPI

No dedicated dashboard model is delivered. Analysis uses the standard views:

| KPI | Where |
|---|---|
| Complaint volume per month and severity | Graph view on `ls.complaint` |
| Complaints per product and status, with average closure duration | Pivot view on `ls.complaint`, measure `closure_duration_days` |
| Open complaints past their closure target | List view, filter *Overdue*, red decoration |
| Complaints requiring regulatory reporting | Filter *Regulatory Reporting Required* |
| Complaints with a declared CAPA | Filter *CAPA Required* |
| Root cause distribution against conclusion | Pivot view on `ls.complaint.investigation` |
| Adverse events per month and seriousness | Graph view on `ls.complaint.adverse_event` |
| Adverse events past their reporting deadline | Filter *Reporting Overdue*, red decoration |

## 10. Search views, filters and group-by

### `ls.complaint`
- Searchable: reference, subject, description, complainant, product, lot, responsible, category.
- Filters: My Complaints, Received by Me, Open, Closed, Cancelled, Overdue, Critical, Regulatory Reporting Required, CAPA Required, Receipt Date (period), Archived.
- Group by: Status, Severity, Category, Complaint Type, Product, Responsible, Channel, Receipt Month.

### `ls.complaint.investigation`
- Searchable: reference, complaint, investigator, root cause description.
- Filters: My Investigations, Open, Approved, Rejected.
- Group by: Status, Root Cause Category, Conclusion, Investigator.

### `ls.complaint.adverse_event`
- Searchable: reference, complaint, event description, competent authority.
- Filters: Reportable, Serious, Reporting Overdue, Open, Awareness Date (period).
- Group by: Status, Seriousness, Outcome, Causality, Awareness Month.

### `ls.complaint.resolution`
- Searchable: complaint, responsible.
- Filters: My Resolutions, Open, Overdue.
- Group by: Status, Resolution Type, Responsible.

### `ls.complaint.category`
- Searchable: name, code.
- Filters: Investigation Required, Archived.
- Group by: Default Severity.

## 11. Actions

| Action | Type | Purpose |
|---|---|---|
| Complaints | window | list, form, graph, pivot; open complaints by default |
| My Complaints | window | filtered on the responsible user |
| Complaint Analysis | window | pivot first |
| Investigations, Resolutions, Adverse Events, Complaint Categories | window | one per model |
| Complaint Record | report | PDF, bound to the complaint model |
| Overdue / reporting notifications | server (cron) | see section 7 |

## 12. Wizards

| Wizard | Fields | Effect |
|---|---|---|
| Close Complaint (`ls.complaint.close.wizard`) | complaint (read-only), current status (read-only), responsible (read-only), reviewer (required), effectiveness confirmed, complainant informed, closure summary (required) | Calls `action_close`, which re-verifies every closure precondition |
| Cancel Complaint (`ls.complaint.cancel.wizard`) | complaint (read-only), reason (required) | Calls `action_cancel` |

Both wizards re-validate server-side: the wizard is a data collection device,
not the control itself.

## Phase 3 gate

**PASS** — description, menus, navigation, workflows, state machines, approval
workflow, business rules, notifications, scheduled actions, reports, dashboards,
KPI, search views, filters, group-by, actions and wizards are specified, and
each is implemented in Phase 6.
