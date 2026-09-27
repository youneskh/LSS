# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Tests for the audit workflow and its findings."""
from dateutil.relativedelta import relativedelta

from odoo.exceptions import UserError, ValidationError
from odoo.tests import tagged

from .common import SupplierQualificationCommon


@tagged("post_install", "-at_install")
class TestAudit(SupplierQualificationCommon):
    """Cover audit planning, reporting, findings and closure."""

    def setUp(self):
        """Create a draft audit with one major finding for each test."""
        super().setUp()
        self.audit = self.env["ls.supplier.audit"].create({
            "qualification_id": self.qualification.id,
            "audit_type": "on_site",
            "audit_scope": "Scope defined by the test suite.",
            "planned_date": self.today,
            "lead_auditor_id": self.user_assessor.id,
        })
        self.finding = self.env["ls.supplier.audit.finding"].create({
            "audit_id": self.audit.id,
            "name": "F-01",
            "severity": "major",
            "description": "Finding raised by the test suite.",
        })

    def test_sequence_assigned(self):
        """A new audit receives a reference from the company sequence."""
        self.assertTrue(self.audit.name.startswith("SAU/"))

    def test_finding_counters(self):
        """Findings are counted by severity and by open status."""
        self.env["ls.supplier.audit.finding"].create({
            "audit_id": self.audit.id,
            "name": "F-02",
            "severity": "critical",
            "description": "Second finding raised by the test suite.",
        })
        self.audit.invalidate_recordset()
        self.assertEqual(self.audit.major_count, 1)
        self.assertEqual(self.audit.critical_count, 1)
        self.assertEqual(self.audit.finding_count, 2)
        self.assertEqual(self.audit.open_finding_count, 2)

    def test_state_order_enforced(self):
        """An audit cannot skip stages."""
        with self.assertRaises(UserError):
            self.audit.action_start()

    def test_report_requires_outcome_and_conclusion(self):
        """Issuing a report requires an outcome and a conclusion."""
        self.audit.action_plan()
        self.audit.action_start()
        self.audit.action_draft_report()
        with self.assertRaises(UserError):
            self.audit.action_issue_report()
        self.audit.outcome = "acceptable_with_actions"
        with self.assertRaises(UserError):
            self.audit.action_issue_report()
        self.audit.conclusion = "Conclusion recorded by the test suite."
        self.audit.action_issue_report()
        self.assertEqual(self.audit.state, "report_issued")
        self.assertEqual(self.audit.report_date, self.today)

    def test_response_due_date_from_company_setting(self):
        """The response due date follows the company lead time."""
        self.company.ls_audit_response_days = 45
        self.audit.action_plan()
        self.audit.action_start()
        self.audit.action_draft_report()
        self.audit.outcome = "acceptable_with_actions"
        self.audit.conclusion = "Conclusion recorded by the test suite."
        self.audit.action_issue_report()
        self.assertEqual(
            self.audit.response_due_date,
            self.today + relativedelta(days=45),
        )

    def test_critical_finding_blocks_acceptable_outcome(self):
        """An audit with a critical finding cannot conclude Acceptable."""
        self.finding.severity = "critical"
        with self.assertRaises(ValidationError):
            self.audit.outcome = "acceptable"

    def test_cannot_close_with_open_finding(self):
        """An audit with an open finding cannot be closed."""
        self.audit.action_plan()
        self.audit.action_start()
        self.audit.action_draft_report()
        self.audit.outcome = "acceptable_with_actions"
        self.audit.conclusion = "Conclusion recorded by the test suite."
        self.audit.action_issue_report()
        with self.assertRaises(UserError):
            self.audit.action_close()

    def test_finding_workflow(self):
        """A finding travels through response, action, verification, closure."""
        self.audit.action_plan()
        self.audit.action_start()
        self.audit.action_draft_report()
        self.audit.outcome = "acceptable_with_actions"
        self.audit.conclusion = "Conclusion recorded by the test suite."
        self.audit.action_issue_report()

        with self.assertRaises(UserError):
            self.finding.action_register_response()
        self.finding.supplier_response = "Response recorded by the test suite."
        self.finding.action_register_response()
        self.assertEqual(self.finding.state, "response_received")

        with self.assertRaises(UserError):
            self.finding.action_agree_action()
        self.finding.corrective_action = "Action recorded by the test suite."
        self.finding.action_due_date = self.today + relativedelta(days=30)
        self.finding.action_agree_action()
        self.finding.action_mark_implemented()
        self.assertEqual(self.finding.implementation_date, self.today)

        with self.assertRaises(UserError):
            self.finding.action_close()
        self.finding.verification_method = "Verified by the test suite."
        self.finding.action_verify()
        self.assertEqual(self.finding.verified_by_id, self.env.user)
        self.finding.action_close()
        self.assertEqual(self.finding.state, "closed")
        self.assertEqual(self.finding.closure_date, self.today)

    def test_major_finding_requires_corrective_action(self):
        """A major finding cannot progress without a documented action."""
        self.finding.supplier_response = "Response recorded by the test suite."
        with self.assertRaises(ValidationError):
            self.finding.state = "action_agreed"

    def test_close_audit_creates_signature_entry(self):
        """Closing an audit appends a verified signature entry."""
        before = self.env["ls.supplier.signature"].search_count([])
        self._create_closed_audit(self.qualification)
        after = self.env["ls.supplier.signature"].search_count([])
        # One entry for the report issue, one for the finding closure and one
        # for the audit closure.
        self.assertEqual(after, before + 3)

    def test_planned_audit_cannot_be_deleted(self):
        """Deleting a planned audit is refused."""
        self.audit.action_plan()
        with self.assertRaises(UserError):
            self.audit.unlink()

    def test_end_date_cannot_precede_start_date(self):
        """The audit end date must not precede its start date."""
        with self.assertRaises(ValidationError):
            self.audit.write({
                "date_start": self.today,
                "date_stop": self.today - relativedelta(days=1),
            })
