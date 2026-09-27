# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
{
    "name": "Life Sciences - Validation Management",
    "summary": "Validation Master Plans, IQ/OQ/PQ protocols, execution records, "
               "discrepancies, validation summary reports and periodic revalidation.",
    "version": "19.0.1.0.1",
    "category": "Life Sciences/Quality",
    "author": "Life Sciences Suite Architecture Team",
    "website": "https://github.com/OCA",
    "license": "AGPL-3",
    "depends": [
        "mail",
    ],
    "external_dependencies": {
        "python": [],
        "bin": [],
    },
    "data": [
        "security/ls_validation_groups.xml",
        "security/ir.model.access.csv",
        "security/ls_validation_rules.xml",
        "data/ir_sequence_data.xml",
        "data/ir_config_parameter_data.xml",
        "data/ir_cron_data.xml",
        "views/ls_validation_item_views.xml",
        "views/ls_validation_master_plan_views.xml",
        "views/ls_validation_protocol_views.xml",
        "views/ls_validation_execution_views.xml",
        "views/ls_validation_discrepancy_views.xml",
        "views/ls_validation_report_views.xml",
        "views/ls_validation_signature_views.xml",
        "wizards/ls_validation_sign_wizard_views.xml",
        "wizards/ls_validation_revalidation_wizard_views.xml",
        "report/ls_validation_report_actions.xml",
        "report/ls_validation_protocol_templates.xml",
        "report/ls_validation_summary_templates.xml",
        "views/ls_validation_menus.xml",
    ],
    "demo": [
        "demo/ls_validation_demo.xml",
    ],
    "application": True,
}
