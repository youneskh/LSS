# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Tests of the audit report lifecycle and its controls."""

from odoo.exceptions import UserError
from odoo.tests import tagged

from .common import AuditCommon


@tagged("post_install", "-at_install")
class TestAuditReport(AuditCommon):
    """Preparation, review, approval, issuance and locking of reports."""

    def setUp(self):
        """Advance the fixture audit to the completed status."""
        super().setUp()
        self._bring_audit_to_in_progress()
        self.audit.response_ids.filtered("is_mandatory").write(
            {"result": "conform"}
        )
        self.audit.action_complete()

    def test_reference_is_allocated(self):
        """A report receives a reference from its sequence."""
        report = self._create_report()
        self.assertTrue(report.reference.startswith("ARP/"))

    def test_cannot_submit_before_fieldwork_complete(self):
        """A report on an unfinished audit cannot be submitted."""
        audit = self._create_audit(name="Unfinished Audit")
        report = self._create_report(audit=audit)
        with self.assertRaises(UserError):
            report.action_submit_review()

    def test_approval_requires_prior_review(self):
        """A report cannot be approved before it is reviewed."""
        report = self._create_report()
        report.with_user(self.user_lead).action_submit_review()
        with self.assertRaises(UserError):
            report.with_user(self.user_manager).action_approve()

    def test_review_records_reviewer_and_date(self):
        """The review records who reviewed the report and when."""
        report = self._create_report()
        report.with_user(self.user_lead).action_submit_review()
        report.with_user(self.user_manager).action_review()
        self.assertEqual(report.reviewed_by_id, self.user_manager)
        self.assertTrue(report.review_date)

    def test_issue_requires_distribution_list(self):
        """A report without recipient cannot be issued."""
        report = self._create_report(distribution_ids=[(5, 0, 0)])
        report.with_user(self.user_lead).action_submit_review()
        report.with_user(self.user_manager).action_review()
        report.with_user(self.user_manager).action_approve()
        with self.assertRaises(UserError):
            report.with_user(self.user_manager).action_issue()

    def test_full_lifecycle_to_issued(self):
        """A report reaches the issued status through every control."""
        report = self._issue_report()
        self.assertEqual(report.state, "issued")
        self.assertTrue(report.issue_date)
        self.assertTrue(report.approved_by_id)

    def test_issued_report_is_read_only(self):
        """An issued report refuses further modification."""
        report = self._issue_report()
        with self.assertRaises(UserError):
            report.conclusion = "Rewritten after issue"

    def test_issued_report_cannot_be_deleted(self):
        """An issued report cannot be deleted."""
        report = self._issue_report()
        with self.assertRaises(UserError):
            report.unlink()

    def test_reset_to_draft_clears_the_review(self):
        """Resetting to draft removes the recorded review."""
        report = self._create_report()
        report.with_user(self.user_lead).action_submit_review()
        report.with_user(self.user_manager).action_review()
        report.action_reset_to_draft()
        self.assertEqual(report.state, "draft")
        self.assertFalse(report.reviewed_by_id)

    def test_related_statistics_are_exposed(self):
        """The report exposes the audit statistics for printing."""
        report = self._create_report()
        self.assertEqual(report.finding_count, self.audit.finding_count)
        self.assertAlmostEqual(
            report.conformity_rate, self.audit.conformity_rate, places=2
        )

    def test_pdf_report_action_is_registered(self):
        """The printable audit report action is installed."""
        action = self.env.ref("ls_audit.action_report_ls_audit_report")
        self.assertEqual(action.model, "ls.audit.report")
        self.assertEqual(action.report_type, "qweb-pdf")

    def test_pdf_finding_action_is_registered(self):
        """The printable finding action is installed."""
        action = self.env.ref("ls_audit.action_report_ls_audit_finding")
        self.assertEqual(action.model, "ls.audit.finding")
        self.assertEqual(action.report_type, "qweb-pdf")

    def _issue_report(self):
        """Prepare, review, approve and issue a report.

        :return: the issued report.
        :rtype: recordset
        """
        report = self._create_report()
        report.with_user(self.user_lead).action_submit_review()
        report.with_user(self.user_manager).action_review()
        report.with_user(self.user_manager).action_approve()
        report.with_user(self.user_manager).action_issue()
        return report
