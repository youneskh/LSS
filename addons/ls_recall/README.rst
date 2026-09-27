==========================================
Recall and Field Action Management
==========================================

.. |badge1| image:: https://img.shields.io/badge/licence-AGPL--3-blue.png
   :target: https://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

|badge1|

Manage product recalls, market withdrawals, stock recoveries and field
safety corrective actions in Odoo 19 Community Edition.

The module holds the record of a field action from the decision to the
closure: the basis for the decision, who received the affected lots,
what was sent to them, what they said, how much came back, and what was
reported to whom.

**Read** ``doc/14_verification_register.md`` **before deploying.** The
test suite has never been executed and no coverage figure is claimed.

Features
========

* **Recall plans** as versioned controlled documents, with review,
  approval, revision and a mandatory deputy coordinator so a recall can
  be started outside office hours.
* **Five action types**: recall, market withdrawal, stock recovery,
  field safety corrective action, and mock recall for rehearsals.
* **Gated state machine.** Each forward transition asserts that the
  evidence the next phase presupposes already exists, so the state is a
  factual claim rather than a label.
* **Distribution tracing** from completed stock movements of the
  affected lots, idempotent with respect to user-entered data.
* **Consignee reconciliation** with distributed, returned, destroyed,
  unrecoverable, accounted and outstanding quantities, and automatic
  flagging of discrepancies.
* **Controlled communications.** A recall notice cannot be issued until
  five content elements have been confirmed, and cannot be reworded once
  sent.
* **Effectiveness checks** with sampling levels A to E, escalation and
  repeat attempts.
* **Reports** whose figures freeze on approval, with reviewer and
  approver separation.
* **Closure gating** with a manager-only, justified override.
* **Lot warnings** visible to warehouse staff regardless of role.

Regulatory position
===================

The module **supports** implementation of processes that several
frameworks require. It does **not** make an organisation compliant and
is not certified against anything.

Structure is implemented for:

* 21 CFR Part 7 Subpart C — action types, health hazard classes, depth,
  public warning, effectiveness check levels, communication content
  elements, status reports.
* EudraLex Volume 4 Part I Chapter 8 — written arrangements, designated
  coordinator with out-of-hours cover, reconciliation, authority
  notification, periodic rehearsal.
* Regulation (EU) 2017/745 — field safety corrective actions and field
  safety notices.

Explicitly **not** claimed: 21 CFR Part 11 electronic signatures, and
any ANPP mapping. Reasoning in ``doc/02_regulatory_analysis.md``.

Installation
============

Requires Odoo 19.0 Community. Depends on ``mail`` and ``stock`` only.
No third-party Python package is needed.

See ``doc/06_installation_guide.md``.

Configuration
=============

Assign roles, review the two scheduled actions, then create and approve
a recall plan. See ``doc/07_configuration_guide.md``.

Usage
=====

See ``doc/08_user_manual.md`` for a full walkthrough.

Known limitations
=================

* No field-level audit trail; change history is Odoo's chatter over
  tracked fields.
* No electronic signature.
* Record immutability is enforced at application level, not at database
  level.
* Tracing sees only distribution recorded in Odoo; product distributed
  outside must be entered manually.
* Lot-level granularity; no serial-level aggregation tracing.
* One product per field action.

Documentation
=============

===================================== =========================================
``doc/01_business_analysis.md``       Objectives, requirements, roles, risks
``doc/02_regulatory_analysis.md``     Provision-by-provision mapping and limits
``doc/03_functional_specification.md`` States, gates, rules, reports
``doc/04_technical_specification.md`` Models, constraints, security, algorithm
``doc/05_architecture_review.md``     Review, deviations D-01 to D-04
``doc/06_installation_guide.md``      Install, test, upgrade, uninstall
``doc/07_configuration_guide.md``     Roles, sequences, plans, products
``doc/08_user_manual.md``             End-to-end walkthrough
``doc/09_administrator_manual.md``    Data, immutability, inspection readiness
``doc/10_developer_manual.md``        Extension seams and conventions
``doc/11_api_documentation.md``       Model and method reference
``doc/12_test_plan_and_report.md``    What was and was not executed
``doc/13_validation_report.md``       Qualification inputs; status incomplete
``doc/14_verification_register.md``   Every unverified assumption
``doc/15_compliance_checklist.md``    Final checklist with honest statuses
===================================== =========================================

Credits
=======

Authors
-------

* Life Sciences Suite Project

Maintainer
----------

Replace the ``author`` and ``website`` keys in ``__manifest__.py``
before release.

License
=======

AGPL-3. See the LICENSE file of the Odoo Community Association for the
full text of the licence.
