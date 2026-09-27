# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0.html).
"""Tests for the CAPA action model."""

from datetime import timedelta

from odoo.exceptions import UserError, ValidationError
from odoo.tests import tagged

from .common import CapaCommon


@tagged("post_install", "-at_install")
class TestCapaAction(CapaCommon):
    """Action lifecycle, lateness and project task integration."""

    def test_sequence_allocated(self):
        """An action receives a reference from the sequence."""
        action = self._make_action(self._make_issue())
        self.assertTrue(action.name.startswith("CAPA-ACT/"))

    def test_start_moves_to_in_progress(self):
        """Starting a draft action moves it to In Progress."""
        action = self._make_action(self._make_issue())
        action.action_start()
        self.assertEqual(action.state, "in_progress")

    def test_start_blocked_when_not_draft(self):
        """Only draft actions can be started."""
        action = self._make_action(self._make_issue())
        action.action_start()
        with self.assertRaises(UserError):
            action.action_start()

    def test_done_requires_evidence(self):
        """Completion requires documented completion evidence."""
        action = self._make_action(self._make_issue())
        with self.assertRaises(UserError):
            action.action_done()

    def test_done_stamps_completion_date(self):
        """Completion records the actual completion date."""
        action = self._make_action(self._make_issue())
        action.completion_evidence = "Certificate CC-01."
        action.action_done()
        self.assertEqual(action.state, "done")
        self.assertEqual(action.date_done, self.today)

    def test_done_blocked_when_cancelled(self):
        """A cancelled action cannot be completed."""
        action = self._make_action(self._make_issue())
        action.cancellation_reason = "Not applicable."
        action.action_cancel()
        action.completion_evidence = "Evidence."
        with self.assertRaises(UserError):
            action.action_done()

    def test_cancel_requires_reason(self):
        """Cancelling without a reason is rejected."""
        action = self._make_action(self._make_issue())
        with self.assertRaises(ValidationError):
            action.action_cancel()

    def test_cancel_blocked_when_done(self):
        """A completed action cannot be cancelled."""
        action = self._make_action(self._make_issue())
        action.completion_evidence = "Evidence."
        action.action_done()
        action.cancellation_reason = "Too late."
        with self.assertRaises(UserError):
            action.action_cancel()

    def test_reset_to_draft_clears_reason(self):
        """Resetting a cancelled action clears the cancellation reason."""
        action = self._make_action(self._make_issue())
        action.cancellation_reason = "Superseded."
        action.action_cancel()
        action.action_reset_to_draft()
        self.assertEqual(action.state, "draft")
        self.assertFalse(action.cancellation_reason)

    def test_reset_blocked_when_not_cancelled(self):
        """Only cancelled actions can be reset to draft."""
        action = self._make_action(self._make_issue())
        with self.assertRaises(UserError):
            action.action_reset_to_draft()

    def test_is_late_flag(self):
        """An open action past its planned date is late."""
        action = self._make_action(
            self._make_issue(), date_planned=self.today - timedelta(days=1)
        )
        self.assertTrue(action.is_late)

    def test_is_not_late_when_done(self):
        """A completed action is never late."""
        action = self._make_action(
            self._make_issue(), date_planned=self.today - timedelta(days=1)
        )
        action.completion_evidence = "Evidence."
        action.action_done()
        self.assertFalse(action.is_late)

    def test_search_is_late(self):
        """The late flag is searchable."""
        action = self._make_action(
            self._make_issue(), date_planned=self.today - timedelta(days=2)
        )
        found = self.env["ls.capa.action"].search(
            [("is_late", "=", True), ("id", "=", action.id)]
        )
        self.assertIn(action, found)

    def test_search_is_late_negative(self):
        """Searching for non-late actions excludes late ones."""
        action = self._make_action(
            self._make_issue(), date_planned=self.today - timedelta(days=2)
        )
        found = self.env["ls.capa.action"].search(
            [("is_late", "=", False), ("id", "=", action.id)]
        )
        self.assertNotIn(action, found)

    def test_search_is_late_rejects_operator(self):
        """The late search raises on an unsupported operator."""
        # Odoo 19 rejects an ordering operator on a boolean field in its
        # domain parser (ValueError), before the custom search method runs.
        with self.assertRaises(ValueError):
            self.env["ls.capa.action"].search([("is_late", "<", True)])

    def test_root_cause_must_belong_to_same_issue(self):
        """An action cannot reference another CAPA's root cause."""
        first = self._make_issue()
        second = self._make_issue()
        foreign = self._make_root_cause(second)
        with self.assertRaises(ValidationError):
            self._make_action(first, root_cause_id=foreign.id)

    def test_root_cause_same_issue_accepted(self):
        """An action can reference a root cause of its own CAPA."""
        issue = self._make_issue()
        root_cause = self._make_root_cause(issue)
        action = self._make_action(issue, root_cause_id=root_cause.id)
        self.assertEqual(action.root_cause_id, root_cause)

    def test_create_task(self):
        """A project task can be generated from an action."""
        action = self._make_action(self._make_issue())
        result = action.action_create_task()
        self.assertTrue(action.task_id)
        self.assertEqual(result["res_model"], "project.task")
        self.assertEqual(action.task_id.date_deadline.date(), action.date_planned)

    def test_create_task_twice_blocked(self):
        """An action cannot be linked to two tasks."""
        action = self._make_action(self._make_issue())
        action.action_create_task()
        with self.assertRaises(UserError):
            action.action_create_task()

    def test_create_task_uses_configured_project(self):
        """The configured default project is applied when set."""
        project = self.env["project.project"].create({"name": "CAPA Project"})
        self.env["ir.config_parameter"].sudo().set_param(
            "ls_capa.default_project_id", str(project.id)
        )
        action = self._make_action(self._make_issue())
        action.action_create_task()
        self.assertEqual(action.task_id.project_id, project)

    def test_cascade_delete_with_issue(self):
        """Deleting a CAPA removes its actions."""
        issue = self._make_issue()
        action = self._make_action(issue)
        issue.unlink()
        self.assertFalse(action.exists())
