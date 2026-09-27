# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Tests for retention policies and retention status evaluation."""

from datetime import date, timedelta

from dateutil.relativedelta import relativedelta

from odoo import fields
from odoo.exceptions import ValidationError

from .common import LsDocumentCommon


class TestLsDocumentRetentionPolicy(LsDocumentCommon):
    """Due date computation and retention status transitions."""

    def test_due_date_in_years(self):
        """A five year policy adds five years to the trigger date."""
        trigger = date(2026, 1, 15)
        self.assertEqual(
            self.policy.compute_due_date(trigger), date(2031, 1, 15)
        )

    def test_due_date_in_months(self):
        """A policy expressed in months adds the matching month offset."""
        policy = self.env["ls.document.retention_policy"].create(
            {
                "name": "Eighteen months",
                "code": "M18",
                "duration_value": 18,
                "duration_unit": "month",
            }
        )
        self.assertEqual(
            policy.compute_due_date(date(2026, 1, 15)), date(2027, 7, 15)
        )

    def test_due_date_without_trigger_date(self):
        """No trigger date yields no due date."""
        self.assertFalse(self.policy.compute_due_date(False))

    def test_unrealistic_duration_is_rejected(self):
        """Durations beyond two centuries are refused."""
        with self.assertRaises(ValidationError):
            self.env["ls.document.retention_policy"].create(
                {
                    "name": "Too long",
                    "code": "TOOLONG",
                    "duration_value": 500,
                    "duration_unit": "year",
                }
            )

    def test_display_name_includes_code(self):
        """The policy is displayed with its code."""
        self.assertIn("TEST-5Y", self.policy.display_name)

    def test_retention_state_not_applicable_without_policy(self):
        """A document without policy has no retention status."""
        document = self._create_document(retention_policy_id=False)
        document.update_retention_state()
        self.assertEqual(document.retention_state, "not_applicable")

    def test_retention_due_date_follows_effective_date(self):
        """Publishing a document sets the retention due date."""
        document = self._publish_document()
        self.assertEqual(
            document.retention_due_date,
            document.effective_date + relativedelta(years=5),
        )
        self.assertEqual(document.retention_state, "active")

    def test_retention_state_due_soon(self):
        """A due date inside the notice window is flagged as due soon."""
        document = self._publish_document()
        self.policy.duration_value = 1
        self.policy.duration_unit = "month"
        document.invalidate_recordset()
        document.update_retention_state()
        self.assertEqual(document.retention_state, "due_soon")

    def test_retention_state_elapsed_and_cron_notifies(self):
        """An elapsed retention period is detected by the scheduled action."""
        document = self._publish_document()
        document.write({"effective_date": fields.Date.today() - timedelta(days=4000)})
        document.invalidate_recordset()
        self.env["ls.document.document"]._cron_evaluate_retention()
        self.assertEqual(document.retention_state, "elapsed")
        self.assertEqual(document.state, "published")

    def test_cron_archives_when_policy_requires_it(self):
        """The archive end-of-life action withdraws the document."""
        self.policy.end_of_life_action = "archive"
        document = self._publish_document()
        document.write({"effective_date": fields.Date.today() - timedelta(days=4000)})
        document.invalidate_recordset()
        self.env["ls.document.document"]._cron_evaluate_retention()
        self.assertEqual(document.state, "archived")

    def test_cron_respects_legal_hold(self):
        """A document under legal hold is never archived automatically."""
        self.policy.end_of_life_action = "archive"
        document = self._publish_document()
        document.write(
            {
                "effective_date": fields.Date.today() - timedelta(days=4000),
                "legal_hold": True,
            }
        )
        document.invalidate_recordset()
        self.env["ls.document.document"]._cron_evaluate_retention()
        self.assertEqual(document.state, "published")
        self.assertEqual(document.retention_state, "elapsed")

    def _publish_document(self):
        """Create, approve and publish a document as the manager.

        :return: the published ``ls.document.document`` record.
        """
        document = self._create_document(
            approver_ids=[(6, 0, [self.user_approver.id])]
        )
        self._create_version(document)
        document.action_submit_review()
        self._approve_all(document)
        document.with_user(self.user_manager).action_publish()
        return document
