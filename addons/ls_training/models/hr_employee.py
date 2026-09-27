# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Training information exposed on the employee record."""

from odoo import _, api, fields, models


class HrEmployee(models.Model):
    """Add the training history and compliance status to employees."""

    _inherit = "hr.employee"

    ls_training_certification_ids = fields.One2many(
        comodel_name="ls.training.certification",
        inverse_name="employee_id",
        string="Training Certifications",
    )
    ls_training_certification_count = fields.Integer(
        string="Certification Count",
        compute="_compute_ls_training_counters",
    )
    ls_training_attendance_ids = fields.One2many(
        comodel_name="ls.training.attendance",
        inverse_name="employee_id",
        string="Training Attendance",
    )
    ls_training_assessment_ids = fields.One2many(
        comodel_name="ls.training.competency.assessment",
        inverse_name="employee_id",
        string="Competency Assessments",
    )
    ls_training_required_count = fields.Integer(
        string="Mandatory Courses",
        compute="_compute_ls_training_compliance",
    )
    ls_training_compliant_count = fields.Integer(
        string="Compliant Courses",
        compute="_compute_ls_training_compliance",
    )
    ls_training_compliance_rate = fields.Float(
        string="Training Compliance (%)",
        compute="_compute_ls_training_compliance",
        help="Share of mandatory courses for which the employee holds a "
             "valid, non-expired certification.",
    )

    @api.depends("ls_training_certification_ids")
    def _compute_ls_training_counters(self):
        """Count the certifications held by each employee."""
        grouped = self.env["ls.training.certification"]._read_group(
            domain=[("employee_id", "in", self.ids)],
            groupby=["employee_id"],
            aggregates=["__count"],
        )
        mapped = {employee.id: count for employee, count in grouped}
        for record in self:
            record.ls_training_certification_count = mapped.get(record.id, 0)

    def _compute_ls_training_compliance(self):
        """Compare mandatory requirements against valid certifications.

        The rate is deliberately not stored: it depends on the current
        date through the certification status and would otherwise become
        stale between two scheduled recomputations.
        """
        requirement_model = self.env["ls.training.requirement"]
        certification_model = self.env["ls.training.certification"]
        for record in self:
            requirements = requirement_model._get_requirements_for_employee(
                record
            ).filtered("mandatory")
            required_courses = requirements.course_id
            record.ls_training_required_count = len(required_courses)
            if not required_courses:
                record.ls_training_compliant_count = 0
                record.ls_training_compliance_rate = 100.0
                continue
            valid_certifications = certification_model.search(
                [
                    ("employee_id", "=", record.id),
                    ("course_id", "in", required_courses.ids),
                    ("state", "in", ("valid", "expiring")),
                ]
            )
            compliant_courses = valid_certifications.course_id
            record.ls_training_compliant_count = len(compliant_courses)
            record.ls_training_compliance_rate = (
                100.0 * len(compliant_courses) / len(required_courses)
            )

    def action_view_ls_training_certifications(self):
        """Open this employee's training certifications."""
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id(
            "ls_training.ls_training_certification_action"
        )
        action["domain"] = [("employee_id", "=", self.id)]
        action["context"] = {"default_employee_id": self.id}
        return action

    def action_print_ls_training_record(self):
        """Print the consolidated training record of this employee."""
        return self.env.ref(
            "ls_training.ls_training_employee_record_report_action"
        ).report_action(self)

    def action_view_ls_training_requirements(self):
        """Open the training requirements applying to this employee."""
        self.ensure_one()
        requirements = self.env[
            "ls.training.requirement"
        ]._get_requirements_for_employee(self)
        return {
            "type": "ir.actions.act_window",
            "name": _("Applicable Training Requirements"),
            "res_model": "ls.training.requirement",
            "view_mode": "list,form",
            "domain": [("id", "in", requirements.ids)],
        }
