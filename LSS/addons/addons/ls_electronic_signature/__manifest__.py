# Part of the Life Sciences Suite. See LICENSE file for full copyright details.
{
    "name": "Life Sciences - Electronic Signatures",
    "summary": (
        "Electronic signatures with signature manifestations, signature/record "
        "linking, and identification code and password controls."
    ),
    "version": "19.0.1.1.0",
    "category": "Life Sciences/Quality",
    "license": "AGPL-3",
    "author": "Life Sciences Suite Architecture Team",
    "maintainers": ["life-sciences-suite"],
    "development_status": "Beta",
    "depends": [
        "base",
        "mail",
    ],
    "external_dependencies": {"python": []},
    "data": [
        "security/ls_signature_groups.xml",
        "security/ir.model.access.csv",
        "security/ls_signature_record_rules.xml",
        "data/ir_config_parameter_data.xml",
        "data/ls_signature_meaning_data.xml",
        "data/mail_template_data.xml",
        "data/ir_cron_data.xml",
        "report/ls_signature_manifestation_templates.xml",
        "report/ls_signature_certificate_templates.xml",
        "report/ls_signature_reports.xml",
        "wizards/ls_signature_wizard_views.xml",
        "views/ls_signature_meaning_views.xml",
        "views/ls_signature_policy_views.xml",
        "views/ls_signature_log_views.xml",
        "views/ls_signature_attempt_views.xml",
        "views/ls_signature_session_views.xml",
        "views/ls_signature_request_views.xml",
        "views/ls_signature_integrity_check_views.xml",
        "views/res_config_settings_views.xml",
        "views/ls_signature_menus.xml",
    ],
    "demo": [
        "demo/ls_signature_demo.xml",
    ],
    "application": True,
}
