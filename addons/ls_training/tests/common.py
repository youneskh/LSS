# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Shared fixtures for the ls_training test suite."""

from odoo import fields
from odoo.tests.common import TransactionCase


class LsTrainingCommon(TransactionCase):
    """Base fixture building a small but complete training data set."""

    @classmethod
    def setUpClass(cls):
        """Create companies, employees, courses and a ready-to-run session."""
        super().setUpClass()
        cls.company = cls.env.ref("base.main_company")
        cls.other_company = cls.env["res.company"].create(
            {"name": "LS Second Site"}
        )
        cls.env.user.company_ids = [
            fields.Command.link(cls.other_company.id)
        ]

        cls.department = cls.env["hr.department"].create(
            {"name": "Production", "company_id": cls.company.id}
        )
        cls.job_operator = cls.env["hr.job"].create(
            {"name": "Production Operator", "company_id": cls.company.id}
        )
        cls.job_supervisor = cls.env["hr.job"].create(
            {"name": "Production Supervisor", "company_id": cls.company.id}
        )

        cls.employee = cls.env["hr.employee"].create(
            {
                "name": "Amina Operator",
                "company_id": cls.company.id,
                "department_id": cls.department.id,
                "job_id": cls.job_operator.id,
                "work_email": "amina.operator@example.com",
            }
        )
        cls.employee_two = cls.env["hr.employee"].create(
            {
                "name": "Karim Operator",
                "company_id": cls.company.id,
                "department_id": cls.department.id,
                "job_id": cls.job_operator.id,
                "work_email": "karim.operator@example.com",
            }
        )
        cls.trainer = cls.env["hr.employee"].create(
            {
                "name": "Sofia Trainer",
                "company_id": cls.company.id,
                "job_id": cls.job_supervisor.id,
            }
        )

        cls.competency = cls.env["ls.training.competency"].create(
            {
                "name": "GMP Documentation Practice",
                "code": "CMP-DOC",
                "minimum_level": "proficient",
                "reassessment_months": 12,
                "company_id": cls.company.id,
            }
        )

        cls.course = cls.env["ls.training.course"].create(
            {
                "name": "GMP Fundamentals",
                "version": "1.0",
                "course_type": "gmp",
                "delivery_mode": "classroom",
                "duration_hours": 4.0,
                "validity_months": 12,
                "requires_assessment": True,
                "pass_score": 80.0,
                "company_id": cls.company.id,
                "competency_ids": [
                    fields.Command.link(cls.competency.id)
                ],
            }
        )
        cls.course.action_submit_review()
        cls.course.action_approve()

        cls.course_no_expiry = cls.env["ls.training.course"].create(
            {
                "name": "Site Induction",
                "version": "1.0",
                "course_type": "induction",
                "delivery_mode": "self_study",
                "duration_hours": 1.0,
                "validity_months": 0,
                "requires_assessment": False,
                "company_id": cls.company.id,
            }
        )
        cls.course_no_expiry.action_submit_review()
        cls.course_no_expiry.action_approve()

        cls.session = cls.env["ls.training.session"].create(
            {
                "course_id": cls.course.id,
                "company_id": cls.company.id,
                "date_start": "2026-06-01 08:00:00",
                "date_end": "2026-06-01 12:00:00",
                "trainer_employee_id": cls.trainer.id,
                "location": "Training Room 1",
            }
        )

    @classmethod
    def _create_attendance(cls, session, employee, attended=True, score=0.0):
        """Create one attendance line and return it."""
        return cls.env["ls.training.attendance"].create(
            {
                "session_id": session.id,
                "employee_id": employee.id,
                "attended": attended,
                "score": score,
            }
        )

    @classmethod
    def _run_session_to_done(cls, session):
        """Drive a session through its full state machine to 'done'."""
        session.action_confirm()
        session.action_start()
        session.action_close()
        return session
