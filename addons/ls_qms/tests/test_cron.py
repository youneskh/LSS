# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0.html).
"""Scheduled actions of the quality management system."""

from dateutil.relativedelta import relativedelta

from .common import LsQmsCommon


class TestCron(LsQmsCommon):
    """Review, monitoring and retention scheduled actions."""

    def _activity_count(self, record):
        """Return the number of activities linked to ``record``."""
        return self.env["mail.activity"].search_count(
            [("res_model", "=", record._name), ("res_id", "=", record.id)]
        )

    def test_01_document_review_reminder(self):
        """A document reaching its review date receives one activity."""
        sop = self._publish(self._create_sop())
        sop.write({"date_next_review": self.today + relativedelta(days=5)})
        created = self.env[
            "ls.qms.document.mixin"
        ]._cron_document_review_reminder()
        self.assertGreaterEqual(created, 1)
        self.assertEqual(self._activity_count(sop), 1)

    def test_02_document_review_reminder_is_idempotent(self):
        """A second run does not duplicate the activity."""
        sop = self._publish(self._create_sop())
        sop.write({"date_next_review": self.today + relativedelta(days=5)})
        self.env["ls.qms.document.mixin"]._cron_document_review_reminder()
        self.env["ls.qms.document.mixin"]._cron_document_review_reminder()
        self.assertEqual(self._activity_count(sop), 1)

    def test_03_document_not_due_is_ignored(self):
        """A document far from its review date receives no activity."""
        sop = self._publish(self._create_sop())
        sop.write({"date_next_review": self.today + relativedelta(days=400)})
        self.env["ls.qms.document.mixin"]._cron_document_review_reminder()
        self.assertEqual(self._activity_count(sop), 0)

    def test_04_objective_monitoring(self):
        """An objective below target near its due date is flagged."""
        objective = self._create_objective(
            date_target=self.today + relativedelta(days=5)
        )
        objective.action_start()
        created = self.env["ls.qms.objective"]._cron_objective_monitoring()
        self.assertGreaterEqual(created, 1)
        self.assertEqual(self._activity_count(objective), 1)

    def test_05_achieved_objective_is_not_flagged(self):
        """An objective at one hundred percent receives no activity."""
        objective = self._create_objective(
            date_target=self.today + relativedelta(days=5)
        )
        objective.action_start()
        self.env["ls.qms.objective.measurement"].create(
            {
                "objective_id": objective.id,
                "date": self.today,
                "value": objective.target_value,
            }
        )
        self.env["ls.qms.objective"]._cron_objective_monitoring()
        self.assertEqual(self._activity_count(objective), 0)

    def test_06_retention_review(self):
        """A record past its retention date is flagged for review."""
        record = self._create_quality_record()
        record.with_user(self.user_author).action_confirm()
        record.sudo().write(
            {"date_retention_until": self.today - relativedelta(days=1)}
        )
        created = self.env["ls.qms.quality_record"]._cron_retention_review()
        self.assertGreaterEqual(created, 1)
        self.assertEqual(self._activity_count(record), 1)

    def test_07_retention_review_is_idempotent(self):
        """A second run does not duplicate the retention activity."""
        record = self._create_quality_record()
        record.with_user(self.user_author).action_confirm()
        record.sudo().write(
            {"date_retention_until": self.today - relativedelta(days=1)}
        )
        self.env["ls.qms.quality_record"]._cron_retention_review()
        self.env["ls.qms.quality_record"]._cron_retention_review()
        self.assertEqual(self._activity_count(record), 1)
