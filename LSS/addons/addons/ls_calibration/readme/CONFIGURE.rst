#. Assign the security groups to the users in
   :menuselection:`Settings --> Users & Companies --> Users`:

   * *Calibration / Viewer*: read-only access.
   * *Calibration / Technician*: performs the calibrations and records the
     readings.
   * *Calibration / Manager*: maintains the register and the plans, approves
     or rejects the calibration records.

   The groups are created without a category. The refactoring of the
   ``res.groups`` categories into privileges announced for Odoo 19 could not
   be verified from official documentation, therefore no category is set by
   the module. Assign the groups to a privilege in the target database if a
   grouped presentation is required in the user form.

#. Adjust the generation horizon in :menuselection:`Settings --> Technical
   --> System Parameters`. The parameter
   ``ls_calibration.generation_horizon_days`` defines how many days in
   advance the scheduled action creates the calibration records of the due
   plans. The default value is 30 days.

#. Review the two scheduled actions in :menuselection:`Settings --> Technical
   --> Scheduled Actions`:

   * *Calibration: notify due and overdue instruments*, daily.
   * *Calibration: generate due calibration records*, daily.

#. Set the alert lead time on each instrument. It defines how many days
   before the due date the instrument is reported as *Due Soon*. The default
   value is 30 days.

#. Optionally create instrument categories in the Maintenance application.
   The module reuses ``maintenance.equipment.category`` rather than creating
   a parallel taxonomy. Creating a category requires the access rights of the
   Maintenance application.
