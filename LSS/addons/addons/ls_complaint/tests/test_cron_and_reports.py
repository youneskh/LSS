# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Tests for the scheduled actions, the data files and the printed report."""

from datetime import timedelta

from odoo import fields
from odoo.tests import tagged

from .common import TestLsComplaintCommon


@tagged("post_install", "-at_install")
class TestCronAndReports(TestLsComplaintCommon):
    """Verify the scheduled actions, the delivered data and the PDF report."""

    def test_01_overdue_cron_creates_activity(self):
        """The scheduled action creates one activity per overdue complaint."""
        complaint = self._create_complaint()
        complaint.receipt_date = fields.Datetime.now() - timedelta(days=90)
        complaint.invalidate_recordset()
        created = self.env["ls.complaint"]._cron_notify_overdue_complaints()
        self.assertGreaterEqual(created, 1)
        self.assertTrue(complaint.activity_ids)

    def test_02_overdue_cron_is_idempotent(self):
        """A second run does not duplicate the activity."""
        complaint = self._create_complaint()
        complaint.receipt_date = fields.Datetime.now() - timedelta(days=90)
        complaint.invalidate_recordset()
        self.env["ls.complaint"]._cron_notify_overdue_complaints()
        count_first = len(complaint.activity_ids)
        self.env["ls.complaint"]._cron_notify_overdue_complaints()
        self.assertEqual(len(complaint.activity_ids), count_first)

    def test_03_adverse_event_cron_creates_activity(self):
        """The reporting scheduled action notifies the responsible user."""
        complaint = self._create_complaint()
        event = self.env["ls.complaint.adverse_event"].create(
            {
                "complaint_id": complaint.id,
                "event_description": "Reaction.",
                "reportable": True,
                "awareness_date": fields.Date.context_today(self.env.user)
                - timedelta(days=60),
            }
        )
        event.invalidate_recordset()
        created = self.env[
            "ls.complaint.adverse_event"
        ]._cron_notify_due_adverse_event_reports()
        self.assertGreaterEqual(created, 1)
        self.assertTrue(event.activity_ids)

    def test_04_sequences_are_installed(self):
        """The three sequences delivered by the module are present."""
        for code in (
            "ls.complaint",
            "ls.complaint.investigation",
            "ls.complaint.adverse_event",
        ):
            sequence = self.env["ir.sequence"].search([("code", "=", code)], limit=1)
            self.assertTrue(sequence, f"Sequence {code} is missing")

    def test_05_crons_are_installed(self):
        """The two scheduled actions delivered by the module are present."""
        self.assertTrue(self.env.ref("ls_complaint.cron_ls_complaint_overdue"))
        self.assertTrue(
            self.env.ref("ls_complaint.cron_ls_complaint_adverse_event_due")
        )

    def test_06_mail_templates_are_installed(self):
        """The two mail templates delivered by the module are present."""
        acknowledgement = self.env.ref(
            "ls_complaint.mail_template_complaint_acknowledgement"
        )
        closure = self.env.ref("ls_complaint.mail_template_complaint_closure")
        self.assertEqual(acknowledgement.model_id.model, "ls.complaint")
        self.assertEqual(closure.model_id.model, "ls.complaint")

    def test_07_report_renders(self):
        """The complaint record report renders without error."""
        complaint = self._create_complaint()
        report = self.env.ref("ls_complaint.action_report_ls_complaint")
        html = report._render_qweb_html(report.report_name, complaint.ids)[0]
        self.assertIn(complaint.name.encode(), html)

    def test_08_smart_button_actions(self):
        """The smart buttons return window actions on the child models."""
        complaint = self._create_complaint()
        self.assertEqual(
            complaint.action_view_investigations()["res_model"],
            "ls.complaint.investigation",
        )
        self.assertEqual(
            complaint.action_view_resolutions()["res_model"],
            "ls.complaint.resolution",
        )
        self.assertEqual(
            complaint.action_view_adverse_events()["res_model"],
            "ls.complaint.adverse_event",
        )
