# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Tests for the scheduled actions of the module."""

from dateutil.relativedelta import relativedelta

from odoo import fields
from odoo.tests.common import tagged

from .common import LsTrainingCommon


@tagged("post_install", "-at_install")
class TestLsTrainingCron(LsTrainingCommon):
    """Scheduled status refresh and expiry reminders."""

    def setUp(self):
        """Create one certification used by every scheduled-action test."""
        super().setUp()
        self.certification = self.env["ls.training.certification"].create(
            {
                "employee_id": self.employee.id,
                "course_id": self.course.id,
                "company_id": self.company.id,
            }
        )

    def test_refresh_updates_expired_status(self):
        """The daily refresh moves a lapsed certification to expired.

        The certification is aged with SQL to reproduce a record whose
        status was stored while it was still valid. Pending ORM computations
        are flushed first, otherwise they would overwrite the SQL values.
        """
        self.env.flush_all()
        self.env.cr.execute(
            "UPDATE ls_training_certification "
            "SET date_granted = %s, date_expiry = %s, state = %s WHERE id = %s",
            (
                fields.Date.today() - relativedelta(days=370),
                fields.Date.today() - relativedelta(days=5),
                "valid",
                self.certification.id,
            ),
        )
        self.certification.invalidate_recordset()
        self.assertEqual(self.certification.state, "valid")
        self.env[
            "ls.training.certification"
        ]._cron_refresh_certification_state()
        self.certification.invalidate_recordset()
        self.assertEqual(self.certification.state, "expired")

    def test_refresh_skips_revoked(self):
        """A revoked certification keeps its terminal status.

        The refresh must not resurrect a revoked record into 'expired',
        even when its expiry date has passed.
        """
        self.certification.write(
            {
                "revocation_reason": "Reason.",
                "revoked": True,
                "date_granted": fields.Date.today() - relativedelta(days=370),
                "date_expiry": fields.Date.today() - relativedelta(days=5),
            }
        )
        self.assertEqual(self.certification.state, "revoked")
        self.env[
            "ls.training.certification"
        ]._cron_refresh_certification_state()
        self.certification.invalidate_recordset()
        self.assertEqual(self.certification.state, "revoked")

    def test_reminder_queues_mail_for_expiring(self):
        """An expiring certification produces a reminder message."""
        self.certification.write(
            {"date_expiry": fields.Date.today() + relativedelta(days=5)}
        )
        self.assertEqual(self.certification.state, "expiring")
        sent = self.env[
            "ls.training.certification"
        ]._cron_send_expiry_reminders()
        self.assertGreaterEqual(sent, 1)

    def test_reminder_skips_valid_certifications(self):
        """A certification far from expiry produces no reminder."""
        self.certification.write(
            {"date_expiry": fields.Date.today() + relativedelta(days=300)}
        )
        self.env["ls.training.certification"].search(
            [("id", "!=", self.certification.id)]
        ).write({"revocation_reason": "Reason.", "revoked": True})
        sent = self.env[
            "ls.training.certification"
        ]._cron_send_expiry_reminders()
        self.assertEqual(sent, 0)

    def test_reminder_requires_work_email(self):
        """Employees without a work email are not notified."""
        self.employee.write({"work_email": False})
        self.certification.write(
            {"date_expiry": fields.Date.today() + relativedelta(days=5)}
        )
        sent = self.env[
            "ls.training.certification"
        ]._cron_send_expiry_reminders()
        self.assertEqual(sent, 0)

    def test_cron_records_exist_and_are_active(self):
        """Both scheduled actions are installed and enabled."""
        for xml_id in (
            "ls_training.ls_training_cron_refresh_certification_state",
            "ls_training.ls_training_cron_send_expiry_reminders",
        ):
            cron = self.env.ref(xml_id)
            self.assertTrue(cron.active)
            self.assertEqual(cron.interval_type, "days")
