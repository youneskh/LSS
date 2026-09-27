# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
{
    "name": "Life Sciences Suite - Medical Devices",
    "version": "19.0.1.0.1",
    "category": "Life Sciences/Medical Devices",
    "summary": (
        "Device register, UDI assignments, ISO 14971 risk management, "
        "clinical evaluation, technical documentation, CE marking and "
        "post-market surveillance for Odoo 19 Community."
    ),
    "author": "Life Sciences Suite Architecture Team",
    "website": "https://github.com/life-sciences-suite",
    "license": "AGPL-3",
    "depends": [
        "base",
        "mail",
        "product",
        "stock",
    ],
    "external_dependencies": {
        "python": ["dateutil"],
    },
    "data": [
        "security/ls_medical_device_groups.xml",
        "security/ir.model.access.csv",
        "security/ls_medical_device_rules.xml",
        "data/ir_sequence_data.xml",
        "data/device_class_data.xml",
        "data/clinical_evidence_source_data.xml",
        "data/technical_file_section_template_data.xml",
        "views/device_class_views.xml",
        "views/notified_body_views.xml",
        "views/device_views.xml",
        "views/udi_views.xml",
        "views/risk_assessment_views.xml",
        "views/clinical_evaluation_views.xml",
        "views/pmcf_evaluation_views.xml",
        "views/technical_file_views.xml",
        "views/ce_marking_views.xml",
        "views/pms_views.xml",
        "views/pms_report_views.xml",
        "wizards/device_state_wizard_views.xml",
        "wizards/pms_report_wizard_views.xml",
        "report/report_actions.xml",
        "report/device_regulatory_summary_report.xml",
        "report/risk_management_report.xml",
        "report/pms_periodic_report.xml",
        "views/menus.xml",
    ],
    "demo": [
        "demo/ls_medical_device_demo.xml",
    ],
    "post_init_hook": "post_init_hook",
    "application": True,
}
