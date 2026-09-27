# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Tests of the impartiality and segregation of duties controls."""

from odoo.exceptions import UserError, ValidationError
from odoo.tests import tagged

from .common import AuditCommon


@tagged("post_install", "-at_install")
class TestAuditIndependence(AuditCommon):
    """An auditor may not audit, answer or verify their own work."""

    def test_lead_auditor_cannot_be_auditee(self):
        """The lead auditor cannot appear among the auditees."""
        with self.assertRaises(ValidationError):
            self.audit.auditee_ids = [(4, self.user_lead.id)]

    def test_team_member_cannot_be_auditee(self):
        """A team auditor cannot appear among the auditees."""
        with self.assertRaises(ValidationError):
            self.audit.auditee_ids = [(4, self.user_auditor.id)]

    def test_auditor_cannot_own_the_audited_area(self):
        """A user owning an audited area cannot join the audit team."""
        self.area_other.responsible_id = self.user_auditor.id
        with self.assertRaises(ValidationError):
            self.audit.area_ids = [(4, self.area_other.id)]

    def test_finding_auditee_cannot_be_the_raiser(self):
        """The auditor who raised a finding cannot also answer it."""
        with self.assertRaises(ValidationError):
            self._create_finding(auditee_id=self.user_lead.id)

    def test_finding_cannot_be_verified_by_the_auditee(self):
        """Effectiveness verification cannot be done by the auditee."""
        finding = self._prepare_finding_for_verification()
        finding.write(
            {
                "verification_method": "Re-inspection of the point of use.",
                "verification_result": "No obsolete document present.",
            }
        )
        with self.assertRaises(UserError):
            finding.with_user(self.user_auditee).action_verify_and_close()

    def test_finding_can_be_verified_by_the_lead_auditor(self):
        """The lead auditor can verify and close the finding."""
        finding = self._prepare_finding_for_verification()
        finding.write(
            {
                "verification_method": "Re-inspection of the point of use.",
                "verification_result": "No obsolete document present.",
            }
        )
        finding.with_user(self.user_lead).action_verify_and_close()
        self.assertEqual(finding.state, "closed")
        self.assertEqual(finding.verified_by_id, self.user_lead)

    def test_report_preparer_cannot_review(self):
        """The preparer of a report cannot review it."""
        self._complete_audit()
        report = self._create_report()
        report.with_user(self.user_lead).action_submit_review()
        with self.assertRaises(UserError):
            report.with_user(self.user_lead).action_review()

    def test_report_preparer_cannot_approve(self):
        """The preparer of a report cannot approve it."""
        self._complete_audit()
        report = self._create_report()
        report.with_user(self.user_lead).action_submit_review()
        report.with_user(self.user_manager).action_review()
        with self.assertRaises(UserError):
            report.with_user(self.user_lead).action_approve()

    def _complete_audit(self):
        """Advance the fixture audit to the completed status."""
        self._bring_audit_to_in_progress()
        self.audit.response_ids.filtered("is_mandatory").write(
            {"result": "conform"}
        )
        self.audit.action_complete()

    def _prepare_finding_for_verification(self):
        """Create a finding and move it to the verification status."""
        self._complete_audit()
        finding = self._create_finding(category=self.category_minor)
        finding.action_issue()
        wizard = self.env["ls.audit.finding.response"].create(
            {
                "finding_id": finding.id,
                "root_cause": "Withdrawal step missing in the procedure.",
                "correction": "Obsolete copy removed immediately.",
                "corrective_action": "Procedure revised to add a "
                                     "withdrawal check.",
                "action_due_date": self.today,
            }
        )
        wizard.with_user(self.user_auditee).action_submit()
        finding.with_user(self.user_lead).action_accept_response()
        finding.with_user(self.user_auditee).action_request_verification()
        return finding
