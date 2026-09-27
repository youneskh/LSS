# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0.html).
{
    "name": "Life Sciences - Audit Trail",
    "summary": "Tamper-evident, field-level audit trail for GxP-regulated Odoo data.",
    "version": "19.0.1.0.1",
    "category": "Life Sciences/Quality",
    "author": "Life Sciences Suite Architecture Team",
    "website": "https://github.com/OCA",
    "license": "AGPL-3",
    "depends": [
        "base",
        "mail",
    ],
    # The load order matters: the report actions are referenced by a button in
    # the evidence pack form, and the wizard actions are referenced by menu
    # items, so both must be loaded before the files that reference them.
    "data": [
        "security/ls_audit_trail_groups.xml",
        "security/ir.model.access.csv",
        "security/ls_audit_trail_record_rules.xml",
        "data/ir_cron_data.xml",
        "report/ls_audit_trail_report_actions.xml",
        "report/ls_audit_trail_report_templates.xml",
        "views/ls_audit_trail_log_views.xml",
        "views/ls_audit_trail_rule_views.xml",
        "views/ls_audit_trail_verification_views.xml",
        "views/ls_audit_trail_evidence_pack_views.xml",
        "views/res_company_views.xml",
        "wizards/ls_audit_trail_verify_wizard_views.xml",
        "wizards/ls_audit_trail_purge_wizard_views.xml",
        "views/ls_audit_trail_menus.xml",
    ],
    "demo": [
        "demo/ls_audit_trail_demo.xml",
    ],
    "images": [
        "static/description/icon.png",
    ],
    "application": True,
}
