# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Definition of which employees must complete which training course."""

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class LsTrainingRequirement(models.Model):
    """A rule stating that a population of employees must hold a course.

    Requirements are the source of the training matrix. A requirement
    targets either one named employee, or a population described by job
    position and/or department. Resolution is performed through the ORM so
    that record rules and multi-company boundaries are always honoured.
    """

    _name = "ls.training.requirement"
    _description = "Training Requirement"
    _order = "course_id, job_id, department_id"

    course_id = fields.Many2one(
        comodel_name="ls.training.course",
        string="Required Course",
        required=True,
        ondelete="cascade",
        index=True,
    )
    company_id = fields.Many2one(comodel_name="res.company", required=True,
                                 index=True,
                                 default=lambda self: self.env.company,)
    active = fields.Boolean(default=True,)
    job_id = fields.Many2one(
        comodel_name="hr.job",
        string="Job Position",
        ondelete="cascade",
        index=True,
    )
    department_id = fields.Many2one(comodel_name="hr.department", ondelete="cascade",
                                    index=True,)
    employee_id = fields.Many2one(
        comodel_name="hr.employee",
        string="Specific Employee",
        ondelete="cascade",
        index=True,
        help="Set to require the course from one named employee. Leave "
             "empty to target a job position and/or a department.",
    )
    mandatory = fields.Boolean(default=True,
                               help="Mandatory requirements are counted in the compliance rate. "
                               "Non-mandatory requirements are reported but excluded.",)
    grace_days = fields.Integer(
        string="Grace Period (Days)",
        default=30,
        help="Number of days a newly targeted employee has to complete the "
             "course before being reported as overdue.",
    )
    note = fields.Text(
        string="Justification",
        help="Reason why this training is required for this population.",
    )
    target_employee_count = fields.Integer(
        string="Targeted Employees",
        compute="_compute_target_employee_count",
    )

    _grace_days_positive = models.Constraint(
        "CHECK(grace_days >= 0)",
        "The grace period cannot be negative.",
    )

    @api.depends("job_id", "department_id", "employee_id", "company_id")
    def _compute_target_employee_count(self):
        """Count the employees currently matched by each requirement."""
        for record in self:
            record.target_employee_count = len(record._get_target_employees())

    @api.depends("course_id", "job_id", "department_id", "employee_id")
    def _compute_display_name(self):
        """Describe the requirement as 'course -> population'."""
        for record in self:
            if record.employee_id:
                target = record.employee_id.name
            else:
                parts = []
                if record.job_id:
                    parts.append(record.job_id.name)
                if record.department_id:
                    parts.append(record.department_id.name)
                target = " / ".join(parts) if parts else _("Undefined")
            record.display_name = "%s -> %s" % (
                record.course_id.name or "",
                target,
            )

    @api.constrains("course_id", "job_id", "department_id", "employee_id")
    def _check_target_defined(self):
        """A requirement must target an identifiable population.

        ``course_id`` (required) is listed so that the rule is also checked
        on creation when none of the target fields is supplied.
        """
        for record in self:
            if not (
                record.employee_id or record.job_id or record.department_id
            ):
                raise ValidationError(
                    _("A training requirement must target a specific "
                      "employee, a job position or a department.")
                )

    @api.constrains(
        "course_id", "job_id", "department_id", "employee_id", "company_id"
    )
    def _check_unique_requirement(self):
        """Forbid two identical requirements for the same course.

        A SQL unique constraint is not usable here because PostgreSQL
        treats NULL values as distinct, which would allow duplicates when
        the optional target fields are empty.
        """
        for record in self:
            duplicate = self.search_count(
                [
                    ("id", "!=", record.id),
                    ("course_id", "=", record.course_id.id),
                    ("job_id", "=", record.job_id.id),
                    ("department_id", "=", record.department_id.id),
                    ("employee_id", "=", record.employee_id.id),
                    ("company_id", "=", record.company_id.id),
                ]
            )
            if duplicate:
                raise ValidationError(
                    _("Requirement '%s' already exists.")
                    % record.display_name
                )

    @api.constrains("employee_id", "job_id", "department_id", "company_id")
    def _check_target_company(self):
        """Targets must belong to the company owning the requirement."""
        for record in self:
            employee_company = record.employee_id.company_id
            if employee_company and employee_company != record.company_id:
                raise ValidationError(
                    _("Employee '%s' does not belong to company '%s'.")
                    % (record.employee_id.name, record.company_id.name)
                )

    def _get_target_employees(self):
        """Resolve the employees matched by this single requirement.

        :return: an ``hr.employee`` recordset. Empty when the requirement
            targets nobody.
        """
        self.ensure_one()
        if self.employee_id:
            return self.employee_id
        domain = [("company_id", "=", self.company_id.id)]
        if self.job_id:
            domain.append(("job_id", "=", self.job_id.id))
        if self.department_id:
            domain.append(("department_id", "=", self.department_id.id))
        if len(domain) == 1:
            return self.env["hr.employee"].browse()
        return self.env["hr.employee"].search(domain)

    @api.model
    def _get_requirements_for_employee(self, employee):
        """Return the active requirements that apply to one employee.

        :param employee: a single ``hr.employee`` record.
        :return: an ``ls.training.requirement`` recordset.
        """
        domain = [
            ("active", "=", True),
            ("company_id", "=", employee.company_id.id),
            "|",
            ("employee_id", "=", employee.id),
            "&",
            ("employee_id", "=", False),
            "&",
            "|",
            ("job_id", "=", False),
            ("job_id", "=", employee.job_id.id),
            "|",
            ("department_id", "=", False),
            ("department_id", "=", employee.department_id.id),
        ]
        candidates = self.search(domain)
        return candidates.filtered(
            lambda requirement: requirement.employee_id
            or requirement.job_id
            or requirement.department_id
        )

    def action_view_target_employees(self):
        """Open the employees currently matched by this requirement."""
        self.ensure_one()
        employees = self._get_target_employees()
        return {
            "type": "ir.actions.act_window",
            "name": _("Targeted Employees"),
            "res_model": "hr.employee",
            "view_mode": "list,form",
            "domain": [("id", "in", employees.ids)],
        }
