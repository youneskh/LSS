# Part of the Life Sciences Suite for Odoo 19 Community Edition.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Tests for the scheduled monitoring actions."""

from datetime import timedelta

from odoo import fields
from odoo.tests import tagged

from .common import RecallCommon


@tagged("post_install", "-at_install")
class TestCron(RecallCommon):
    """The scheduled actions raise activities and change nothing else."""

    def test_overdue_recall_raises_one_activity(self):
        """A recall past its target date is flagged once."""
        execution = self._create_execution(
            # Decided ten days ago: the target date cannot precede the decision.
            decision_date=fields.Datetime.now() - timedelta(days=10),
            target_completion_date=fields.Date.today() - timedelta(days=3)
        )
        execution.action_initiate()
        flagged = self.env["ls.recall.execution"]._cron_monitor_open_recalls()
        self.assertGreaterEqual(flagged, 1)
        self.assertTrue(execution.activity_ids)
        before = len(execution.activity_ids)
        self.env["ls.recall.execution"]._cron_monitor_open_recalls()
        self.assertEqual(len(execution.activity_ids), before)

    def test_cron_does_not_change_state(self):
        """Monitoring never advances or closes a recall."""
        execution = self._create_execution(
            # Decided ten days ago: the target date cannot precede the decision.
            decision_date=fields.Datetime.now() - timedelta(days=10),
            target_completion_date=fields.Date.today() - timedelta(days=1)
        )
        execution.action_initiate()
        self.env["ls.recall.execution"]._cron_monitor_open_recalls()
        self.assertEqual(execution.state, "initiated")

    def test_closed_recall_not_flagged(self):
        """A finalised recall is out of scope for monitoring."""
        execution = self._create_execution(
            # Decided ten days ago: the target date cannot precede the decision.
            decision_date=fields.Datetime.now() - timedelta(days=10),
            target_completion_date=fields.Date.today() - timedelta(days=5)
        )
        execution.action_initiate()
        wizard = self.env["ls.recall.close.wizard"].create(
            {
                "execution_id": execution.id,
                "mode": "cancel",
                "justification": "Withdrawn.",
            }
        )
        wizard.action_confirm()
        self.env["ls.recall.execution"]._cron_monitor_open_recalls()
        self.assertFalse(execution.activity_ids)

    def test_mock_recall_not_monitored(self):
        """Rehearsals are excluded from the open-action monitor."""
        execution = self._create_execution(
            action_type="mock_recall",
            classification="not_classified",
            health_hazard_evaluation=False,
            depth=False,
            # Decided ten days ago: the target date cannot precede the decision.
            decision_date=fields.Datetime.now() - timedelta(days=10),
            target_completion_date=fields.Date.today() - timedelta(days=5),
        )
        execution.action_initiate()
        self.env["ls.recall.execution"]._cron_monitor_open_recalls()
        self.assertFalse(execution.activity_ids)

    def test_mock_recall_due_date_computed_from_approval(self):
        """The next rehearsal is due one interval after approval."""
        self.plan.mock_recall_interval_months = 6
        self.plan.action_submit_review()
        self.plan.action_approve()
        self.assertTrue(self.plan.next_mock_recall_date)
        expected = self.plan.approval_date.date()
        self.assertGreater(self.plan.next_mock_recall_date, expected)

    def test_overdue_mock_recall_raises_an_activity(self):
        """An overdue rehearsal is flagged on the plan."""
        self.plan.mock_recall_interval_months = 1
        self.plan.action_submit_review()
        self.plan.action_approve()
        self.plan.write(
            {"approval_date": fields.Datetime.now() - timedelta(days=120)}
        )
        self.plan.invalidate_recordset()
        flagged = self.env["ls.recall.plan"]._cron_check_mock_recall_due()
        self.assertGreaterEqual(flagged, 1)
        self.assertTrue(self.plan.activity_ids)
