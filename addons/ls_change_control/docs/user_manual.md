# User Manual

Module: `ls_change_control`

## 1. Overview of the process

```
Draft -> Under Review -> Impact Assessment -> Approved -> Implementation -> Verified -> Closed
                    \                  /
                     -> Rejected <----
   Draft, Under Review, Impact Assessment, Approved -> Cancelled
```

At any moment, the yellow banner at the top of a change request lists exactly
what is outstanding before the next step. Read it first when a button you
expect is not there.

## 2. Requester

### 2.1 Raise a change request

Change Control, Change Requests, New.

| Field | What to write |
|-------|--------------|
| Title | A short sentence identifying the change |
| Change Category | The category matching the nature of the change. It determines who will assess and who will approve |
| Change Type | Permanent, or Temporary with a mandatory end date |
| Current Situation | The situation **before** the change, factually |
| Proposed Change | The situation **after** the change, factually |
| Justification | Why the change is required |
| Requested Target Date | When you would like the change to be effective. It is indicative |
| Impact tab | Your initial declaration: GMP impact, product quality impact, regulatory impact, and whether revalidation, training, document update or customer notification are expected |

Save. The request receives a reference such as `CC/2026/00001` and stays in
Draft, where you can still modify everything.

### 2.2 Submit

Submit for Review.

**From this moment the description of the change is frozen.** Title, category,
change type, current situation, proposed change and justification can no
longer be modified, by anybody, including the quality unit. If the change
itself must be modified, a new request is required. This is intentional: it is
what makes the record trustworthy.

After submission, only a change control manager may modify the request.

### 2.3 Follow your requests

Change Control, Change Requests, My Change Requests. You receive a
notification when your change is approved or rejected, and you follow the
chatter of the request for every event.

## 3. Change control manager

### 3.1 Review a submitted request

Open the request in Under Review and complete:

| Field | Why |
|-------|-----|
| Change Control Manager | Who drives this request. Mandatory |
| Classification | Minor, Major or Critical |
| Impact Areas | The areas that must be assessed. Pre-filled from the category, adjust as needed |
| Approvals tab | Assign an approver to every line without one |

If the request is incomplete, use Return to Draft, which sends it back to the
requester. This is possible only in Under Review.

### 3.2 Open the assessment

Start Impact Assessment. The module then creates:

* one impact assessment per selected impact area;
* one approval per line of the approval template of the category.

Each approver receives a notification and a to-do activity.

The button refuses to proceed while the banner lists an outstanding item: no
manager assigned, no impact area, no approval, or an approval without an
approver.

### 3.3 Assign the assessors

In the Impact tab, set the Assessor of each assessment. An assessor must hold
at least the Requester group.

### 3.4 Plan the implementation

Once the request is Approved, open the Implementation tab and add the actions.
Each action requires a name, a type, a responsible person and a planned date.

Then Start Implementation. The button refuses to proceed if no action has been
planned.

### 3.5 Plan the verification

In the Verification tab, add at least one verification when the category
requires it. **Write the acceptance criteria before the verification is
performed**: they define in advance what will count as an effective change.

### 3.6 Declare verified, then close

Declare Verified once no action is open and the verification concludes that
the change is effective. Then Close, and write the closure statement, which is
the conclusion of the change and is retained in the record.

### 3.7 Reject or cancel

Reject is available in Under Review and Impact Assessment. Cancel is available
until the implementation starts. Both require a justification, and both are
final: a rejected or cancelled request is never reopened.

## 4. Subject matter expert: perform an assessment

Change Control, Change Requests, Impact Assessments, filter My Assessments.

Open your assessment and complete:

| Field | Rule |
|-------|------|
| Impact Level | No Impact, Low, Medium or High |
| Assessment | Mandatory. Explain **why** the change does or does not impact your area |
| Actions Required | Mandatory as soon as the impact is not No Impact |

Then Complete Assessment.

**A completed assessment can never be modified or deleted.** Re-read before
completing. Only you, as the assigned assessor, or a change control manager,
may complete it.

## 5. Approver: record a decision

Change Control, Approvals, My Approvals.

Read the request and, above all, the impact assessments, before deciding.

| Decision | Procedure |
|----------|-----------|
| Approve | Click Approve and confirm |
| Reject | Write the Comment first, save, then click Reject and confirm |

What is recorded with your decision: your identity, the date and time in UTC,
and the meaning of the signature.

**A recorded decision can never be modified or deleted.** Only you may record
your own decision: a colleague or a manager cannot record it for you.

The request becomes Approved automatically when the last mandatory approval is
granted. A single rejection rejects the whole request.

If your approval has been pending longer than the delay configured for your
site, you receive a daily reminder.

## 6. Responsible for an implementation action

Change Control, Execution, Implementation Actions, filter My Actions.

| Step | Button |
|------|--------|
| Begin working on the action | Start |
| Complete the action | Fill the Evidence Reference, then Mark as Done |

**The evidence reference is mandatory.** Write what allows a third party to
find the proof of completion, for example `SOP-PROD-014 rev. 5, effective
2026-09-01`, or `Qualification report QR-2026-018`.

A closed action can no longer be modified. Only a change control manager may
cancel an action, and only after a cancellation reason has been recorded.

When every action is Done or Cancelled, the actual implementation date is
computed automatically from the completion dates, and the planned verification
date follows.

## 7. Verifier: conclude on effectiveness

Change Control, Execution, Effectiveness Verifications, filter My
Verifications.

Read the acceptance criteria, perform the verification, then write the
Conclusion, which is mandatory.

| Outcome | Button | Consequence |
|---------|--------|-------------|
| The criteria are met | Conclude: Effective | The change may be declared verified |
| The criteria are not met | Tick Follow-up Required, fill the Follow-up Reference, then Conclude: Not Effective | The change cannot be declared verified until the situation is resolved |

A completed verification can never be modified or deleted.

## 8. Print the change control record

Open a request, Print, Change Control Record.

The PDF contains every section: description, impact declaration, assessments,
approvals with the signature metadata, implementation actions with their
evidence, verifications with their criteria and conclusions, and the outcome.

The footer records who printed it and when, and states that the printed
document is uncontrolled: the controlled record is the electronic record.

## 9. Search and analysis

Useful filters on the change requests: Open, Implementation Late, Verification
Due, GMP Impact, Regulatory Action Required, Critical.

Useful groupings: Status, Category, Classification, Change Control Manager,
Regulatory Impact.

Change Control, Reporting, Change Request Analysis opens the graph and pivot
views for reporting on the process.

## 10. Frequently encountered situations

| Situation | Explanation |
|-----------|-------------|
| I cannot modify my request any more | It has been submitted. The description of a change is frozen at submission. Ask a change control manager, or raise a new request |
| The Start Impact Assessment button does nothing | Read the yellow banner: an item is outstanding, most often an approval without an approver |
| I cannot approve | Either you are not the assigned approver, or the request is not in Impact Assessment |
| I cannot close my action | The evidence reference is empty |
| Declare Verified is refused | An action is still open, or no verification is completed, or a verification concluded Not Effective |
| The request stays in Impact Assessment although everything is approved | An assessment of a mandatory area is not completed |
| I made a mistake in a completed assessment | It cannot be corrected. Report it to the change control manager, who will record the correction in the chatter of the request |
