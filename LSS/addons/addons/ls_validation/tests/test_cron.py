# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Tests of the scheduled action refreshing the validation status."""

from dateutil.relativedelta import relativedelta

from odoo import fields
from odoo.tests import tagged

from .common import ValidationCommon


@tagged("post_install", "-at_install")
class TestCron(ValidationCommon):
    """Status refresh and revalidation activities."""

    def setUp(self):
        """Validate the item of the fixture through an approved report."""
        super().setUp()
        self.protocol = self._create_protocol(test_count=1, critical=False)
        self._approve_protocol(self.protocol)
        self.execution = self._execute_protocol(self.protocol)
        self.report = self.env["ls.validation.report"].create(
            {
                "name": "Summary report",
                "item_id": self.item.id,
                "execution_ids": [(6, 0, self.execution.ids)],
                "summary": "<p>Passed.</p>",
                "conclusion": "validated",
                "validity_months": 36,
            }
        )
        self.report.action_submit_review()
        self._sign(self.report, "action_approve", self.user_approver)

    def test_status_becomes_expired_after_the_validity(self):
        """An expired validity is reflected by the scheduled action."""
        self.item.invalidate_recordset()
        self.assertEqual(self.item.validation_state, "validated")
        past = fields.Date.context_today(self.report) - relativedelta(years=4)
        # Pending ORM computations must reach the database before the raw
        # SQL update, otherwise they would overwrite it at the next flush.
        self.env.flush_all()
        self.env.cr.execute(
            "UPDATE ls_validation_report SET valid_from = %s, valid_until = %s "
            "WHERE id = %s",
            (past, past + relativedelta(months=36), self.report.id),
        )
        self.report.invalidate_recordset()
        changed = self.env["ls.validation.item"]._cron_refresh_validation_status()
        self.item.invalidate_recordset()
        self.assertEqual(self.item.validation_state, "expired")
        self.assertGreaterEqual(changed, 1)

    def test_activity_is_scheduled_once_for_an_expiring_item(self):
        """The scheduled action creates a single revalidation activity."""
        self.env.flush_all()
        self.env.cr.execute(
            "UPDATE ls_validation_report SET valid_until = %s WHERE id = %s",
            (fields.Date.context_today(self.report), self.report.id),
        )
        self.report.invalidate_recordset()
        self.env["ls.validation.item"]._cron_refresh_validation_status()
        self.env["ls.validation.item"]._cron_refresh_validation_status()
        activities = self.env["mail.activity"].search(
            [
                ("res_model", "=", "ls.validation.item"),
                ("res_id", "=", self.item.id),
            ]
        )
        self.assertEqual(len(activities), 1)

    def test_retired_items_are_ignored(self):
        """A retired item is left untouched by the scheduled action."""
        self.item.action_retire()
        self.env["ls.validation.item"]._cron_refresh_validation_status()
        self.item.invalidate_recordset()
        self.assertEqual(self.item.validation_state, "retired")

    def test_refresh_cron_is_active(self):
        """The shipped scheduled action is active after installation."""
        cron = self.env.ref("ls_validation.cron_ls_validation_refresh_status")
        self.assertTrue(cron.active)
