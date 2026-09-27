# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Tests of the implementation actions."""

from odoo.exceptions import AccessError, UserError
from odoo.tests import tagged

from .common import ChangeControlCommon


@tagged("post_install", "-at_install")
class TestImplementation(ChangeControlCommon):
    """Verify the execution rules of the implementation actions."""

    def setUp(self):
        """Bring one request to the Implementation state with one action."""
        super().setUp()
        self.request = self._create_request(user=self.user_requester)
        self._to_approved(self.request)
        self.action = self._add_implementation(self.request)
        self.request.with_user(self.user_manager).action_start_implementation()

    def test_action_cannot_start_before_approval(self):
        """An action of a draft request cannot be executed."""
        other = self._create_request(user=self.user_requester)
        action = self.implementation_model.with_user(self.user_manager).create(
            {
                "request_id": other.id,
                "name": "Too early",
                "action_type": "training",
                "responsible_id": self.user_requester.id,
                "date_planned": "2026-12-31",
            }
        )
        with self.assertRaises(UserError):
            action.with_user(self.user_requester).action_start()

    def test_only_responsible_or_manager_may_execute(self):
        """A third party cannot execute an action."""
        with self.assertRaises(AccessError):
            self.action.with_user(self.user_other_requester).action_start()

    def test_start_moves_to_in_progress(self):
        """Starting an action moves it to In Progress."""
        self.action.with_user(self.user_requester).action_start()
        self.assertEqual(self.action.state, "in_progress")

    def test_closing_requires_an_evidence_reference(self):
        """An action cannot be closed without traceable evidence."""
        with self.assertRaises(UserError):
            self.action.with_user(self.user_requester).action_done()
        self.action.with_user(self.user_manager).write(
            {"evidence_reference": "SOP-001 rev. 3"}
        )
        self.action.with_user(self.user_requester).action_done()
        self.assertEqual(self.action.state, "done")
        self.assertEqual(self.action.done_by_id, self.user_requester)
        self.assertTrue(self.action.date_done)

    def test_closed_action_is_immutable(self):
        """A closed action can no longer be modified."""
        self.action.with_user(self.user_manager).write(
            {"evidence_reference": "SOP-001 rev. 3"}
        )
        self.action.with_user(self.user_requester).action_done()
        with self.assertRaises(UserError):
            self.action.with_user(self.user_manager).write({"name": "Rewritten"})

    def test_started_action_cannot_be_deleted(self):
        """An action that has been started is retained."""
        self.action.with_user(self.user_requester).action_start()
        with self.assertRaises(UserError):
            self.action.with_user(self.user_manager).unlink()

    def test_cancellation_requires_a_reason_and_a_manager(self):
        """Cancelling an action is reserved to managers and justified."""
        with self.assertRaises(AccessError):
            self.action.with_user(self.user_requester).action_cancel()
        with self.assertRaises(UserError):
            self.action.with_user(self.user_manager).action_cancel()
        self.action.with_user(self.user_manager).write(
            {"cancellation_reason": "Covered by another action."}
        )
        self.action.with_user(self.user_manager).action_cancel()
        self.assertEqual(self.action.state, "cancelled")

    def test_actual_implementation_date_needs_every_action_closed(self):
        """The implementation date is only set when no action is open."""
        second = self._add_implementation(self.request, name="Second action")
        self.action.with_user(self.user_manager).write(
            {"evidence_reference": "EV-1"}
        )
        self.action.with_user(self.user_requester).action_done()
        self.assertFalse(self.request.date_actual_implementation)
        second.with_user(self.user_manager).write({"evidence_reference": "EV-2"})
        second.with_user(self.user_requester).action_done()
        self.assertTrue(self.request.date_actual_implementation)

    def test_cancelled_actions_do_not_block_the_implementation_date(self):
        """A cancelled action is a closed action."""
        second = self._add_implementation(self.request, name="Second action")
        self.action.with_user(self.user_manager).write(
            {"evidence_reference": "EV-1"}
        )
        self.action.with_user(self.user_requester).action_done()
        second.with_user(self.user_manager).write(
            {"cancellation_reason": "Not required."}
        )
        second.with_user(self.user_manager).action_cancel()
        self.assertTrue(self.request.date_actual_implementation)

    def test_state_cannot_be_written_directly(self):
        """The action state is only set by the workflow."""
        with self.assertRaises(AccessError):
            self.action.with_user(self.user_manager).write({"state": "done"})
