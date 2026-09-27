# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0.html).
{
    "name": "Life Sciences - CAPA Management",
    "summary": "Corrective and Preventive Action management for regulated "
               "Life Sciences organizations.",
    "version": "19.0.1.0.2",
    "category": "Life Sciences/Quality",
    "author": "Life Sciences Suite Architecture Team",
    "website": "https://github.com/OCA",
    "license": "AGPL-3",
    "depends": [
        "base",
        "mail",
        "project",
    ],
    "external_dependencies": {"python": []},
    "data": [
        "security/ls_capa_groups.xml",
        "security/ir.model.access.csv",
        "security/ls_capa_security.xml",
        "data/ir_sequence_data.xml",
        "data/ls_capa_category_data.xml",
        "data/ir_cron_data.xml",
        "views/capa_category_views.xml",
        "views/capa_root_cause_views.xml",
        "views/capa_action_views.xml",
        "views/capa_effectiveness_views.xml",
        "views/capa_issue_views.xml",
        "wizards/capa_close_wizard_views.xml",
        "report/capa_issue_report.xml",
        "report/capa_issue_report_templates.xml",
        "views/ls_capa_menus.xml",
    ],
    "demo": [
        "demo/ls_capa_demo.xml",
    ],
}
