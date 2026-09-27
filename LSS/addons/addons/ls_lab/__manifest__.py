# Part of the Life Sciences Suite. See LICENSE file for full copyright and licensing details.
{
    "name": "Life Sciences — Laboratory Management",
    "version": "19.0.1.0.1",
    "category": "Manufacturing/Quality",
    "summary": "QC laboratory: samples, test methods, specifications, results, "
               "OOS/OOT investigations, stability studies and certificates of analysis",
    "description": """
Laboratory Management for regulated Life Sciences environments
==============================================================

Provides a quality-control laboratory system covering:

* Analytical test method register with approval lifecycle and versioning
* Product specifications with explicit acceptance criteria and versioning
* Sample registration, testing, second-person review and approval
* Test results whose conformity evaluation is derived from the approved
  specification and is never writable by a user
* Out-of-specification and out-of-trend investigations with a two-phase
  structure, authorised retest and resample, conclusion and disposition
* Stability studies with configurable storage conditions and time points
* Certificates of Analysis with a QWeb PDF report

This module supports implementation of laboratory processes. It does not
certify compliance with any regulatory framework. Electronic signature
functionality is limited to signature-intent confirmation and does not
implement re-authentication; FDA 21 CFR Part 11 compliance is not claimed.
See doc/ for the full regulatory analysis and validation report.
""",
    "author": "Life Sciences Suite",
    "website": "https://github.com/OCA",
    "license": "LGPL-3",
    "depends": [
        "base",
        "mail",
        "product",
        "stock",
        "uom",
    ],
    "data": [
        "security/ls_lab_security.xml",
        "security/ir.model.access.csv",
        "data/ir_sequence_data.xml",
        "data/ir_cron_data.xml",
        "views/ls_lab_storage_condition_views.xml",
        "views/ls_lab_test_method_views.xml",
        "views/ls_lab_specification_views.xml",
        "views/ls_lab_sample_views.xml",
        "views/ls_lab_test_result_views.xml",
        "views/ls_lab_oos_views.xml",
        "views/ls_lab_stability_views.xml",
        "views/ls_lab_coa_views.xml",
        "wizard/ls_lab_wizard_views.xml",
        "report/ls_lab_report_actions.xml",
        "report/ls_lab_coa_template.xml",
        "report/ls_lab_oos_template.xml",
        "views/ls_lab_menus.xml",
    ],
    "application": True,
}
