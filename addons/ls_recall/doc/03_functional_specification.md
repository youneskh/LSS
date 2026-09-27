# Phase 3 — Functional Specification

Module: `ls_recall` — Recall and Field Action Management

---

## 1. Navigation

Root menu **Recalls** (visible to the viewer group and above).

```
Recalls
├── Field Actions
│   ├── Recalls                 → open, real actions (default filters)
│   ├── All Field Actions       → unfiltered, includes rehearsals
│   └── Initiate Recall         → wizard (coordinator and above)
├── Execution
│   ├── Consignees
│   ├── Communications
│   ├── Effectiveness Checks
│   └── Reports
└── Configuration               (manager only)
    └── Recall Plans
```

## 2. Recall plan

### 2.1 State machine

```
draft ──submit──▶ under_review ──approve──▶ approved ──obsolete──▶ obsolete
  ▲                     │                       │
  └───────reject────────┘                       └──new revision──▶ (new draft, v+1)
```

### 2.2 Business rules

| # | Rule |
|---|------|
| P1 | The reference is allocated from sequence `ls.recall.plan` and is unique per company. |
| P2 | Approval is refused unless a procedure is documented. |
| P3 | Approval is refused unless a deputy coordinator is named. |
| P4 | An approved or obsolete plan cannot have its content edited; only workflow and bookkeeping fields remain writable. |
| P5 | A new revision copies the plan at version n+1 in draft and sets version n to obsolete and inactive. The reference is retained across versions. |
| P6 | A plan restricted to products or categories must list at least one. |
| P7 | Only a draft plan can be deleted. |
| P8 | The next rehearsal date is the later of the last closed mock recall or the approval date, plus the interval. |

## 3. Field action

### 3.1 State machine

```
planned ─▶ initiated ─▶ in_progress ─▶ communication ─▶ effectiveness_check ─▶ closed
   ▲            │
   └── reset ───┘ (only while no related record exists)

any state except closed/cancelled ──cancel──▶ cancelled
```

### 3.2 Transition gates

| Transition | Gate |
|------------|------|
| planned → initiated | A reason is stated; at least one lot is named. For a real action additionally: a classification other than "not classified", a depth, and a health hazard evaluation. |
| initiated → in_progress | Distribution tracing runs and produces at least one consignee line. |
| in_progress → communication | At least one communication is in state sent or acknowledged. |
| communication → effectiveness_check | The number of non-cancelled effectiveness checks is at least the number required by the level. |
| effectiveness_check → closed | Via the closure wizard only. See §3.4. |
| initiated → planned | No consignee line, communication or effectiveness check exists. |
| any → cancelled | A justification is entered. |

### 3.3 Derived quantities

| Field | Definition |
|-------|------------|
| `qty_distributed` | Σ line `qty_shipped` |
| `qty_accounted` | Σ (`qty_returned` + `qty_destroyed` + `qty_not_recovered`) |
| `qty_outstanding` | `qty_distributed` − `qty_accounted` |
| `reconciliation_rate` | `qty_accounted` ÷ `qty_distributed` × 100, or 0 when nothing was distributed |
| `consignee_count` | Count of **distinct** partners across lines |
| `response_rate` | Distinct partners with a response ÷ distinct partners × 100 |
| `effectiveness_required_count` | Consignees × level coverage ÷ 100, **rounded up**; 0 for level E |
| `effectiveness_coverage` | Distinct partners with a performed check ÷ required × 100 |
| `initiation_delay_hours` | Earliest communication `sent_date` − `decision_date`, in hours |

Worked example of the rounding: 10 consignees at level D (2%) gives
10 × 2 ÷ 100 = 0.2, rounded up to **1**. Level C (10%) gives 1.0 exactly,
so **1**. Level A gives **10**. This is why the module rounds up: a
literal 0.2 consignees would otherwise mean no check at all.

### 3.4 Closure checks

Evaluated together and displayed before anything is written.

| # | Check | Applies to |
|---|-------|-----------|
| C1 | Every consignee line is marked notified. | All actions |
| C2 | No line is in discrepancy status. | All actions |
| C3 | Performed effectiveness checks ≥ required. | All actions |
| C4 | Reconciliation rate ≥ the plan's target, or 100% when no plan is linked. | Real actions only |
| C5 | An approved or submitted final report exists. | Real actions only |
| C6 | The competent authority has been notified. | Real recalls classified class I or class II only |

A failed check may be overridden only by a member of the manager group,
and only with a justification, which is written to the recall and to the
chatter together with a note that the checks failed.

## 4. Consignee line

| # | Rule |
|---|------|
| L1 | One line per (recall, consignee, lot). Enforced by a unique constraint. |
| L2 | Quantities cannot be negative. Enforced by a check constraint. |
| L3 | Status is derived: discrepancy → reconciled → responded → notified → pending, evaluated in that order. |
| L4 | Editing a quantity writes a before/after entry to the recall chatter. |
| L5 | An on-change warning appears as soon as the accounted quantity exceeds the shipped quantity. |
| L6 | Lines of a closed or cancelled recall cannot be edited. |

