# 05 — User Manual

How to run an audit end to end. Menus are under **Quality**.

---

## 1. The shape of the process

```
Programme  ──►  Audit  ──►  Findings  ──►  Report  ──►  Closure
 (annual)      (one          (one per      (concludes    (nothing
                engagement)   departure)    the audit)    left open)
```

Nothing here can be skipped. The software refuses out-of-order transitions
rather than warning about them.

---

## 2. The audit programme

**Quality → Audits → Programmes**

### 2.1 Create

Give it a name, a start and end date, a responsible person, and an objective.
State in the objective **how frequency was decided** — process criticality,
regulatory impact, prior results. An inspector will ask.

### 2.2 Add audits

Create audits and link them to the programme. Each audit's planned date must
fall inside the programme period; the software refuses dates outside it.

### 2.3 Approve, start, close

| Action | Precondition |
|---|---|
| **Approve** | At least one audit exists. An empty programme cannot be approved |
| **Start** | Programme is approved |
| **Close** | **Every** audit has reached closed or cancelled |

The completion rate on the programme form shows closed audits over total.

### 2.4 Cancel

Requires a written justification, stored on the record and posted to the
chatter.

---

## 3. Planning an audit

**Quality → Audits → Audits → New**

### 3.1 Fill in

| Field | Notes |
|---|---|
| Name, Audit Type | |
| Areas | What is being audited. Drives the impartiality check |
| **Objective** | Required. What the audit is to determine |
| **Scope** | Required. Boundaries — shifts, lines, period. **State exclusions explicitly** |
| **Criteria** | Required. What you audit *against*: SOPs, standards, regulations |
| Lead Auditor, Auditors, Auditees | See §3.2 |
| Planned Date | Must fall inside the programme period |

Objective, scope and criteria are required because ISO 13485 clause 8.2.4
requires them to be defined and recorded. They are not optional prose.

### 3.2 If the team is refused

Two rules, both hard:

- **A team member cannot be an auditee.**
- **A team member cannot own an audited area.**

If you are blocked, either the team is wrong or the area ownership is wrong.
Fix the data, not the rule.

### 3.3 Load the checklist

Click **Load Checklist**, pick an approved checklist, confirm.

The question text is **copied** into the audit. A later version of the
template will never change what this audit asked.

To load a different checklist afterwards, tick **Replace Existing**. This
discards assessments already recorded, and it is refused once fieldwork has
started.

---

## 4. Scheduling

Click **Schedule**. The software now checks the team:

| Check | Failure message means |
|---|---|
| Lead auditor holds a qualification flagged Lead Auditor | Register or flag them |
| No team member's qualification has expired | Renew it |
| Every team member's scope covers every audited area | Widen the scope, or change the team. Empty scope = no restriction |

A checklist must be loaded before fieldwork can start.

---

## 5. Fieldwork

Click **Start**. The actual start time is recorded.

**Quality → Audits → Questions**, or the Questions tab on the audit.

For each question record a result:

| Result | Evidence |
|---|---|
| Conform | Optional |
| **Non-Conform** | **Required** |
| **Observation** | **Required** |
| Not Applicable | Optional. Excluded from the conformity rate |
| Pending | Not yet assessed |

Your name and the assessment time are recorded automatically.

### 5.1 Raising a finding from a question

On a non-conform question click **Create Finding**. The form opens pre-filled
and linked back to the question, so the trail from question to finding is
never lost.

### 5.2 Completing

Click **Complete**. Refused while any **mandatory** question is pending.
Optional questions do not block.

The conformity rate is conform ÷ assessed, with Not Applicable excluded.

---

## 6. Findings

**Quality → Findings**

### 6.1 Raising one

| Field | Notes |
|---|---|
| Name | One sentence: what departs from what |
| Area | Must be one of the audit's areas |
| Category | Drives severity, deadline, and whether root cause and CAPA are mandatory |
| Description | The departure |
| Evidence | What you saw. Document numbers, quantities, locations |
| Auditee | Who must answer. **Cannot be the person raising it** |

Click **Issue**. The response due date is computed from the category's
deadline.

### 6.2 Responding — the auditee

Open the finding, click **Submit Response**. One wizard collects everything:

| Field | Required when |
|---|---|
| Root Cause | The category requires it |
| Correction | Always — the immediate fix |
| Corrective Action | Always — what stops recurrence |
| CAPA Reference | The category requires it |
| Action Due Date | Always |

**Correction and corrective action are different things.** Removing the
obsolete document is a correction. Changing the procedure so obsolete
documents get withdrawn is a corrective action. A response with only a
correction is the most common reason a response gets rejected.

### 6.3 Accepting or rejecting — the lead auditor

- **Accept** → the finding moves to Action In Progress.
- **Reject** → back to Issued. The auditee resubmits.

Reject when the root cause is a restatement of the symptom, or when the
corrective action would not prevent recurrence.

### 6.4 Verification and closure

When actions are complete, click **Request Verification**, then record:

| Field | Notes |
|---|---|
| Verification Method | *How* you checked. Re-inspection, record review, re-audit |
| Verification Result | *What you found* |

Click **Verify and Close**.

Two rules:

- Both fields must be filled. "Closed" without documented verification is
  refused.
- **The auditee cannot close their own finding.**

ISO 13485 clause 8.2.4 requires follow-up to include verification of the
actions taken and reporting of verification results. That is what these two
fields are.

---

## 7. The report

**Quality → Reports**

Four separate acts, deliberately attributable to different people.

| Step | Who | Rule |
|---|---|---|
| **Prepare** | Usually the lead auditor | Fill executive summary, conclusion, distribution list |
| **Submit for Review** | Preparer | Refused if the audit is not yet completed |
| **Review** | Someone else | **The preparer cannot review their own report** |
| **Approve** | Someone else | **The preparer cannot approve.** Refused before review |
| **Issue** | Approver | Refused with an empty distribution list |

Once issued the report is **read-only and cannot be deleted**.

Note: under the FDA QMSR, effective February 2026, internal audit reports are
no longer exempt from FDA inspection. Write accordingly.

Print with **Print → Audit Report**. Findings are listed in a register table.

---

## 8. Closing the audit

| Step | Precondition |
|---|---|
| **Follow-up** | A report has been **issued** |
| **Close** | **No finding is still open** |

A closed audit becomes read-only. It can still be archived and followed.

---

## 9. Things that will surprise you

| Situation | Why |
|---|---|
| You cannot edit a closed audit or issued report | Working as designed. Records are immutable once final |
| You cannot edit an approved checklist | Issue a new version instead |
| You cannot delete an issued finding | Cancel it with a justification instead |
| An auditee sees almost nothing | Correct. Auditees see their own findings, audits they are in, and issued reports naming them as recipient |
| A draft report is invisible to the auditee | Correct. Only issued reports are distributed |
| A finding you raised cannot be assigned to you | Correct. That would be auditing your own work |

---

## 10. What arrives automatically

| Notification | When |
|---|---|
| Activity for the lead auditor | An audit is past its planned date and not started. Once, not repeatedly |
| Overdue finding notice | A finding passes its response due date |
| Qualification expiry notice | Weekly, for qualifications expiring within 60 days or already expired |
