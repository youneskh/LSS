# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0.html).
"""Tests for the CAPA state machine and its gating business rules."""

from odoo.exceptions import UserError, ValidationError
from odoo.tests import tagged

from .common import CapaCommon


@tagged("post_install", "-at_install")
class TestCapaWorkflow(CapaCommon):
    """Every transition of the eight-state CAPA lifecycle."""

    def test_full_happy_path(self):
        """A CAPA can travel the whole lifecycle to Closed."""
        issue = self._make_issue()
        self._advance_to_verified(issue)
        self.assertEqual(issue.state, "verified")
        issue.closure_summary = "Actions implemented and verified."
        issue.action_close()
        self.assertEqual(issue.state, "closed")
        self.assertTrue(issue.date_closed)
        self.assertEqual(issue.closed_by_id, self.env.user)

    def test_assess_requires_impact_assessment(self):
        """Assessment is blocked until an impact assessment is documented."""
        issue = self._make_issue()
        with self.assertRaises(UserError):
            issue.action_assess()

    def test_assess_succeeds_with_impact_assessment(self):
        """Assessment succeeds once the impact assessment is present."""
        issue = self._make_issue()
        issue.impact_assessment = "No product impact."
        issue.action_assess()
        self.assertEqual(issue.state, "assessed")

    def test_assess_rejects_whitespace_only_assessment(self):
        """A whitespace-only impact assessment does not satisfy the gate."""
        issue = self._make_issue()
        issue.impact_assessment = "   \n  "
        with self.assertRaises(UserError):
            issue.action_assess()

    def test_transition_from_wrong_state_is_blocked(self):
        """A transition raises when the source state is wrong."""
        issue = self._make_issue()
        with self.assertRaises(UserError):
            issue.action_complete()

    def test_action_planning_requires_confirmed_root_cause(self):
        """Action planning is blocked without a confirmed root cause."""
        issue = self._make_issue()
        issue.impact_assessment = "Assessed."
        issue.action_assess()
        issue.action_start_investigation()
        self._make_root_cause(issue)
        with self.assertRaises(UserError):
            issue.action_start_action_planning()

    def test_action_planning_succeeds_after_confirmation(self):
        """Confirming the root cause unblocks action planning."""
        issue = self._make_issue()
        issue.impact_assessment = "Assessed."
        issue.action_assess()
        issue.action_start_investigation()
        self._make_root_cause(issue).action_confirm()
        issue.action_start_action_planning()
        self.assertEqual(issue.state, "action_planning")

    def test_start_progress_requires_an_action(self):
        """Execution cannot start with no planned action."""
        issue = self._make_issue()
        issue.impact_assessment = "Assessed."
        issue.action_assess()
        issue.action_start_investigation()
        self._make_root_cause(issue).action_confirm()
        issue.action_start_action_planning()
        with self.assertRaises(UserError):
            issue.action_start_progress()

    def test_complete_requires_all_actions_settled(self):
        """Completion is blocked while an action is still open."""
        issue = self._make_issue()
        self._advance_to_in_progress(issue)
        self._make_action(issue)
        with self.assertRaises(UserError):
            issue.action_complete()

    def test_complete_accepts_cancelled_actions(self):
        """Cancelled actions do not block completion."""
        issue = self._make_issue()
        action = self._advance_to_in_progress(issue)
        action.cancellation_reason = "No longer applicable."
        action.action_cancel()
        issue.action_complete()
        self.assertEqual(issue.state, "completed")

    def test_verify_requires_effective_check(self):
        """Verification needs at least one Effective conclusion."""
        issue = self._make_issue()
        action = self._advance_to_in_progress(issue)
        action.completion_evidence = "Evidence."
        action.action_done()
        issue.action_complete()
        with self.assertRaises(UserError):
            issue.action_verify()

    def test_verify_blocked_by_pending_check(self):
        """A check still open blocks verification."""
        issue = self._make_issue()
        action = self._advance_to_in_progress(issue)
        action.completion_evidence = "Evidence."
        action.action_done()
        issue.action_complete()
        effective = self._make_effectiveness(issue)
        effective.conclusion = "No recurrence."
        effective.action_mark_effective()
        self._make_effectiveness(issue)
        with self.assertRaises(UserError):
            issue.action_verify()

    def test_close_requires_summary(self):
        """Closure is blocked without a closure summary."""
        issue = self._make_issue()
        self._advance_to_verified(issue)
        with self.assertRaises(UserError):
            issue.action_close()

    def test_close_summary_constraint(self):
        """A closed record cannot have its summary cleared."""
        issue = self._make_issue()
        self._advance_to_verified(issue)
        issue.closure_summary = "Verified effective."
        issue.action_close()
        with self.assertRaises(ValidationError):
            issue.closure_summary = False

    def test_close_wizard_closes_the_capa(self):
        """The closure wizard writes the summary and closes the CAPA."""
        issue = self._make_issue()
        self._advance_to_verified(issue)
        wizard = (
            self.env["ls.capa.close.wizard"]
            .with_context(default_issue_id=issue.id)
            .create({"issue_id": issue.id, "closure_summary": "All verified."})
        )
        wizard.action_confirm_close()
        self.assertEqual(issue.state, "closed")
        self.assertEqual(issue.closure_summary, "All verified.")

    def test_close_wizard_rejects_blank_summary(self):
        """The wizard refuses a whitespace-only summary."""
        issue = self._make_issue()
        self._advance_to_verified(issue)
        wizard = self.env["ls.capa.close.wizard"].create(
            {"issue_id": issue.id, "closure_summary": "   "}
        )
        with self.assertRaises(UserError):
            wizard.action_confirm_close()

    def test_close_wizard_defaults_from_issue(self):
        """The wizard pre-fills an existing summary from the CAPA."""
        issue = self._make_issue()
        self._advance_to_verified(issue)
        issue.closure_summary = "Draft summary."
        defaults = (
            self.env["ls.capa.close.wizard"]
            .with_context(default_issue_id=issue.id)
            .default_get(["issue_id", "closure_summary"])
        )
        self.assertEqual(defaults.get("closure_summary"), "Draft summary.")

    def test_open_close_wizard_action(self):
        """The CAPA exposes an action opening the closure wizard."""
        issue = self._make_issue()
        self._advance_to_verified(issue)
        action = issue.action_open_close_wizard()
        self.assertEqual(action["res_model"], "ls.capa.close.wizard")
        self.assertEqual(action["context"]["default_issue_id"], issue.id)

    def test_open_close_wizard_blocked_before_verified(self):
        """The closure wizard cannot be opened before verification."""
        issue = self._make_issue()
        with self.assertRaises(UserError):
            issue.action_open_close_wizard()

    def test_state_changes_are_logged(self):
        """Each transition posts a message in the chatter."""
        issue = self._make_issue()
        before = len(issue.message_ids)
        issue.impact_assessment = "Assessed."
        issue.action_assess()
        self.assertGreater(len(issue.message_ids), before)
