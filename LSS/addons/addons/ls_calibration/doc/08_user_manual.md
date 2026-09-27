# User Manual

Module: `ls_calibration` `19.0.1.0.0`. Audience: metrology technicians,
quality assurance, laboratory and production staff.

## 1. Concepts

| Term | Meaning in this module |
|------|------------------------|
| Instrument | The measuring, monitoring or test device whose result is used to accept or reject something. |
| Calibration plan | The periodic programme applied to one instrument: interval, procedure, test points. |
| Test point | One nominal value applied to the instrument, with its acceptance limits. |
| As-found reading | The reading taken **before** any adjustment. It tells you whether the instrument was still fit during the period that has just elapsed. |
| As-left reading | The reading taken **after** the adjustment. It tells you whether the instrument is fit for the period that begins. |
| Calibration record | The evidence of one calibration event. |
| Reference standard | The instrument or artefact used to produce the nominal value. |
| Certificate | The document issued at the end of the calibration. |

The distinction between as-found and as-left is the reason the module exists.
An out-of-tolerance as-found reading means that measurements already taken
with this instrument may be wrong, which is why the module refuses to close
such a record without an impact assessment.

## 2. Registering an instrument

**Calibration → Instruments → New**

1. Enter the name. The reference is assigned automatically.
2. In *Identification*, enter the category, the manufacturer, the model, the
   serial number, the related equipment if any, and the physical location.
3. In *Classification*, set the criticality, the GxP impact, the responsible
   user and the alert lead time.
4. In the *Metrological Data* tab, enter the measuring range, the unit, the
   tolerance type and the maximum permissible error.
5. Click **Set In Service**.

An instrument in *Draft* is not monitored. Only an instrument *In Service*
appears in the due and overdue notifications.

## 3. Creating a calibration plan

**Calibration → Calibration Plans → New**

1. Select the instrument. The reference is assigned automatically.
2. Enter the description and the reference of the written procedure.
3. Set the interval and its unit, and the start date.
4. If the calibration is subcontracted, tick *Externally Calibrated* and
   select the provider.
5. In the *Test Points* tab, add one line per nominal value. The unit and the
   tolerance are proposed from the instrument and can be adjusted. The lower
   and upper limits are computed automatically.
6. In the *Method* tab, summarise the method.
7. Click **Activate**.

The plan cannot be activated without at least one test point. As long as no
calibration has been approved, the due date is the start date.

## 4. Finding the calibrations to perform

**Calibration → Calibration Status → Due and Overdue** lists the instruments
whose calibration falls within their alert lead time or is already overdue.

The status is shown as a coloured badge:

| Badge | Meaning |
|-------|---------|
| Valid | The due date is further away than the alert lead time. |
| Due Soon | The due date is within the alert lead time. |
| Overdue | The due date has passed. |
| Not Scheduled | No active plan produces a due date. |
| Not Applicable | The instrument is out of service or retired. |

The responsible user of an instrument also receives an activity in the chatter
when the instrument becomes due or overdue.

## 5. Performing a calibration

### 5.1 Obtaining the record

A draft record is normally already available, created by the daily scheduled
action. Otherwise use **Calibration → Calibration Status → Generate
Calibration Records**, or open the plan and click **Create Calibration
Record**.

### 5.2 Recording the results

1. Open the record and click **Start**.
2. Check the calibration date and the performer. The date is the moment the
   calibration was actually performed.
3. Record the ambient temperature and humidity if the method requires them.
4. In the *Test Points* tab, enter the **As Found** reading of each point.
   The as-left value is proposed equal to it; change it only if you adjusted
   the instrument. The two verdict columns update immediately.
5. If you adjusted the instrument, tick *Adjustment Performed*.
6. In the *Reference Standards* tab, select the standards you used. If a
   standard is not managed in the register, type its identification and its
   certificate number in *External Standard Reference*.
7. Write the conclusion.
8. Click **Submit to Review**.

### 5.3 What the system checks before accepting the submission

| Check | Message when it fails |
|-------|-----------------------|
| The calibration date is filled | The calibration date is required before review |
| The performer is filled | The user who performed the calibration is required |
| At least one test point exists | The record does not contain any test point |
| At least one reference standard, internal or external | At least one reference standard is required |
| An out-of-tolerance as-found result carries an impact assessment | An impact assessment is required |
| No reference standard is overdue | The standard is overdue and cannot be used to justify a calibration |

### 5.4 Handling an out-of-tolerance result

When at least one as-found reading falls outside its limits, an *Out of
Tolerance* tab appears. It is mandatory to describe the impact of the
situation on the products, the batches and the decisions taken with this
instrument since the previous calibration, and to reference the deviation or
corrective action opened in the quality system.

The overall result is then:

| As found | As left | Result |
|----------|---------|--------|
| In tolerance | In tolerance | Pass |
| Out of tolerance | In tolerance | Pass After Adjustment |
| Any | Out of tolerance | Fail |

A *Fail* means the instrument is not fit for use. Set it out of service.

## 6. Approving a calibration

Reserved to the *Calibration / Manager* group.

1. Open the record, state *To Review*.
2. Check the readings, the standards used and, if present, the impact
   assessment.
3. Click **Approve**, or **Reject** and give a reason.

The system refuses the approval when you are the user recorded as the
performer. This is intentional and cannot be bypassed from the interface.

Once approved, the record is locked: neither it nor its test points can be
modified or deleted by anyone. The next due date of the plan and of the
instrument is recomputed from the calibration date and the interval.

A rejected record returns to *Draft* with **Reset to Draft**, keeping the
rejection reason visible.

## 7. Certificates

**Calibration → Certificates → New**

For an internal certificate, select the instrument and the approved
calibration record, then click **Issue**. Print it with **Print → Calibration
Certificate**.

For a certificate received from an external laboratory, set the issuer type
to *External*, select the issuing laboratory, enter its accreditation
reference, attach the received document and click **Issue**. The document is
mandatory for an external certificate.

An issued certificate can no longer be modified. When a newer certificate
replaces it, open it and click **Supersede**.

## 8. Consulting the history

Open an instrument. The tabs *Calibration Plans*, *Calibration Records* and
*Certificates* show its complete history. The message thread at the bottom of
each record shows who did what and when, including the meaning of each
signature.

Print a calibration record with **Print → Calibration Record**.

## 9. Withdrawing an instrument

Click **Set Out of Service** when the instrument leaves production
temporarily; its status becomes *Not Applicable* and it stops generating
notifications. Click **Retire** when it leaves definitively; its active plans
become obsolete. Nothing is deleted: the history remains available.

## 10. What you cannot do, and why

| Attempt | Response | Reason |
|---------|----------|--------|
| Modify an approved record | Refused | The record is the evidence of a completed calibration. |
| Delete a record that is not draft | Refused | Evidence retention. Cancel it instead. |
| Approve a calibration you performed | Refused | Segregation of duties. |
| Submit an out-of-tolerance record without assessment | Refused | Products already released may be affected. |
| Use an overdue standard | Refused | The calibration would not be traceable. |
| Modify an issued certificate | Refused | Issue a new one and supersede the old one. |
| Activate a plan without a test point | Refused | A plan with no acceptance criterion cannot produce a verdict. |
