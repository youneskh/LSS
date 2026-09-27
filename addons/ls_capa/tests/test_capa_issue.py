# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0.html).
"""Tests for the CAPA record model."""

from datetime import timedelta

from odoo.exceptions import UserError
from odoo.tests import tagged

from .common import CapaCommon


@tagged("post_install", "-at_install")
class TestCapaIssue(CapaCommon):
    """Creation, sequencing, computed fields and scheduled actions."""

    def test_sequence_allocated_on_create(self):
        """A CAPA reference is taken from the sequence on creation."""
        issue = self._make_issue()
        self.assertNotEqual(issue.name, "New")
        self.assertTrue(issue.name.startswith("CAPA/"))

    def test_sequence_unique_across_records(self):
        """Two CAPA records never share the same reference."""
        first = self._make_issue()
        second = self._make_issue()
        self.assertNotEqual(first.name, second.name)

    def test_explicit_name_is_preserved(self):
        """An explicitly supplied reference is not overwritten."""
        issue = self._make_issue(name="CAPA/MANUAL/00001")
        self.assertEqual(issue.name, "CAPA/MANUAL/00001")

    def test_copy_reallocates_reference(self):
        """Duplicating a CAPA allocates a fresh reference."""
        issue = self._make_issue()
        duplicate = issue.copy()
        self.assertNotEqual(duplicate.name, issue.name)
        self.assertTrue(duplicate.name.startswith("CAPA/"))

    def test_default_state_is_identified(self):
        """A new CAPA starts in the Identified state."""
        self.assertEqual(self._make_issue().state, "identified")

    def test_due_date_computed_from_category(self):
        """The due date is derived from the category lead time."""
        issue = self._make_issue()
        self.assertEqual(
            issue.date_due,
            issue.date_identified + timedelta(
                days=self.category.default_due_days
            ),
        )

    def test_due_date_recomputed_when_category_changes(self):
        """Changing the category re-proposes the due date."""
        issue = self._make_issue()
        other = self.env["ls.capa.category"].create(
            {"name": "Slow", "code": "SLOW", "default_due_days": 90}
        )
        issue.category_id = other
        self.assertEqual(
            issue.date_due, issue.date_identified + timedelta(days=90)
        )

    def test_due_date_manually_overridable(self):
        """A manually entered due date is retained."""
        issue = self._make_issue()
        manual = issue.date_identified + timedelta(days=7)
        issue.date_due = manual
        self.assertEqual(issue.date_due, manual)

    def test_relation_counts(self):
        """Smart button counters reflect the linked records."""
        issue = self._make_issue()
        self._make_root_cause(issue)
        self._make_action(issue)
        self._make_action(issue)
        self._make_effectiveness(issue)
        self.assertEqual(issue.root_cause_count, 1)
        self.assertEqual(issue.action_count, 2)
        self.assertEqual(issue.effectiveness_count, 1)

    def test_progress_zero_without_actions(self):
        """Progress is zero when no action exists."""
        self.assertEqual(self._make_issue().progress, 0.0)

    def test_progress_ignores_cancelled_actions(self):
        """Cancelled actions are excluded from the progress denominator."""
        issue = self._make_issue()
        done = self._make_action(issue)
        cancelled = self._make_action(issue)
        done.completion_evidence = "Evidence."
        done.action_done()
        cancelled.cancellation_reason = "Superseded."
        cancelled.action_cancel()
        self.assertEqual(issue.progress, 100.0)

    def test_progress_partial(self):
        """Progress reports the share of completed actions."""
        issue = self._make_issue()
        first = self._make_action(issue)
        self._make_action(issue)
        first.completion_evidence = "Evidence."
        first.action_done()
        self.assertEqual(issue.progress, 50.0)

    def test_is_overdue_flag(self):
        """An open CAPA past its due date is flagged as overdue."""
        issue = self._make_issue()
        issue.date_due = self.today - timedelta(days=1)
        self.assertTrue(issue.is_overdue)
        self.assertEqual(issue.days_to_due, -1)

    def test_is_not_overdue_when_due_in_future(self):
        """A CAPA with a future due date is not overdue."""
        issue = self._make_issue()
        issue.date_due = self.today + timedelta(days=5)
        self.assertFalse(issue.is_overdue)
        self.assertEqual(issue.days_to_due, 5)

    def test_is_overdue_false_without_due_date(self):
        """A CAPA without a due date is never overdue."""
        issue = self._make_issue(category_id=False)
        issue.date_due = False
        self.assertFalse(issue.is_overdue)

    def test_search_overdue_true(self):
        """Searching on the overdue flag returns overdue records."""
        issue = self._make_issue()
        issue.date_due = self.today - timedelta(days=3)
        found = self.env["ls.capa.issue"].search(
            [("is_overdue", "=", True), ("id", "=", issue.id)]
        )
        self.assertIn(issue, found)

    def test_search_overdue_false(self):
        """Searching for non-overdue records excludes overdue ones."""
        issue = self._make_issue()
        issue.date_due = self.today - timedelta(days=3)
        found = self.env["ls.capa.issue"].search(
            [("is_overdue", "=", False), ("id", "=", issue.id)]
        )
        self.assertNotIn(issue, found)

    def test_search_overdue_rejects_unsupported_operator(self):
        """The overdue search raises on an unsupported operator."""
        # Odoo 19 rejects an ordering operator on a boolean field in its
        # domain parser (ValueError), before the custom search method runs.
        with self.assertRaises(ValueError):
            self.env["ls.capa.issue"].search([("is_overdue", ">", True)])

    def test_unlink_allowed_in_identified_state(self):
        """A CAPA still in Identified can be deleted."""
        issue = self._make_issue()
        issue.unlink()
        self.assertFalse(issue.exists())

    def test_unlink_blocked_after_progress(self):
        """A CAPA that progressed cannot be deleted."""
        issue = self._make_issue()
        issue.impact_assessment = "Assessed."
        issue.action_assess()
        with self.assertRaises(UserError):
            issue.unlink()

    def test_cron_posts_message_on_overdue(self):
        """The scheduled action posts a reminder on overdue records."""
        issue = self._make_issue()
        issue.date_due = self.today - timedelta(days=2)
        before = len(issue.message_ids)
        self.env["ls.capa.issue"]._cron_notify_overdue()
        self.assertGreater(len(issue.message_ids), before)

    def test_cron_ignores_closed_records(self):
        """The scheduled action skips closed CAPA records."""
        issue = self._make_issue()
        self._advance_to_verified(issue)
        issue.closure_summary = "Closed after verification."
        issue.action_close()
        issue.date_due = self.today - timedelta(days=2)
        before = len(issue.message_ids)
        self.env["ls.capa.issue"]._cron_notify_overdue()
        self.assertEqual(len(issue.message_ids), before)

    def test_navigation_actions_return_domains(self):
        """The smart button actions target the correct models."""
        issue = self._make_issue()
        self.assertEqual(
            issue.action_view_root_causes()["res_model"],
            "ls.capa.root_cause",
        )
        self.assertEqual(
            issue.action_view_actions()["res_model"], "ls.capa.action"
        )
        self.assertEqual(
            issue.action_view_effectiveness()["res_model"],
            "ls.capa.effectiveness",
        )

    def test_category_issue_count_and_action(self):
        """The category counts its CAPA records and opens them."""
        issue = self._make_issue()
        self.assertEqual(self.category.issue_count, 1)
        action = self.category.action_view_issues()
        self.assertEqual(action["res_model"], "ls.capa.issue")
        self.assertEqual(
            action["domain"], [("category_id", "=", self.category.id)]
        )
        self.assertTrue(issue.exists())
