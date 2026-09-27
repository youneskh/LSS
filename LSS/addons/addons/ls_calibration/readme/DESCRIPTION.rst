The calibration of the measuring, monitoring and test instruments is a
recurring requirement of every quality management standard applicable to the
Life Sciences industries. A measurement that is used to accept or reject a
product, a process or an environmental condition is only meaningful when the
instrument that produced it is traceable to a recognised standard and is
verified at a defined interval.

Odoo 19 Community provides the Maintenance application, which manages
equipment and maintenance requests, but it does not manage metrological data,
calibration intervals, as-found and as-left readings, out-of-tolerance
handling or calibration certificates. This module adds those capabilities.

Functional scope
~~~~~~~~~~~~~~~~

* Instrument register with measuring range, unit, maximum permissible error,
  criticality, GxP impact classification and life cycle states.
* Calibration plans defining the interval, the written procedure reference,
  the test points and their acceptance limits.
* Automatic computation of the last calibration date, of the next due date
  and of the calibration status: valid, due soon, overdue, not scheduled or
  not applicable.
* Calibration records carrying the as-found readings, the as-left readings,
  the reference standards used, the ambient conditions and the conclusion.
* Automatic verdict per test point and overall result: pass, pass after
  adjustment, or fail.
* Mandatory impact assessment when the as-found readings are out of
  tolerance.
* Refusal of a reference standard whose own calibration is overdue.
* Review and approval workflow with segregation of duties: the user who
  performed the calibration cannot approve it.
* Locking of approved records: neither the record nor its test points can be
  modified or deleted afterwards.
* Calibration certificates issued internally or registered from an external
  accredited laboratory, with the certificate document attached.
* Two scheduled actions: notification of the instruments that are due or
  overdue, and generation of the calibration records of the due plans.
* Two PDF reports: the calibration record and the calibration certificate.
