# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Tests for the approval routing and its segregation of duties."""

from odoo.exceptions import UserError

from .common import LsDocumentCommon


class TestLsDocumentApproval(LsDocumentCommon):
    """Approval decisions, guards and rejection handling."""

    def setUp(self):
        """Create a document submitted for review."""
        super().setUp()
        self.document = self._create_document(
            approver_ids=[(6, 0, [self.user_approver.id])]
        )
        self._create_version(self.document)
        self.document.action_submit_review()
        self.approval = self.document.approval_ids

    def test_approval_targets_the_latest_version(self):
        """The approval refers to the version submitted for review."""
        self.assertEqual(
            self.approval.version_id, self.document.latest_version_id
        )

    def test_approver_can_approve(self):
        """The designated approver can record an approval."""
        self.approval.with_user(self.user_approver).action_approve()
        self.assertEqual(self.approval.state, "approved")
        self.assertTrue(self.approval.decision_date)

    def test_another_user_cannot_approve(self):
        """A user who is not the designated approver cannot decide."""
        with self.assertRaises(UserError):
            self.approval.with_user(self.user_approver_2).action_approve()

    def test_direct_write_cannot_bypass_the_identity_check(self):
        """A direct write of the decision is subject to the same check."""
        with self.assertRaises(UserError):
            self.approval.with_user(self.user_editor).write(
                {"state": "approved"}
            )

    def test_decision_cannot_be_changed(self):
        """A recorded decision cannot be revised."""
        self.approval.with_user(self.user_approver).action_approve()
        with self.assertRaises(UserError):
            self.approval.with_user(self.user_approver).action_approve()

    def test_rejection_returns_document_to_draft(self):
        """Refusing an approval sends the document back to draft."""
        self.approval.with_user(self.user_approver).action_reject()
        self.assertEqual(self.approval.state, "rejected")
        self.assertEqual(self.document.state, "draft")

    def test_rejection_cancels_other_pending_approvals(self):
        """Refusal by one approver cancels the remaining requests."""
        document = self._create_document(
            name="Two approvers",
            approver_ids=[
                (6, 0, [self.user_approver.id, self.user_approver_2.id])
            ],
        )
        self._create_version(document)
        document.action_submit_review()
        first = document.approval_ids.filtered(
            lambda item: item.approver_id == self.user_approver
        )
        first.with_user(self.user_approver).action_reject()
        second = document.approval_ids.filtered(
            lambda item: item.approver_id == self.user_approver_2
        )
        self.assertEqual(second.state, "cancelled")

    def test_reject_wizard_records_the_reason(self):
        """The rejection wizard stores the reason on the approval."""
        wizard = (
            self.env["ls.document.reject.wizard"]
            .with_user(self.user_approver)
            .create({"document_id": self.document.id, "reason": "Scope unclear."})
        )
        wizard.action_confirm_rejection()
        self.assertEqual(self.approval.state, "rejected")
        self.assertEqual(self.approval.comment, "Scope unclear.")
        self.assertEqual(self.document.state, "draft")

    def test_reject_wizard_requires_a_pending_approval(self):
        """A user without pending approval cannot use the wizard."""
        wizard = (
            self.env["ls.document.reject.wizard"]
            .with_user(self.user_approver_2)
            .create({"document_id": self.document.id, "reason": "No mandate."})
        )
        with self.assertRaises(UserError):
            wizard.action_confirm_rejection()

    def test_action_reject_on_document_opens_the_wizard(self):
        """The document Reject button returns the wizard action."""
        action = self.document.action_reject()
        self.assertEqual(action["res_model"], "ls.document.reject.wizard")

    def test_action_reject_blocked_outside_review(self):
        """The Reject button is refused outside the review state."""
        self.approval.with_user(self.user_approver).action_reject()
        with self.assertRaises(UserError):
            self.document.action_reject()

    def test_decided_approval_cannot_be_deleted(self):
        """A recorded decision cannot be removed from the history."""
        self.approval.with_user(self.user_approver).action_approve()
        with self.assertRaises(UserError):
            self.approval.unlink()

    def test_resubmission_cancels_the_previous_cycle(self):
        """Submitting again cancels the approvals of the previous cycle."""
        self.approval.with_user(self.user_approver).action_reject()
        self.document.action_submit_review()
        cancelled = self.document.approval_ids.filtered(
            lambda item: item.state == "cancelled"
        )
        pending = self.document.approval_ids.filtered(
            lambda item: item.state == "pending"
        )
        self.assertTrue(pending)
        self.assertFalse(cancelled & pending)
