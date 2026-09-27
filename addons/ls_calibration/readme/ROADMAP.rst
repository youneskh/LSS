Known limitations
~~~~~~~~~~~~~~~~~

* **Electronic signature.** The module records the identity of the signer,
  the date and time of the signature and its meaning in the message thread.
  It does **not** re-authenticate the user at the moment of the signature.
  Re-authentication is a requirement of FDA 21 CFR Part 11 for a compliant
  electronic signature and is expected to be provided by a dedicated module
  of the Life Sciences Suite. This module must not be presented as
  implementing Part 11 electronic signatures on its own.

* **Audit trail.** Field level tracking is provided by the standard Odoo
  ``mail.thread`` mechanism on the tracked fields only. A complete field
  level audit trail with tamper evidence is out of the scope of this module.

* **Dependency on the Life Sciences core.** The functional specification of
  the suite lists ``ls_qms`` as a dependency of the calibration module. That
  module does not exist, therefore declaring the dependency would prevent the
  installation. The dependency is deliberately omitted. A bridge module can
  add the quality management links once ``ls_qms`` is available.

* **Calibration status is not stored.** The status is computed at read time
  so that it is always accurate. As a consequence it cannot be used in a
  group by or in a pivot view. The provided filters cover the operational
  need.

* **Grouping of the search on the calibration status.** The search method
  filters the candidate instruments in Python. The approach is suitable for
  the number of instruments of a manufacturing site and is documented in the
  technical specification.

Roadmap
~~~~~~~

* Bridge module with ``ls_qms`` to link an out-of-tolerance event to a
  deviation and to a corrective action.
* Bridge module with ``ls_lab`` to block the recording of a test result
  produced by an instrument whose calibration is overdue.
* Import of the calibration certificates of the external laboratories from a
  structured file.
