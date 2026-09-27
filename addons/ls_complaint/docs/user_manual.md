# User Manual

## 1. Register a complaint

Complaints → Complaint Handling → All Complaints → *New*.

| Field | Notes |
|---|---|
| Subject | Short, searchable |
| Reception, Receipt Date | Defaults to now; it cannot be in the future and can only be changed while the complaint is in Received |
| Reception Channel | Choose *Other Channel* only if none fits; a description then becomes mandatory |
| Responsible | Required before the assessment can start |
| Category | Required before the assessment can start; it also sets the target dates |
| Complainant tab | Partner, type and contact details; selecting a partner fills the contact fields |
| Complaint Description | The complainant's own words, not an interpretation |
| Product tab | Untick *Product Related* for a service, delivery or documentation complaint. Otherwise a product is mandatory from the assessment onwards. Enter the lot as a system record when it exists, otherwise as free text |
| Sample Available | Tick when a physical unit was returned, and record its reference |

Saving assigns a reference such as `CMP/2026/00001`. The status is **Received**.

## 2. Assess

1. Set the responsible user and the category.
2. Click **Start Assessment**. The status becomes **Assessment** and the
   assessor and the date are stamped.
3. On the *Assessment* tab, write the assessment summary and tick the potential
   safety and regulatory impact flags when relevant.
4. Set the severity and the complaint type.

If a safety event is reported, create the adverse event now — see section 5 —
because its presence blocks the investigation waiver.

## 3. Investigate

Click **Start Investigation**. The status becomes **Investigation** and a draft
investigation is created automatically, assigned to the responsible user.

Open the investigation and:

1. **Start** it.
2. Record the methodology; *Other Methodology* requires a description.
3. Write the investigation plan and the investigation summary.
4. Set the root cause category and, unless it is *Not Determined*, its
   description.
5. Set the conclusion: confirmed, not confirmed or inconclusive.
6. Assess the impact on other batches, and tick *Other Batches Impacted* when
   applicable.
7. **Complete** it.

A second person, holding the Complaint Reviewer level, then **Approves** it. The
system refuses approval by the investigator of that record. To reject instead,
write the reason on the *Rejection* tab and click **Reject**.

Several investigations may exist on one complaint; all must be finalised, and at
least one approved when the category requires an investigation.

## 4. Waive the investigation

Only when the category does not require an investigation and no adverse event
exists. Write the justification in *Investigation Waiver Justification* on the
Assessment tab, then click **Waive Investigation**. The status moves directly to
Resolution and the justification is posted in the message history.

## 5. Record an adverse event

From the complaint, *Adverse Events* tab or stat button → *New*.

1. Awareness Date — the date the organisation became aware; reporting deadlines
   count from it.
2. Event Date, when known.
3. Event Description, seriousness, outcome.
4. Causality assessment and its rationale.
5. *Subject* tab: pseudonym, age range and sex only. **Never enter a name, an
   address, a file number or any other directly identifying data.**
6. *Regulatory Reporting* tab: decide whether the event is reportable, and write
   the rationale — the regulation and the article applied, and the reasoning. A
   reportable event also requires the competent authority.
7. Click **Assess**.

If the event is reportable, the due date appears once a deadline is configured
on the category, and a to-do activity is created when the deadline is reached.
After submitting the report to the authority, record the acknowledgement
reference and click **Record Submission**.

Finally **Close** the event. A reportable event cannot be closed before its
submission is recorded, and a declared follow-up requires follow-up notes.

## 6. Declare a CAPA

When the investigation shows a systemic cause, click **CAPA Required** and give
the justification. Raise the CAPA in the system used for that purpose, then
enter its identifier in *CAPA Reference*. Without that reference the complaint
cannot move on, and cannot be closed.

## 7. Resolve

Click **Start Resolution**, then add one resolution per action, from the
*Resolutions* tab.

| Field | Notes |
|---|---|
| Resolution Type | Replacement, credit note, refund, repair, product return, customer information, no action justified, field safety notice, recall initiated |
| Description | What will be done |
| Responsible, Due Date | Accountability |
| Completion Evidence | **Mandatory** before *Mark as Done*: the delivery note, the credit note number, the notification reference |

To abandon an action, write the cancellation reason and click **Cancel**.
Completed and cancelled resolutions can no longer be edited.

## 8. Close

Click **Close**. The system first verifies that:

- at least one resolution exists and none is still open;
- every adverse event is closed;
- a CAPA reference exists when a CAPA was declared.

The wizard then asks for the reviewer — who must differ from the responsible
user — the closure summary, the confirmation that the resolution was effective,
and whether the complainant was informed.

**After closure the record is read-only.** A closed complaint is never corrected;
if new information appears, raise a new complaint and refer to the first one.

## 9. Cancel

Only a Complaint Manager can cancel, and only a complaint that is not already
closed. The wizard requires a reason. A cancelled complaint is read-only but can
be returned to Received by a manager.

Cancellation exists so that a duplicate or erroneous entry is never deleted.

## 10. Find and analyse

Filters on the complaint list: My Complaints, Received by Me, Open, Closed,
Cancelled, Overdue, Critical, Regulatory Reporting Required, CAPA Required,
Receipt Date, Archived.

Group by: Status, Severity, Category, Complaint Type, Product, Responsible,
Channel, Receipt Month.

Reporting → Complaint Analysis opens a pivot with products in rows, status in
columns and the average closure duration as the measure. The graph view shows
volume per month and severity.

Overdue complaints appear in red. Critical open complaints appear in orange.

## 11. Print

With a complaint open: *Print* → *Complaint Record*. The PDF contains the
identification, the reception details, the complainant, the product and lot, the
description, the assessment, the investigations with their root causes, the
adverse events with their reporting status, the resolutions, the CAPA fields and
the closure. Attachments are not embedded.

## 12. What the system will refuse, and why

| Refusal | Reason |
|---|---|
| Starting the assessment without a responsible user or a category | The category drives the targets and the investigation requirement |
| Starting the investigation without severity, type and assessment summary | The assessment must be documented before it is acted upon |
| Approving your own investigation | Independence of the review |
| Completing an investigation without a root cause description | A determined cause must be stated |
| Marking a resolution done without evidence | An action without evidence is not an action |
| Closing with an open resolution or adverse event | Obligations remain open |
| Closing with a reviewer equal to the responsible user | Independence of the review |
| Modifying a closed complaint | The record is final |
| Deleting a complaint past Received | Quality records are not deleted; cancel instead |
