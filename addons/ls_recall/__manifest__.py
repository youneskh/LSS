# Part of the Life Sciences Suite for Odoo 19 Community Edition.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
{
    "name": "Life Sciences - Recall and Field Action Management",
    "version": "19.0.1.0.1",
    "category": "Manufacturing/Quality",
    "summary": "Plan, execute, communicate, verify and close product "
               "recalls, market withdrawals and field safety corrective "
               "actions.",
    "author": "Life Sciences Suite Architecture Team",
    "license": "AGPL-3",
    "development_status": "Beta",
    "depends": [
        "mail",
        "stock",
    ],
    "data": [
        "security/ls_recall_security.xml",
        "security/ir.model.access.csv",
        "data/ir_sequence_data.xml",
        "data/ir_cron_data.xml",
        "views/ls_recall_plan_views.xml",
        "views/ls_recall_execution_views.xml",
        "views/ls_recall_line_views.xml",
        "views/ls_recall_communication_views.xml",
        "views/ls_recall_effectiveness_views.xml",
        "views/ls_recall_report_views.xml",
        "views/stock_lot_views.xml",
        "wizards/ls_recall_initiate_wizard_views.xml",
        "wizards/ls_recall_close_wizard_views.xml",
        "report/ls_recall_report_actions.xml",
        "report/ls_recall_notice_template.xml",
        "report/ls_recall_summary_template.xml",
        "views/ls_recall_menus.xml",
    ],
    "demo": [
        "demo/ls_recall_demo.xml",
    ],
    "application": True,
}
