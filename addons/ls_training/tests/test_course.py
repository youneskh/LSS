# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Tests for the training course model and its approval lifecycle."""

from psycopg2 import errors as pg_errors

from odoo.exceptions import UserError, ValidationError
from odoo.tests.common import tagged

from .common import LsTrainingCommon


@tagged("post_install", "-at_install")
class TestLsTrainingCourse(LsTrainingCommon):
    """Course master data, constraints and state machine."""

    def test_code_generated_from_sequence(self):
        """A course created without a code receives one from the sequence."""
        course = self.env["ls.training.course"].create(
            {"name": "Cleaning Validation", "duration_hours": 2.0}
        )
        self.assertTrue(course.code)
        self.assertNotEqual(course.code, "New")
        self.assertTrue(course.code.startswith("TRN/CRS/"))

    def test_explicit_code_is_preserved(self):
        """An explicitly supplied code is not overwritten."""
        course = self.env["ls.training.course"].create(
            {
                "name": "Deviation Handling",
                "code": "TRN-DEV-001",
                "duration_hours": 2.0,
            }
        )
        self.assertEqual(course.code, "TRN-DEV-001")

    def test_display_name_contains_code_and_version(self):
        """The display name exposes the code and the version."""
        self.assertIn(self.course.code, self.course.display_name)
        self.assertIn("v1.0", self.course.display_name)

    def test_duration_must_be_positive(self):
        """A zero or negative duration is rejected."""
        with self.assertRaises(ValidationError):
            self.course.write({"duration_hours": 0.0})

    def test_pass_score_bounds(self):
        """The pass score must stay within 0 and 100."""
        with self.assertRaises(ValidationError):
            self.course.write({"pass_score": 120.0})
        with self.assertRaises(ValidationError):
            self.course.write({"pass_score": -1.0})

    def test_validity_months_not_negative(self):
        """A negative certification validity is rejected."""
        with self.assertRaises(ValidationError):
            self.course.write({"validity_months": -6})

    def test_elearning_requires_url(self):
        """External e-Learning courses must carry their URL."""
        with self.assertRaises(ValidationError):
            self.env["ls.training.course"].create(
                {
                    "name": "Data Integrity e-Learning",
                    "duration_hours": 1.0,
                    "delivery_mode": "external_elearning",
                }
            )

    def test_elearning_with_url_is_accepted(self):
        """An e-Learning course with a URL is created successfully."""
        course = self.env["ls.training.course"].create(
            {
                "name": "Data Integrity e-Learning",
                "duration_hours": 1.0,
                "delivery_mode": "external_elearning",
                "elearning_url": "https://learning.example.com/di",
            }
        )
        self.assertEqual(course.delivery_mode, "external_elearning")

    def test_code_unique_per_company(self):
        """Two courses of one company cannot share a code."""
        with self.assertRaises(pg_errors.UniqueViolation):
            with self.env.cr.savepoint():
                self.env["ls.training.course"].create(
                    {
                        "name": "Duplicate",
                        "code": self.course.code,
                        "duration_hours": 1.0,
                        "company_id": self.company.id,
                    }
                )

    def test_workflow_draft_to_approved(self):
        """A course follows draft, review and approved in order."""
        course = self.env["ls.training.course"].create(
            {"name": "Line Clearance", "duration_hours": 1.0}
        )
        self.assertEqual(course.state, "draft")
        course.action_submit_review()
        self.assertEqual(course.state, "review")
        course.action_approve()
        self.assertEqual(course.state, "approved")

    def test_cannot_approve_a_draft_course(self):
        """Approval requires the course to be under review first."""
        course = self.env["ls.training.course"].create(
            {"name": "Line Clearance", "duration_hours": 1.0}
        )
        with self.assertRaises(UserError):
            course.action_approve()

    def test_cannot_submit_an_approved_course(self):
        """An approved course cannot be resubmitted for review."""
        with self.assertRaises(UserError):
            self.course.action_submit_review()

    def test_reset_to_draft_from_approved(self):
        """An approved course can be returned to draft for revision."""
        self.course.action_reset_to_draft()
        self.assertEqual(self.course.state, "draft")

    def test_reset_to_draft_rejected_when_already_draft(self):
        """Resetting a draft course raises a user error."""
        course = self.env["ls.training.course"].create(
            {"name": "Line Clearance", "duration_hours": 1.0}
        )
        with self.assertRaises(UserError):
            course.action_reset_to_draft()

    def test_obsolete_blocked_by_open_sessions(self):
        """A course with an open session cannot be made obsolete."""
        with self.assertRaises(UserError):
            self.course.action_set_obsolete()

    def test_obsolete_allowed_without_open_sessions(self):
        """A course whose sessions are cancelled can be retired."""
        self.session.action_cancel()
        self.course.action_set_obsolete()
        self.assertEqual(self.course.state, "obsolete")

    def test_obsolete_requires_approved_state(self):
        """Only an approved course can be made obsolete."""
        course = self.env["ls.training.course"].create(
            {"name": "Line Clearance", "duration_hours": 1.0}
        )
        with self.assertRaises(UserError):
            course.action_set_obsolete()

    def test_onchange_requires_assessment_clears_pass_score(self):
        """Disabling assessment resets the pass score to zero."""
        course = self.course.new(
            {"requires_assessment": True, "pass_score": 90.0}
        )
        course.requires_assessment = False
        course._onchange_requires_assessment()
        self.assertEqual(course.pass_score, 0.0)

    def test_onchange_requires_assessment_sets_default(self):
        """Enabling assessment proposes a default pass score."""
        course = self.course.new(
            {"requires_assessment": False, "pass_score": 0.0}
        )
        course.requires_assessment = True
        course._onchange_requires_assessment()
        self.assertEqual(course.pass_score, 80.0)

    def test_session_and_certification_counters(self):
        """Smart-button counters reflect the related records."""
        self.assertEqual(self.course.session_count, 1)
        self.assertEqual(self.course.certification_count, 0)

    def test_action_view_sessions_returns_filtered_action(self):
        """The sessions button filters on the current course."""
        action = self.course.action_view_sessions()
        self.assertEqual(action["res_model"], "ls.training.session")
        self.assertIn(("course_id", "=", self.course.id), action["domain"])

    def test_action_view_certifications_returns_filtered_action(self):
        """The certifications button filters on the current course."""
        action = self.course.action_view_certifications()
        self.assertEqual(
            action["res_model"], "ls.training.certification"
        )
        self.assertIn(("course_id", "=", self.course.id), action["domain"])
