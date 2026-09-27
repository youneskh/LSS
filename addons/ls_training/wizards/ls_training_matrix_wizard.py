# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Generation of the role-based training matrix.

The matrix is produced through the ORM into transient lines rather than
through a PostgreSQL view. This keeps requirement resolution, record rules
and multi-company boundaries in one place, and avoids coupling the module
to the physical column layout of the ``hr`` tables.
"""

from odoo import _, api, fields, models
from odoo.exceptions import UserError

MATRIX_LINE_LIMIT = 20000


class LsTrainingMatrixLine(models.TransientModel):
    """One employee/course cell of a generated training matrix."""

    _name = "ls.training.matrix.line"
    _description = "Training Matrix Line"
    _order = "employee_id, course_id"

    wizard_id = fields.Many2one(
        comodel_name="ls.training.matrix.wizard",
        string="Matrix",
        required=True,
        ondelete="cascade",
        index=True,
    )
    employee_id = fields.Many2one(comodel_name="hr.employee", required=True,
                                  ondelete="cascade",
                                  index=True,)
    department_id = fields.Many2one(comodel_name="hr.department", related="employee_id.department_id",
                                    store=True,)
    job_id = fields.Many2one(
        comodel_name="hr.job",
        string="Job Position",
        related="employee_id.job_id",
        store=True,
    )
    course_id = fields.Many2one(comodel_name="ls.training.course", required=True,
                                ondelete="cascade",
                                index=True,)
    requirement_id = fields.Many2one(comodel_name="ls.training.requirement", ondelete="cascade",)
    mandatory = fields.Boolean()
    certification_id = fields.Many2one(
        comodel_name="ls.training.certification",
        string="Latest Certification",
        ondelete="cascade",
    )
    date_granted = fields.Date(
        string="Granted On",
    )
    date_expiry = fields.Date(
        string="Expires On",
    )
    status = fields.Selection(
        selection=[
            ("not_trained", "Not Trained"),
            ("valid", "Valid"),
            ("expiring", "Expiring Soon"),
            ("expired", "Expired"),
            ("revoked", "Revoked"),
        ],
        required=True,
    )

    @api.depends("employee_id", "course_id")
    def _compute_display_name(self):
        """Display the employee and course of the matrix cell."""
        for record in self:
            record.display_name = "%s / %s" % (
                record.employee_id.name or "",
                record.course_id.name or "",
            )


class LsTrainingMatrixWizard(models.TransientModel):
    """Build the training matrix for a chosen population."""

    _name = "ls.training.matrix.wizard"
    _description = "Training Matrix"

    company_id = fields.Many2one(comodel_name="res.company", required=True,
                                 default=lambda self: self.env.company,)
    department_ids = fields.Many2many(
        comodel_name="hr.department",
        relation="ls_training_matrix_wizard_department_rel",
        column1="wizard_id",
        column2="department_id",
        string="Departments",
        help="Leave empty to cover every department of the company.",
    )
    job_ids = fields.Many2many(
        comodel_name="hr.job",
        relation="ls_training_matrix_wizard_job_rel",
        column1="wizard_id",
        column2="job_id",
        string="Job Positions",
        help="Leave empty to cover every job position of the company.",
    )
    mandatory_only = fields.Boolean(
        string="Mandatory Requirements Only",
        default=True,
    )
    line_ids = fields.One2many(
        comodel_name="ls.training.matrix.line",
        inverse_name="wizard_id",
        string="Matrix Lines",
    )

    def _get_scope_employees(self):
        """Resolve the employees covered by the wizard scope."""
        self.ensure_one()
        domain = [("company_id", "=", self.company_id.id)]
        if self.department_ids:
            domain.append(("department_id", "in", self.department_ids.ids))
        if self.job_ids:
            domain.append(("job_id", "in", self.job_ids.ids))
        return self.env["hr.employee"].search(domain)

    def _prepare_matrix_lines(self, employees):
        """Build the matrix line values for the given employees.

        :param employees: an ``hr.employee`` recordset.
        :return: a list of dictionaries suitable for ``create``.
        """
        self.ensure_one()
        requirement_model = self.env["ls.training.requirement"]
        certification_model = self.env["ls.training.certification"]
        values_list = []
        for employee in employees:
            requirements = requirement_model._get_requirements_for_employee(
                employee
            )
            if self.mandatory_only:
                requirements = requirements.filtered("mandatory")
            seen_courses = set()
            for requirement in requirements:
                course = requirement.course_id
                if course.id in seen_courses:
                    continue
                seen_courses.add(course.id)
                certification = certification_model.search(
                    [
                        ("employee_id", "=", employee.id),
                        ("course_id", "=", course.id),
                    ],
                    order="date_granted desc, id desc",
                    limit=1,
                )
                values_list.append(
                    {
                        "wizard_id": self.id,
                        "employee_id": employee.id,
                        "course_id": course.id,
                        "requirement_id": requirement.id,
                        "mandatory": requirement.mandatory,
                        "certification_id": certification.id or False,
                        "date_granted": certification.date_granted or False,
                        "date_expiry": certification.date_expiry or False,
                        "status": (
                            certification.state
                            if certification
                            else "not_trained"
                        ),
                    }
                )
        return values_list

    def action_generate(self):
        """Generate the matrix and open it in a list and pivot view."""
        self.ensure_one()
        self.line_ids.unlink()
        employees = self._get_scope_employees()
        if not employees:
            raise UserError(
                _("No employee matches the selected scope.")
            )
        values_list = self._prepare_matrix_lines(employees)
        if not values_list:
            raise UserError(
                _("No training requirement applies to the selected scope.")
            )
        if len(values_list) > MATRIX_LINE_LIMIT:
            raise UserError(
                _("The selected scope produces %d matrix lines, which "
                  "exceeds the limit of %d. Narrow the scope by department "
                  "or job position.")
                % (len(values_list), MATRIX_LINE_LIMIT)
            )
        self.env["ls.training.matrix.line"].create(values_list)
        action = self.env["ir.actions.actions"]._for_xml_id(
            "ls_training.ls_training_matrix_line_action"
        )
        action["domain"] = [("wizard_id", "=", self.id)]
        action["context"] = {"search_default_group_by_employee": 1}
        return action
