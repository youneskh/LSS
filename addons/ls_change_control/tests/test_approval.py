# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Tests of the approval decisions."""

from psycopg2 import IntegrityError

from odoo.exceptions import AccessError, UserError
from odoo.tests import tagged
from odoo.tools import mute_logger

from .common import ChangeControlCommon


@tagged("post_install", "-at_install")
class TestApproval(ChangeControlCommon):
    """Verify the decision rules and the immutability of decisions."""

    def setUp(self):
        """Bring one request to the Impact Assessment state."""
        super().setUp()
        self.request = self._create_request(user=self.user_requester)
        self._to_impact_assessment(self.request)
        self._complete_assessments(self.request)
        self.approval_qa = self.request.approval_ids.filtered(
            lambda a: a.approval_role == "quality_assurance"
        )
        self.approval_prod = self.request.approval_ids.filtered(
            lambda a: a.approval_role == "production"
        )

    @mute_logger("odoo.sql_db")
    def test_one_approval_per_role(self):
        """The same role cannot appear twice on one request."""
        with self.assertRaises(IntegrityError):
            with self.cr.savepoint():
                self.approval_model.create(
                    {
                        "request_id": self.request.id,
                        "approval_role": "quality_assurance",
                    }
                )

    def test_request_date_is_stamped_on_creation(self):
        """The approval carries the date on which it was requested."""
        self.assertTrue(self.approval_qa.date_requested)

    def test_only_the_assigned_approver_may_decide(self):
        """Another user cannot record the decision of an approver."""
        with self.assertRaises(AccessError):
            self.approval_qa.with_user(self.user_approver_prod).action_approve()
        with self.assertRaises(AccessError):
            self.approval_qa.with_user(self.user_manager).action_approve()

    def test_approval_records_the_signature_metadata(self):
        """A decision stores the author, the date and its meaning."""
        self.approval_qa.with_user(self.user_approver_qa).action_approve()
        self.assertEqual(self.approval_qa.state, "approved")
        self.assertEqual(self.approval_qa.decided_by_id, self.user_approver_qa)
        self.assertTrue(self.approval_qa.date_decision)
        self.assertTrue(self.approval_qa.signature_meaning)

    def test_request_stays_pending_until_the_last_approval(self):
        """A single approval does not approve the request."""
        self.approval_qa.with_user(self.user_approver_qa).action_approve()
        self.assertEqual(self.request.state, "impact_assessment")
        self.approval_prod.with_user(self.user_approver_prod).action_approve()
        self.assertEqual(self.request.state, "approved")

    def test_a_decided_approval_is_immutable(self):
        """A recorded decision can never be modified or deleted."""
        self.approval_qa.with_user(self.user_approver_qa).action_approve()
        with self.assertRaises(UserError):
            self.approval_qa.with_user(self.user_manager).write(
                {"comment": "Rewritten."}
            )
        with self.assertRaises(UserError):
            self.approval_qa.with_user(self.user_manager).unlink()

    def test_deciding_twice_is_refused(self):
        """An approval carries exactly one decision."""
        self.approval_qa.with_user(self.user_approver_qa).action_approve()
        with self.assertRaises(UserError):
            self.approval_qa.with_user(self.user_approver_qa).action_approve()

    def test_rejection_requires_a_comment(self):
        """An approver must justify a rejection."""
        with self.assertRaises(UserError):
            self.approval_qa.with_user(self.user_approver_qa).action_reject()

    def test_rejection_rejects_the_request(self):
        """One rejection is enough to reject the whole request."""
        self.approval_qa.with_user(self.user_approver_qa).write(
            {"comment": "The risk assessment is missing."}
        )
        self.approval_qa.with_user(self.user_approver_qa).action_reject()
        self.assertEqual(self.approval_qa.state, "rejected")
        self.assertEqual(self.request.state, "rejected")
        self.assertIn("risk assessment", self.request.rejection_reason)

    def test_decision_fields_cannot_be_written_directly(self):
        """The decision fields are only set by the workflow."""
        for values in (
            {"state": "approved"},
            {"date_decision": "2026-01-01 00:00:00"},
            {"signature_meaning": "Forged"},
        ):
            with self.assertRaises(AccessError):
                self.approval_qa.with_user(self.user_manager).write(values)

    def test_decision_is_refused_outside_the_assessment_state(self):
        """A decision cannot be recorded on a request under review."""
        request = self._create_request(user=self.user_requester)
        self._prepare_review(request)
        approval = self.approval_model.with_user(self.user_manager).create(
            {
                "request_id": request.id,
                "approval_role": "validation",
                "user_id": self.user_approver_qa.id,
            }
        )
        with self.assertRaises(UserError):
            approval.with_user(self.user_approver_qa).action_approve()

    def test_non_mandatory_approval_does_not_block(self):
        """An optional approval never blocks the transition to Approved."""
        optional = self.approval_model.with_user(self.user_manager).create(
            {
                "request_id": self.request.id,
                "approval_role": "validation",
                "user_id": self.user_approver_qa.id,
                "mandatory": False,
            }
        )
        self.approval_qa.with_user(self.user_approver_qa).action_approve()
        self.approval_prod.with_user(self.user_approver_prod).action_approve()
        self.assertEqual(self.request.state, "approved")
        self.assertEqual(optional.state, "pending")
