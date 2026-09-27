=======================================
Life Sciences - Supplier Qualification
=======================================

.. |badge1| image:: https://img.shields.io/badge/licence-AGPL--3-blue.png
    :target: https://www.gnu.org/licenses/agpl-3.0-standalone.html
    :alt: License: AGPL-3
.. |badge2| image:: https://img.shields.io/badge/odoo-19.0-purple.png
    :alt: Odoo 19.0 Community

|badge1| |badge2|

Supplier registration, assessment, audit, approval, performance monitoring and
periodic review for regulated life-sciences organisations, on Odoo 19
Community Edition.

.. IMPORTANT::
   This module **does not certify compliance with any regulatory framework**.
   It is a record-keeping and workflow tool. Compliance depends on an
   organisation's procedures, people, validation activities and decisions.
   See ``doc/02_regulatory_analysis.md`` for the precise statement of limits.

.. contents::
   :local:

What it does
============

The module holds one **qualification dossier** per supplier per company, and
everything else hangs off it: the qualified scope, the assessments, the audits
and their findings, the performance scorecards, the periodic reviews and an
append-only signature log.

* **The approval says what it covers.** A dossier cannot be approved without at
  least one qualified material or service, and every approval carries an end of
  validity.
* **Prerequisites are configuration, not code.** The supplier category decides
  whether an assessment and an audit are required and how long an approval
  lasts. The dossier shows what is still missing and refuses submission until
  the list is empty.
* **Past results do not move.** Scoring scale, thresholds and the mandatory
  minimum are frozen onto each assessment at creation, so editing a
  questionnaire never changes a recorded result.
* **Decisions are logged and the log is tamper-evident.** Signer, timestamp,
  stated meaning, written justification and a JSON snapshot of the signed
  values, chained with SHA-256, with a verification action that detects
  modification made directly in the database.
* **Approvals expire by themselves.** A daily job expires elapsed approvals and
  warns beforehand.
* **Purchasing is gated.** At confirmation, a purchase order is ignored, warned
  about, or refused, depending on a per-company setting, with an optional check
  that ordered products are inside the qualified scope.
* **Segregation of duties without a rigid role split.** The approver of a
  dossier cannot be one of its assessors or lead auditors, and an assessment
  cannot be reviewed by its own assessor. Switchable per company as a
  documented decision.

Installation
============

Copy the module into your ``addons_path`` and install it::

    odoo-bin -d <database> -i ls_supplier_qualification --stop-after-init

Dependencies: ``base``, ``mail``, ``product``, ``purchase``. All Community
Edition. No external Python package is required. ``purchase_stock`` is
optional and only enables the automatic delivery counters.

Full instructions, including three post-installation verification points, are
in ``doc/06_installation_guide.md``.

Configuration
=============

Ships with a working starter configuration: 10 supplier categories, 32
assessment criteria, 2 questionnaires and 13 framework designations.

.. WARNING::
   The shipped criticality levels, intervals, weights, thresholds and criterion
   wording are **proposals made by this module**. They are not derived from any
   regulation. Review and approve them under your own change control before
   first use. See ``doc/07_configuration_guide.md``.

Company settings live under **Settings → Supplier Qualification**: governance
(segregation of duties, reminder lead times), purchase control level, and the
performance scorecard weights and thresholds.

Usage
=====

**Supplier Qualification** menu:

* **Qualification** — dossiers, qualified scope, expiring approvals
* **Evaluation** — assessments, audits, audit findings
* **Monitoring** — performance evaluations, periodic reviews, signature log
* **Configuration** — categories, criteria, templates, reference standards
  (manager only)

Typical flow: register a supplier, define the scope, run an assessment, run an
audit if the category requires one, submit for approval, approve with a
justification and a signature, then monitor performance and review periodically.

See ``doc/08_user_manual.md``.

Security groups
===============

============================ ====================================================
Group                        Grants
============================ ====================================================
Supplier Viewer              Read access to every qualification record.
Supplier Assessor            Viewer, plus conducting assessments, audits and
                             performance evaluations. No approval, no delete,
                             no configuration.
Supplier Manager             Assessor, plus configuration, approval, status
                             changes and review decisions.
============================ ====================================================

No group is granted automatically to new users. No group holds write access to
the signature log.

Known issues and limitations
============================

* **Electronic signature.** The approval dialog asks the signer to retype their
  own login. That confirms intent; it does not re-authenticate the signer.
  Re-authentication is delegated to a future ``ls_electronic_signature`` module.
  Until then, cover the second identification component by other documented
  means. See ``doc/02_regulatory_analysis.md`` §2.4.
* **Framework mapping.** The mapping between module functions and regulatory
  frameworks is an architectural recommendation, not a verified clause-by-clause
  mapping.
* **ANPP requirements.** The published ANPP (Algeria) requirements for supplier
  qualification could not be verified from official documentation. The module
  provides a placeholder entry so an organisation can attach its own verified
  requirements, and makes no statement about their content.
* **Delivery counters.** Automatic counters require ``purchase_stock``. Without
  it the button reports the missing module and the counters stay manual.
* **Delivery status.** The test suite and the standard linters were not executed
  in the environment where this module was built. See
  ``doc/12_test_report.md`` §7.1 and ``doc/13_static_analysis_report.md`` §8.1,
  and close the four items in ``doc/15_compliance_checklist.md`` §10.6 before
  production use.

Testing
=======

141 tests across 14 modules::

    odoo-bin -d <test_database> -i ls_supplier_qualification \
        --test-enable --test-tags /ls_supplier_qualification --stop-after-init

Offline consistency checks, needing only Python and ``lxml``::

    python3 tools/static_check.py .

Documentation
=============

``doc/`` contains the ten delivery phases, four manuals and the API reference:

=================================== ==========================================
File                                Content
=================================== ==========================================
01_business_analysis.md             Objectives, requirements, roles, risks
02_regulatory_analysis.md           Frameworks, limits, Part 11 statement
03_functional_specification.md      Menus, state machines, business rules
04_technical_specification.md       Models, fields, constraints, security
05_architecture_review.md           Findings, deviations, verification points
06_installation_guide.md            Install, verify, upgrade, uninstall
07_configuration_guide.md           Every configurable value explained
08_user_manual.md                   Day-to-day use
09_administrator_manual.md          Security, signature log, monitoring
10_developer_manual.md              Conventions, design, extension points
11_api_documentation.md             Public methods and RPC examples
12_test_report.md                   Test design, traceability, execution status
13_static_analysis_report.md        Checks performed and gaps
14_validation_report.md             Validation approach and outstanding evidence
15_compliance_checklist.md          Final 50-point checklist
=================================== ==========================================

Credits
=======

Authors
-------

* Life Sciences Suite Architecture Team

Licence
-------

AGPL-3. See the ``LICENSE`` reference in each source file header.
