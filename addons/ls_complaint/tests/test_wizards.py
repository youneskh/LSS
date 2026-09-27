# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Tests for the closure and cancellation wizards."""

from odoo.exceptions import UserError, ValidationError
from odoo.tests import tagged

from .common import TestLsComplaintCommon


@tagged("post_install", "-at_install")
class TestWizards(TestLsComplaintCommon):
    """Verify that the wizards apply the expected controls."""

    def setUp(self):
        """Create a complaint ready to be closed."""
        super().setUp()
        self.complaint = self._create_complaint()
        self._bring_to_investigation(self.complaint)
        self._approve_investigation(self.complaint.investigation_ids)
        self.complaint.action_start_resolution()
        self._add_done_resolution(self.complaint)

    def test_01_close_wizard_requires_effectiveness(self):
        """Closure is refused while the effectiveness is not confirmed."""
        wizard = self.env["ls.complaint.close.wizard"].create(
            {
                "complaint_id": self.complaint.id,
                "closure_summary": "Handled.",
                "reviewer_id": self.user_reviewer.id,
            }
        )
        with self.assertRaises(UserError):
            wizard.action_confirm()

    def test_02_close_wizard_reviewer_constraint(self):
        """The wizard refuses a reviewer equal to the responsible user."""
        with self.assertRaises(ValidationError):
            self.env["ls.complaint.close.wizard"].create(
                {
                    "complaint_id": self.complaint.id,
                    "closure_summary": "Handled.",
                    "reviewer_id": self.complaint.owner_id.id,
                    "effectiveness_confirmed": True,
                }
            )

    def test_03_close_wizard_closes_complaint(self):
        """A complete wizard closes the complaint."""
        wizard = self.env["ls.complaint.close.wizard"].create(
            {
                "complaint_id": self.complaint.id,
                "closure_summary": "Root cause corrected.",
                "reviewer_id": self.user_reviewer.id,
                "effectiveness_confirmed": True,
                "customer_notified": True,
            }
        )
        result = wizard.action_confirm()
        self.assertEqual(result["type"], "ir.actions.act_window_close")
        self.assertEqual(self.complaint.state, "closed")
        self.assertEqual(self.complaint.closure_summary, "Root cause corrected.")
        self.assertTrue(self.complaint.customer_notified)

    def test_04_close_wizard_related_fields(self):
        """The wizard exposes the current status and the responsible user."""
        wizard = self.env["ls.complaint.close.wizard"].create(
            {
                "complaint_id": self.complaint.id,
                "closure_summary": "Handled.",
                "reviewer_id": self.user_reviewer.id,
            }
        )
        self.assertEqual(wizard.complaint_state, "resolution")
        self.assertEqual(wizard.owner_id, self.complaint.owner_id)

    def test_05_cancel_wizard_cancels_complaint(self):
        """The cancellation wizard cancels the complaint with its reason."""
        wizard = self.env["ls.complaint.cancel.wizard"].create(
            {
                "complaint_id": self.complaint.id,
                "reason": "Duplicate record.",
            }
        )
        result = wizard.action_confirm()
        self.assertEqual(result["type"], "ir.actions.act_window_close")
        self.assertEqual(self.complaint.state, "cancelled")
        self.assertEqual(self.complaint.cancellation_reason, "Duplicate record.")
