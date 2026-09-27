# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Regression tests for the findings of the 2026-09-25 audit.

F-15 date-dependent stored fields refreshed by the scheduled job, F-43
segregation of duties on the approvals of the post-market documents.
"""

from datetime import date

from dateutil.relativedelta import relativedelta
from freezegun import freeze_time

from odoo.exceptions import UserError
from odoo.tests import tagged

from .common import MedicalDeviceCommon


@tagged("post_install", "-at_install")
class TestAuditFixes(MedicalDeviceCommon):
    """Behaviour restored by the 2026-09-25 remediation."""

    def test_cron_refreshes_the_overdue_periodic_report(self):
        """A report falling due without any edit is flagged by the job."""
        device = self.device_iia
        if not device.periodic_report_interval_months:
            self.skipTest("The class IIa fixture declares no reporting interval.")
        placement = date.today() - relativedelta(days=10)
        device.write({"state": "on_market", "market_placement_date": placement})
        self.env.flush_all()
        self.assertFalse(device.periodic_report_overdue)
        due = placement + relativedelta(months=device.periodic_report_interval_months)
        with freeze_time(due + relativedelta(days=1)):
            self.env["ls.md.device"]._cron_check_post_market_obligations()
            self.env.flush_all()
            device.invalidate_recordset()
            self.assertTrue(device.periodic_report_overdue)
        self.assertTrue(device.activity_ids)

    def test_author_cannot_approve_the_pms_report(self):
        """The author of a post-market surveillance report cannot approve it."""
        report = self.env["ls.md.pms_report"].create(
            {
                "device_id": self.device_iia.id,
                "report_type": "psur",
                "period_start": date(2025, 1, 1),
                "period_end": date(2025, 12, 31),
                "author_id": self.user_regulatory.id,
                "data_analysis_summary": "Analysis recorded for the test.",
                "benefit_risk_conclusion": "Benefit-risk remains favourable.",
                "conclusion": "favourable",
            }
        )
        report.action_submit_for_review()
        with self.assertRaises(UserError):
            report.with_user(self.user_regulatory).action_approve()
