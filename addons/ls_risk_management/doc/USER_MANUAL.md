# User Manual

## 1. What this module does

It records identified risks, estimates and evaluates them against your
organisation's approved acceptability criteria, tracks the risk control
measures applied, records who accepted the residual risk, and keeps risks
under periodic review. It also provides FMEA worksheets.

Prerequisite: a Risk Manager must have approved a risk matrix. See
`CONFIGURATION.md`.

---

## 2. The risk lifecycle

```
Draft ──▶ Assessed ──▶ Risk Control ──▶ Monitoring ──▶ Closed
  │                                                      ▲
  └────────────────── Cancelled ◀───────────────────────┘
```

| State | Meaning | How to leave it |
|---|---|---|
| **Draft** | Identified, not yet formally assessed | Requires an **approved initial assessment**, then *Mark Assessed* |
| **Assessed** | An approved estimation exists | *Start Risk Control* |
| **Risk Control** | Control measures are being applied and verified | *Move to Monitoring*, which requires completeness confirmation and, where the acceptability demands it, a residual risk acceptance |
| **Monitoring** | Residual risk accepted, under periodic review | *Close* |
| **Closed** | Retired, with a recorded reason | Terminal |
| **Cancelled** | Withdrawn, with a recorded reason | *Reset to Draft* |

---

## 3. Recording a risk

**Risk Management → Risk Register → New.**

Fill the title, the risk type and the owner. Then complete the **Risk
Analysis** tab. The four hazard fields are deliberately separate:

| Field | What belongs here |
|---|---|
| **Hazard** | The potential source of harm |
| **Sequence of Events** | How the hazard leads to exposure |
| **Hazardous Situation** | The circumstance of exposure |
| **Harm** | The injury or damage that results |

Recording "contamination" in all four adds nothing. Recording the chain is
what makes the estimation defensible later.

---

## 4. Assessing a risk

Click **Assess** on the risk, or select several risks in the list and use
**Assess** to estimate them together. Risks assessed together must share one
matrix.

1. Choose the **Assessment Type**: *Initial* for the first estimation,
   *Residual* after control measures, *Periodic Review* for scheduled review,
   *Production / Post-Production Information* when field information triggers
   re-estimation. A risk may have only one non-cancelled initial assessment.
2. Choose **Severity** and **Probability** from the matrix scales. The risk
   level and acceptability are derived from the matrix and cannot be typed in.
3. Write the **Estimation Rationale**. It is mandatory at confirmation.
4. **Confirm**, then a *different* person with the Risk Manager role
   **Approves**. You cannot approve your own assessment.

Only approved assessments drive the risk's current evaluation. An approved
assessment cannot be edited; cancel it with a reason and record a new one.

---

## 5. Applying risk control measures

On the **Risk Control** tab, add measures. Choose the **Risk Control Option**:

1. *Inherent Safety by Design* - preferred
2. *Protective Measure in the Device or Manufacturing Process*
3. *Information for Safety* - least preferred

Measures are ordered by this preference, so reliance on the weaker options is
visible. Where you select a less preferred option, record why in **Option
Analysis**.

Each measure passes through: **Approve** (Risk Manager) → **Start** →
**Mark Implemented** → **Verify Effectiveness**.

Two evidence fields are mandatory at the corresponding step, and the person
who verified implementation cannot verify effectiveness.

If a measure introduces a new hazard, tick **Introduces New Risk**, describe
it, and use **Create Risk Record for New Risk** to raise it in the register.

---

## 6. Residual risk and closure

1. When every measure is verified, a Risk Manager clicks **Confirm Control
   Completeness**.
2. If the current acceptability is *Acceptable Only With Risk Control* or
   *Not Acceptable*, a Risk Manager clicks **Accept Residual Risk** and records
   a justification. When the acceptability is *Not Acceptable*, a
   **benefit-risk analysis** is also required, and the module refuses without
   it.
3. **Move to Monitoring** sets the next review date.
4. **Close** requires a reason and re-checks that the residual decision exists.

---

## 7. Periodic review

Open risks carry a **Next Review Date**. Overdue risks appear in
**Reporting → Reviews Due**, are highlighted in the register, and generate a
daily notification to the risk owner. Record the review as an assessment of
type *Periodic Review*.

---

## 8. FMEA

**Risk Management → FMEA → FMEA Worksheets → New.**

Record the scope and the team, then add failure modes on the **Failure Modes**
tab. For each row give the item, its function, the failure mode, the effect,
the cause and the current controls, then rate **Severity**, **Occurrence** and
**Detection** from 1 to 10.

The **RPN** is the product of the three. A row is flagged **Action Required**
when the RPN reaches the worksheet threshold, or when the severity reaches the
severity threshold on its own — a severe failure is not excused by being rare
and detectable.

Workflow: **Start** → **Submit for Review** → **Record Review** →
**Approve** → **Close**. The facilitator cannot review or approve their own
worksheet. Approval is refused while any row requiring action has no
recommended action. Closing is refused while any required action is open.

After actions are taken, record the revised ratings; the revised RPN and the
reduction achieved are computed.

Use the warning icon on a row to raise it as a risk register entry, which
carries the failure mode across as the hazard and the effect as the harm.

**These ratings are an industry convention, not a requirement of
ISO 14971:2019.** The thresholds were set by your organisation.

---

## 9. Reports

- **Risk Record** - the full risk file: analysis, assessment history, control
  measures, residual decisions, review dates and closure.
- **FMEA Worksheet** - the worksheet with its team, ratings and actions.

Both are available from the **Print** menu.

---

## 10. What this module does not do

- It does not hold your risk management plan or risk management file.
- Its approvals are **not** 21 CFR Part 11 electronic signatures.
- It does not make your organisation compliant with anything. It records the
  evidence that supports your own compliance activities.
