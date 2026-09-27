# User Manual

Module: `ls_recall` — Recall and Field Action Management

---

## 1. What this module does, in one paragraph

It holds the record of a field action from the moment the decision is
taken to the moment the action is closed: the decision and its basis,
who received the affected lots, what was sent to them, what they said,
how much came back, and what was reported to whom. It does not send
anything, does not move stock and does not decide anything for you.

## 2. Choosing the action type

| Type | Use when |
|------|----------|
| Recall | Product already distributed must be removed or corrected |
| Market Withdrawal | Product is removed for a reason that is not a violation attracting legal action |
| Stock Recovery | The product never left your direct control |
| Field Safety Corrective Action | A medical device action under EU MDR |
| Mock Recall | A rehearsal. Excluded from metrics; resets the plan's next-due date on closure. |

## 3. Walkthrough of a recall

### Step 1 — Open the record

**Recalls → Field Actions → Initiate Recall.**

Select the approved plan; the coordinator and effectiveness level are
inherited. Choose the product, tick the affected lots, state the reason
in language a consignee will understand, and set the decision date.

Leave "Trace distribution immediately" ticked unless the affected lots
are still being determined.

The record opens in **Planned**.

### Step 2 — Complete the decision and initiate

Before the record will leave Planned, a real action needs:

* a classification other than "Not Classified",
* a depth (wholesale, retail, or consumer/user),
* a health hazard evaluation,
* a reason,
* at least one lot.

Press **Initiate**. The record moves to **Initiated** and stamps the
time.

> The classification field carries the three definitions from 21 CFR
> 7.3(m) in its help text. Under 21 CFR 7.41 the classification is
> assigned by the competent authority; what you record here is your own
> assessment and, once you have it, what the authority told you.

### Step 3 — Trace distribution

Press **Trace Distribution and Start**.

The system scans completed deliveries of the affected lots to customer
locations and creates one Consignees line per consignee and lot, with
the quantity shipped and a link to the source transfers.

Check the chatter. If a quantity could not be attributed to a consignee
— usually a transfer with no partner — it is stated there, and you must
add that consignee by hand.

**If product was distributed outside Odoo, tracing will not find it.**
Add those consignees manually on the Consignees tab. Re-tracing later
will not remove them.

The record moves to **In Progress**.

### Step 4 — Notify

Open the Communications tab and create a Recall Notice.

Enter the subject and body, and select the recipients. Then open the
**Content Confirmation** tab and confirm each of the five elements:

1. identifies the product, size, lot or serial numbers,
2. states the reason and the hazard,
3. gives instructions on what to do with the product,
4. requests a response,
5. gives a contact point.

These correspond to the elements listed in 21 CFR 7.49(a). **The system
cannot read your text.** Ticking these boxes is your statement that you
checked it; the tick is recorded against your name and the time, which
is what makes the check auditable.

Tick **Urgent** for a class I or class II recall.

Press **Approve Text**, then **Record as Sent** once the notice has
actually gone out through your normal channel. This marks the
recipients' lines as notified.

Notify the competent authority with a separate communication of type
**Authority Notification**. Recording it as sent sets the notification
flag and date on the recall itself.

**A sent communication can no longer be reworded, cancelled or deleted.**
Get it right before you press the button.

Press **Move to Communication**.

### Step 5 — Effectiveness checks

Press **Plan Effectiveness Checks**. One check is created per consignee.

The number you must perform is shown on the Strategy tab as
**Effectiveness Required Count**, derived from the level:

| Level | Consignees to contact |
|-------|----------------------|
| A | 100% |
| B | Your entered percentage, strictly between 10% and 100% |
| C | 10% |
| D | 2% |
| E | None |

Fractions round up: 2% of 10 consignees is one consignee, not none.

For each check, record the method, the outcome, and what was said, then
press **Record as Performed**. A check cannot be marked performed
without an outcome.

If you cannot reach a consignee, press **Escalate and Retry**. The check
is marked escalated and the next attempt is created automatically with
the attempt number incremented, so the file shows how hard you tried.

Press **Move to Effectiveness Check** once enough checks are planned.

### Step 6 — Reconcile

On the Consignees tab, for each line record what happened to the goods:

| Column | Meaning |
|--------|---------|
| Quantity Returned | Physically came back to you |
| Quantity Destroyed On Site | Destroyed by the consignee under an agreed procedure, with evidence retained |
| Quantity Not Recoverable | The consignee has confirmed it cannot be returned — already administered or used |

The footer shows distributed, accounted, outstanding and the
reconciliation rate.

A line turns **red** if you have accounted for more than was shipped.
That is a data problem, not an achievement, and it blocks closure until
resolved.

### Step 7 — Report

Create a report on the Reports tab, type **Final**.

Write the situation summary, the actions taken, the product disposition
and the conclusion. Press **Review**. A second person presses
**Approve** — the system refuses to let the reviewer approve their own
review.

**Approval freezes the figures.** The report keeps the numbers as they
stood at that moment even though the recall keeps moving. This is why a
report submitted in March still says what it said in March.

Record the submission against the named recipients.

### Step 8 — Close

Press **Close Recall**. The wizard lists every check with PASS or FAIL:

| Check | Applies to |
|-------|-----------|
| All consignees notified | All |
| No quantity discrepancy | All |
| Effectiveness checks performed ≥ required | All |
| Reconciliation rate ≥ target | Real actions |
| An approved final report exists | Real actions |
| Competent authority notified | Real class I and II recalls |

Resolve the failures and try again. If a check genuinely cannot be met —
a consignee has ceased trading, product was consumed — a **Manager** may
tick the override and must write the justification. The justification is
stored on the recall and posted to the chatter together with a note that
the checks failed. It will be read at your next inspection; write it as
though it will be.

Enter the justification and confirm. **The record becomes read-only.**

## 4. Cancelling

If the decision is reversed — the defect is not confirmed on retest —
press **Cancel** and state why. The record stays. Do not delete it: a
decision that was genuinely taken is part of the history, and after
initiation the system will refuse to delete it anyway.

## 5. Rehearsals

Run a mock recall exactly like a real one. It is exempt from the hazard
evaluation gate at initiation, and from the reconciliation, final report
and authority checks at closure. Closing it resets the plan's next-due
date.

## 6. Lot warnings

A lot named in an open real field action shows an **Under Recall**
ribbon on its form. This is visible to warehouse staff whether or not
they hold a recall role, deliberately: the person picking the goods is
the one who most needs the warning.

The module warns. It does not block picking. Blocking is your warehouse
procedure.

## 7. Things the module will not let you do, and why

| Refusal | Reason |
|---------|--------|
| Initiate without a hazard evaluation | The evaluation drives the strategy that follows |
| Change the classification after initiation | It is a change-controlled decision; cancel and reopen if it was wrong |
| Approve a notice with an unconfirmed element | The recipient needs all five elements to act |
| Reword a sent notice | It is evidence of what was issued |
| Mark a check performed without an outcome | The outcome is the point of the check |
| Approve your own review | Segregation of duties |
| Edit an approved report | The figures were frozen deliberately |
| Delete an initiated recall | Cancel it instead, with a reason |
| Close with failed checks (as a coordinator) | Overrides are a manager decision |

## 8. What this module does not claim

The **Attestation** field on the closure wizard is a free text field.
It is **not** an electronic signature under 21 CFR Part 11. Use it to
record the reference of a signed record held elsewhere. If you need
compliant electronic signatures, they must be implemented at suite level.