Float comparison uses a fixed tolerance of 1e-6 rather than exact
equality.

## 5. Communication

### 5.1 State machine

```
draft ──approve──▶ approved ──send──▶ sent ──acknowledge──▶ acknowledged
  │                    │
  └────cancel──────────┴──▶ cancelled        (cancellation impossible once sent)
```

### 5.2 Business rules

| # | Rule |
|---|------|
| M1 | Reference allocated from sequence `ls.recall.communication`. |
| M2 | Every type except public warning requires at least one recipient. |
| M3 | A recall notice or field safety notice requires all five content confirmations before approval and before sending. Other types do not. |
| M4 | Approval requires a non-empty body. |
| M5 | Sending marks the recipients' consignee lines as notified and stamps the notification date. |
| M6 | Sending an authority notification sets `authority_notified` and its date on the recall. |
| M7 | A sent communication cannot be reworded, cancelled or deleted. Only the acknowledgement fields remain writable. |

## 6. Effectiveness check

| # | Rule |
|---|------|
| E1 | Generation creates one planned check per consignee line not already covered; running it again adds nothing. |
| E2 | The consignee defaults from the linked line. |
| E3 | A check cannot be recorded as performed without an outcome. |
| E4 | Performing stamps the user and the server time, and marks the consignee line as having responded. |
| E5 | Escalating sets the check to escalated and creates the next attempt in planned state with the attempt number incremented. |
| E6 | Outcomes "action taken" and "product not held" count as successful; "no action taken" and "not reachable" do not. |
| E7 | A check must belong to the same recall as its consignee line. |

## 7. Report

### 7.1 State machine

```
draft ──review──▶ reviewed ──approve──▶ approved ──submit──▶ submitted
```

| # | Rule |
|---|------|
| T1 | Reference allocated from sequence `ls.recall.report`. |
| T2 | Review requires a situation summary. |
| T3 | The approver must be a different user from the reviewer. |
| T4 | Approval copies twelve figures from the recall into snapshot fields and stamps `snapshot_taken_on`. |
| T5 | Once approved, content is frozen; only submission fields remain writable. |
| T6 | Submission requires at least one named recipient. |
| T7 | At most one final report per recall. |
| T8 | The reporting period must not end before it starts. |

## 8. Notifications and scheduled actions

| Scheduled action | Frequency | Behaviour |
|------------------|-----------|-----------|
| Recall: monitor open field actions | Daily | Raises one activity on a real, open action that is past its target completion date, or that is initiated or in progress with no communication sent. Skips actions that already carry an open activity. Changes no state. |
| Recall: monitor mock recall due dates | Weekly | Raises one activity on an approved plan whose next rehearsal date has passed. Skips plans that already carry an open activity. |

Neither scheduled action changes a workflow state. Every transition in
the record is attributable to a named person by design.

## 9. Reports (printable)

| Document | Model | Content |
|----------|-------|---------|
| Recall Notice | `ls.recall.communication` | Urgency banner when marked urgent; product, lots, action type, classification and depth; reason; the user's message; a response request; issue metadata. Section order follows 21 CFR 7.49(a). |
| Recall Report | `ls.recall.report` | Subject, reconciliation table, consignee and check table, the four narrative sections, and the preparer/reviewer/approver block. Prints frozen figures once approved and live figures while draft, and says which it is showing. |

## 10. Search, filters and grouping

**Field actions.** Search on reference, product, lot, coordinator and
defect reference. Filters: open, closed, class I, class II, real actions,
rehearsals, past target date, authority not notified, my recalls. Group
by status, classification, action type, product, coordinator, decision
month. Graph (bar) and pivot views on classification × state with
distributed and accounted quantities as measures.

**Consignees.** Filters: not notified, no response, quantity
outstanding, discrepancy. Group by recall, consignee, status.

**Communications.** Filters: not yet sent, sent, authority
notifications. Group by recall, type, status.

**Effectiveness checks.** Filters: to do, performed, not reachable.
Group by recall, outcome, method.

**Reports.** Filters: final reports, not yet approved. Group by recall,
type, status.

**Plans.** Filters: approved, not yet approved, rehearsal due, archived.
Group by status, coordinator.

## 11. Wizards

| Wizard | Purpose |
|--------|---------|
| Initiate Recall | Opens a field action in one screen, inheriting the coordinator and effectiveness level from the selected approved plan, and optionally tracing distribution immediately. |
| Close Recall | Serves both closure and cancellation. In closure mode it renders the check results as a pass/fail list, offers a manager-only override, and requires a justification. In cancellation mode it requires only the justification. |

## 12. Lot integration

A lot named in an open real field action shows an "Under Recall" ribbon
and a smart button on its form. The ribbon is visible to any user who
can see the lot, including warehouse staff with no recall role; the
smart button leading to the recall records is restricted to the recall
roles. The rationale is in `05_architecture_review.md` §4.
