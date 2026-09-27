# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
{
    "name": "Life Sciences - Change Control",
    "summary": "Regulated change control: request, impact assessment, "
               "approval, implementation and effectiveness verification.",
    "version": "19.0.1.0.1",
    "category": "Life Sciences/Quality",
    "author": "Life Sciences Suite Architecture Team",
    "website": "https://github.com/OCA",
    "license": "AGPL-3",
    "depends": [
        "base",
        "mail",
        "hr",
    ],
    "data": [
        "security/ls_change_control_groups.xml",
        "security/ir.model.access.csv",
        "security/ls_change_control_rules.xml",
        "data/ir_sequence_data.xml",
        "data/ls_change_control_impact_area_data.xml",
        "data/ls_change_control_category_data.xml",
        "data/mail_template_data.xml",
        "data/ir_cron_data.xml",
        "report/change_control_request_templates.xml",
        "report/change_control_request_report.xml",
        "views/change_control_impact_area_views.xml",
        "views/change_control_category_views.xml",
        "views/change_control_assessment_views.xml",
        "views/change_control_approval_views.xml",
        "views/change_control_implementation_views.xml",
        "views/change_control_verification_views.xml",
        "views/change_control_request_views.xml",
        "views/res_company_views.xml",
        "wizards/change_control_decision_wizard_views.xml",
        "views/ls_change_control_menus.xml",
    ],
    "demo": [
        "demo/ls_change_control_demo.xml",
    ],
    "application": True,
}
