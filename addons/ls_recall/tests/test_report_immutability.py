# Part of the Life Sciences Suite for Odoo 19 Community Edition.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Tests for recall reports, their approval and their frozen figures."""

from odoo.exceptions import UserError, ValidationError
from odoo.tests import tagged

from .common import RecallCommon


@tagged("post_install", "-at_install")
class TestReportImmutability(RecallCommon):
    """An approved report states figures that no longer move."""

    def _create_report(self, execution, **overrides):
        """Create a draft report on a recall."""
        values = {
            "execution_id": execution.id,
            "report_type": "final",
            "summary": "<p>Recall complete.</p>",
        }
        values.update(overrides)
        return self.env["ls.recall.report"].create(values)

    def test_reference_allocated(self):
        """A report receives a reference on creation."""
        report = self._create_report(self._create_execution())
        self.assertTrue(report.name.startswith("RCR/"))

    def test_review_requires_a_summary(self):
        """A report without a summary cannot be reviewed."""
        report = self._create_report(self._create_execution(), summary=False)
        with self.assertRaises(UserError):
            report.action_review()

    def test_approval_requires_a_prior_review(self):
        """A draft report cannot jump straight to approval."""
        report = self._create_report(self._create_execution())
        with self.assertRaises(UserError):
            report.action_approve()

    def test_reviewer_cannot_approve_own_review(self):
        """Review and approval are performed by different people."""
        report = self._create_report(self._create_execution())
        report.with_user(self.user_coordinator).action_review()
        with self.assertRaises(UserError):
            report.with_user(self.user_coordinator).action_approve()

    def test_approval_freezes_the_figures(self):
        """Approval copies the recall totals into the report."""
        execution = self._create_execution()
        self._add_line(execution, self.partner_a, self.lot_1, 100.0)
        execution.line_ids.qty_returned = 80.0
        report = self._create_report(execution)
        report.with_user(self.user_coordinator).action_review()
        report.with_user(self.user_manager).action_approve()
        self.assertEqual(report.snapshot_qty_distributed, 100.0)
        self.assertEqual(report.snapshot_qty_accounted, 80.0)
        self.assertTrue(report.snapshot_taken_on)

        execution.line_ids.qty_returned = 95.0
        self.assertEqual(execution.qty_accounted, 95.0)
        self.assertEqual(report.snapshot_qty_accounted, 80.0)

    def test_approved_report_content_is_frozen(self):
        """An approved report can no longer be reworded."""
        report = self._create_report(self._create_execution())
        report.with_user(self.user_coordinator).action_review()
        report.with_user(self.user_manager).action_approve()
        with self.assertRaises(UserError):
            report.summary = "<p>Rewritten after approval.</p>"

    def test_submission_requires_recipients(self):
        """Submission records who the report went to."""
        report = self._create_report(self._create_execution())
        report.with_user(self.user_coordinator).action_review()
        report.with_user(self.user_manager).action_approve()
        with self.assertRaises(UserError):
            report.action_submit()
        report.submitted_partner_ids = [(6, 0, [self.partner_authority.id])]
        report.action_submit()
        self.assertEqual(report.state, "submitted")
        self.assertTrue(report.submission_date)

    def test_only_one_final_report_per_recall(self):
        """A recall carries at most one final report."""
        execution = self._create_execution()
        self._create_report(execution)
        with self.assertRaises(ValidationError):
            self._create_report(execution)

    def test_reporting_period_must_be_ordered(self):
        """The period cannot end before it starts."""
        with self.assertRaises(ValidationError):
            self._create_report(
                self._create_execution(),
                period_start="2026-06-10",
                period_end="2026-06-01",
            )

    def test_approved_report_cannot_be_deleted(self):
        """An approved report stays on the record."""
        report = self._create_report(self._create_execution())
        report.with_user(self.user_coordinator).action_review()
        report.with_user(self.user_manager).action_approve()
        with self.assertRaises(UserError):
            report.unlink()
