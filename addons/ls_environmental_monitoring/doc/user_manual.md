# User Manual — `ls_environmental_monitoring`

For the people who run the monitoring programme day to day.

---

## 1. Finding what needs doing

**Operations → Samples Due** opens with the *Overdue* filter applied. It lists
every sample awaiting collection.

Useful filters on **Operations → All Samples**:

| Filter | Shows |
|---|---|
| Scheduled | Awaiting collection |
| In Progress | Collected but not yet approved |
| Overdue | Past the scheduled date, not yet collected |
| Threshold Breached | Any result that exceeded a threshold |
| Unscheduled | Raised outside the routine plan |
| Collected by Me | Your own samples |

---

## 2. The sample lifecycle

```
Draft → Scheduled → Collected → In Analysis → Results Entered → Reviewed → Approved
                                                                              │
                                              (any state before Approved) → Cancelled
```

The system refuses any transition not shown. You cannot record collection on a
draft sample without scheduling it first.

### 2.1 Recording collection

Open the sample and press **Record Collection**. The system stamps the current
time and your user name; neither can be typed in. A collection time in the
future is rejected.

A sample with no result lines cannot be collected — there would be nothing to
measure. Add the parameters first.

### 2.2 Starting analysis

Press **Start Analysis**. For microbiological parameters this marks the start of
incubation.

### 2.3 Entering results

On the **Results** tab, enter a value for each parameter.

- For a quantitative parameter, enter the number and tick **Recorded**. The tick
  is what distinguishes a genuine result of zero from no result at all — an
  important distinction for colony counts.
- For a qualitative parameter, choose Pass or Fail.
- Record **Organism Identified** where identification was performed.

Press **Submit Results**. Every result must have a value; the system refuses a
partial submission. Each result is then evaluated automatically against the
approved limits and the outcome appears immediately.

### 2.4 Review and approval

Both require the **Manager** role, and neither may be performed by the person
who entered the results. This is enforced by the system, not by convention.

Press **Review**, then **Approve**. Approval is the point at which:

- the sample and its results become read-only;
- excursions are opened for any breach requiring one.

**Return to Analysis** sends a sample back for correction before approval and
clears the review.

### 2.5 Cancelling

**Cancel** requires a reason, which is retained on the record. A cancelled
sample is kept, not deleted, so the gap in the schedule remains explained.

---

## 3. Reading an outcome

| Outcome | Meaning |
|---|---|
| Within Limits | No configured threshold was breached |
| Alert Limit Exceeded | The alert threshold was passed |
| Action Limit Exceeded | The action threshold was passed |
| Specification Exceeded | The specification threshold was passed |
| **No Approved Limit** | **No approved limit covers this point and parameter. The value was recorded but not assessed.** Report this to your manager |
| Not Evaluated | No value recorded yet |

The sample's overall outcome is the most severe outcome among its results.

A value **exactly equal** to a threshold counts as within limits.

Each result also shows the thresholds that were applied at the moment of
evaluation. These are stored on the result, so a later revision of the limit
does not change what a historical result was judged against.

---

## 4. Excursions

An excursion opens automatically when an approved sample contains:

- an action exceedance, always;
- a specification exceedance, always, and marked as requiring investigation;
- an alert exceedance, only where the limit is configured to escalate.

All breaches on one sample share a single excursion, because they describe one
event at one location and time.

### 4.1 Working an excursion

```
Open → Impact Assessment → Investigation → Pending Closure → Closed
```

1. **Start Assessment**, then record what was done on detection under
   **Immediate Actions**.
2. Complete the **Impact Assessment** and set **Product Impact**. Closure cannot
   be proposed while product impact is *Not Yet Assessed*.
3. **Open Investigation** where one is needed. This requires the impact
   assessment to be complete. A specification breach is flagged as requiring
   investigation automatically, and then also requires a **Root Cause** before
   closure.
4. **Propose Closure**, then a different user presses **Close** and records a
   justification.

The person who closes an excursion must not be its owner.

### 4.2 Linking to a corrective action

This module does not manage corrective action. Record the identifier of the
record raised in your CAPA or deviation system in **External Record Reference**.
This field stays editable after closure.

### 4.3 Excursions are never deleted

An excursion is evidence that a breach occurred. One raised in error is
**cancelled**, which keeps the record.

---

## 5. Correcting an approved result

Approved results are frozen. If an error is found afterwards:

1. Open the result and press **Amend Result**.
2. Enter the corrected value and a reason. Both are required.
3. The original value is retained on the record and shown alongside the
   correction, together with who amended it and when.

A result may be amended **once**. A further correction requires a new
investigation, so that a record is not repeatedly rewritten.

---

## 6. Trend analysis

**Trending → Run Trend Analysis**

Choose a period and, optionally, restrict to particular areas, sampling points
or parameters. Only results on **approved** samples are included, so the
analysis reflects released data.

Each line reports, per sampling point and parameter: the number of results, the
counts of alert, action and specification exceedances, the exceedance rate, and
the minimum, maximum, mean, median and standard deviation.

### Reading the figures honestly

- **A statistic that cannot be calculated is flagged as unavailable, not shown
  as zero.** A standard deviation needs at least two values.
- **Direction** compares the mean of the later half of the series with the mean
  of the earlier half. It is a descriptive indicator to prompt review. **It is
  not a test of statistical significance and must not be reported as one.**
- Below six results, or where the earlier half averages zero, direction is
  reported as *Insufficient Data* rather than a figure the data cannot support.

Record your interpretation under **Conclusion**, then **Mark as Reviewed**. The
conclusion is mandatory, and a reviewed analysis cannot be recomputed — create a
new one instead.

---

## 7. Printing records

- **Environmental Monitoring Record** from a sample: location, criteria applied,
  results, any amendments, and the full execution record of who did what.
- **Excursion Report** from an excursion: detection, breaching results,
  assessment, investigation and closure.

Both state that they are printed extracts and that the electronic record is the
primary record.

---

## 8. Common questions

**A result shows "No Approved Limit". Why?**
No approved limit covers that sampling point, parameter and occupancy state. The
value was recorded but not assessed. Ask your manager to configure and approve a
limit. Use **Sampling Points → Without Approved Limits** to find gaps.

**I cannot approve a sample I entered results for.**
Correct. Review and approval require a different user holding the Manager role.

**Where did my alert exceedance excursion go?**
Alert exceedances do not open an excursion unless the limit is configured to
escalate. The result is still visible under **Results → Threshold Breaches** and
is counted in trend analysis.

**Why can I not delete a sample?**
Only a draft sample can be deleted. Anything further along is cancelled instead,
so the record is retained.

**Why does temperature need two limits?**
A limit is a single bound. A parameter constrained above and below needs one
upper-bound limit and one lower-bound limit. The system applies whichever
produces the more severe outcome.
