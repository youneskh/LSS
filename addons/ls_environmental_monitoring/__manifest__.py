# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
{
    "name": "Life Sciences - Environmental Monitoring",
    "version": "19.0.1.0.1",
    "category": "Manufacturing/Quality",
    "summary": (
        "Environmental monitoring programme management for regulated "
        "manufacturing areas: sampling points, monitoring plans, samples, "
        "results, limit evaluation, excursions and trend analysis."
    ),
    "author": "Life Sciences Suite Architecture Team",
    "website": "https://github.com/life-sciences-suite",
    "license": "AGPL-3",
    "depends": [
        "base",
        "mail",
    ],
    "data": [
        "security/ls_env_groups.xml",
        "security/ls_env_record_rules.xml",
        "security/ir.model.access.csv",
        "data/ls_env_sequence.xml",
        "data/ls_env_parameter_data.xml",
        "data/ls_env_cron.xml",
        "views/ls_env_grade_views.xml",
        "views/ls_env_area_views.xml",
        "views/ls_env_parameter_views.xml",
        "views/ls_env_method_views.xml",
        "views/ls_env_sampling_point_views.xml",
        "views/ls_env_limit_views.xml",
        "views/ls_env_plan_views.xml",
        "views/ls_env_sample_views.xml",
        "views/ls_env_result_views.xml",
        "views/ls_env_excursion_views.xml",
        "views/ls_env_trend_views.xml",
        "wizards/ls_env_schedule_wizard_views.xml",
        "wizards/ls_env_trend_wizard_views.xml",
        "wizards/ls_env_excursion_close_wizard_views.xml",
        "report/ls_env_report_actions.xml",
        "report/ls_env_sample_report_templates.xml",
        "report/ls_env_excursion_report_templates.xml",
        "views/ls_env_menus.xml",
    ],
    "application": True,
}
