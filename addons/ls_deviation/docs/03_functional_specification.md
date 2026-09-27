# 03 — Functional Specification

**Phase gate: PASS**

## 3.1 Navigation

```
Quality Management
├── Deviations
│   ├── All Deviations          (default filter: Open)
│   ├── My Deviations           (default filters: Mine + Open)
│   ├── Investigations          (Investigator+)
│   ├── Product Dispositions    (Investigator+)
│   └── Immediate Actions
├── Reporting
│   ├── Deviation Analysis      (pivot, graph, list)
│   └── Transition Log          (read-only)
└── Configuration               (Manager only)
    ├── Deviation Types
    ├── Deviation Categories
    ├── Root Cause Analysis Methods
    └── Tags
```

Closure targets are configured in **Settings → Deviation Management**.

## 3.2 State machine

| From | To | Trigger | Guard |
|---|---|---|---|
| — | Reported | Record created | — |
| Reported | Assessed | Complete Assessment | Severity set; impact assessment narrative present; investigator assigned |
| Assessed | Investigation | Start Investigation | At least one investigation record exists |
| Investigation | Disposition | Proceed to Disposition | All investigations completed; extension rationale present; a disposition exists if the deviation has an assessed impact |
| Disposition | CAPA Required | Require CAPA | CAPA decision rationale present |
| Disposition | Closed | Close Deviation (wizard) | Conclusions, follow-up, CAPA rationale; no open immediate actions; no draft dispositions |
| CAPA Required | Closed | Close Deviation (wizard) | As above, plus a CAPA reference when CAPA is required |
| Assessed | Reported | Send Back | Reason mandatory |
| Investigation | Assessed | Send Back | Reason mandatory |
| Disposition | Investigation | Send Back | Reason mandatory |
| CAPA Required | Disposition | Send Back | Reason mandatory |
| any non-terminal | Cancelled | Cancel (wizard) | Reason mandatory |
| Closed / Cancelled | — | none | Terminal |

Any transition not in this table raises a `UserError` naming the source and
target states.

## 3.3 Business rules

| # | Rule |
|---|---|
| FR-1 | Reference is generated from the `ls.deviation` sequence, prefix `DEV/<year>/`, padded to 5 digits, unique per company |
| FR-2 | Occurrence date ≤ detection date ≤ recording date |
| FR-3 | A planned deviation requires a justification |
| FR-4 | An affected quantity requires a product |
| FR-5 | Affected quantity ≥ 0 (database check constraint) |
| FR-6 | Disposition quantity > 0 (database check constraint) |
| FR-7 | A disposition lot, where given, must belong to the dispositioned product |
| FR-8 | An investigation cannot complete without both findings and a root cause |
| FR-9 | An investigation completion date cannot precede its start date |
| FR-10 | An immediate action cannot be marked done without completion evidence |
| FR-11 | Only a Manager may approve or reject a disposition |
| FR-12 | Only a draft disposition may be approved |
| FR-13 | Deletion is blocked once the deviation leaves the Reported state |
| FR-14 | A terminal record is not writable except by a Manager |
| FR-15 | Duplicating a deviation resets state to Reported and clears the reference |
| FR-16 | The target closure date may only increase, and only through the extension wizard |
| FR-17 | The transition log rejects write and unlink for every user |
| FR-18 | `has_impact` is true when any of the five impact flags is set |
| FR-19 | `is_overdue` is true when an open record's target closure date has passed |
| FR-20 | Multi-company isolation is enforced by global record rules on all six transactional models |

## 3.4 Notifications and scheduled actions

**Scheduled action:** "Deviation: notify overdue records", daily, calls
`ls.deviation._cron_notify_overdue()`. It selects open deviations with a
target closure date in the past, subscribes the assigned investigator and QA
reviewer as followers, and sends the overdue mail template. It returns the
count of records processed so the behaviour is assertable from tests.

**Tracked fields** posting to the chatter: title, description, justification,
type, category, severity, planned flag, all three dates, target closure date,
closure date, reporter, owner, QA reviewer, department, product, manufacturing
order, equipment, location, all five impact flags, CAPA flag, CAPA reference
and state.

**Message subtypes:** "Deviation Closed" and "Deviation Cancelled", routed by
`_track_subtype` so followers can subscribe to outcomes without receiving
every intermediate transition.

## 3.5 Reports, dashboards and KPIs

**PDF report** (`Deviation Report`, bound to the model as a print action)
contains identification, classification, chronology, ownership, description,
justification, subject, impact assessment, immediate actions, investigations
with findings and root cause, the 211.192 extension section, dispositions,
conclusions, follow-up, CAPA decision and the full transition log. It closes
with a statement that it is not an electronic signature record.

**Analysis views:** pivot (category × severity, measuring days open) and graph
(bar, category × severity), plus calendar and activity views.

**KPIs available without customisation:** open deviation count, overdue count,
days open per deviation, deviations by category, by severity, by type, by
department, by investigator, by detection month, count with patient safety
impact, count requiring CAPA.

## 3.6 Search, filters and grouping

Searchable: reference, title, description, product, affected lots,
manufacturing order, owner, reporter, type, category.

Filters: My Deviations, Awaiting My QA Review, Open, Closed, Overdue,
Critical, Major, Minor, Patient Safety Impact, CAPA Required, Detected This
Month.

Group by: status, severity, type, category, department, investigator,
product, detection month.

## 3.7 Wizards

| Wizard | Purpose | Mandatory input |
|---|---|---|
| Close Deviation | Records closure evidence and transitions to Closed | Conclusions, follow-up, CAPA decision rationale, QA reviewer; CAPA reference when CAPA required |
| Cancel or Send Back | Cancels, or returns the record one step | Reason |
| Extend Target Closure Date | Moves the target date later | New date, justification |
