# User Manual

Module: `ls_supplier_qualification` · Odoo 19 Community Edition
Audience: Quality officers, assessors, auditors, buyers

---

## 1. What this module is for

It holds the evidence that a supplier was evaluated before you bought from it,
records who approved it and for what, and makes the approval expire so that the
decision is revisited.

One **qualification dossier** exists per supplier per company. Everything else
attaches to it.

## 2. The dossier at a glance

Open **Supplier Qualification → Qualification → Qualification Dossiers**.

The status bar across the top shows where the dossier stands:

| Status | Meaning |
|--------|---------|
| Registered | Created; nothing evaluated yet. |
| Under Assessment | Evaluation in progress. |
| Under Audit | An audit is being conducted. |
| Pending Approval | Prerequisites met; waiting for a manager. |
| Approved | Usable, within its scope, until the validity end date. |
| Conditionally Approved | Usable, with written conditions attached. |
| Suspended | Temporarily not usable. |
| Expired | The validity elapsed. |
| Disqualified | Terminal. |

A blue banner lists what is still missing before the dossier can be submitted
for approval. When the banner disappears, you are ready.

Six smart buttons across the top open the qualified scope, the assessments, the
audits, the performance evaluations, the reviews and the signature log.

## 3. Register a supplier

1. **Qualification Dossiers → New**.
2. Pick the **Supplier** and the **Supplier Category**.
3. The criticality and the requalification interval are proposed by the
   category; change them if this supplier warrants it.
4. Set the **Responsible** — the person who receives the reminders.
5. Save, then press **Start Assessment**.

You cannot open a second live dossier for the same supplier in the same
company. If one exists, requalify it instead.

## 4. Define what the supplier may supply

Open the **Qualified Scope** tab and add one line per material or service.

| Field | What to put in it |
|-------|-------------------|
| Designation | The material or service as your quality department names it. |
| Catalogue Product | Optional. Required if you want the purchase scope check to work. |
| Type | Active substance, excipient, packaging, component, service, and so on. |
| Specification Reference | Your internal specification number. |
| Manufacturing Site | When it differs from the supplier's address. |
| Evaluated Batches | The lots you actually assessed. |
| Scope Valid Until | Optional. Leave empty to follow the dossier validity. |

A line starts *Under Qualification*. A manager presses **Qualify** to move it
to *Qualified*, which stamps the qualification date.

**A dossier with no qualified scope line cannot be approved.** The approval has
to say what it covers.

## 5. Conduct an assessment

**Evaluation → Assessments → New.**

1. Select the **dossier** and the **template**.
2. Press **Load Criteria from Template**. The questions appear with their
   weights.
3. Press **Start**.
4. Score each criterion from 0 to the scale maximum. Record what you looked at
   in **Evidence**.
5. Any criterion scored below the minimum acceptable score **must** carry a
   comment. The system refuses completion otherwise.
6. Tick **Raise Finding** on a criterion you intend to follow up separately.
7. Write the **Conclusion**. It is mandatory.
8. Press **Complete**.

The score, the percentage and the result (Pass, Conditional, Fail) are computed
as you type. The scoring rules shown in the *frozen* group are the ones copied
from the template when the assessment was created; a later change to the
template does not affect this assessment.

**A mandatory criterion scored below the minimum forces a Fail**, whatever the
percentage says.

Completing an assessment writes an entry in the signature log under your name.

## 6. Review an assessment

A second person opens the completed assessment and presses **Review**.

If segregation of duties is enabled, the assessor cannot review their own work;
the system says so by name. A reviewed assessment can no longer be cancelled.

## 7. Conduct an audit

**Evaluation → Audits → New.**

1. Select the dossier, the **audit type**, the **planned date**, the **lead
   auditor** and the **team**. Fill in the **Scope** tab.
2. Set **Audit Basis** to the frameworks you are auditing against.
3. Press **Plan**. An activity is scheduled for the lead auditor.
4. On site, press **Start**, then record findings in the **Findings** tab.
5. Press **Draft Report**, set the **Outcome**, write the **Conclusion**.
6. Press **Issue Report**. The response due date is derived from the company
   lead time. If the supplier contact has an e-mail address, the report
   summary is queued to them.

An audit reporting a critical finding cannot conclude *Acceptable*. Use
*Acceptable with Actions* or *Not Acceptable*.

## 8. Follow a finding to closure

Each finding walks six steps, and each step needs its own information:

| Step | Button | Required first |
|------|--------|----------------|
| Open → Response Received | Register Response | Supplier Response |
| → Action Agreed | Agree Action | Corrective Action and Due Date |
| → Implemented | Mark Implemented | — |
| → Verified | Verify | Verification Method |
| → Closed | Close | — |

Critical and major findings require a documented corrective action before they
can progress past the response stage.

