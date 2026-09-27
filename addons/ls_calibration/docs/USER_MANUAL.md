# ls_calibration — User and Administrator Manual

Phase 9 of the development framework.

---

## 1. Who does what

| Task | Viewer | Technician | Approver | Manager |
|---|---|---|---|---|
| Read everything | yes | yes | yes | yes |
| Create instrument categories | no | no | no | yes |
| Create reference standards | no | no | no | yes |
| Create an instrument | no | no | no | yes |
| Edit an instrument | no | yes | yes | yes |
| Quarantine an instrument | no | yes | yes | yes |
| Place an instrument in service | no | no | yes | yes |
| Retire an instrument | no | no | no | yes |
| Create calibration points | no | no | no | yes |
| Create a calibration plan | no | no | no | yes |
| Approve a calibration plan | no | no | yes | yes |
| Close a calibration plan | no | no | no | yes |
| Generate a schedule | no | yes | yes | yes |
| Create a calibration record | no | yes | yes | yes |
| Enter readings | no | yes | yes | yes |
| Mark performed, submit for review | no | yes | yes | yes |
| Review and approve a record | no | no | yes | yes |
| Reject a record | no | no | yes | yes |
| Delete a draft record | no | no | no | yes |
| Assess an out-of-tolerance event | no | no | yes | yes |
| Close an out-of-tolerance event | no | no | no | yes |
| Create a certificate | no | no | yes | yes |
| Delete a certificate | **never** | **never** | **never** | **never** |

---

## 2. Administrator: initial configuration

### 2.1 Instrument categories

**Calibration ▸ Configuration ▸ Instrument Categories**

A category groups instruments into a family and carries the defaults applied to
new instruments in it. Categories may be nested; the complete name shows the
parent chain.

| Field | Guidance |
|---|---|
| Category Name | The family, for example *Analytical Balances*. |
| Code | Short, unique per company. Appears in exports. |
| Parent Category | Optional. A category cannot become its own ancestor. |
| Default Interval | Proposed on new instruments; the instrument may override it. |
| Default Criticality | Proposed on new instruments. |

### 2.2 Reference standards

**Calibration ▸ Configuration ▸ Reference Standards**

Register every artefact used to calibrate. The traceability fields are what
make a calibration result defensible under ISO 13485 clause 7.6 and
21 CFR 820.72.

| Field | Guidance |
|---|---|
| Standard ID | Unique per company. |
| Traceability Certificate No. | The number of the certificate that calibrated *this standard*. |
| Issuing Laboratory | Who issued that certificate. |
| Accreditation Reference | Recorded as supplied. **The module does not verify it against any register.** |
| Valid Until | Required. Drives the *Currently Valid* flag, refreshed daily. |
| Measurement Uncertainty | Recorded for reference. **Not propagated into any calculation.** |

An expired standard is shown with a red *Expired* ribbon and a red list row.
The module does **not** block its use on a calibration; that judgement is left
to the reviewer, and the certificate report prints the expiry date so the
reviewer can see it.

### 2.3 Users and segregation of duties

Assign exactly one calibration group per user. The groups are cumulative:
Manager implies Approver implies Technician implies Viewer.

Because the module refuses a calibration approved by the user who performed it,
a site needs **at least two people** with Approver rights, or one Technician
plus two Approvers, for the workflow to complete.

### 2.4 Scheduled actions

**Settings ▸ Technical ▸ Scheduled Actions**

| Action | Default | Notes |
|---|---|---|
| Calibration: refresh instrument status | Active, daily | Required. Calibration status depends on today's date and will not update on its own. |
| Calibration: notify upcoming and overdue calibrations | **Inactive**, weekly | Activate once you want chatter reminders. |
| Calibration: refresh reference standard validity | Active, daily | Required for the *Currently Valid* flag. |

---

## 3. Technician: day-to-day operation

### 3.1 Registering an instrument

**Calibration ▸ Instruments ▸ Instrument Register ▸ New** (Manager creates;
Technician edits.)

1. Enter the name. Leave **Instrument ID** as `/` to draw the next sequence
   number, or type your own asset number.
2. Select the **Category**. The interval and criticality are proposed from it.
3. Fill the **Metrology** tab: unit, range minimum, range maximum, resolution.
   The span is computed. **The range must be entered before you can use a
   percent-of-span tolerance.**
4. Set **Criticality**. A critical instrument is flagged GxP Critical
   automatically; you may override the flag.
5. Add at least one row in the **Calibration Points** tab.
6. Ask an Approver to press **Place in Service**.

An instrument with no calibration point cannot enter service.

### 3.2 Defining calibration points

Each row is one nominal value and its acceptance tolerance.

| Tolerance Type | Enter | Meaning |
|---|---|---|
| Absolute | `0.001` | ±0.001 in the instrument's unit |
| % of Reading | `0.5` | ±0.5 % of the nominal value |
| % of Span | `1.0` | ±1.0 % of (range max − range min) |

**A percentage is a percentage.** Type `0.5` for half a percent, not `50` and
not `0.005`.

The lower and upper limits are computed and shown read-only. Once a point has
been used in a calibration that has passed data entry, its nominal value and
tolerance are frozen: **archive the point and create a new one** rather than
editing it, so that the pass/fail basis of the existing record is not altered
retroactively.

### 3.3 Executing a calibration

