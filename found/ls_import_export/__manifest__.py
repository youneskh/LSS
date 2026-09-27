# Part of the Life Sciences Suite for Odoo 19 Community Edition.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
{
    "name": "Life Sciences - Import & Export Compliance",
    "version": "19.0.1.0.0",
    "category": "Life Sciences/Quality",
    "summary": "Foreign-trade compliance platform for regulated life-sciences "
               "imports and exports: authorisations, customs, banking "
               "domiciliation, shipments, landed cost and a cited "
               "regulatory provision registry.",
    "author": "Life Sciences Suite Architecture Team",
    "website": "https://github.com/OCA",
    "license": "AGPL-3",
    "development_status": "Alpha",
    "depends": [
        "mail",
        "product",
        "stock",
        "uom",
        "account",
        "purchase",
        "sale",
    ],
    "data": [
        "security/ls_import_export_security.xml",
        "security/ir.model.access.csv",
        "data/ir_sequence_data.xml",
        "data/ls_import_export_regulatory_questions_data.xml",
        "views/ls_import_export_provision_views.xml",
        "views/ls_import_export_requirement_views.xml",
        "views/ls_import_export_regulatory_question_views.xml",
        "views/ls_import_export_menus.xml",
    ],
    "demo": [
        "demo/ls_import_export_demo.xml",
    ],
    "installable": True,
    "application": True,
    "auto_install": False,
}