**An audit cannot be closed while any finding is open.** Close the findings
first, then close the audit.

## 9. Submit for approval and get approved

Press **Submit for Approval** on the dossier. The prerequisites are re-checked;
if anything is missing you get the list.

A Supplier Manager then presses **Approve** and completes the dialog:

* **Decision** — Approve, or Approve with Conditions.
* **Requalification interval** and **Valid Until** — the interval is proposed
  from the dossier; the date is derived from it and can be overridden.
* **Conditions** — mandatory for a conditional approval. Say what must be done
  and by when.
* **Justification** — mandatory. It is stored word for word in the signature
  log.
* **Confirm Your Login** — retype your own login.

The dialog states plainly that retyping your login confirms intent and does not
re-authenticate you. That is accurate: full electronic-signature
re-authentication belongs to a separate module that is not yet part of the
suite.

If you assessed or led the audit on this dossier and segregation of duties is
enabled, the approval is refused and the message names you.

## 10. Suspend, reinstate, disqualify

Press **Change Status** on an approved or suspended dossier.

* **Suspend** — stops use immediately. The reason appears as a banner.
* **Reinstate** — returns to Approved, or to Conditionally Approved if
  conditions were attached. Refused if the approval has expired in the
  meantime; requalify instead.
* **Disqualify** — terminal. A new dossier can then be opened for the same
  supplier if the relationship restarts.

All three need a justification and a login confirmation, and all three are
recorded in the signature log.

## 11. Record performance

**Monitoring → Performance Evaluations → New.**

1. Select the dossier and the period.
2. Enter the counters: deliveries received and late, lots inspected and
   rejected, non-conformities, complaints. On-time delivery and quality
   acceptance are computed from them.
3. Enter documentation compliance and responsiveness as percentages.
4. Press **Confirm**.

The overall score is the weighted mean of the four indicators, and the rating
letter follows the company thresholds. A rating of C or D raises a follow-up
activity on the dossier automatically.

Two confirmed evaluations of the same dossier cannot cover overlapping periods.

If `purchase_stock` is installed, **Recompute Delivery Counters** fills the
delivery figures from received purchase order lines. If it is not, the button
says so and you enter the counters by hand.

## 12. Run a periodic review

**Monitoring → Periodic Reviews → New.**

1. Select the dossier and the period reviewed.
2. Press **Collect Evidence**. Assessments, audits and evaluations of that
   period are attached.
3. Write the **Summary**.
4. Choose a **Decision**:

| Decision | Effect on the dossier |
|----------|----------------------|
| Maintain Approval | Extends the validity to the new date, or by the dossier interval. |
| Maintain with Conditions | Same, and writes the conditions; status becomes Conditionally Approved. |
| Requalification Required | Returns the dossier to Under Assessment and clears the approval. |
| Suspend | Suspends the dossier. |
| Disqualify | Disqualifies the supplier. |

5. Press **Complete Review** and confirm.

Conditions are mandatory for a conditional decision; a justification is
mandatory for any adverse decision. A completed review cannot be undone.

## 13. What buyers see

On a purchase order, a banner appears when the supplier has a qualification
issue: no dossier, not approved, expired, or a product outside the qualified
scope.

At confirmation, depending on the company setting, the order goes through, goes
through with the issue logged in the chatter, or is refused with a message
naming the problem.

The contact form shows a green banner with the validity date for an approved
supplier, or an amber banner with the current status otherwise, plus a smart
button to the dossier.

## 14. Reports

| Report | Printed from |
|--------|--------------|
| Supplier Qualification Dossier | The dossier. Consolidates scope, assessments, audits, performance, reviews and the signature log. |
| Supplier Assessment Report | An assessment. Every criterion with its score, evidence and comment. |
| Supplier Audit Report | An audit. Findings, severity summary, outcome and conclusion. |

The dossier report carries a footer stating that it reflects the status
recorded in the system and is not a certificate of compliance with any
regulatory framework. That wording is deliberate; do not remove it.

## 15. Finding things quickly

Useful filters on the dossier list: *Expiring Soon*, *High Risk*, *Open
Critical Findings*, *Pending Approval*, *Audit Due*, *Review Due*.

**Qualification → Expiring Approvals** opens the same list pre-filtered on
approvals reaching their end of validity within the company reminder lead time.

Group by Status, Category, Criticality, Risk Level or Responsible. The graph
and pivot views give counts by category and status, and mean scores by
supplier.

## 16. What the risk level means

A number this module computes to help you prioritise. It is not from any
regulation.

Criticality adds 2 (critical) or 1 (major). A Fail assessment adds 3, a
Conditional one adds 1. A D rating adds 3, a C rating adds 1. Each open
critical finding adds 3; each open major finding adds 1. Four or more is High,
two or three is Medium, below two is Low.
