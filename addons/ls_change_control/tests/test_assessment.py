# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Tests of the impact assessment rules."""

from psycopg2 import IntegrityError

from odoo.exceptions import AccessError, UserError
from odoo.tests import tagged
from odoo.tools import mute_logger

from .common import ChangeControlCommon


@tagged("post_install", "-at_install")
class TestAssessment(ChangeControlCommon):
    """Verify the completion rules and the immutability of assessments."""

    def setUp(self):
        """Bring one request to the Impact Assessment state."""
        super().setUp()
        self.request = self._create_request(user=self.user_requester)
        self._to_impact_assessment(self.request)
        self.assessment = self.request.assessment_ids[0]
        self.assessment.with_user(self.user_manager).write(
            {"assessor_id": self.user_assessor.id}
        )

    @mute_logger("odoo.sql_db")
    def test_one_assessment_per_area(self):
        """The same area cannot be assessed twice on one request."""
        with self.assertRaises(IntegrityError):
            with self.cr.savepoint():
                self.assessment_model.create(
                    {
                        "request_id": self.request.id,
                        "impact_area_id": self.assessment.impact_area_id.id,
                    }
                )

    def test_completion_requires_a_written_assessment(self):
        """An empty assessment cannot be completed."""
        with self.assertRaises(UserError):
            self.assessment.with_user(self.user_assessor).action_complete()

    def test_declared_impact_requires_actions(self):
        """An impact must be accompanied by the required actions."""
        self.assessment.with_user(self.user_assessor).write(
            {"impact": "high", "assessment": "The procedure must be revised."}
        )
        with self.assertRaises(UserError):
            self.assessment.with_user(self.user_assessor).action_complete()
        self.assessment.with_user(self.user_assessor).write(
            {"actions_required": "Revise SOP-001."}
        )
        self.assessment.with_user(self.user_assessor).action_complete()
        self.assertEqual(self.assessment.state, "completed")

    def test_only_assessor_or_manager_may_complete(self):
        """A third party cannot complete an assessment."""
        self.assessment.with_user(self.user_assessor).write(
            {"assessment": "No impact."}
        )
        with self.assertRaises(AccessError):
            self.assessment.with_user(self.user_other_requester).action_complete()
        self.assessment.with_user(self.user_assessor).action_complete()
        self.assertEqual(self.assessment.state, "completed")

    def test_completion_stamps_the_author_and_the_date(self):
        """Completion records who completed the assessment and when."""
        self.assessment.with_user(self.user_assessor).write(
            {"assessment": "No impact."}
        )
        self.assessment.with_user(self.user_assessor).action_complete()
        self.assertEqual(self.assessment.completed_by_id, self.user_assessor)
        self.assertTrue(self.assessment.date_completed)

    def test_completed_assessment_is_immutable(self):
        """A completed assessment can no longer be modified."""
        self.assessment.with_user(self.user_assessor).write(
            {"assessment": "No impact."}
        )
        self.assessment.with_user(self.user_assessor).action_complete()
        with self.assertRaises(UserError):
            self.assessment.with_user(self.user_manager).write(
                {"assessment": "Rewritten."}
            )
        with self.assertRaises(UserError):
            self.assessment.with_user(self.user_manager).unlink()

    def test_state_cannot_be_written_directly(self):
        """The assessment state is only set by the workflow."""
        with self.assertRaises(AccessError):
            self.assessment.with_user(self.user_manager).write(
                {"state": "completed"}
            )

    def test_completion_is_refused_outside_the_assessment_state(self):
        """Assessments are only completed during the assessment phase."""
        request = self._create_request(user=self.user_requester)
        self._prepare_review(request)
        assessment = self.assessment_model.with_user(self.user_manager).create(
            {
                "request_id": request.id,
                "impact_area_id": self.area_documentation.id,
                "assessor_id": self.user_assessor.id,
                "assessment": "No impact.",
            }
        )
        with self.assertRaises(UserError):
            assessment.with_user(self.user_assessor).action_complete()

    def test_completing_all_assessments_clears_the_blocking_reasons(self):
        """Once every assessment is completed, only approvals remain."""
        self._complete_assessments(self.request)
        reasons = self.request.blocking_reasons or ""
        self.assertNotIn("Assessment of area", reasons)
