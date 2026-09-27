# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Tests for the ls.complaint.resolution model."""

from odoo.exceptions import UserError
from odoo.tests import tagged

from .common import TestLsComplaintCommon


@tagged("post_install", "-at_install")
class TestResolution(TestLsComplaintCommon):
    """Verify the resolution state machine and its controls."""

    def setUp(self):
        """Create a complaint and an attached draft resolution."""
        super().setUp()
        self.complaint = self._create_complaint()
        self.resolution = self.env["ls.complaint.resolution"].create(
            {
                "complaint_id": self.complaint.id,
                "resolution_type": "credit_note",
                "description": "Credit note issued to the customer.",
                "owner_id": self.user_investigator.id,
            }
        )

    def test_01_display_name(self):
        """The display name combines the complaint and the resolution type."""
        self.assertIn(self.complaint.name, self.resolution.display_name)
        self.assertIn("Credit Note", self.resolution.display_name)

    def test_02_company_inherited(self):
        """The company is inherited from the parent complaint."""
        self.assertEqual(self.resolution.company_id, self.complaint.company_id)

    def test_03_done_requires_evidence(self):
        """Completion is refused without objective evidence."""
        self.resolution.action_start()
        with self.assertRaises(UserError):
            self.resolution.action_done()
        self.resolution.completion_evidence = "Credit note CN-0001."
        self.resolution.action_done()
        self.assertEqual(self.resolution.state, "done")
        self.assertTrue(self.resolution.completion_date)

    def test_04_cancel_requires_reason(self):
        """Cancellation without a documented reason is refused."""
        with self.assertRaises(UserError):
            self.resolution.action_cancel()
        self.resolution.cancellation_reason = "Superseded by a replacement."
        self.resolution.action_cancel()
        self.assertEqual(self.resolution.state, "cancelled")

    def test_05_finalised_resolution_is_frozen(self):
        """A completed resolution can no longer be modified."""
        self.resolution.completion_evidence = "Credit note CN-0002."
        self.resolution.action_done()
        with self.assertRaises(UserError):
            self.resolution.description = "Tampered"

    def test_06_unlink_guard(self):
        """A started resolution cannot be deleted."""
        self.resolution.action_start()
        with self.assertRaises(UserError):
            self.resolution.unlink()

    def test_07_wrong_state_transition(self):
        """A transition from a wrong state raises a user error."""
        self.resolution.completion_evidence = "Evidence."
        self.resolution.action_done()
        with self.assertRaises(UserError):
            self.resolution.action_start()