**Calibration ▸ Calibrations ▸ Open Calibrations**

1. Open the draft record and press **Start**. Reading lines are created, one
   per calibration point.
2. In the **Readings** tab, enter the **As Found** value for each point.
   Entering a value ticks *Found?* automatically. A row outside its limits
   turns red immediately.
3. If you adjust the instrument, tick **Adjustment Performed** and enter the
   **As Left** values.
4. In the **Reference Standards** tab, add every standard you used.
   **At least one is required.**
5. In the **Conditions** tab, record ambient temperature and humidity.
6. Press **Mark Performed**, then **Submit for Review**.

You cannot mark a record performed with no as-found value, and you cannot
submit one that cites no reference standard.

### 3.4 Reading the result

| Overall result | Meaning |
|---|---|
| Pass | Every as-found reading was inside tolerance. |
| Pass After Adjustment | At least one as-found reading was outside tolerance; every as-left reading is inside. **The instrument was out of tolerance during the preceding period.** |
| Fail | The as-left series is outside tolerance or was not recorded after an as-found failure. |
| Not Applicable | No reading was recorded in either series. |

### 3.5 Generating a schedule

**Calibration ▸ Planning ▸ Generate Scheduled Calibrations**

Set the horizon date. Leave the plan and category restrictions empty to include
every approved plan of the company. Draft records are created; nothing is
marked as performed. Running the wizard twice over the same horizon creates
nothing the second time.

---

## 4. Approver: review and approval

### 4.1 Reviewing

Open a record in **Under Review** and check, at minimum: the reference
standards used and whether any had expired at the calibration date; the
environmental conditions; every reading against its limits; and the procedure
reference.

Press **Record Review** to log your review. You cannot review a calibration you
performed.

### 4.2 Approving

Press **Approve**. You cannot approve a calibration you performed, nor one you
reviewed. A third user is required.

On approval the instrument's last calibration date and next due date are
refreshed, its status recomputes, and — if the as-found series failed and the
instrument requires OOT assessment — an out-of-tolerance event is raised and
the instrument is placed in quarantine.

**After approval the record is locked.** Any attempt to change a data field
raises an error. The chatter remains usable, and certificates and OOT events
can still be attached.

### 4.3 Rejecting

Press **Reject**. A reason is mandatory and cannot be blank. The record returns
to Rejected, the review sign-off is cleared, and the technician can press
**Start** to rework it.

---

## 5. Handling an out-of-tolerance event

**Calibration ▸ Out of Tolerance ▸ OOT Events**

An event is created automatically when an approved calibration has a failing
as-found series. The instrument is placed in quarantine at the same time.

| Step | Who | What is required |
|---|---|---|
| Start Assessment | Approver | — |
| Complete Assessment | Approver | Impact assessment text, product impact classification, disposition, and a justification for the disposition. All four are mandatory. |
| Close | Manager | A CAPA reference when the product impact is Potential or Confirmed. The closing user must differ from the assessing user. |

**Affected period.** The event is pre-filled with the window from the previous
approved calibration to the detection date. That is the period during which
measurements from this instrument may have been wrong. Record the batches or
data sets generated in that window in **Affected Batches / Data Sets**.

Returning the instrument to service after closure is a separate, deliberate
step: press **Place in Service** on the instrument.

---

## 6. Certificates

**Calibration ▸ Calibrations ▸ Certificates**

A certificate can only be attached to an **approved** record.

| Type | Requirement |
|---|---|
| Internal | Print with the **Print Certificate** button. |
| External | The received document must be attached before saving. |

Leave the number as `/` for an internal certificate to draw a sequence number;
for an external one, type the number issued by the laboratory.

**Certificates can never be deleted, by anyone.** Archive a superseded
certificate instead, so that the record of what was issued remains complete.

---

## 7. Interpreting calibration status

**Calibration ▸ Instruments ▸ Calibration Status**

| Status | Meaning |
|---|---|
| Never Calibrated | No approved calibration record exists. |
| OK | The due date is further away than the Due Soon threshold. |
| Due Soon | The due date is within the threshold, 30 days by default. |
| Overdue | The due date has passed. |

Status is stored and refreshed by the daily scheduled action. **If that action
is disabled the status will freeze at its last computed value.**

Only **approved** records advance the due date. A calibration that has been
performed but not yet approved does not release the instrument.

---

## 8. Troubleshooting

| Symptom | Cause and remedy |
|---|---|
| "cannot move from X to Y" | The transition is not in the state machine. Check §3.2 of the functional specification for the permitted paths. |
| "has no calibration point defined" | Add at least one point before placing the instrument in service or approving its plan. |
| "must cite at least one reference standard" | Add a standard in the Reference Standards tab. |
| "must be approved by a different user" | Segregation of duties. A third user is needed. |
| "is approved and can no longer be modified" | Correct behaviour. Create a new calibration record; do not attempt to edit history. |
| "acceptance criteria can no longer be changed" | The point has been used in a committed record. Archive it and create a new point. |
| "already has an approved calibration plan whose effective period overlaps" | Close or set an end date on the existing plan first. |
| "reports a product impact and requires a corrective action reference" | Enter the CAPA reference on the Disposition tab. |
| Statuses look stale | The daily refresh scheduled action is disabled. Re-enable it. |
| An instrument is stuck in quarantine | An OOT event put it there. Close the event, then press Place in Service. |
