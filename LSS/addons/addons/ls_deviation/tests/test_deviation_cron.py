# Copyright 2026 Life Sciences Suite
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Scheduled action tests."""

from datetime import timedelta

from odoo import fields
from odoo.tests import tagged

from .common import DeviationCommon


@tagged("post_install", "-at_install")
class TestDeviationCron(DeviationCommon):
    """Verify the overdue notification scheduled action."""

    def test_cron_counts_only_overdue_open_records(self):
        """The cron selects open records past their target date."""
        today = fields.Date.context_today(self.env.user)
        overdue = self._create_deviation(
            due_date=today - timedelta(days=2),
            owner_id=self.user_investigator.id,
        )
        self._create_deviation(due_date=today + timedelta(days=5))
        closed = self._create_deviation(due_date=today - timedelta(days=2))
        closed.state = "closed"

        notified = self.env["ls.deviation"]._cron_notify_overdue()
        self.assertGreaterEqual(notified, 1)

        selected = self.env["ls.deviation"].search(
            [
                ("state", "not in", ["closed", "cancelled"]),
                ("due_date", "!=", False),
                ("due_date", "<", today),
            ]
        )
        self.assertIn(overdue, selected)
        self.assertNotIn(closed, selected)

    def test_cron_subscribes_owner_and_reviewer(self):
        """Owners and QA reviewers are subscribed to the overdue record."""
        today = fields.Date.context_today(self.env.user)
        deviation = self._create_deviation(
            due_date=today - timedelta(days=1),
            owner_id=self.user_investigator.id,
            qa_reviewer_id=self.user_manager.id,
        )
        self.env["ls.deviation"]._cron_notify_overdue()
        followers = deviation.message_partner_ids
        self.assertIn(self.user_investigator.partner_id, followers)
        self.assertIn(self.user_manager.partner_id, followers)

    def test_cron_is_idempotent(self):
        """Running the cron twice does not fail."""
        today = fields.Date.context_today(self.env.user)
        self._create_deviation(
            due_date=today - timedelta(days=1),
            owner_id=self.user_investigator.id,
        )
        first = self.env["ls.deviation"]._cron_notify_overdue()
        second = self.env["ls.deviation"]._cron_notify_overdue()
        self.assertEqual(first, second)

    def test_cron_handles_no_overdue_records(self):
        """The cron returns zero when nothing is overdue."""
        self.env["ls.deviation"].search([]).write({"due_date": False})
        self.assertEqual(self.env["ls.deviation"]._cron_notify_overdue(), 0)
