# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
{
    "name": "Life Sciences - Document Management",
    "summary": "Controlled document management for regulated Life Sciences use",
    "version": "19.0.1.0.1",
    "category": "Life Sciences/Quality",
    "author": "Life Sciences Suite Architecture Team",
    "website": "https://github.com/OCA",
    "license": "AGPL-3",
    "depends": [
        "base",
        "mail",
    ],
    "data": [
        "security/ls_document_groups.xml",
        "security/ir.model.access.csv",
        "security/ls_document_record_rules.xml",
        "data/ir_sequence_data.xml",
        "data/ir_cron_data.xml",
        "wizard/ls_document_wizard_views.xml",
        "views/ls_document_retention_policy_views.xml",
        "views/ls_document_tag_views.xml",
        "views/ls_document_folder_views.xml",
        "views/ls_document_version_views.xml",
        "views/ls_document_approval_views.xml",
        "views/ls_document_link_views.xml",
        "views/ls_document_document_views.xml",
        "report/ls_document_control_record_templates.xml",
        "report/ls_document_control_record_report.xml",
        "views/ls_document_menus.xml",
    ],
    "demo": [
        "demo/ls_document_demo.xml",
    ],
    "application": True,
}
