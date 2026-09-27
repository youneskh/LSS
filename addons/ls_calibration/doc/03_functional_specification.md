# Phase 3 — Functional Specification

Module: `ls_calibration`.

## 3.1 Functional description

The module manages the complete life cycle of the calibration of a measuring
instrument, from its registration to the issue of its calibration
certificate.

An **instrument** is the master record. It carries its identification, its
metrological characteristics and its classification. It has a life cycle:
draft, in service, out of service, retired.

A **calibration plan** attaches a periodic programme to an instrument. It
carries the interval, the written procedure reference and the list of test
points with their acceptance limits. Only an active plan produces due dates.

A **calibration record** is one calibration event. It is generated from a
plan or created manually. It carries one line per test point with the
as-found reading, taken before any adjustment, and the as-left reading, taken
after. Each reading is compared with the acceptance limits and receives a
verdict. The overall result is derived: pass, pass after adjustment, or fail.

A **calibration certificate** is the document issued at the end of the
calibration, either produced internally from an approved record or received
from an external accredited laboratory.

## 3.2 Menus and navigation

```
Calibration
├── Instruments                      → ls.calibration.instrument
├── Calibration Plans                → ls.calibration.plan
├── Calibration Records              → ls.calibration.record
├── Certificates                     → ls.calibration.certificate
├── Calibration Status
│   ├── Due and Overdue              → instruments filtered on the status
│   └── Generate Calibration Records → wizard (technician and manager)
└── Reporting
    └── Calibration Analysis         → pivot and graph of the records
```

The root menu is visible to the *Calibration / Viewer* group and therefore to
the two groups that imply it.

## 3.3 State machines

### 3.3.1 Instrument

```
draft ──action_set_in_service──> in_service
in_service ──action_set_out_of_service──> out_of_service
out_of_service ──action_set_in_service──> in_service
any ──action_retire──> retired            (closes the active plans)
retired ──action_reset_to_draft──> draft
```

An instrument that is out of service or retired has the calibration status
*Not Applicable*.

### 3.3.2 Calibration plan

```
draft ──action_activate──> active          (requires at least one test point)
active ──action_suspend──> suspended       (clears the next due date)
suspended ──action_activate──> active
any ──action_set_obsolete──> obsolete      (clears the next due date)
suspended | obsolete ──action_reset_to_draft──> draft
```

### 3.3.3 Calibration record

```
draft ──action_start──> in_progress
in_progress ──action_submit_review──> to_review     (completeness checks)
to_review ──action_approve──> approved              (manager, not the performer)
to_review ──action_reject──> rejected               (reason required)
rejected ──action_reset_to_draft──> draft
draft | in_progress | to_review | rejected ──action_cancel──> cancelled
```

`approved` and `cancelled` are terminal and locked.

### 3.3.4 Certificate

```
draft ──action_issue──> issued        (external: document required)
issued ──action_supersede──> superseded
```

## 3.4 Approval workflow

1. The technician completes the readings and clicks **Submit to Review**. The
   system records the submitter and the submission time.
2. The system verifies the completeness of the record. Any failure blocks the
   transition with an explicit message.
3. A user of the *Calibration / Manager* group opens the record and clicks
   **Approve** or **Reject**.
4. Approval is refused when the approver is the user recorded as the
   performer.
5. On approval, the system records the approver and the approval time, posts
   the meaning of the signature in the message thread, and locks the record.
6. The next due date of the plan and of the instrument is recomputed.

## 3.5 Business rules

| # | Rule | Enforcement |
|---|------|-------------|
| BRU-01 | The instrument reference is unique per company. | Database constraint |
| BRU-02 | The maximum of the measuring range is not lower than its minimum. | Database constraint |
| BRU-03 | The alert lead time and the tolerances are not negative. | Database constraints |
| BRU-04 | The calibration interval is strictly positive. | Database constraint |
| BRU-05 | The plan referenced by a record belongs to the instrument of the record. | Python constraint |
| BRU-06 | An instrument is not a reference standard for its own calibration. | Python constraint |
| BRU-07 | The validity end date of a certificate is not earlier than its issue date. | Python constraint |
| BRU-08 | The record referenced by a certificate belongs to the instrument of the certificate. | Python constraint |
| BRU-09 | A plan is not activated without at least one test point. | Workflow check |
| BRU-10 | A record is not submitted without a calibration date, a performer, at least one test point and at least one reference standard, internal or external. | Workflow check |
| BRU-11 | A record whose as-found readings are out of tolerance is not submitted without an impact assessment. | Workflow check |
| BRU-12 | A reference standard whose own calibration is overdue at the calibration date is refused. | Workflow check |
| BRU-13 | The approver is not the performer. | Workflow check |
| BRU-14 | Approval is restricted to the manager group. | Workflow check and access rights |
| BRU-15 | An approved or cancelled record cannot be modified. | `write` override |
| BRU-16 | A record that left the draft state cannot be deleted. | `unlink` override |
| BRU-17 | The lines of a record that left the in-progress state cannot be created, modified or deleted. | `create`, `write` and `unlink` overrides |
| BRU-18 | An issued certificate cannot be modified, except its state and its notes, nor deleted. | `write` and `unlink` overrides |
| BRU-19 | An external certificate is not issued without its document attached. | Workflow check |
| BRU-20 | Retiring an instrument makes its active plans obsolete. | Workflow action |

