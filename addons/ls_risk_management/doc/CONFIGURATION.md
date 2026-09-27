# Configuration Guide

Configuration is performed by a user in the **Risk Manager** group.

---

## 1. Define the risk acceptability criteria

This is the first and most important configuration step, and the module will
not let you assess a risk until it is complete.

ISO 14971:2019 requires the manufacturer to establish objective criteria for
risk acceptability, and does not itself specify acceptable risk levels. The
module therefore ships **no usable criteria**. The included 5x5 matrix is an
unapproved example.

### 1.1 Start from the example or from scratch

Open **Risk Management → Configuration → Risk Matrices**.

Either open *EXAMPLE 5x5 Risk Matrix* and adapt it, or create a new matrix.

### 1.2 Complete the matrix

1. **Name, Code, Reference Document.** Put the identifier of the controlled
   procedure or risk management plan that defines these criteria into
   *Reference Document*. This is what an inspector will ask for.
2. **Severity Scale tab.** One line per level. *Value* is the ordinal rank,
   higher meaning more severe. *Definition* must be objective: a reader should
   be able to classify a harm without asking the author what was meant.
3. **Probability Scale tab.** Same, for probability of occurrence of harm.
4. Click **Generate Missing Cells**. Every severity and probability
   combination receives a cell, initialised to the lowest band and
   `Acceptable`, so nothing is inferred on your behalf.
5. **Cells tab.** Set the *Risk Level* and the *Acceptability* of every cell
   deliberately. The three acceptability values are:
   - *Acceptable* - no risk control is required on this basis alone.
   - *Acceptable Only With Risk Control* - the risk requires a recorded
     residual risk acceptance decision before it can be monitored or closed.
   - *Not Acceptable* - as above, and the residual acceptance additionally
     requires a benefit-risk analysis.
6. Click **Approve**. Approval is refused while any cell is missing.
7. Set **Default Matrix** so new risks adopt it. Only one active default is
   permitted per company.

### 1.3 Revising criteria

Approved matrices cannot be edited. Create a new matrix, approve it, then set
**Set Obsolete** on the old one. Existing assessments keep their original
matrix reference, so historical records remain interpretable.

---

## 2. Risk taxonomy

**Risk Management → Configuration → Risk Categories.** Ten starter categories
are shipped, hierarchical, editable and per company. Categories are optional
on a risk.

---

## 3. Review cadence

`Review Interval (Months)` on each risk defaults to 12. Change the default for
your organisation by setting it on each risk, or by adapting
`DEFAULT_REVIEW_INTERVAL_MONTHS` in `models/constants.py` in a custom
inheriting module.

The scheduled action *Life Sciences Risk: notify overdue risk reviews* runs
daily and notifies the risk owner of any open risk past its review date.
Adjust or disable it under **Settings → Technical → Automation → Scheduled
Actions**.

---

## 4. FMEA thresholds

Set per worksheet:

| Field | Default | Meaning |
|---|---|---|
| RPN Action Threshold | 100 | RPN at or above which action is required |
| Severity Action Threshold | 9 | Severity at or above which action is required irrespective of RPN |

Both are **organisation-defined**. The 1-10 scales and the Risk Priority
Number are an industry convention, not a requirement of ISO 14971:2019.

---

## 5. Users and roles

| Group | Grants |
|---|---|
| **Risk Viewer** | Read everything |
| **Risk Analyst** | Viewer, plus create and edit risks, assessments, control measures and FMEA. **Cannot** approve anything, accept residual risk, or close a risk. |
| **Risk Manager** | Analyst, plus approve assessments and matrices, confirm control completeness, accept residual risk, close and cancel records, and configure the taxonomy and matrices. |

Assign under **Settings → Users & Companies → Users**.

Two role restrictions are enforced by the ORM and cannot be bypassed through
the interface, the external API or an automation:

- The person who performed an assessment cannot approve it.
- The person who verified the implementation of a control measure cannot
  verify its effectiveness.

Provision at least two Risk Managers, or approvals will deadlock.

---

## 6. Multi-company

Risks, assessments, control measures, FMEA worksheets, categories and matrices
are company-scoped and isolated by global record rules. Each company needs its
own approved default matrix.

Numbering sequences ship company-independent. For per-company numbering, an
administrator may create additional `ir.sequence` records with the same code
and a company set. See `VERIFICATION_LOG.md` for the caveat on this behaviour.
