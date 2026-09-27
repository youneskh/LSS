# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
{
    "name": "Life Sciences - Calibration Management",
    "summary": "Instrument register, calibration plans, calibration records, "
    "out-of-tolerance handling and calibration certificates",
    "version": "19.0.1.0.1",
    "category": "Life Sciences/Quality",
    "author": "Life Sciences Suite Architecture Team",
    "license": "AGPL-3",
    "development_status": "Beta",
    "depends": [
        "base",
        "web",
        "mail",
        "maintenance",
    ],
    "external_dependencies": {"python": ["dateutil"]},
    "data": [
        "security/ls_calibration_security.xml",
        "security/ir.model.access.csv",
        "data/ir_sequence_data.xml",
        "data/ir_config_parameter_data.xml",
        "data/ir_cron_data.xml",
        "views/ls_calibration_instrument_views.xml",
        "views/ls_calibration_plan_views.xml",
        "views/ls_calibration_record_views.xml",
        "views/ls_calibration_certificate_views.xml",
        "wizards/ls_calibration_record_generate_views.xml",
        "wizards/ls_calibration_record_reject_views.xml",
        "report/ls_calibration_record_report.xml",
        "report/ls_calibration_certificate_report.xml",
        "views/ls_calibration_menus.xml",
    ],
    "demo": [
        "demo/ls_calibration_demo.xml",
    ],
    "application": True,
}
