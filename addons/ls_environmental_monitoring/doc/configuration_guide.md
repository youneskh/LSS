# Configuration Guide — `ls_environmental_monitoring`

The module ships **no configuration data at all**. Nothing works until the steps
below have been completed. This is deliberate: shipping example thresholds into
a regulated system risks their being mistaken for approved acceptance criteria.

Work through the sections in order; each depends on the one before.

---

## Step 1 — Cleanroom grades

**Configuration → Cleanroom Grades**

Create one record per classification your site uses.

| Field | Guidance |
|---|---|
| Grade | The designation used in your own documentation |
| Code | Short code; appears in reports |
| Sequence | Order from most to least stringent |
| Reference Document | The internal document that defines this grade |

A grade carries **no acceptance criteria**. Criteria belong to limits, which are
set per sampling point.

---

## Step 2 — Areas

**Configuration → Areas**

Create one record per room, suite or zone. Areas may be nested: set Parent Area
to build a hierarchy used for reporting roll-up.

Assign the classification grade. Sampling points inherit it and may override it.

---

## Step 3 — Parameters

**Configuration → Parameters**

Create one record per measured characteristic.

| Field | Guidance |
|---|---|
| Parameter Type | Determines grouping and filtering. Choose the closest match |
| Result Type | *Quantitative* records a number evaluated against thresholds. *Qualitative* records pass or fail |
| Unit of Measure | Free text, so units specific to monitoring can be used |
| Requires Incubation | Marks microbiological parameters |
| Displayed Decimals | Presentation only |

A qualitative failure is evaluated as an action exceedance, because a
qualitative parameter has no intermediate alert level.

---

## Step 4 — Methods

**Configuration → Methods**

Create one record per documented sampling or test method. A method is tied to
exactly one parameter.

Record the **Controlling Procedure** identifier. Recording the method against
every result is what makes the result attributable to a defined procedure.

---

## Step 5 — Sampling points

**Programme → Sampling Points**

Create one record per physical location where samples are taken.

| Field | Guidance |
|---|---|
| Position | Precise enough for a different operator to find the same spot |
| Selection Rationale | **Complete this.** It is the record of why this location is monitored, and is what an inspector will ask for |
| Critical Location | Set for locations identified as critical by risk assessment |

A point with no approved limits is highlighted in the list view and can be
filtered with *Without Approved Limits*.

---

## Step 6 — Limits

**Programme → Limits**

This is where acceptance criteria are set. **The module supplies no values.**

For each combination of sampling point, parameter and occupancy state:

1. Choose the **Bound Direction**. *Upper* means a breach occurs above the
   threshold; *lower* means below. A parameter constrained on both sides, such
   as temperature, needs **two limit records**, one per direction.
2. Tick the thresholds you are defining and enter their values. An unticked
   threshold is ignored during evaluation — it is not treated as zero.
3. Set **Occupancy State**. A limit set for a specific state takes precedence
   over one set for *Any State*, so a general fallback can coexist with a
   state-specific override.
4. Decide **Raise Excursion on Alert**. Off by default: alert exceedances are
   visible and trended but do not open a formal excursion. Action and
   specification exceedances always open one.
5. Complete **Justification**. Approval is refused without it.
6. Record the **Controlling Document**.

### Threshold ordering

For an upper bound, alert must not exceed action, and action must not exceed
specification. The reverse applies to a lower bound. A configuration that
violates this is rejected, because it would make the less severe threshold
unreachable.

### Boundary behaviour

A value **exactly equal** to a threshold is treated as **compliant**. This
matches the usual reading of "not more than". If your procedure requires the
opposite, set the threshold accordingly.

### Approval

Limits are approved by a user other than the author. Once approved:

- the thresholds cannot be edited;
- the record cannot be deleted;
- changing a value means creating a revision, which supersedes the predecessor
  on approval.

---

## Step 7 — Monitoring plans

**Programme → Monitoring Plans**

A plan is the approved schedule. Only approved plans generate samples.

For each line, set the sampling point, parameter, method, occupancy state,
frequency and start date. A plan may hold only one line per combination of
point, parameter and occupancy state.

**Frequency:** *day* and *week* advance by a fixed number of days. *Month* and
*year* advance by calendar arithmetic, so a plan starting on 31 January falls
due on 28 February, not on 2 March.

Complete the **Rationale** and set a **Next Review Due** date. A plan is
approved by a user other than its author and must contain at least one line.

---

## Step 8 — Assign roles

**Settings → Users & Companies → Users**

| Role | Assign to |
|---|---|
| Viewer | Anyone needing read access, such as auditors |
| Technician | Operators who collect samples and enter results |
| Manager | Quality staff who approve limits and plans, review and approve samples, and close excursions |

Roles do not imply one another, so assign the single role each user needs.

Because review and approval require the manager role, and must be performed by
someone other than the person who entered the results, **at least one manager
and one technician are required** for the workflow to complete.

---

## Step 9 — Scheduled jobs

**Settings → Technical → Scheduled Actions**

Both jobs run daily and are active on installation.

- *Generate Scheduled Samples* creates the samples that have fallen due. It is
  idempotent: running it repeatedly does not duplicate anything. Deactivate it
  if you prefer to generate manually.
- *Notify Overdue Samples* posts a message on each sample past its scheduled
  date and not yet collected.

---

## Configuration checklist

- [ ] Grades created, each with a reference document
- [ ] Areas created and nested correctly, each with a grade
- [ ] Parameters created with the correct result type and unit
- [ ] Methods created, each naming its controlling procedure
- [ ] Sampling points created, each with a completed selection rationale
- [ ] Limits created, justified and **approved**, for every point and parameter
- [ ] Both bound directions created for any parameter constrained on both sides
- [ ] Plans created, justified and **approved**, with a review due date
- [ ] At least one manager and one technician assigned
- [ ] Scheduled jobs reviewed
- [ ] The filter *Sampling Points → Without Approved Limits* returns nothing
