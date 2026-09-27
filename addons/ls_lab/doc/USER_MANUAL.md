# USER MANUAL — `ls_lab`

For laboratory analysts, reviewers and managers.

---

## 1. The principle behind the design

Two rules explain most of what you will encounter:

1. **You record values; the system records verdicts.** Whether a result conforms
   is computed from the approved specification. There is no field in which you
   can type "pass". This is deliberate.

2. **Approved records are frozen, never edited.** Methods, specifications and
   certificates are superseded by new versions. Nothing that has been approved
   can be quietly changed afterwards.

---

## 2. Registering a sample

Laboratory → Samples → Sample Register → New.

| Field | Notes |
|-------|-------|
| Product | Required. |
| Lot / Serial | The stock lot, when the batch is tracked in this database. |
| Batch Reference | Free text, for batches not tracked as stock lots. |
| Sample Type | Raw material, in process, finished product, stability, retain, water, cleaning verification, packaging. |
| Specification | Required. Only **approved** specifications are selectable. |
| Quantity, Unit | Amount received. |
| Sampling / Receipt data | Dates, who sampled, who received, sampling point. |
| Due Date | Drives the overdue notice. |
| Priority | Normal or urgent. |

On save the sample receives a reference and **one result line is created for each
line of the specification**. You cannot shorten this list.

If the product has no approved specification, register is blocked. Create and
approve the specification first.

---

## 3. Recording results

The sample must be in **Testing** before results can be entered:

Received → **Start** → In Progress → **Start Testing** → Testing.

For each result line, open it and record the value in the field matching the
method's result type:

- **Numeric result** for numeric methods
- **Text result** for text methods
- **Pass / Fail result** for pass/fail methods

Also record the test date and, where applicable, the instrument reference. Then
press **Record Result**.

On recording, the system evaluates the value against the acceptance criterion and
sets the evaluation to Conforms, Out Of Specification, or Informative.

**If the result is out of specification, an investigation is created
automatically** and linked to the result. You do not need to raise it.

### Out of trend

If you determine that a result is out of trend, tick **Out Of Trend** and record
the **justification**. The justification is mandatory.

The system performs **no statistical trend analysis**. The determination is yours,
made outside the system; the field records it and the basis for it. Flagging a
result out of trend also raises an investigation.

---

## 4. Reviewing results

Second-person review is required and enforced.

1. Open the result and press **Review**.
2. You cannot review a result you recorded. The system refuses it.
3. Once reviewed, the recorded values are locked. A correction requires a retest
   under an investigation.

When every mandatory result carries a value, press **Confirm Results Recorded**
on the sample. When every mandatory result is reviewed, press **Review** on the
sample.

You cannot review a sample if you recorded any of its results.

---

## 5. Approving a sample

A Laboratory Manager presses **Approve** on a reviewed sample. This opens the
signature-intent confirmation.

Approval is refused when:

- you are the user who reviewed the sample; or
- any investigation on the sample is still open.

> **Signature limitation.** Confirming records your user identity, the timestamp
> and the meaning selected. It does **not** re-authenticate you and is **not** an
> FDA 21 CFR Part 11 electronic signature. Your organisation's procedures
> determine what weight this record carries.

---

## 6. Investigating an OOS or OOT

Laboratory → Specifications → OOS / OOT.

### Phase I — the laboratory investigation

Press **Start Phase I**, then work through the assessment checklist: analyst
interviewed, calculation verified, instrument performance verified, standards and
reagents verified, sample integrity verified, method adherence verified.

Record the **findings** and select the **Phase I conclusion**:

- **Assignable Laboratory Cause Identified** — the laboratory explains the result.
- **No Assignable Laboratory Cause** — it does not.

Press **Complete Phase I**. Both findings and a conclusion are required.

### After Phase I

| Phase I conclusion | Next step |
|--------------------|-----------|
| Assignable laboratory cause | **Conclude** directly. |
| No assignable laboratory cause | **Start Phase II**. |

Phase II is unavailable when a laboratory cause was found, and conclusion is
unavailable when one was not. The path is not optional.

### Phase II — beyond the laboratory

Record the findings, the manufacturing review and the root cause, then press
**Complete Phase II**. Findings are required.

### Retest and resample

A retest result **cannot be recorded until a retest is authorised**.

1. Write the **retest justification** — the scientific basis for retesting.
2. A Laboratory Manager presses **Authorise Retest**.
3. The authorising user and timestamp are recorded.

Resampling follows the same pattern. Attempting to create a retest result without
authorisation is refused.

### Closing

Record the **final conclusion** and the **product disposition** (reject, release,
remain in quarantine, further investigation), with the justification, and a CAPA
reference if one was raised. Then press **Close**.

Closure is refused when either the conclusion or the disposition is missing, or
when you are the investigator. A different user from the quality unit must close
it.

The module records the disposition decision and who made it. It does not make it.

---

## 7. Stability studies

Laboratory → Stability → Stability Studies.

Time point due dates are derived from the study start date plus the interval in
months. Changing the start date moves every due date.

To pull a sample: open the time point and press **Create Sample**, or use the
button in the time point list. Confirm the specification, storage condition,
quantity and pull date. A stability sample is created, linked to the time point,
and its result lines are generated.

The time point then moves Planned → Sampled → Tested → Completed.

If a pull is missed, record **notes** explaining why, then press **Mark Missed**.
Notes are mandatory.

---

## 8. Certificates of Analysis

Laboratory → Reports → Certificates of Analysis.

1. Create a certificate against an **approved** sample.
2. Review the reported results — these are the specification lines flagged
   **Show On CoA**.
3. Add a customer and remarks if required.
4. Press **Issue Certificate** and confirm the signature intent.
5. Print the PDF from the Print menu.

An issued certificate is frozen. To correct one, record a **revision reason** and
press **Create Revision**: the original becomes Superseded and a new draft version
is created.

---

## 9. Cancelling a sample

Press **Cancel** and record the reason. The reason is mandatory and is stored
permanently with your user name. The sample and its results are retained; nothing
is deleted.

A sample that has been approved or reported cannot be cancelled.

---

## 10. Why an action is unavailable

| Message | Reason |
|---------|--------|
| "not available ... in their current state" | The state machine does not allow it yet. |
| "still has N mandatory test(s) without a recorded result" | Record the missing results. |
| "cannot be approved while N investigation(s) remain open" | Close the investigations first. |
| "You performed test ... and cannot review your own result" | A different user must review. |
| "reviewed sample ... cannot also approve it" | A third user must approve. |
| "approved and cannot be modified" | Create a new version instead. |
| "cannot be recorded without a documented retest authorisation" | Authorise the retest first. |
| "A written scientific justification is required" | Fill the justification field. |

None of these is a defect. Each corresponds to a documented business rule.
