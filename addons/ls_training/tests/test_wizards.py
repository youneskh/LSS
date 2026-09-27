# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Tests for the registration wizard and the training matrix wizard."""

from odoo import fields
from odoo.exceptions import UserError
from odoo.tests.common import tagged

from .common import LsTrainingCommon


@tagged("post_install", "-at_install")
class TestLsTrainingWizards(LsTrainingCommon):
    """Bulk registration and matrix generation."""

    def _register_wizard(self, **overrides):
        """Instantiate the registration wizard for the fixture session."""
        values = {"session_id": self.session.id}
        values.update(overrides)
        return self.env["ls.training.session.register.wizard"].create(values)

    def test_register_selected_employees(self):
        """Selected employees are registered on the session."""
        wizard = self._register_wizard(
            selection_mode="employees",
            employee_ids=[fields.Command.set(self.employee.ids)],
        )
        wizard.action_register()
        self.assertEqual(self.session.attendee_count, 1)

    def test_register_by_department(self):
        """Every employee of a department is registered."""
        wizard = self._register_wizard(
            selection_mode="department",
            department_id=self.department.id,
        )
        wizard.action_register()
        self.assertEqual(self.session.attendee_count, 2)

    def test_register_by_job(self):
        """Every employee holding a job position is registered."""
        wizard = self._register_wizard(
            selection_mode="job", job_id=self.job_operator.id
        )
        wizard.action_register()
        self.assertEqual(self.session.attendee_count, 2)

    def test_register_by_requirement(self):
        """Employees required to take the course are registered."""
        self.env["ls.training.requirement"].create(
            {
                "course_id": self.course.id,
                "job_id": self.job_operator.id,
                "company_id": self.company.id,
            }
        )
        wizard = self._register_wizard(selection_mode="requirement")
        wizard.action_register()
        self.assertEqual(self.session.attendee_count, 2)

    def test_department_mode_requires_department(self):
        """Department mode without a department raises a user error."""
        wizard = self._register_wizard(selection_mode="department")
        with self.assertRaises(UserError):
            wizard.action_register()

    def test_job_mode_requires_job(self):
        """Job mode without a job position raises a user error."""
        wizard = self._register_wizard(selection_mode="job")
        with self.assertRaises(UserError):
            wizard.action_register()

    def test_already_registered_are_skipped(self):
        """Re-running the wizard does not duplicate attendance."""
        self._create_attendance(self.session, self.employee)
        wizard = self._register_wizard(
            selection_mode="job", job_id=self.job_operator.id
        )
        wizard.action_register()
        self.assertEqual(self.session.attendee_count, 2)

    def test_certified_employees_excluded(self):
        """Employees holding a valid certification are skipped."""
        self.env["ls.training.certification"].create(
            {
                "employee_id": self.employee.id,
                "course_id": self.course.id,
                "company_id": self.company.id,
            }
        )
        wizard = self._register_wizard(
            selection_mode="job",
            job_id=self.job_operator.id,
            exclude_certified=True,
        )
        wizard.action_register()
        self.assertEqual(self.session.attendee_count, 1)

    def test_no_remaining_employee_raises(self):
        """A selection resolving to nobody raises a user error."""
        self._create_attendance(self.session, self.employee)
        wizard = self._register_wizard(
            selection_mode="employees",
            employee_ids=[fields.Command.set(self.employee.ids)],
        )
        with self.assertRaises(UserError):
            wizard.action_register()

    def test_capacity_checked_by_wizard(self):
        """The wizard refuses to overbook a session."""
        self.session.write({"capacity": 1})
        wizard = self._register_wizard(
            selection_mode="job", job_id=self.job_operator.id
        )
        with self.assertRaises(UserError):
            wizard.action_register()

    def test_register_on_closed_session_rejected(self):
        """A closed session accepts no further registration."""
        self._create_attendance(
            self.session, self.employee, attended=True, score=95.0
        )
        self._run_session_to_done(self.session)
        wizard = self._register_wizard(
            selection_mode="employees",
            employee_ids=[fields.Command.set(self.employee_two.ids)],
        )
        with self.assertRaises(UserError):
            wizard.action_register()

    def test_onchange_clears_unused_criteria(self):
        """Switching mode clears the criteria of the other modes."""
        wizard = self._register_wizard(
            selection_mode="department", department_id=self.department.id
        )
        wizard.selection_mode = "job"
        wizard._onchange_selection_mode()
        self.assertFalse(wizard.department_id)

    def test_matrix_generation(self):
        """The matrix wizard produces one line per requirement cell."""
        self.env["ls.training.requirement"].create(
            {
                "course_id": self.course.id,
                "job_id": self.job_operator.id,
                "company_id": self.company.id,
            }
        )
        wizard = self.env["ls.training.matrix.wizard"].create(
            {"company_id": self.company.id}
        )
        action = wizard.action_generate()
        self.assertEqual(action["res_model"], "ls.training.matrix.line")
        self.assertEqual(len(wizard.line_ids), 2)
        self.assertEqual(
            set(wizard.line_ids.mapped("status")), {"not_trained"}
        )

    def test_matrix_reports_valid_status(self):
        """A certified employee is reported as valid in the matrix."""
        self.env["ls.training.requirement"].create(
            {
                "course_id": self.course.id,
                "employee_id": self.employee.id,
                "company_id": self.company.id,
            }
        )
        self.env["ls.training.certification"].create(
            {
                "employee_id": self.employee.id,
                "course_id": self.course.id,
                "company_id": self.company.id,
            }
        )
        wizard = self.env["ls.training.matrix.wizard"].create(
            {
                "company_id": self.company.id,
                "department_ids": [
                    fields.Command.set(self.department.ids)
                ],
            }
        )
        wizard.action_generate()
        line = wizard.line_ids.filtered(
            lambda item: item.employee_id == self.employee
        )
        self.assertEqual(line.status, "valid")

    def test_matrix_without_requirements_raises(self):
        """Generating a matrix with no requirement raises a user error."""
        wizard = self.env["ls.training.matrix.wizard"].create(
            {"company_id": self.company.id}
        )
        with self.assertRaises(UserError):
            wizard.action_generate()

    def test_matrix_without_employees_raises(self):
        """An empty scope raises a user error."""
        empty_department = self.env["hr.department"].create(
            {"name": "Empty", "company_id": self.company.id}
        )
        wizard = self.env["ls.training.matrix.wizard"].create(
            {
                "company_id": self.company.id,
                "department_ids": [
                    fields.Command.set(empty_department.ids)
                ],
            }
        )
        with self.assertRaises(UserError):
            wizard.action_generate()

    def test_matrix_mandatory_filter(self):
        """Non-mandatory requirements are excluded when requested."""
        self.env["ls.training.requirement"].create(
            {
                "course_id": self.course.id,
                "employee_id": self.employee.id,
                "company_id": self.company.id,
                "mandatory": False,
            }
        )
        wizard = self.env["ls.training.matrix.wizard"].create(
            {"company_id": self.company.id, "mandatory_only": True}
        )
        with self.assertRaises(UserError):
            wizard.action_generate()

    def test_matrix_line_display_name(self):
        """Matrix lines name their employee and course."""
        self.env["ls.training.requirement"].create(
            {
                "course_id": self.course.id,
                "employee_id": self.employee.id,
                "company_id": self.company.id,
            }
        )
        wizard = self.env["ls.training.matrix.wizard"].create(
            {"company_id": self.company.id}
        )
        wizard.action_generate()
        line = wizard.line_ids[0]
        self.assertIn(self.employee.name, line.display_name)
