# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
{
    "name": "Life Sciences - Training Management",
    "summary": "Training courses, sessions, certifications, competencies "
               "and the role-based training matrix for regulated "
               "Life Sciences environments.",
    "version": "19.0.1.0.1",
    "category": "Human Resources/Training",
    "author": "Life Sciences Suite Architecture Team",
    "website": "https://github.com/OCA",
    "license": "AGPL-3",
    "development_status": "Beta",
    "depends": [
        "base",
        "mail",
        "hr",
    ],
    "external_dependencies": {
        "python": [],
        "bin": [],
    },
    "data": [
        "security/ls_training_groups.xml",
        "security/ir.model.access.csv",
        "security/ls_training_record_rules.xml",
        "data/ir_config_parameter_data.xml",
        "data/ir_sequence_data.xml",
        "data/mail_template_data.xml",
        "data/ir_cron_data.xml",
        "views/ls_training_competency_views.xml",
        "views/ls_training_course_views.xml",
        "views/ls_training_session_views.xml",
        "views/ls_training_attendance_views.xml",
        "views/ls_training_certification_views.xml",
        "views/ls_training_competency_assessment_views.xml",
        "views/ls_training_requirement_views.xml",
        "views/hr_employee_views.xml",
        "wizards/ls_training_session_register_wizard_views.xml",
        "wizards/ls_training_matrix_wizard_views.xml",
        "report/ls_training_report_actions.xml",
        "report/ls_training_certificate_template.xml",
        "report/ls_training_employee_record_template.xml",
        "views/ls_training_menus.xml",
    ],
    "demo": [
        "demo/ls_training_demo.xml",
    ],
    "application": True,
}
