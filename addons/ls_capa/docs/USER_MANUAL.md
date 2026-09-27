# ls_capa — User Manual

Audience: quality staff raising, investigating, executing and closing
CAPA records.

**Regulatory note.** This manual describes how the software behaves. It
does not replace your organization's CAPA procedure. Where the two
differ, your procedure governs.

---

## 1. The CAPA lifecycle

A CAPA passes through eight statuses. The buttons available in the form
header change with the status, and each transition is checked by the
server — a step cannot be skipped by editing the record directly.

```
Identified → Assessed → Investigation → Action Planning
          → In Progress → Completed → Verified → Closed
```

| Status | Meaning | Who acts |
|---|---|---|
| Identified | Issue recorded | Investigator |
| Assessed | Impact evaluated | Investigator |
| Investigation | Root cause being analysed | Investigator |
| Action Planning | Actions being defined | Coordinator |
| In Progress | Actions being executed | Coordinator |
| Completed | All actions settled | Coordinator |
| Verified | Effectiveness confirmed | Manager |
| Closed | Formally closed | Manager |

## 2. Raising a CAPA

*Quality > CAPA > CAPA Records > New*

Complete at minimum:

- **Title** — a short statement of the issue.
- **Issue Description** — what was observed, where and when. State
  facts, not conclusions.
- **Source** — the process that generated the CAPA.
- **Source Reference** — the originating record number, for example the
  deviation or audit report reference.
- **CAPA Type** — Corrective, Preventive, or both.
- **Severity** — Critical, Major or Minor.
- **CAPA Owner** — the person accountable for reaching closure.

The reference is allocated automatically on save. The due date is
proposed from the category lead time and can be edited.

If containment action was already taken, record it under **Immediate
Action / Correction**. Keep it separate from the corrective action plan:
a correction fixes the instance, a corrective action removes the cause.

## 3. Assessing impact

Open the **Impact Assessment** tab. Tick the applicable impacts (product
quality, regulatory, patient or user safety) and write the assessment.

Press **Assess**. The button refuses to proceed while the impact
assessment text is empty — this gate exists so that severity decisions
are documented rather than implied.

## 4. Investigating root cause

Press **Start Investigation**, then open the **Root Cause Analysis** tab
and add a line. Three methods are supported.

### Five Whys

Enter the successive Why answers. **Why 1 is mandatory.** Stop when you
reach a cause you can act on; not all five levels are required.

### Ishikawa (cause and effect)

Select the diagram category in which the cause was located: People,
Equipment, Material, Method, Measurement or Environment. **The category
is mandatory** for this method.

### FMEA

Enter Severity, Occurrence and Detection ratings on a **1 to 10** scale.
The Risk Priority Number is computed automatically as the product of the
three. Values outside 1–10 are rejected.

### Confirming

Write the **Root Cause Statement** as a verifiable cause, not a symptom.
Tick **Primary Root Cause** on the principal contributor. Press
**Confirm**.

Action planning cannot start until at least one analysis is Confirmed.

## 5. Planning actions

Press **Plan Actions**, then open the **Actions** tab and add lines.

For each action set the type (Corrective or Preventive), a description
worded so completion can be objectively verified, the responsible
person, and the planned completion date. Optionally link the action to
the root cause it eliminates.

Press **Start Execution** once the plan is complete. At least one action
must exist.

## 6. Executing actions

Open an action and use the header buttons.

- **Start** — moves the action to In Progress.
- **Mark Done** — requires **Completion Evidence** to be filled in
  first. Record the document or record number proving the action was
  performed. The completion date is stamped automatically.
- **Cancel** — requires a **Cancellation Reason**. A completed action
  cannot be cancelled.
- **Create Task** — generates a linked task in the Project application
  for the responsible person. One task per action.

Late actions are shown in red in lists and carry a **Late** ribbon.

Press **Complete** on the CAPA once every action is Done or Cancelled.

## 7. Verifying effectiveness

Open the **Effectiveness** tab and add a check.

Define the **Acceptance Criteria before performing the check**. Criteria
written after the evidence is seen are not verification. State something
measurable, for example "no recurrence across the next twenty batches".

Choose the verification method, the verifier and the planned date. Plan
the check far enough after implementation for evidence to accumulate.

When the evidence is available, write the **Conclusion** citing what was
reviewed, then press **Conclude Effective** or **Conclude Not
Effective**. A conclusion is mandatory; the buttons refuse an empty one.

Press **Verify Effectiveness** on the CAPA. This requires at least one
check concluded Effective and no check still open.

### When a CAPA was not effective

Press **Raise Follow-up CAPA** on the ineffective check. A new CAPA is
created, pre-filled from the original and referencing it as its source.
Only one follow-up can be raised per check.

## 8. Closing

Press **Close CAPA**. A dialog asks for the **Closure Summary**, which
is mandatory. Confirm that the actions were implemented and verified as
effective.

On closure the system records the closure date and the closing user. A
closed CAPA cannot have its closure summary removed.

## 9. Finding CAPA records

The search panel offers filters for My CAPA Records, Open, Closed,
Overdue, Critical and Regulatory Impact, and grouping by status,
severity, source, category, type, owner and identification month.

Views available: list, kanban (grouped by status by default), form,
pivot and graph for trend analysis.

## 10. Printing

With a CAPA open or selected, use *Print > CAPA Record*. The PDF
contains the issue, impact assessment, all root cause analyses, all
actions, all effectiveness checks and the closure summary.

## 11. What you cannot do

These restrictions are intentional.

- You cannot skip a workflow step.
- You cannot delete a CAPA that progressed beyond Identified. Archive it
  instead.
- You cannot complete an action without evidence, or cancel one without
  a reason.
- You cannot verify a CAPA without an effective check, or close one
  without a summary.
- Only a CAPA Manager can verify, close, delete or configure.
