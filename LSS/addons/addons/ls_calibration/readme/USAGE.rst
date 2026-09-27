Registering an instrument
~~~~~~~~~~~~~~~~~~~~~~~~~

Open :menuselection:`Calibration --> Instruments` and create the instrument.
Fill in the measuring range, the unit, the maximum permissible error, the
criticality and the GxP impact. Click :guilabel:`Set In Service` when the
instrument is released for production use.

Defining a calibration plan
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Open :menuselection:`Calibration --> Calibration Plans` and create the plan.
Set the interval, the start date and the reference of the written procedure.
Add one test point per nominal value that will be applied, with its
tolerance. Click :guilabel:`Activate`. A plan cannot be activated without at
least one test point.

Performing a calibration
~~~~~~~~~~~~~~~~~~~~~~~~

The calibration records are created by the scheduled action, by the wizard
:menuselection:`Calibration --> Calibration Status --> Generate Calibration
Records`, or manually from the plan with :guilabel:`Create Calibration
Record`. Open the record, click :guilabel:`Start`, enter the as-found and
as-left readings of every test point, select the reference standards used and
click :guilabel:`Submit to Review`.

Approving a calibration
~~~~~~~~~~~~~~~~~~~~~~~

A Calibration Manager opens the record and clicks :guilabel:`Approve` or
:guilabel:`Reject`. The approval is refused when the approver is the user who
performed the calibration. Once approved, the record is locked and the next
due date of the plan is recomputed automatically.

Monitoring
~~~~~~~~~~

:menuselection:`Calibration --> Calibration Status --> Due and Overdue` lists
the instruments requiring attention. :menuselection:`Calibration -->
Reporting --> Calibration Analysis` provides the pivot and graph views of the
approved calibration records.
