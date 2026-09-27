# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Tests for training requirements and employee compliance."""

from psycopg2 import errors as pg_errors

from odoo.exceptions import ValidationError
from odoo.tests.common import tagged

from .common import LsTrainingCommon


@tagged("post_install", "-at_install")
class TestLsTrainingRequirement(LsTrainingCommon):
    """Requirement targeting, resolution and compliance computation."""

    def _create_requirement(self, **overrides):
        """Create a requirement with sensible defaults."""
        values = {
            "course_id": self.course.id,
            "job_id": self.job_operator.id,
            "company_id": self.company.id,
        }
        values.update(overrides)
        return self.env["ls.training.requirement"].create(values)

    def test_requirement_needs_a_target(self):
        """A requirement without any target is rejected."""
        with self.assertRaises(ValidationError):
            self.env["ls.training.requirement"].create(
                {"course_id": self.course.id, "company_id": self.company.id}
            )

    def test_target_by_job(self):
        """A job-based requirement resolves to that job's employees."""
        requirement = self._create_requirement()
        employees = requirement._get_target_employees()
        self.assertIn(self.employee, employees)
        self.assertIn(self.employee_two, employees)
        self.assertNotIn(self.trainer, employees)

    def test_target_by_department(self):
        """A department-based requirement resolves to its employees."""
        requirement = self._create_requirement(
            job_id=False, department_id=self.department.id
        )
        employees = requirement._get_target_employees()
        self.assertIn(self.employee, employees)

    def test_target_by_job_and_department(self):
        """Combined criteria intersect rather than union."""
        other_department = self.env["hr.department"].create(
            {"name": "Quality Control", "company_id": self.company.id}
        )
        requirement = self._create_requirement(
            department_id=other_department.id
        )
        self.assertEqual(len(requirement._get_target_employees()), 0)

    def test_target_specific_employee(self):
        """An individual requirement resolves to that employee only."""
        requirement = self._create_requirement(
            job_id=False, employee_id=self.employee.id
        )
        employees = requirement._get_target_employees()
        self.assertEqual(employees, self.employee)

    def test_target_employee_count(self):
        """The computed counter matches the resolved population."""
        requirement = self._create_requirement()
        self.assertEqual(requirement.target_employee_count, 2)

    def test_duplicate_requirement_rejected(self):
        """Two identical requirements cannot coexist."""
        self._create_requirement()
        with self.assertRaises(ValidationError):
            self._create_requirement()

    def test_negative_grace_period_rejected(self):
        """A negative grace period is rejected by the SQL constraint."""
        with self.assertRaises(pg_errors.CheckViolation):
            with self.env.cr.savepoint():
                self._create_requirement(grace_days=-1)

    def test_employee_company_must_match(self):
        """A requirement cannot target an employee of another company."""
        foreign = self.env["hr.employee"].create(
            {"name": "Foreign", "company_id": self.other_company.id}
        )
        with self.assertRaises(ValidationError):
            self._create_requirement(job_id=False, employee_id=foreign.id)

    def test_requirements_for_employee(self):
        """Requirement lookup returns every rule applying to an employee."""
        self._create_requirement()
        self._create_requirement(
            course_id=self.course_no_expiry.id,
            job_id=False,
            department_id=self.department.id,
        )
        requirements = self.env[
            "ls.training.requirement"
        ]._get_requirements_for_employee(self.employee)
        self.assertEqual(len(requirements), 2)

    def test_display_name_for_role_requirement(self):
        """The display name describes course and target population."""
        requirement = self._create_requirement()
        self.assertIn(self.course.name, requirement.display_name)
        self.assertIn(self.job_operator.name, requirement.display_name)

    def test_display_name_for_individual_requirement(self):
        """An individual requirement names the employee."""
        requirement = self._create_requirement(
            job_id=False, employee_id=self.employee.id
        )
        self.assertIn(self.employee.name, requirement.display_name)

    def test_action_view_target_employees(self):
        """The smart button returns an employee action."""
        requirement = self._create_requirement()
        action = requirement.action_view_target_employees()
        self.assertEqual(action["res_model"], "hr.employee")

    def test_compliance_rate_without_requirements(self):
        """An employee with no requirement is fully compliant."""
        self.assertEqual(self.trainer.ls_training_compliance_rate, 100.0)

    def test_compliance_rate_without_certification(self):
        """An untrained employee scores zero against a requirement."""
        self._create_requirement()
        self.employee.invalidate_recordset()
        self.assertEqual(self.employee.ls_training_required_count, 1)
        self.assertEqual(self.employee.ls_training_compliance_rate, 0.0)

    def test_compliance_rate_with_certification(self):
        """A valid certification satisfies the requirement."""
        self._create_requirement()
        self._create_attendance(
            self.session, self.employee, attended=True, score=95.0
        )
        self._run_session_to_done(self.session)
        self.employee.invalidate_recordset()
        self.assertEqual(self.employee.ls_training_compliant_count, 1)
        self.assertEqual(self.employee.ls_training_compliance_rate, 100.0)

    def test_non_mandatory_excluded_from_compliance(self):
        """Non-mandatory requirements do not affect the rate."""
        self._create_requirement(mandatory=False)
        self.employee.invalidate_recordset()
        self.assertEqual(self.employee.ls_training_required_count, 0)
        self.assertEqual(self.employee.ls_training_compliance_rate, 100.0)

    def test_certification_counter_on_employee(self):
        """The employee certification counter reflects issued records."""
        self._create_attendance(
            self.session, self.employee, attended=True, score=95.0
        )
        self._run_session_to_done(self.session)
        self.employee.invalidate_recordset()
        self.assertEqual(
            self.employee.ls_training_certification_count, 1
        )

    def test_employee_actions(self):
        """The employee smart buttons return usable actions."""
        self._create_requirement()
        certification_action = (
            self.employee.action_view_ls_training_certifications()
        )
        self.assertEqual(
            certification_action["res_model"], "ls.training.certification"
        )
        requirement_action = (
            self.employee.action_view_ls_training_requirements()
        )
        self.assertEqual(
            requirement_action["res_model"], "ls.training.requirement"
        )
