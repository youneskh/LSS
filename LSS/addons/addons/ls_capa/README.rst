================================
Life Sciences - CAPA Management
================================

.. |badge1| image:: https://img.shields.io/badge/licence-AGPL--3-blue.png
.. |badge2| image:: https://img.shields.io/badge/odoo-19.0-purple.png

|badge1| |badge2|

Corrective and Preventive Action (CAPA) management for organizations
operating under GxP, ISO 9001, ISO 13485 and comparable quality frameworks.

This module implements module ``ls_capa`` of the Life Sciences Suite
functional specification (section 7.3).

**Regulatory notice.** This module is designed to *support* the
implementation of CAPA processes. It does not certify, guarantee or
establish compliance with any regulatory framework. Compliance depends on
organizational procedures, computerised system validation, personnel
training and ongoing monitoring, none of which are supplied by software.

.. contents::
   :local:

Features
========

* CAPA records with an eight-state lifecycle: Identified, Assessed,
  Investigation, Action Planning, In Progress, Completed, Verified, Closed.
* Issue classification by source, CAPA type, severity, priority and
  configurable category.
* Impact assessment covering product quality, regulatory status and
  patient or user safety.
* Root cause analysis with three methods: Five Whys, Ishikawa
  (cause and effect) and FMEA with an automatically computed Risk
  Priority Number.
* Corrective and preventive action planning, execution tracking and
  optional mirroring to ``project.task``.
* Effectiveness verification against acceptance criteria defined in
  advance, with escalation to a follow-up CAPA when a check concludes
  Not Effective.
* Four segregated security groups, multi-company record rules, full
  chatter tracking and a printable CAPA report.

Workflow and gating rules
=========================

Each transition is gated by a business rule. The gates are design
decisions of this module, not verbatim regulatory text.

.. list-table::
   :header-rows: 1

   * - Transition
     - Gate
   * - Identified to Assessed
     - An impact assessment is documented.
   * - Assessed to Investigation
     - None.
   * - Investigation to Action Planning
     - At least one root cause analysis is Confirmed.
   * - Action Planning to In Progress
     - At least one action exists.
   * - In Progress to Completed
     - Every action is Done or Cancelled.
   * - Completed to Verified
     - At least one effectiveness check concluded Effective, and no
       check is still open.
   * - Verified to Closed
     - A closure summary is recorded.

Actions require completion evidence before they can be marked Done, and a
cancellation reason before they can be cancelled. CAPA records that
progressed beyond Identified cannot be deleted; they are archived.

Security groups
===============

.. list-table::
   :header-rows: 1

   * - Group
     - Capability
   * - CAPA Viewer
     - Read-only access to all CAPA data.
   * - CAPA Investigator
     - Creates CAPA records and performs root cause analyses.
   * - CAPA Coordinator
     - Additionally plans and executes actions and effectiveness checks.
   * - CAPA Manager
     - Full access including verification, closure, deletion and
       configuration.

Groups form an implication chain, so each level inherits the level below.

Configuration
=============

#. Go to *Quality > Configuration > CAPA Categories* to review the five
   preloaded categories and their default resolution lead times.
#. To mirror actions into a specific project, set the system parameter
   ``ls_capa.default_project_id`` to the numeric id of that project under
   *Settings > Technical > System Parameters*. When unset, generated tasks
   are created without a project.
#. The scheduled action *CAPA: Notify Overdue Records* is shipped
   **inactive**. Activate it under *Settings > Technical > Scheduled
   Actions* if daily overdue reminders are wanted.

Regulatory mapping
==================

The following mapping states which clause each capability is intended to
support. It is a design intent statement and is not a compliance
certification. Clause numbers are cited from the published structure of
the referenced standards.

.. list-table::
   :header-rows: 1

   * - Capability
     - Intended to support
   * - CAPA lifecycle and records
     - ISO 9001:2015 clause 10.2; ISO 13485:2016 clause 8.5;
       FDA 21 CFR Part 820.100
   * - Root cause analysis
     - ISO 13485:2016 clause 8.5.2; GMP deviation investigation practice
   * - Effectiveness verification
     - ISO 13485:2016 clause 8.5.2; FDA 21 CFR Part 820.100(a)(4)
   * - Chatter tracking of field changes and state transitions
     - Data integrity expectations for attributable, contemporaneous
       records
   * - Segregated security groups
     - Segregation of duties between investigation, execution and
       verification

**Verification note.** The mapping above reflects the module design
intent. Whether an implementation satisfies any given clause can only be
determined by the implementing organization through validation.

Architectural decisions
=======================

**AD-01: dependency on ls_qms is deferred.**
The functional specification lists ``ls_qms`` and ``project`` as
dependencies of ``ls_capa``. ``ls_qms`` is an architectural
recommendation in that specification and does not exist as an
installable Odoo module. Declaring a dependency on a non-existent module
would make ``ls_capa`` uninstallable. This module therefore depends on
``base``, ``mail`` and ``project`` only, and is fully functional
standalone. When ``ls_qms`` is delivered, integration should be added
through a separate bridge module (for example ``ls_qms_capa``) following
the OCA glue-module pattern, rather than by adding the dependency here.

**AD-02: own root menu.**
For the same reason, this module creates its own *Quality* root menu. A
bridge module can reparent the CAPA menu under the ``ls_qms`` root.

**AD-03: model naming follows the specification.**
The specification names the model ``ls.capa.root_cause``. Odoo
convention would favour ``ls.capa.root.cause``. The specification naming
is retained so that traceability between specification and code is
unambiguous.

**AD-04: no electronic signature in this module.**
The specification assigns electronic signatures to
``ls_electronic_signature``. Approval steps here are recorded through
tracked state transitions and the chatter audit trail. Organizations
subject to FDA 21 CFR Part 11 signature requirements must implement that
module and bind it to the CAPA transitions; this module alone does not
provide compliant electronic signatures.

Known limitations
=================

* Field-level audit trail relies on the Odoo ``mail.thread`` tracking
  mechanism. It is not a tamper-evident, hash-chained audit trail. Where
  that is required, ``ls_audit_trail`` must be implemented.
* Deleting a CAPA in the Identified state removes it and its children
  permanently. Organizations requiring full retention should restrict
  the CAPA Manager group accordingly.
* The module does not implement periodic CAPA trending reports beyond the
  supplied pivot and graph views.

Testing
=======

Run the test suite with::

    odoo --test-enable --stop-after-init -i ls_capa -d <database>

The suite contains 112 tests across seven modules covering creation and
sequencing, the full state machine and every gate, all three root cause
methods, action and effectiveness lifecycles, SQL and Python
constraints, and access rights for all four groups.

Credits
=======

Authors
-------

* Life Sciences Suite Architecture Team

License
-------

AGPL-3. See the LICENSE file for the full licence text.
