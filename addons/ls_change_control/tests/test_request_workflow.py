# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Tests of the change request state machine."""

from odoo.exceptions import AccessError, UserError
from odoo.tests import tagged

from .common import ChangeControlCommon


@tagged("post_install", "-at_install")
class TestRequestWorkflow(ChangeControlCommon):
    """Verify each transition of the lifecycle and its guards."""

    def test_sequence_is_allocated_on_create(self):
        """A new request receives a reference from the sequence."""
        request = self._create_request(user=self.user_requester)
        self.assertNotEqual(request.name, "New")
        self.assertTrue(request.name.startswith("CC/"))
        self.assertEqual(request.state, "draft")

    def test_references_are_unique(self):
        """Two requests never share the same reference."""
        first = self._create_request(user=self.user_requester)
        second = self._create_request(user=self.user_requester)
        self.assertNotEqual(first.name, second.name)

    def test_display_name_contains_reference_and_title(self):
        """The display name concatenates the reference and the title."""
        request = self._create_request(user=self.user_requester)
        self.assertIn(request.name, request.display_name)
        self.assertIn("Test change", request.display_name)

    def test_requester_is_subscribed_on_create(self):
        """The requester follows the request from its creation."""
        request = self._create_request(user=self.user_requester)
        self.assertIn(
            self.user_requester.partner_id,
            request.message_partner_ids,
        )

    def test_submit_moves_to_under_review(self):
        """Submitting a draft request moves it to Under Review."""
        request = self._create_request(user=self.user_requester)
        request.with_user(self.user_requester).action_submit_review()
        self.assertEqual(request.state, "under_review")

    def test_only_requester_or_manager_may_submit(self):
        """A third party cannot submit somebody else's request."""
        request = self._create_request(user=self.user_requester)
        with self.assertRaises(AccessError):
            request.with_user(self.user_other_requester).action_submit_review()

    def test_manager_may_submit_on_behalf(self):
        """A change control manager may submit any draft request."""
        request = self._create_request(user=self.user_requester)
        request.with_user(self.user_manager).action_submit_review()
        self.assertEqual(request.state, "under_review")

    def test_submit_twice_is_refused(self):
        """A request that is not draft can no longer be submitted."""
        request = self._create_request(user=self.user_requester)
        request.with_user(self.user_requester).action_submit_review()
        with self.assertRaises(UserError):
            request.with_user(self.user_requester).action_submit_review()

    def test_start_assessment_requires_manager(self):
        """Only a change control manager may start the assessment."""
        request = self._create_request(user=self.user_requester)
        self._prepare_review(request)
        with self.assertRaises(AccessError):
            request.with_user(self.user_requester).action_start_assessment()

    def test_start_assessment_requires_a_manager_assignment(self):
        """The review cannot end without a change control manager."""
        request = self._create_request(user=self.user_requester)
        request.with_user(self.user_requester).action_submit_review()
        request.with_user(self.user_manager).write(
            {"impact_area_ids": [(6, 0, [self.area_documentation.id])]}
        )
        with self.assertRaises(UserError):
            request.with_user(self.user_manager).action_start_assessment()

    def test_start_assessment_generates_assessments_and_approvals(self):
        """The category template drives the generated records."""
        request = self._create_request(user=self.user_requester)
        self._to_impact_assessment(request)
        self.assertEqual(request.state, "impact_assessment")
        self.assertEqual(len(request.assessment_ids), 2)
        self.assertEqual(len(request.approval_ids), 2)
        self.assertEqual(
            set(request.approval_ids.mapped("approval_role")),
            {"quality_assurance", "production"},
        )
        self.assertEqual(
            set(request.assessment_ids.mapped("impact_area_id")),
            {self.area_documentation, self.area_process},
        )

    def test_start_assessment_is_idempotent_on_generation(self):
        """Generation never duplicates an existing assessment or approval."""
        request = self._create_request(user=self.user_requester)
        self._prepare_review(request)
        request.with_user(self.user_manager)._generate_assessments()
        request.with_user(self.user_manager)._generate_approvals()
        request.with_user(self.user_manager).action_start_assessment()
        self.assertEqual(len(request.assessment_ids), 2)
        self.assertEqual(len(request.approval_ids), 2)

    def test_reset_to_draft_from_under_review(self):
        """A manager may return a request under review to draft."""
        request = self._create_request(user=self.user_requester)
        request.with_user(self.user_requester).action_submit_review()
        request.with_user(self.user_manager).action_reset_draft()
        self.assertEqual(request.state, "draft")

    def test_reset_to_draft_is_refused_after_assessment_started(self):
        """A request under assessment is never returned to draft."""
        request = self._create_request(user=self.user_requester)
        self._to_impact_assessment(request)
        with self.assertRaises(UserError):
            request.with_user(self.user_manager).action_reset_draft()

    def test_request_is_approved_when_all_approvals_granted(self):
        """The request reaches Approved once every guard is cleared."""
        request = self._create_request(user=self.user_requester)
        self._to_approved(request)
        self.assertEqual(request.state, "approved")
        self.assertTrue(request.date_approved)
        self.assertTrue(request.date_planned_implementation)

    def test_request_is_not_approved_while_an_assessment_is_pending(self):
        """A pending mandatory assessment blocks the approval."""
        request = self._create_request(user=self.user_requester)
        self._to_impact_assessment(request)
        self._grant_approvals(request)
        self.assertEqual(request.state, "impact_assessment")
        self.assertTrue(request.blocking_reasons)

    def test_start_implementation_requires_an_action(self):
        """An approved request without action cannot start implementation."""
        request = self._create_request(user=self.user_requester)
        self._to_approved(request)
        with self.assertRaises(UserError):
            request.with_user(self.user_manager).action_start_implementation()

    def test_full_lifecycle_to_closed(self):
        """The complete lifecycle reaches the Closed state."""
        request = self._create_request(user=self.user_requester)
        self._to_approved(request)
        action = self._add_implementation(request)
        request.with_user(self.user_manager).action_start_implementation()
        self.assertEqual(request.state, "implementation")

        action.with_user(self.user_requester).action_start()
        action.with_user(self.user_manager).write(
            {"evidence_reference": "SOP-001 rev. 2"}
        )
        action.with_user(self.user_requester).action_done()
        self.assertTrue(request.date_actual_implementation)
        self.assertTrue(request.date_verification_planned)

        verification = self._add_verification(request)
        verification.with_user(self.user_manager).write(
            {"conclusion": "The revised procedure is applied."}
        )
        verification.with_user(self.user_requester).action_complete_effective()

        request.with_user(self.user_manager).action_verify()
        self.assertEqual(request.state, "verified")

        request.with_user(self.user_manager).action_close("Change closed.")
        self.assertEqual(request.state, "closed")
        self.assertTrue(request.date_closed)
        self.assertEqual(request.closure_statement, "Change closed.")

    def test_close_requires_a_statement(self):
        """A closure without a statement is refused."""
        request = self._create_request(user=self.user_requester)
        self._to_approved(request)
        self._add_implementation(request)
        request.with_user(self.user_manager).action_start_implementation()
        with self.assertRaises(UserError):
            request.with_user(self.user_manager).action_close("   ")

    def test_reject_from_under_review(self):
        """A manager may reject a request under review."""
        request = self._create_request(user=self.user_requester)
        request.with_user(self.user_requester).action_submit_review()
        request.with_user(self.user_manager).action_reject("Not justified.")
        self.assertEqual(request.state, "rejected")
        self.assertEqual(request.rejection_reason, "Not justified.")
        self.assertTrue(request.date_rejected)

    def test_reject_requires_a_reason(self):
        """A rejection without a reason is refused."""
        request = self._create_request(user=self.user_requester)
        request.with_user(self.user_requester).action_submit_review()
        with self.assertRaises(UserError):
            request.with_user(self.user_manager).action_reject("")

    def test_rejected_request_is_final(self):
        """A rejected request cannot be reopened."""
        request = self._create_request(user=self.user_requester)
        request.with_user(self.user_requester).action_submit_review()
        request.with_user(self.user_manager).action_reject("Not justified.")
        with self.assertRaises(UserError):
            request.with_user(self.user_manager).action_reset_draft()

    def test_cancel_requires_manager_and_reason(self):
        """Cancellation is reserved to managers and requires a reason."""
        request = self._create_request(user=self.user_requester)
        with self.assertRaises(AccessError):
            request.with_user(self.user_requester).action_cancel("No longer needed.")
        with self.assertRaises(UserError):
            request.with_user(self.user_manager).action_cancel("")
        request.with_user(self.user_manager).action_cancel("No longer needed.")
        self.assertEqual(request.state, "cancelled")

    def test_cancel_is_refused_after_implementation_started(self):
        """An implemented change is never cancelled."""
        request = self._create_request(user=self.user_requester)
        self._to_approved(request)
        self._add_implementation(request)
        request.with_user(self.user_manager).action_start_implementation()
        with self.assertRaises(UserError):
            request.with_user(self.user_manager).action_cancel("Too late.")

    def test_decision_wizard_closes_the_request(self):
        """The decision wizard delegates to the request method."""
        request = self._create_request(user=self.user_requester)
        self._to_approved(request)
        action = self._add_implementation(request)
        request.with_user(self.user_manager).action_start_implementation()
        action.with_user(self.user_manager).write(
            {"evidence_reference": "SOP-001 rev. 2"}
        )
        action.with_user(self.user_requester).action_done()
        verification = self._add_verification(request)
        verification.with_user(self.user_manager).write({"conclusion": "Applied."})
        verification.with_user(self.user_requester).action_complete_effective()
        request.with_user(self.user_manager).action_verify()

        wizard = (
            self.env["ls.change_control.decision_wizard"]
            .with_user(self.user_manager)
            .create(
                {
                    "request_id": request.id,
                    "mode": "close",
                    "reason": "Closed through the wizard.",
                }
            )
        )
        wizard.action_confirm()
        self.assertEqual(request.state, "closed")

    def test_copy_resets_the_lifecycle(self):
        """Duplicating a request produces a fresh draft."""
        request = self._create_request(user=self.user_requester)
        self._to_impact_assessment(request)
        copy = request.with_user(self.user_manager).copy()
        self.assertEqual(copy.state, "draft")
        self.assertNotEqual(copy.name, request.name)
        self.assertFalse(copy.assessment_ids)
        self.assertFalse(copy.approval_ids)

    def test_verify_is_blocked_while_actions_are_open(self):
        """An open implementation action blocks the verification step."""
        request = self._create_request(user=self.user_requester)
        self._to_approved(request)
        self._add_implementation(request)
        request.with_user(self.user_manager).action_start_implementation()
        with self.assertRaises(UserError):
            request.with_user(self.user_manager).action_verify()
