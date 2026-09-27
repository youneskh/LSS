=============================================
Life Sciences - Training Management
=============================================

.. |badge1| image:: https://img.shields.io/badge/maturity-Beta-yellow.png
    :alt: Beta
.. |badge2| image:: https://img.shields.io/badge/licence-AGPL--3-blue.png
    :alt: License: AGPL-3
.. |badge3| image:: https://img.shields.io/badge/odoo-19.0-purple.png
    :alt: Odoo 19.0 Community

|badge1| |badge2| |badge3|

Training, certification and competency management for regulated Life
Sciences environments — pharmaceutical manufacturing, medical devices,
medical plastics, cosmetics and laboratories.

.. IMPORTANT::
   This release has **never been installed or executed**. It was developed
   without access to an Odoo 19 runtime. Read ``doc/verification_notes.md``
   before installing, and install on a scratch database first.

.. contents::
   :local:

Features
========

**Controlled course catalogue**

* Four-state approval lifecycle: Draft, Under Review, Approved, Obsolete
* Explicit versioning; the version in force is frozen onto every
  certification issued
* Only approved courses can be scheduled
* Classroom, on-the-job, self-study and external e-Learning delivery modes
* Configurable certification validity and assessment pass mark

**Session delivery**

* Five-state lifecycle with enforced sequencing
* Bulk registration by selected employees, department, job position, or
  training requirement
* Optional exclusion of employees who already hold a valid certification
* Capacity control
* Attendance and assessment score captured per attendee

**Derived outcomes**

The pass/fail result is computed from recorded evidence — presence, and
where the course requires it, the assessment score against the pass mark.
It cannot be typed directly, so any outcome can be reconstructed from its
inputs.

Absence yields *Pending*, not *Failed*, because non-attendance is not a
failed assessment.

**Append-only certifications**

* Issued automatically when a session closes
* Recorded manually for externally delivered training
* Never deletable — revocation with a documented reason is the only
  withdrawal path
* Renewal creates a new record; history is never overwritten
* Status computed from the expiry date and refreshed nightly

**Training requirements and matrix**

* Requirements target a job position, a department, or a named employee
* Mandatory requirements drive the per-employee compliance rate
* The matrix reports every employee/course cell as Valid, Expiring Soon,
  Expired, Revoked or Not Trained
* List and pivot views, with a Gaps filter

**Competency assessments**

Evidence that someone can do the job, kept separate from evidence that they
attended a class. Named assessor, demonstrated level, written evidence,
confirmation lock, and optional periodic reassessment.

**Automation**

* Daily refresh of certification status
* Daily expiry reminders inside a configurable warning window
* Email template addressed to the employee's work email

**Reporting**

* Training Certificate (PDF, per certification)
* Individual Training Record (PDF, per employee)

Regulatory position
===================

This module **supports implementation** of training and competence
processes of the kind expected by ISO 9001:2015, ISO 13485:2016, GMP
guidance, ISO 22716:2007, ISO 15378:2017 and FDA 21 CFR Part 211.

It does **not** implement FDA 21 CFR Part 11. There is no electronic
signature and no field-level audit trail. Do not represent this module as
Part 11 compliant.

It implements nothing ANPP-specific, because ANPP training-record
requirements could not be verified from official sources.

**Software does not deliver compliance.** Compliance is produced by an
organisation's procedures, its trained personnel, its quality system and
its own validation of the tools it uses. See ``doc/regulatory_analysis.md``.

Data integrity controls
=======================

+--------------------------------------+-----------------------------------+
| Control                              | Mechanism                         |
+======================================+===================================+
| Outcome reproducible from evidence   | ``result`` computed, not writable |
+--------------------------------------+-----------------------------------+
| Historical accuracy preserved        | Course version frozen at issuance |
+--------------------------------------+-----------------------------------+
| Evidence not retroactively altered   | Write guards on closed sessions   |
+--------------------------------------+-----------------------------------+
| Records not destroyable              | ``unlink`` raises on certification|
+--------------------------------------+-----------------------------------+
| Withdrawal traceable                 | Revocation requires a reason      |
+--------------------------------------+-----------------------------------+
| Sequencing enforced                  | Two guarded state machines        |
+--------------------------------------+-----------------------------------+
| Authorisation enforced               | 4 groups, 31 ACL lines, 13 rules  |
+--------------------------------------+-----------------------------------+

Installation
============

Copy ``ls_training`` into your ``addons_path``, update the apps list, and
install. Full instructions, including the anticipated failure mode and its
one-line fix, are in ``doc/installation_guide.md``.

Requires ``base``, ``mail`` and ``hr``. No additional Python package. No
custom JavaScript.

Configuration
=============

See ``doc/configuration_guide.md``. In summary:

#. Assign the four training groups
#. Ensure every employee has a Related User and a Work Email
#. Set ``ls_training.expiry_warning_days`` (default 30)
#. Create competencies, then courses, then approve them
#. Define training requirements
#. Verify both scheduled actions are active

Usage
=====

See ``doc/user_manual.md``.

Known issues
============

* The test suite (146 tests) has never been executed.
* Five Odoo 19 API assumptions are unverified; each is catalogued in
  ``doc/verification_notes.md`` with its remediation. The highest-risk one
  ships with a working alternate file.
* Matrix generation issues O(employees × courses) queries, bounded at
  20 000 lines.
* The compliance rate is not stored and therefore cannot be searched or
  grouped.
* Reminders repeat daily and do not escalate to managers.

Roadmap
=======

* Bridge module for ``ls_electronic_signature`` (Part 11 signature on
  session closure)
* Bridge module for ``ls_audit_trail`` (field-level audit trail)
* Bridge module for ``ls_document_management`` (courses linked to
  controlled SOPs)
* Bridge module for Odoo eLearning (``website_slides``)
* Manager escalation on overdue mandatory training
* SQL-view matrix variant, once the Odoo 19 ``hr`` schema is confirmed

Credits
=======

Authors
-------

* Life Sciences Suite Architecture Team

License
-------

AGPL-3. See the ``LICENSE`` file of the Odoo Community Association or
https://www.gnu.org/licenses/agpl-3.0.