## 3.6 Notifications

| Event | Recipient | Mechanism |
|-------|-----------|-----------|
| Instrument due soon or overdue | Responsible user of the instrument | Activity of type *To Do* with the due date as deadline, created once per instrument and per situation |
| Submission for approval | Followers of the record | Message in the thread |
| Approval | Followers of the record | Message in the thread stating the signer, the time and the meaning of the signature |
| Rejection | Followers of the record | Message in the thread stating the signer and the reason |
| Change of a tracked field | Followers | Standard Odoo change tracking |

Tracked fields: instrument name, reference, serial number, responsible,
criticality, GxP impact, state; plan reference, instrument, interval,
responsible, state; record reference, instrument, plan, type, calibration
date, performer, as-found status, as-left status, result, submitter,
approver, state; certificate number, instrument, issuer type, issue date,
validity end date, state.

## 3.7 Scheduled actions

| Name | Model | Frequency | Behaviour |
|------|-------|-----------|-----------|
| Calibration: notify due and overdue instruments | `ls.calibration.instrument` | Daily, 01:00 | Schedules one activity for each in-service instrument whose status is due soon or overdue, unless an identical activity is already open. Returns the number of activities scheduled. |
| Calibration: generate due calibration records | `ls.calibration.plan` | Daily, 02:00 | Creates one draft record, with the test points of the plan, for each active plan whose next due date falls within the configured horizon and which has no open record. Returns the number of records created. |

## 3.8 Reports

| Report | Model | Content |
|--------|-------|---------|
| Calibration Record | `ls.calibration.record` | Identification of the instrument and of the plan, execution data, reference standards, table of the test points with limits and both readings and their verdicts, statuses and result, out-of-tolerance block when applicable, conclusion, submission and approval signatures, statement that the electronic record remains the original evidence. |
| Calibration Certificate | `ls.calibration.certificate` | Identification of the instrument, issuer and accreditation, validity dates, and, when a record is linked, the calibration date, the result, the next due date and the table of the as-left readings. |

Both reports are bound to their model and are available from the print menu.

## 3.9 Dashboards and key indicators

The module provides the indicators through standard views rather than through
a custom client-side dashboard, so that no JavaScript is introduced.

| Indicator | Where |
|-----------|-------|
| Number of instruments due or overdue | *Calibration Status → Due and Overdue*, record count |
| Distribution of the results per instrument | *Reporting → Calibration Analysis*, pivot: instrument in rows, result in columns |
| Calibration volume per month | *Reporting → Calibration Analysis*, graph: calibration date by month, grouped by result |
| Records awaiting approval | *Calibration Records*, filter *To Review* |
| Out-of-tolerance events | *Calibration Records*, filter *As Found Out of Tolerance* |
| Instruments per criticality | *Instruments*, group by *Criticality* |
| Expired certificates | *Certificates*, filter *Expired* |

The calibration status is computed at read time and is therefore not
available as a group-by axis. This is a deliberate trade-off documented in
the technical specification: an always-accurate status is preferred to a
groupable but potentially stale one.

## 3.10 Search views, filters and group by

| Model | Search fields | Filters | Group by |
|-------|---------------|---------|----------|
| Instrument | name, reference, serial number, category, responsible, location | Overdue; Due Soon; Valid; Not Scheduled; In Service; Critical; Direct GxP Impact; My Instruments; Archived | State; Category; Criticality; GxP Impact; Responsible; Next Calibration Date |
| Plan | reference, instrument, procedure reference, responsible | Active Plans; Due; Externally Calibrated; My Plans; Archived | Instrument; State; Responsible; Next Due Date |
| Record | reference, instrument, plan, performer, approver | To Review; Open; Approved; As Found Out of Tolerance; Failed; Performed by Me; This Year | Instrument; Calibration Type; Result; State; Performed By; Calibration Month |
| Certificate | number, instrument, record, issuing laboratory | Issued; External; Expired | Instrument; Issuer Type; State; Issue Date |

## 3.11 Actions

| Action | Type | Purpose |
|--------|------|---------|
| Instruments | Window | List and form of the register |
| Calibration Status | Window | Instruments due soon or overdue |
| Calibration Plans | Window | List and form of the plans |
| Calibration Records | Window | List, form, pivot and graph of the records |
| Calibration Analysis | Window | Pivot and graph, filtered on the approved records |
| Certificates | Window | List and form of the certificates |
| Generate Calibration Records | Window, dialog | Generation wizard |
| Reject Calibration Record | Window, dialog | Rejection wizard |
| Calibration Record | Report | PDF of a record |
| Calibration Certificate | Report | PDF of a certificate |

## 3.12 Wizards

**Generate Calibration Records** (`ls.calibration.record.generate`). Fields:
due until date, company, optional list of plans. When started from a
selection of plans, those plans are preselected. It creates one record per
active plan that is due at the selected date and that has no open record. It
refuses to run when no plan is due, and when every due plan already has an
open record. It returns the list of the created records.

**Reject Calibration Record** (`ls.calibration.record.reject`). Fields:
record, mandatory reason. It rejects the record, stores the reason and posts
it in the thread.

## Gate

**Phase 3: PASS.** Functional description, navigation, four state machines,
approval workflow, twenty business rules, notifications, scheduled actions,
reports, indicators, search views, actions and wizards are specified and are
traceable to Phase 1.
