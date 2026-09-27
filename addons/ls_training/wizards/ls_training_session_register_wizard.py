# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Bulk registration of employees on a training session."""

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class LsTrainingSessionRegisterWizard(models.TransientModel):
    """Register a population of employees on one session in a single step.

    Employees already registered are silently skipped rather than raising,
    because the usual operational pattern is to re-run the wizard after a
    department changes and expect it to top up the attendee list.
    """

    _name = "ls.training.session.register.wizard"
    _description = "Register Employees on a Training Session"

    session_id = fields.Many2one(comodel_name="ls.training.session", required=True,
                                 ondelete="cascade",)
    company_id = fields.Many2one(comodel_name="res.company", related="session_id.company_id",)
    selection_mode = fields.Selection(
        selection=[
            ("employees", "Selected Employees"),
            ("department", "All Employees of a Department"),
            ("job", "All Employees of a Job Position"),
            ("requirement", "All Employees Required to Take the Course"),
        ],
        string="Select By",
        required=True,
        default="employees",
    )
    employee_ids = fields.Many2many(
        comodel_name="hr.employee",
        relation="ls_training_register_wizard_employee_rel",
        column1="wizard_id",
        column2="employee_id",
        string="Employees",
    )
    department_id = fields.Many2one(comodel_name="hr.department")
    job_id = fields.Many2one(
        comodel_name="hr.job",
        string="Job Position",
    )
    exclude_certified = fields.Boolean(
        string="Skip Already Certified",
        default=True,
        help="Exclude employees who already hold a valid certification for "
             "this course.",
    )

    @api.onchange("selection_mode")
    def _onchange_selection_mode(self):
        """Clear the criteria that do not belong to the chosen mode."""
        for wizard in self:
            if wizard.selection_mode != "employees":
                wizard.employee_ids = [fields.Command.clear()]
            if wizard.selection_mode != "department":
                wizard.department_id = False
            if wizard.selection_mode != "job":
                wizard.job_id = False

    def _get_candidate_employees(self):
        """Resolve the employees selected by the wizard criteria.

        :return: an ``hr.employee`` recordset, before exclusions.
        """
        self.ensure_one()
        employee_model = self.env["hr.employee"]
        company = self.session_id.company_id
        if self.selection_mode == "employees":
            return self.employee_ids
        if self.selection_mode == "department":
            if not self.department_id:
                raise UserError(_("Select a department."))
            return employee_model.search(
                [
                    ("company_id", "=", company.id),
                    ("department_id", "=", self.department_id.id),
                ]
            )
        if self.selection_mode == "job":
            if not self.job_id:
                raise UserError(_("Select a job position."))
            return employee_model.search(
                [
                    ("company_id", "=", company.id),
                    ("job_id", "=", self.job_id.id),
                ]
            )
        requirements = self.env["ls.training.requirement"].search(
            [
                ("active", "=", True),
                ("company_id", "=", company.id),
                ("course_id", "=", self.session_id.course_id.id),
            ]
        )
        employees = employee_model.browse()
        for requirement in requirements:
            employees |= requirement._get_target_employees()
        return employees

    def action_register(self):
        """Create the missing attendance lines and return to the session."""
        self.ensure_one()
        session = self.session_id
        if session.state not in ("draft", "confirmed", "in_progress"):
            raise UserError(
                _("Session '%s' is %s; no attendee can be added.")
                % (session.display_name, session.state)
            )
        employees = self._get_candidate_employees()
        employees -= session.attendance_ids.employee_id
        if self.exclude_certified:
            certified = self.env["ls.training.certification"].search(
                [
                    ("employee_id", "in", employees.ids),
                    ("course_id", "=", session.course_id.id),
                    ("state", "in", ("valid", "expiring")),
                ]
            )
            employees -= certified.employee_id
        if not employees:
            raise UserError(
                _("No employee remains to be registered on session '%s'.")
                % session.display_name
            )
        if session.capacity:
            free_seats = session.capacity - len(session.attendance_ids)
            if len(employees) > free_seats:
                raise UserError(
                    _("Session '%s' has %d free seat(s) but %d employee(s) "
                      "were selected.")
                    % (session.display_name, free_seats, len(employees))
                )
        self.env["ls.training.attendance"].create(
            [
                {"session_id": session.id, "employee_id": employee.id}
                for employee in employees
            ]
        )
        return {
            "type": "ir.actions.act_window",
            "res_model": "ls.training.session",
            "res_id": session.id,
            "view_mode": "form",
            "target": "current",
        }
