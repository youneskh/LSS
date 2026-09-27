# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Tests for groups, access rights and record rules."""

from odoo import fields
from odoo.exceptions import AccessError
from odoo.tests.common import tagged

from .common import LsTrainingCommon


@tagged("post_install", "-at_install")
class TestLsTrainingSecurity(LsTrainingCommon):
    """Access-right matrix and record-rule scoping."""

    @classmethod
    def setUpClass(cls):
        """Create one user per training group and link them to employees."""
        super().setUpClass()
        cls.group_learner = cls.env.ref(
            "ls_training.group_ls_training_learner"
        )
        cls.group_viewer = cls.env.ref(
            "ls_training.group_ls_training_viewer"
        )
        cls.group_trainer = cls.env.ref(
            "ls_training.group_ls_training_trainer"
        )
        cls.group_manager = cls.env.ref(
            "ls_training.group_ls_training_manager"
        )
        cls.internal_group = cls.env.ref("base.group_user")

        cls.user_learner = cls._create_user(
            "ls_learner", cls.group_learner
        )
        cls.user_viewer = cls._create_user("ls_viewer", cls.group_viewer)
        cls.user_trainer = cls._create_user("ls_trainer", cls.group_trainer)
        cls.user_manager = cls._create_user("ls_manager", cls.group_manager)

        cls.employee.write({"user_id": cls.user_learner.id})

    @classmethod
    def _create_user(cls, login, group):
        """Create an internal user belonging to one training group."""
        return cls.env["res.users"].create(
            {
                "name": login,
                "login": login,
                "email": "%s@example.com" % login,
                "company_id": cls.company.id,
                "company_ids": [fields.Command.set(cls.company.ids)],
                "group_ids": [
                    fields.Command.set([cls.internal_group.id, group.id])
                ],
            }
        )

    def test_groups_are_installed(self):
        """All four training groups exist after installation."""
        for group in (
            self.group_learner,
            self.group_viewer,
            self.group_trainer,
            self.group_manager,
        ):
            self.assertTrue(group.id)

    def test_group_hierarchy(self):
        """Each group implies the one below it."""
        self.assertIn(self.group_learner, self.group_viewer.implied_ids)
        self.assertIn(self.group_viewer, self.group_trainer.implied_ids)
        self.assertIn(self.group_trainer, self.group_manager.implied_ids)

    def test_record_rules_are_installed(self):
        """The declared record rules were loaded successfully."""
        for xml_id in (
            "ls_training.ls_training_course_company_rule",
            "ls_training.ls_training_certification_company_rule",
            "ls_training.ls_training_certification_learner_rule",
            "ls_training.ls_training_certification_viewer_rule",
        ):
            rule = self.env.ref(xml_id)
            self.assertTrue(rule.id)

    def test_learner_cannot_create_course(self):
        """A learner has no write access to course master data."""
        with self.assertRaises(AccessError):
            self.env["ls.training.course"].with_user(
                self.user_learner
            ).create({"name": "Forbidden", "duration_hours": 1.0})

    def test_viewer_cannot_create_session(self):
        """A viewer cannot schedule sessions."""
        with self.assertRaises(AccessError):
            self.env["ls.training.session"].with_user(
                self.user_viewer
            ).create(
                {
                    "course_id": self.course.id,
                    "date_start": "2026-06-05 08:00:00",
                    "date_end": "2026-06-05 12:00:00",
                }
            )

    def test_trainer_can_create_session(self):
        """A trainer can schedule a session."""
        session = self.env["ls.training.session"].with_user(
            self.user_trainer
        ).create(
            {
                "course_id": self.course.id,
                "date_start": "2026-06-05 08:00:00",
                "date_end": "2026-06-05 12:00:00",
            }
        )
        self.assertTrue(session.id)

    def test_trainer_cannot_create_course(self):
        """Course approval remains a manager responsibility."""
        with self.assertRaises(AccessError):
            self.env["ls.training.course"].with_user(
                self.user_trainer
            ).create({"name": "Forbidden", "duration_hours": 1.0})

    def test_manager_can_create_course(self):
        """A manager owns the course master data."""
        course = self.env["ls.training.course"].with_user(
            self.user_manager
        ).create({"name": "Allowed", "duration_hours": 1.0})
        self.assertTrue(course.id)

    def test_trainer_cannot_delete_session(self):
        """Deleting sessions is reserved to managers."""
        session = self.env["ls.training.session"].with_user(
            self.user_trainer
        ).create(
            {
                "course_id": self.course.id,
                "date_start": "2026-06-05 08:00:00",
                "date_end": "2026-06-05 12:00:00",
            }
        )
        with self.assertRaises(AccessError):
            session.unlink()

    def test_learner_sees_only_own_certification(self):
        """The learner record rule hides other employees' records."""
        own = self.env["ls.training.certification"].create(
            {
                "employee_id": self.employee.id,
                "course_id": self.course.id,
                "company_id": self.company.id,
            }
        )
        other = self.env["ls.training.certification"].create(
            {
                "employee_id": self.employee_two.id,
                "course_id": self.course.id,
                "company_id": self.company.id,
            }
        )
        visible = self.env["ls.training.certification"].with_user(
            self.user_learner
        ).search([])
        self.assertIn(own, visible)
        self.assertNotIn(other, visible)

    def test_viewer_sees_every_certification(self):
        """A viewer is not restricted to their own records."""
        other = self.env["ls.training.certification"].create(
            {
                "employee_id": self.employee_two.id,
                "course_id": self.course.id,
                "company_id": self.company.id,
            }
        )
        visible = self.env["ls.training.certification"].with_user(
            self.user_viewer
        ).search([])
        self.assertIn(other, visible)

    def test_learner_sees_only_own_attendance(self):
        """Attendance is scoped to the learner's own employee record."""
        own = self._create_attendance(self.session, self.employee)
        other = self._create_attendance(self.session, self.employee_two)
        visible = self.env["ls.training.attendance"].with_user(
            self.user_learner
        ).search([])
        self.assertIn(own, visible)
        self.assertNotIn(other, visible)

    def test_multi_company_rule_hides_foreign_courses(self):
        """A course of another company is invisible to the user."""
        foreign_course = self.env["ls.training.course"].create(
            {
                "name": "Foreign Course",
                "duration_hours": 1.0,
                "company_id": self.other_company.id,
            }
        )
        visible = self.env["ls.training.course"].with_user(
            self.user_viewer
        ).search([])
        self.assertNotIn(foreign_course, visible)

    def test_learner_cannot_write_certification(self):
        """Learners hold read-only access to their own certifications."""
        certification = self.env["ls.training.certification"].create(
            {
                "employee_id": self.employee.id,
                "course_id": self.course.id,
                "company_id": self.company.id,
            }
        )
        with self.assertRaises(AccessError):
            certification.with_user(self.user_learner).write(
                {"score": 100.0}
            )
