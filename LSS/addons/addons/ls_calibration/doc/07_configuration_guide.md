# Configuration Guide

Module: `ls_calibration` `19.0.1.0.0`.

## 1. Security groups

Assign the groups in **Settings → Users & Companies → Users**.

| Group | Assign to | Grants |
|-------|-----------|--------|
| *Calibration / Viewer* | Production supervisors, auditors, laboratory staff who only consult the status | Read on the register, the plans, the records and the certificates |
| *Calibration / Technician* | Metrology technicians | Read on the register and the plans; create and complete the calibration records, the test point results and the certificates; submit for approval |
| *Calibration / Manager* | Quality assurance, metrology manager | Everything above, plus the maintenance of the register and the plans, the approval and the rejection of the records, the issue of the certificates and the deletion of draft records |

Each group implies the previous one, so a manager does not need to receive
the two other groups.

**Group category.** The groups are created without a category. The Odoo 19
refactoring of the `res.groups` categories into privileges could not be
verified from official documentation, therefore the module does not set a
field whose name it cannot confirm. If a grouped presentation is required in
the user form, assign the three groups to a privilege directly in the target
database, in developer mode.

## 2. System parameters

**Settings → Technical → Parameters → System Parameters**

| Key | Default | Effect |
|-----|---------|--------|
| `ls_calibration.generation_horizon_days` | `30` | Number of days ahead for which the scheduled action creates the calibration records of the due plans. Increase it to prepare the work further in advance; decrease it to reduce the number of open draft records. |

## 3. Scheduled actions

**Settings → Technical → Automation → Scheduled Actions**

| Action | Default | Recommendation |
|--------|---------|----------------|
| *Calibration: notify due and overdue instruments* | Daily, 01:00 | Keep daily. Running it less often delays the notification of an overdue instrument. |
| *Calibration: generate due calibration records* | Daily, 02:00 | Keep daily and after the notification action. |

Both actions log the number of objects they created, which allows the
administrator to monitor them from the action form.

## 4. Sequences

**Settings → Technical → Sequences & Identifiers → Sequences**

| Sequence | Default prefix | Note |
|----------|----------------|------|
| Calibration Instrument | `INS/` | Adjust the prefix and the padding to the identification scheme of the site before creating the first instrument. |
| Calibration Plan | `CP/` | |
| Calibration Record | `CAL/%(year)s/` | The year is that of the creation of the record. |
| Calibration Certificate | `CERT/%(year)s/` | |

Changing a prefix after records exist produces a discontinuity in the
numbering. In a regulated environment this is a change that must go through
change control.

## 5. Instrument categories

The module reuses the equipment categories of the Maintenance application
rather than creating a parallel taxonomy. Create the categories in
**Maintenance → Configuration → Equipment Categories**. Creating a category
requires the access rights of the Maintenance application; the calibration
groups alone do not grant them.

Suggested categories for a Life Sciences site: balances, thermometers and
temperature loggers, pressure gauges, pH meters, timers, volumetric
instruments, particle counters, torque tools, reference standards.

## 6. Per-instrument configuration

| Field | Guidance |
|-------|----------|
| Alert lead time | Number of days before the due date from which the instrument is reported as *Due Soon*. Set it to at least the time needed to organise the calibration, including the shipment time for an externally calibrated instrument. Default 30 days. |
| Criticality | Output of the quality risk management process of the organisation. |
| GxP impact | Direct, indirect or none, as classified by the organisation. |
| Measuring range and unit | Used as the default proposal for the test points. |
| Maximum permissible error | Default tolerance proposed on the test points of the plans of this instrument. |

## 7. Per-plan configuration

| Field | Guidance |
|-------|----------|
| Interval and unit | The interval defined by the organisation, based on the criticality, the stability of the instrument and its history. |
| Start date | Date of the first calibration expected under this plan. It is the due date as long as no record has been approved. |
| Procedure reference | Identifier of the approved written procedure. The module references it; it does not manage the document. |
| Test points | At least one; the plan cannot be activated otherwise. Enter one point per nominal value that will actually be applied. |
| Externally calibrated and provider | Set when the calibration is subcontracted. The provider is proposed on the generated records. |

## 8. Configuration checklist

| # | Item | Done |
|---|------|------|
| CFG-01 | Sequences adjusted to the site identification scheme, before the first instrument is created | |
| CFG-02 | Equipment categories created | |
| CFG-03 | Groups assigned, with at least two distinct people so that segregation of duties is possible | |
| CFG-04 | Generation horizon set | |
| CFG-05 | Scheduled actions verified as active | |
| CFG-06 | Instruments registered with their metrological data | |
| CFG-07 | Calibration plans created, with their test points, and activated | |
| CFG-08 | Alert lead times set per instrument | |
| CFG-09 | Existing calibration certificates loaded for the instruments already in service | |
| CFG-10 | A first calibration cycle performed end to end in a test database | |
