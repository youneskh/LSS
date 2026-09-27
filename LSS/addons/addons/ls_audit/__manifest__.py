# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
{
    "name": "Life Sciences - Audit Management",
    "version": "19.0.1.0.1",
    "category": "Life Sciences/Quality",
    "summary": "Plan, conduct, report and follow up internal, supplier and "
               "regulatory audits in regulated Life Sciences environments.",
    "author": "Life Sciences Suite Architecture Team",
    "website": "https://github.com/OCA",
    "license": "AGPL-3",
    "depends": [
        "base",
        "mail",
        "hr",
    ],
    "data": [
        # Security must load before any view referencing a group.
        "security/ls_audit_groups.xml",
        "security/ir.model.access.csv",
        "security/ls_audit_record_rules.xml",
        # Master data.
        "data/ir_sequence_data.xml",
        "data/ls_audit_finding_category_data.xml",
        "data/mail_template_data.xml",
        "data/ir_cron_data.xml",
        # Wizards must load before the views that reference their actions.
        "wizards/ls_audit_checklist_load_views.xml",
        "wizards/ls_audit_finding_response_views.xml",
        "wizards/ls_audit_cancel_views.xml",
        # Views.
        "views/ls_audit_type_views.xml",
        "views/ls_audit_area_views.xml",
        "views/ls_audit_auditor_views.xml",
        "views/ls_audit_finding_category_views.xml",
        "views/ls_audit_checklist_views.xml",
        "views/ls_audit_response_views.xml",
        "views/ls_audit_finding_views.xml",
        "views/ls_audit_report_views.xml",
        "views/ls_audit_program_views.xml",
        "views/ls_audit_schedule_views.xml",
        "views/ls_audit_menus.xml",
        # Printable reports.
        "report/ls_audit_report_actions.xml",
        "report/ls_audit_report_templates.xml",
        "report/ls_audit_finding_templates.xml",
    ],
    "demo": [
        "demo/ls_audit_demo.xml",
    ],
    "application": True,
}
