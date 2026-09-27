# User Manual

**Module:** `ls_medical_plastics`

---

## 1. Recording a moulding run

A run is the production record of one moulding campaign. It advances through
seven states and cannot skip any of them.

```
draft -> setup -> startup_check -> running -> completed -> reviewed -> closed
                                                    \
                                                     -> cancelled (draft/setup/startup only)
```

### 1.1 Create the run (Operator)

**Medical Plastics → Production → Injection Moulding → New**

Select the component; the tool list then offers only tools declared for that
component and currently in service. Selecting the tool preselects the work
centre and the approved parameter specification automatically.

Optionally link the manufacturing order and set the produced lot.

### 1.2 Start setup

Click **Start Setup**. The system verifies that:

- the component is **released**;
- the tool is **in service**;
- an **approved** specification exists for this component, tool and work centre.

If any check fails the run stays in draft and the reason is displayed. On
success the specification and **its version number** are frozen onto the run, and
the shot counter start is taken from the tool.

### 1.3 Record setup readings and complete setup

Click **Record Readings**, which opens a grid pre-loaded with every parameter of
the frozen specification, each defaulted to its target value. Untick *Record*
for any parameter not being measured now, enter the measured values and confirm.

Click **Setup Complete** to move to start-up verification.

### 1.4 Start-up verification

Record readings for every parameter whose monitoring frequency is *At Setup
Only* or *At Start-up Verification*, then add the **Material Consumption** lines:
grade, lot reference and quantity. A grade in direct drug contact **requires** a
lot reference.

Click **Confirm Start-up and Run**. Production is refused if:

- a required start-up reading is missing — the missing parameters are named;
- no material consumption has been recorded;
- a **critical** parameter is out of tolerance — the failing parameters are
  named.

This last check is the principal quality gate of the module: production cannot
begin outside the approved process window on a critical parameter.

### 1.5 During the run

Record in-process readings at the frequency the specification requires. Record
scrap as it arises, choosing the reason and, where the defect is attributable,
the cavity. If a cavity is blocked mid-run, add it to **Cavities Blocked During
Run** on the Cavities tab.

### 1.6 Complete the run

Enter the **Shot Counter at End** and the **Quantity Produced** — the total
number of parts taken from the machine, including rejects. Click **Complete
Run**. The end counter cannot be lower than the start counter.

Accepted quantity, rejected quantity and reject rate are computed
automatically.

### 1.7 Review (Manager)

A different person from the operator and setter opens the run and clicks
**Review**. The system refuses if the reviewer is the operator or the setter.

If out-of-tolerance readings exist, a **Deviation Reference** must be entered
first. The reference points at the deviation record raised under the site
procedure; this module does not manage deviations.

To return the run for correction, enter a **Review Comment** and click **Return
For Correction**.

### 1.8 Close (Manager)

Click **Close Run** and confirm. Closing:

- **freezes the record permanently** — no field can be changed afterwards, and
  the run can never be deleted;
- advances the tool cumulative shot counter and re-evaluates its maintenance
  status.

Only closed runs appear in Moulding Analysis, so reported figures rest on
reviewed records only.

---

## 2. Recording parameter readings

### 2.1 Readings cannot be edited

A captured reading is permanent. It cannot be modified or deleted, by anyone,
including a manager. This is enforced both in the model and in the access
rights.

Each reading also stores a **copy of the acceptance criteria in force at the
moment of capture**. Revising the specification later does not change whether a
past reading was in tolerance.

### 2.2 Correcting a wrong value

In the reading grid, select the erroneous reading in the **Corrects Reading**
column, enter the correct value and state the **Reason for Correction**, which is
mandatory.

The original reading is marked superseded but **remains in the record**. It is
excluded from the deviation count, and both values print on the run record with
the reason. Nothing is erased.

---

## 3. Working with tools

### 3.1 Cavity register

Cavities are created automatically from the cavity count. To block one, enter a
**Blocking Reason** — mandatory — and click **Block**. The blocking user and
timestamp are stamped automatically. Blocked cavities reduce the active cavity
count but do not stop the tool.

### 3.2 Maintenance

**Medical Plastics → Tools → Maintenance Records → New**

Select the tool and type, then **Start** — which snapshots the tool shot count —
carry out the work, record the **Findings** and **Actions Taken**, and click
**Complete**. Actions taken are mandatory.

Completing an event with *Resets Maintenance Baseline* set clears the
shots-since-maintenance counter. Setting **Requalification Required**
automatically places the tool in **quarantine**.

A completed maintenance event cannot be deleted.

### 3.3 Returning a tool to service

Open the tool and click **Return To Service**. Confirm which cavities are
active; cavities confirmed active are unblocked automatically. A **quarantined**
tool additionally requires a recorded requalification with its date.

### 3.4 Monitoring what is due

**Medical Plastics → Tools → Due For Maintenance** lists every tool whose
preventive maintenance or requalification is due or overdue. In the tool list,
overdue tools appear in red and tools due soon in orange.

---

## 4. Revising a moulding parameter specification

Never edit an approved specification. Open it and click **New Version**, which
creates a draft copy at the next version number with all parameters copied.

Record the **Reason For Change** — mandatory from version 2 onwards — adjust the
parameters, then submit, review and approve. Approving the new version
**automatically supersedes** the previous one; there is never more than one
approved specification for a given component, tool and work centre.

Runs already closed keep the version they were executed against, because the
version number was frozen at setup.

---

## 5. Tracing product

**Medical Plastics → Reports → Traceability Enquiry**

| Search by | Answers the question |
|---|---|
| Produced Lot | What went into this batch of parts? |
| Material Lot | Which batches used this resin lot? |
| Component and period | What was made, and how did it perform? |
| Tool and period | What did this mould produce? |

By default only closed runs are searched. Tick *Include Runs in Progress* to
widen the search.

**Search** lists the matching runs, **Open Results** opens them for review, and
**Print Records** produces the full moulding run record for every match —
including material lots, all effective readings, corrected readings with their
reasons, and rejects.

A material lot enquiry is the one to use when a resin lot is found to be
non-conforming and the affected production must be identified.
