# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
{
    "name": "Life Sciences - Pharmaceutical Manufacturing",
    "version": "19.0.1.0.1",
    "category": "Manufacturing",
    "summary": (
        "Batch manufacturing, electronic batch records, batch release, "
        "API and excipient master data, stability studies, GS1 "
        "serialisation and CTD dossier management for regulated "
        "pharmaceutical manufacturing."
    ),
    "author": "Life Sciences Suite Architecture Team",
    "license": "AGPL-3",
    "depends": [
        "base",
        "mail",
        "product",
        "stock",
        "mrp",
    ],
    "data": [
        "security/ls_pharma_security.xml",
        "security/ir.model.access.csv",
        "security/ls_pharma_record_rules.xml",
        "data/ir_sequence_data.xml",
        "data/ls_pharma_stability_condition_data.xml",
        "data/ls_pharma_ctd_section_template_data.xml",
        "data/ir_cron_data.xml",
        "report/ls_pharma_report_actions.xml",
        "report/ls_pharma_batch_record_template.xml",
        "report/ls_pharma_release_certificate_template.xml",
        "views/ls_pharma_api_views.xml",
        "views/ls_pharma_excipient_views.xml",
        "views/ls_pharma_batch_views.xml",
        "views/ls_pharma_batch_record_views.xml",
        "views/ls_pharma_batch_release_views.xml",
        "views/ls_pharma_stability_views.xml",
        "views/ls_pharma_serialization_views.xml",
        "views/ls_pharma_ctd_views.xml",
        "views/product_views.xml",
        "views/res_company_views.xml",
        "wizards/ls_pharma_batch_release_wizard_views.xml",
        "wizards/ls_pharma_stability_schedule_wizard_views.xml",
        "wizards/ls_pharma_serial_generate_wizard_views.xml",
        "views/ls_pharma_menus.xml",
    ],
    "demo": [
        "demo/ls_pharma_demo.xml",
    ],
    "application": True,
}
