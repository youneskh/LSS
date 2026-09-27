# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
{
    "name": "Life Sciences - Medical Plastics",
    "version": "19.0.1.0.1",
    "category": "Manufacturing/Manufacturing",
    "summary": (
        "Injection moulding execution records, mould/tool register, moulding "
        "parameter specifications and material traceability for medical "
        "plastics and pharmaceutical primary packaging manufacturing."
    ),
    "author": "Life Sciences Suite Architecture Team",
    "website": "https://github.com/life-sciences-suite",
    "license": "AGPL-3",
    "depends": [
        "base",
        "mail",
        "product",
        "stock",
        "mrp",
    ],
    "data": [
        "security/ls_medical_plastics_groups.xml",
        "data/ir_sequence_data.xml",
        "data/mp_scrap_reason_data.xml",
        "security/ir.model.access.csv",
        "security/ls_medical_plastics_rules.xml",
        "views/mp_material_grade_views.xml",
        "views/mp_component_views.xml",
        "views/mp_tool_views.xml",
        "views/mp_tool_maintenance_views.xml",
        "views/mp_molding_parameter_views.xml",
        "views/mp_injection_molding_views.xml",
        "views/mp_scrap_reason_views.xml",
        "views/mrp_production_views.xml",
        "wizards/mp_reading_wizard_views.xml",
        "wizards/mp_tool_service_wizard_views.xml",
        "wizards/mp_traceability_wizard_views.xml",
        "report/mp_report_actions.xml",
        "report/mp_molding_run_templates.xml",
        "report/mp_tool_logbook_templates.xml",
        "data/ir_cron_data.xml",
        "views/mp_menus.xml",
    ],
    "application": True,
}
