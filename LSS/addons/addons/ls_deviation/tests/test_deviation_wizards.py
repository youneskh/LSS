# Copyright 2026 Life Sciences Suite
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Wizard tests."""

from datetime import timedelta

from odoo import fields
from odoo.exceptions import UserError
from odoo.tests import tagged

from .common import DeviationCommon


@tagged("post_install", "-at_install")
class TestDeviationWizards(DeviationCommon):
    """Verify the closure, cancellation and due date wizards."""

    def _close_wizard(self, deviation, **overrides):
        values = {
            "deviation_id": deviation.id,
            "conclusion": "Investigation concluded.",
            "followup": "No further follow-up required.",
            "capa_decision_rationale": "Isolated event, no systemic cause.",
            "qa_reviewer_id": self.user_manager.id,
        }
        values.update(overrides)
        return self.env["ls.deviation.close.wizard"].create(values)

    def test_close_moves_to_closed(self):
        """Closing through the wizard reaches the closed state."""
        deviation = self._advance_to_disposition(self._create_deviation())
        self._close_wizard(deviation).action_confirm()
        self.assertEqual(deviation.state, "closed")
        self.assertTrue(deviation.closure_date)
        self.assertEqual(deviation.closed_by_id, self.env.user)

    def test_close_writes_conclusions_and_followup(self):
        """The 21 CFR 211.192 conclusions and follow-up are persisted."""
        deviation = self._advance_to_disposition(self._create_deviation())
        self._close_wizard(deviation).action_confirm()
        self.assertEqual(deviation.conclusion, "Investigation concluded.")
        self.assertEqual(deviation.followup, "No further follow-up required.")

    def test_close_requires_capa_reference_when_capa_required(self):
        """A CAPA reference is mandatory when a CAPA is required."""
        deviation = self._advance_to_disposition(self._create_deviation())
        wizard = self._close_wizard(deviation, capa_required=True)
        with self.assertRaises(UserError):
            wizard.action_confirm()

    def test_close_blocked_by_open_immediate_action(self):
        """An open immediate action blocks closure."""
        deviation = self._advance_to_disposition(self._create_deviation())
        self.env["ls.deviation.action"].create(
            {
                "deviation_id": deviation.id,
                "name": "Outstanding action",
                "action_type": "immediate",
                "responsible_id": self.user_investigator.id,
            }
        )
        with self.assertRaises(UserError):
            self._close_wizard(deviation).action_confirm()

    def test_close_blocked_by_draft_disposition(self):
        """An unapproved disposition blocks closure."""
        deviation = self._advance_to_disposition(self._create_deviation())
        self.env["ls.deviation.disposition"].create(
            {
                "deviation_id": deviation.id,
                "product_id": self.product.id,
                "quantity": 5.0,
                "decision": "quarantine",
                "justification": "Pending assessment.",
            }
        )
        with self.assertRaises(UserError):
            self._close_wizard(deviation).action_confirm()

    def test_close_wizard_defaults_from_deviation(self):
        """The wizard pre-fills from the deviation being closed."""
        deviation = self._advance_to_disposition(self._create_deviation())
        deviation.conclusion = "Pre-existing conclusion."
        wizard = (
            self.env["ls.deviation.close.wizard"]
            .with_context(default_deviation_id=deviation.id)
            .create({"deviation_id": deviation.id})
        )
        defaults = wizard.default_get(["conclusion", "deviation_id"])
        self.assertEqual(defaults.get("conclusion"), "Pre-existing conclusion.")

    def test_cancel_records_reason_and_state(self):
        """Cancellation records the reason and reaches the cancelled state."""
        deviation = self._create_deviation()
        wizard = self.env["ls.deviation.cancel.wizard"].create(
            {
                "deviation_id": deviation.id,
                "mode": "cancel",
                "reason": "Raised in error against the wrong batch.",
            }
        )
        wizard.action_confirm()
        self.assertEqual(deviation.state, "cancelled")
        self.assertIn("raised in error", deviation.cancel_reason.lower())

    def test_send_back_returns_to_previous_state(self):
        """A send-back returns the record to the previous state."""
        deviation = self._advance_to_investigation(self._create_deviation())
        wizard = self.env["ls.deviation.cancel.wizard"].create(
            {
                "deviation_id": deviation.id,
                "mode": "send_back",
                "reason": "Investigation scope insufficient.",
            }
        )
        wizard.action_confirm()
        self.assertEqual(deviation.state, "assessed")

    def test_send_back_reason_is_logged(self):
        """The send-back reason reaches the transition log."""
        deviation = self._advance_to_investigation(self._create_deviation())
        self.env["ls.deviation.cancel.wizard"].create(
            {
                "deviation_id": deviation.id,
                "mode": "send_back",
                "reason": "Scope insufficient.",
            }
        ).action_confirm()
        reasons = deviation.stage_log_ids.mapped("reason")
        self.assertIn("Scope insufficient.", reasons)

    def test_send_back_rejected_from_reported(self):
        """A record in the first state cannot be sent back."""
        deviation = self._create_deviation()
        wizard = self.env["ls.deviation.cancel.wizard"].create(
            {
                "deviation_id": deviation.id,
                "mode": "send_back",
                "reason": "Nothing to send back to.",
            }
        )
        with self.assertRaises(UserError):
            wizard.action_confirm()

    def test_due_date_extension_applies(self):
        """A justified extension moves the target closure date."""
        today = fields.Date.context_today(self.env.user)
        deviation = self._create_deviation(due_date=today)
        new_date = today + timedelta(days=15)
        self.env["ls.deviation.due.date.wizard"].create(
            {
                "deviation_id": deviation.id,
                "new_due_date": new_date,
                "justification": "Awaiting supplier laboratory data.",
            }
        ).action_confirm()
        self.assertEqual(deviation.due_date, new_date)

    def test_due_date_cannot_move_earlier(self):
        """An extension must postdate the current target."""
        today = fields.Date.context_today(self.env.user)
        deviation = self._create_deviation(due_date=today)
        wizard = self.env["ls.deviation.due.date.wizard"].create(
            {
                "deviation_id": deviation.id,
                "new_due_date": today - timedelta(days=1),
                "justification": "Pulling the date in.",
            }
        )
        with self.assertRaises(UserError):
            wizard.action_confirm()

    def test_due_date_blocked_on_terminal_record(self):
        """A closed record has an immutable target closure date."""
        today = fields.Date.context_today(self.env.user)
        deviation = self._create_deviation(due_date=today)
        deviation.state = "closed"
        wizard = self.env["ls.deviation.due.date.wizard"].create(
            {
                "deviation_id": deviation.id,
                "new_due_date": today + timedelta(days=5),
                "justification": "Too late.",
            }
        )
        with self.assertRaises(UserError):
            wizard.action_confirm()

    def test_due_date_extension_posts_message(self):
        """The extension justification is posted to the chatter."""
        today = fields.Date.context_today(self.env.user)
        deviation = self._create_deviation(due_date=today)
        before = len(deviation.message_ids)
        self.env["ls.deviation.due.date.wizard"].create(
            {
                "deviation_id": deviation.id,
                "new_due_date": today + timedelta(days=7),
                "justification": "Laboratory retest scheduled.",
            }
        ).action_confirm()
        self.assertGreater(len(deviation.message_ids), before)

    def test_action_helpers_return_window_actions(self):
        """The button helpers return act_window dictionaries."""
        deviation = self._create_deviation()
        for method in (
            "action_open_close_wizard",
            "action_open_cancel_wizard",
            "action_open_due_date_wizard",
            "action_send_back",
        ):
            action = getattr(deviation, method)()
            self.assertEqual(action["type"], "ir.actions.act_window")
            self.assertEqual(action["target"], "new")
