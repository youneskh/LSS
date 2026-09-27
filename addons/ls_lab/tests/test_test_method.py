# Part of the Life Sciences Suite. See LICENSE file for full copyright and licensing details.
"""Tests for the test method lifecycle and immutability."""

from odoo.exceptions import UserError
from odoo.tests import tagged

from .common import LsLabCommon


@tagged("post_install", "-at_install")
class TestLsLabTestMethod(LsLabCommon):
    """Cover BRU-01 and the method approval lifecycle."""

    def test_sequence_assigned_on_create(self):
        """A new method receives a code from the sequence."""
        method = self.env["ls.lab.test_method"].create({"name": "Water content"})
        self.assertNotEqual(method.code, "New")
        self.assertTrue(method.code.startswith("LAB/MTH/"))
        self.assertEqual(method.version, 1)
        self.assertEqual(method.state, "draft")

    def test_lifecycle_draft_to_approved(self):
        """A method moves draft to review to approved and records the approver."""
        method = self.env["ls.lab.test_method"].create({"name": "Dissolution"})
        method.action_submit_review()
        self.assertEqual(method.state, "review")
        method.with_user(self.manager).action_approve()
        self.assertEqual(method.state, "approved")
        self.assertEqual(method.approved_by_id, self.manager)
        self.assertTrue(method.approval_date)

    def test_approve_from_draft_is_refused(self):
        """Approval is only available from the review state."""
        method = self.env["ls.lab.test_method"].create({"name": "Identity"})
        with self.assertRaises(UserError):
            method.action_approve()

    def test_approved_method_is_frozen(self):
        """A controlled field cannot be written on an approved method (BRU-01)."""
        method = self._create_approved_method(name="Frozen method")
        with self.assertRaises(UserError):
            method.write({"name": "Renamed after approval"})

    def test_approved_method_non_controlled_field_is_writable(self):
        """Fields outside the controlled set remain writable when approved."""
        method = self._create_approved_method(name="Partially frozen")
        method.write({"obsolete_reason": "Superseded by a newer procedure"})
        self.assertTrue(method.obsolete_reason)

    def test_obsolete_requires_reason(self):
        """A method cannot be made obsolete without a recorded reason."""
        method = self._create_approved_method(name="Needs reason")
        with self.assertRaises(UserError):
            method.action_set_obsolete()
        method.write({"obsolete_reason": "Replaced by a validated procedure"})
        method.action_set_obsolete()
        self.assertEqual(method.state, "obsolete")

    def test_revision_creates_new_version(self):
        """Creating a revision produces a draft successor linked both ways."""
        method = self._create_approved_method(name="Versioned method")
        action = method.with_user(self.manager).action_create_revision()
        successor = self.env["ls.lab.test_method"].browse(action["res_id"])
        self.assertEqual(successor.version, method.version + 1)
        self.assertEqual(successor.state, "draft")
        self.assertEqual(successor.predecessor_id, method)
        self.assertEqual(method.successor_id, successor)
        self.assertFalse(successor.approved_by_id)

    def test_non_draft_method_cannot_be_deleted(self):
        """Records that left draft cannot be deleted."""
        method = self._create_approved_method(name="Undeletable")
        with self.assertRaises(UserError):
            method.unlink()

    def test_draft_method_can_be_deleted(self):
        """A draft method may still be deleted."""
        method = self.env["ls.lab.test_method"].create({"name": "Disposable"})
        method.unlink()
        self.assertFalse(method.exists())
