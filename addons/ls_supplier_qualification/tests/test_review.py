# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Tests for the periodic review and the application of its decision."""
from dateutil.relativedelta import relativedelta

from odoo.exceptions import UserError, ValidationError
from odoo.tests import tagged

from .common import SupplierQualificationCommon


@tagged("post_install", "-at_install")
class TestReview(SupplierQualificationCommon):
    """Cover evidence collection and every review decision."""

    def setUp(self):
        """Bring the shared dossier to approval and open a draft review."""
        super().setUp()
        self.qualification.action_start_assessment()
        self.assessment = self._create_assessment(self.qualification)
        self._create_material(self.qualification, self.product)
        self.qualification.action_submit_for_approval()
        self._approve(self.qualification)
        self.review = self.env["ls.supplier.review"].create({
            "qualification_id": self.qualification.id,
            "reviewer_id": self.user_manager.id,
            "period_start": self.today - relativedelta(months=12),
            "period_end": self.today,
            "summary": "Summary recorded by the test suite.",
        })

    def test_sequence_assigned(self):
        """A new review receives a reference from the company sequence."""
        self.assertTrue(self.review.name.startswith("SR/"))

    def test_collect_evidence(self):
        """Evidence collection attaches the records of the period."""
        self.review.action_collect_evidence()
        self.assertIn(self.assessment, self.review.assessment_ids)

    def test_maintain_extends_validity(self):
        """Maintaining the approval pushes the validity end date."""
        new_expiry = self.today + relativedelta(months=24)
        self.review.write({
            "decision": "maintain",
            "new_expiry_date": new_expiry,
        })
        self.review.action_done()
        self.assertEqual(self.qualification.state, "approved")
        self.assertEqual(self.qualification.expiry_date, new_expiry)

    def test_maintain_uses_interval_when_no_date_given(self):
        """Without an explicit date the dossier interval is applied."""
        self.review.decision = "maintain"
        self.review.action_done()
        expected = self.review.review_date + relativedelta(
            months=self.qualification.requalification_interval_months
        )
        self.assertEqual(self.qualification.expiry_date, expected)

    def test_conditional_requires_conditions(self):
        """A conditional decision must document its conditions."""
        self.review.decision = "maintain_conditional"
        with self.assertRaises(ValidationError):
            self.review.action_done()

    def test_conditional_writes_conditions(self):
        """A conditional decision writes the conditions on the dossier."""
        self.review.write({
            "decision": "maintain_conditional",
            "new_conditions": "Conditions recorded by the test suite.",
        })
        self.review.action_done()
        self.assertEqual(self.qualification.state, "conditional")
        self.assertTrue(self.qualification.approval_conditions)

    def test_adverse_decision_requires_justification(self):
        """Suspension, disqualification and requalification must be justified."""
        self.review.decision = "suspend"
        with self.assertRaises(ValidationError):
            self.review.action_done()

    def test_suspend_decision(self):
        """A suspend decision suspends the dossier."""
        self.review.write({
            "decision": "suspend",
            "decision_justification": "Justification by the test suite.",
        })
        self.review.action_done()
        self.assertEqual(self.qualification.state, "suspended")
        self.assertTrue(self.qualification.suspension_reason)

    def test_disqualify_decision(self):
        """A disqualify decision disqualifies the dossier."""
        self.review.write({
            "decision": "disqualify",
            "decision_justification": "Justification by the test suite.",
        })
        self.review.action_done()
        self.assertEqual(self.qualification.state, "disqualified")

    def test_requalify_decision_clears_approval(self):
        """A requalification decision clears the approval information."""
        self.review.write({
            "decision": "requalify",
            "decision_justification": "Justification by the test suite.",
        })
        self.review.action_done()
        self.assertEqual(self.qualification.state, "assessment")
        self.assertFalse(self.qualification.approval_date)

    def test_completed_review_is_final(self):
        """A completed review cannot be cancelled or deleted."""
        self.review.decision = "maintain"
        self.review.action_done()
        with self.assertRaises(UserError):
            self.review.action_cancel()
        with self.assertRaises(UserError):
            self.review.unlink()

    def test_review_creates_signature_entry(self):
        """Completing a review appends a signature entry."""
        before = self.env["ls.supplier.signature"].search_count([])
        self.review.decision = "maintain"
        self.review.action_done()
        after = self.env["ls.supplier.signature"].search_count([])
        self.assertEqual(after, before + 1)
