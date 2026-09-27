# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Tests of the scheduled actions."""

from dateutil.relativedelta import relativedelta

from odoo.tests import tagged

from .common import AuditCommon


@tagged("post_install", "-at_install")
class TestCron(AuditCommon):
    """Overdue audits, overdue findings and lapsing qualifications."""

    def test_overdue_audit_cron_creates_one_activity(self):
        """The cron schedules exactly one activity per overdue audit."""
        self.program.date_start = self.today - relativedelta(months=6)
        self.audit.date_planned = self.today - relativedelta(days=5)
        processed = self.env["ls.audit.schedule"]._cron_notify_overdue_audits()
        self.assertGreaterEqual(processed, 1)
        activities = self.env["mail.activity"].search(
            [
                ("res_model", "=", "ls.audit.schedule"),
                ("res_id", "=", self.audit.id),
            ]
        )
        self.assertEqual(len(activities), 1)
        self.assertEqual(activities.user_id, self.user_lead)

    def test_overdue_audit_cron_is_idempotent(self):
        """Running the cron twice does not duplicate the activity."""
        self.program.date_start = self.today - relativedelta(months=6)
        self.audit.date_planned = self.today - relativedelta(days=5)
        audit_model = self.env["ls.audit.schedule"]
        audit_model._cron_notify_overdue_audits()
        audit_model._cron_notify_overdue_audits()
        activities = self.env["mail.activity"].search(
            [
                ("res_model", "=", "ls.audit.schedule"),
                ("res_id", "=", self.audit.id),
            ]
        )
        self.assertEqual(len(activities), 1)

    def test_overdue_audit_cron_ignores_started_audits(self):
        """An audit already in progress is not reported as overdue."""
        self.program.date_start = self.today - relativedelta(months=6)
        self.audit.date_planned = self.today - relativedelta(days=5)
        self._bring_audit_to_in_progress()
        self.env["ls.audit.schedule"]._cron_notify_overdue_audits()
        activities = self.env["mail.activity"].search(
            [
                ("res_model", "=", "ls.audit.schedule"),
                ("res_id", "=", self.audit.id),
            ]
        )
        self.assertFalse(activities)

    def test_overdue_finding_cron_counts_overdue_findings(self):
        """The cron reports findings past their response due date."""
        self._bring_audit_to_in_progress()
        self.audit.response_ids.filtered("is_mandatory").write(
            {"result": "conform"}
        )
        self.audit.action_complete()
        finding = self._create_finding()
        finding.action_issue()
        finding.response_due_date = self.today - relativedelta(days=2)
        processed = self.env[
            "ls.audit.finding"
        ]._cron_notify_overdue_findings()
        self.assertGreaterEqual(processed, 1)

    def test_qualification_cron_reports_lapsing_auditors(self):
        """The cron reports expiring and expired qualifications."""
        self.qualification_auditor.expiry_date = self.today - relativedelta(
            days=1
        )
        processed = self.env[
            "ls.audit.auditor"
        ]._cron_notify_qualification_expiry()
        self.assertGreaterEqual(processed, 1)

    def test_cron_records_are_installed(self):
        """The three scheduled actions are installed and active."""
        xmlids = [
            "cron_ls_audit_overdue_audits",
            "cron_ls_audit_overdue_findings",
            "cron_ls_audit_qualification_expiry",
        ]
        for xmlid in xmlids:
            with self.subTest(cron=xmlid):
                cron = self.env.ref("ls_audit.%s" % xmlid)
                self.assertTrue(cron.active)
                self.assertEqual(cron.state, "code")
