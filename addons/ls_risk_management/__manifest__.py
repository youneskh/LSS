# Part of the Life Sciences Suite. See LICENSE file for full copyright
# and licensing details.
{
    "name": "Life Sciences - Risk Management",
    "summary": "Risk register, risk assessment, risk control and FMEA for "
               "regulated life sciences environments",
    "version": "19.0.1.0.1",
    "category": "Life Sciences/Quality",
    "author": "Life Sciences Suite Architecture Team",
    "website": "https://github.com/OCA",
    "license": "AGPL-3",
    "development_status": "Beta",
    # Declared deviation from the functional specification, section 15.3:
    # the specification lists `ls_qms` as a dependency. `ls_qms` is a suite
    # module that is not part of the standard Odoo 19 Community addons path,
    # so declaring it here would prevent this module from installing on a
    # database that does not already carry it. Integration is provided through
    # the `linked_model_id` / `linked_res_id` extension point instead. The
    # deviation and its rationale are recorded in doc/DEVIATIONS.md.
    "depends": [
        "base",
        "mail",
    ],
    "data": [
        "security/ls_risk_security.xml",
        "security/ir.model.access.csv",
        "security/ls_risk_record_rules.xml",
        "data/ir_sequence_data.xml",
        "data/ir_cron_data.xml",
        "data/ls_risk_category_data.xml",
        "data/ls_risk_matrix_data.xml",
        "views/ls_risk_matrix_views.xml",
        "views/ls_risk_category_views.xml",
        "views/ls_risk_register_views.xml",
        "views/ls_risk_assessment_views.xml",
        "views/ls_risk_mitigation_views.xml",
        "views/ls_risk_fmea_views.xml",
        "wizards/ls_risk_wizard_views.xml",
        "report/ls_risk_report_actions.xml",
        "report/ls_risk_register_report_templates.xml",
        "report/ls_risk_fmea_report_templates.xml",
        "views/ls_risk_menus.xml",
    ],
    "demo": [
        "demo/ls_risk_demo.xml",
    ],
    "images": [
        "static/description/icon.png",
    ],
    "application": True,
}
