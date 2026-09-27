# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0.html).
"""Tests for the cosmetic product safety report."""

from odoo.exceptions import UserError, ValidationError
from odoo.tests import tagged

from .common import LsCosmeticsCommon


@tagged("post_install", "-at_install")
class TestLsCosmeticSafetyAssessment(LsCosmeticsCommon):
    """Verify the Annex I workflow, gating and assessor attribution."""

    def setUp(self):
        """Approve the shared formulation before each test."""
        super().setUp()
        if self.formulation.state != "approved":
            self._approve_formulation()

    def _draft_assessment(self, **overrides):
        """Create a draft report on the approved formulation."""
        values = {
            "name": "CPSR draft",
            "formulation_id": self.formulation.id,
        }
        values.update(overrides)
        return self.assessment_model.create(values)

    def test_part_b_requires_complete_part_a(self):
        """Part B cannot start while a Part A section is empty."""
        assessment = self._draft_assessment()
        assessment.action_start_part_a()
        with self.assertRaises(UserError):
            assessment.action_start_part_b()

    def test_missing_part_a_sections_are_listed(self):
        """Every empty Part A section is reported by name."""
        assessment = self._draft_assessment()
        missing = assessment._missing_part_a_sections()
        self.assertEqual(len(missing), 10)

    def test_part_b_starts_when_part_a_is_complete(self):
        """A fully documented Part A opens Part B."""
        assessment = self._draft_assessment(**self._part_a_values())
        assessment.action_start_part_a()
        assessment.action_start_part_b()
        self.assertEqual(assessment.state, "part_b")

    def test_approval_requires_the_named_assessor(self):
        """Only the user named in section B4 may approve the report."""
        values = dict(self._part_a_values())
        values.update(
            {
                "assessor_partner_id": self.assessor_partner.id,
                "assessor_user_id": self.user_assessor.id,
                "assessor_qualification": "Doctor of Pharmacy",
                "conclusion": "safe",
                "conclusion_statement": "Safe under normal use.",
                "labelled_warnings": "Avoid contact with the eyes.",
                "reasoning": "Margins of safety are adequate.",
            }
        )
        assessment = self._draft_assessment(**values)
        assessment.action_start_part_a()
        assessment.action_start_part_b()
        with self.assertRaises(UserError):
            assessment.with_user(self.user_manager).action_approve()
        assessment.with_user(self.user_assessor).action_approve()
        self.assertEqual(assessment.state, "approved")
        self.assertTrue(assessment.approval_date)

    def test_approval_requires_an_assessor_account(self):
        """A report with no assessor account cannot be approved."""
        values = dict(self._part_a_values())
        values.update(
            {
                "assessor_partner_id": self.assessor_partner.id,
                "assessor_qualification": "Doctor of Pharmacy",
                "conclusion": "safe",
                "conclusion_statement": "Safe under normal use.",
                "labelled_warnings": "Avoid contact with the eyes.",
                "reasoning": "Margins of safety are adequate.",
            }
        )
        assessment = self._draft_assessment(**values)
        assessment.action_start_part_a()
        assessment.action_start_part_b()
        with self.assertRaises(UserError):
            assessment.with_user(self.user_assessor).action_approve()

    def test_children_under_three_requires_specific_assessment(self):
        """Annex I Part B section 3 gating for children under three."""
        formulation = self.formulation_model.create(
            {
                "name": "Baby lotion",
                "for_children_under_three": True,
                "line_ids": [
                    (0, 0, {"ingredient_id": self.aqua.id, "concentration": 100.0})
                ],
            }
        )
        self._approve_formulation(formulation)
        values = dict(self._part_a_values())
        values.update(
            {
                "name": "CPSR baby lotion",
                "formulation_id": formulation.id,
                "assessor_partner_id": self.assessor_partner.id,
                "assessor_user_id": self.user_assessor.id,
                "assessor_qualification": "Doctor of Pharmacy",
                "conclusion": "safe",
                "conclusion_statement": "Safe under normal use.",
                "labelled_warnings": "Keep out of reach of children.",
                "reasoning": "Margins of safety are adequate.",
            }
        )
        assessment = self.assessment_model.create(values)
        assessment.action_start_part_a()
        assessment.action_start_part_b()
        with self.assertRaises(ValidationError):
            assessment.with_user(self.user_assessor).action_approve()

    def test_part_b_is_frozen_after_approval(self):
        """An approved report cannot have its conclusion rewritten."""
        assessment = self._build_approved_assessment()
        with self.assertRaises(UserError):
            assessment.write({"conclusion": "not_safe"})

    def test_review_overdue_search(self):
        """The review overdue search helper returns the expected records."""
        assessment = self._build_approved_assessment()
        assessment.review_date = "2020-01-01"
        overdue = self.assessment_model.search([("review_overdue", "=", True)])
        self.assertIn(assessment, overdue)
        not_overdue = self.assessment_model.search([("review_overdue", "=", False)])
        self.assertNotIn(assessment, not_overdue)

    def test_cron_posts_a_review_reminder(self):
        """The review cron posts one message per overdue report."""
        assessment = self._build_approved_assessment()
        assessment.review_date = "2020-01-01"
        before = len(assessment.message_ids)
        count = self.assessment_model._cron_notify_review_due()
        self.assertGreaterEqual(count, 1)
        self.assertGreater(len(assessment.message_ids), before)
