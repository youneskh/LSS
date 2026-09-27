# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Tests of the finding lifecycle, deadlines and evidence rules."""

from dateutil.relativedelta import relativedelta

from odoo.exceptions import UserError, ValidationError
from odoo.tests import tagged

from .common import AuditCommon


@tagged("post_install", "-at_install")
class TestFindingWorkflow(AuditCommon):
    """Issuance, response, action, verification and closure of findings."""

    def setUp(self):
        """Advance the fixture audit so that findings can be raised."""
        super().setUp()
        self._bring_audit_to_in_progress()
        self.audit.response_ids.filtered("is_mandatory").write(
            {"result": "conform"}
        )
        self.audit.action_complete()

    def test_reference_is_allocated(self):
        """A finding receives a reference from its sequence."""
        finding = self._create_finding()
        self.assertTrue(finding.reference.startswith("FND/"))

    def test_severity_is_inherited_from_category(self):
        """The severity comes from the finding category."""
        finding = self._create_finding(category=self.category_major)
        self.assertEqual(finding.severity, "major")

    def test_response_due_date_uses_category_deadline(self):
        """The response due date is derived from the category deadline."""
        finding = self._create_finding(category=self.category_minor)
        finding.action_issue()
        expected = finding.issue_date + relativedelta(
            days=self.category_minor.response_deadline_days
        )
        self.assertEqual(finding.response_due_date, expected)

    def test_finding_area_must_be_in_audit_scope(self):
        """A finding on an area outside the audit scope is refused."""
        with self.assertRaises(ValidationError):
            self._create_finding(area_id=self.area_other.id)

    def test_issue_sets_status_and_date(self):
        """Issuing a finding records the issue date."""
        finding = self._create_finding()
        finding.action_issue()
        self.assertEqual(finding.state, "open")
        self.assertEqual(finding.issue_date, self.today)

    def test_response_wizard_requires_corrective_action(self):
        """A response without corrective action is refused."""
        finding = self._create_finding(category=self.category_observation)
        finding.action_issue()
        wizard = self.env["ls.audit.finding.response"].create(
            {"finding_id": finding.id, "action_due_date": self.today}
        )
        with self.assertRaises(UserError):
            wizard.action_submit()

    def test_response_wizard_requires_root_cause_when_mandatory(self):
        """A category requiring a root cause enforces it."""
        finding = self._create_finding(category=self.category_minor)
        finding.action_issue()
        wizard = self.env["ls.audit.finding.response"].create(
            {
                "finding_id": finding.id,
                "corrective_action": "Procedure revised.",
                "action_due_date": self.today,
            }
        )
        with self.assertRaises(UserError):
            wizard.action_submit()

    def test_response_wizard_requires_capa_when_mandatory(self):
        """A category requiring a CAPA enforces the reference."""
        finding = self._create_finding(category=self.category_major)
        finding.action_issue()
        wizard = self.env["ls.audit.finding.response"].create(
            {
                "finding_id": finding.id,
                "root_cause": "Training gap.",
                "corrective_action": "Retrain the shift.",
                "action_due_date": self.today,
            }
        )
        with self.assertRaises(UserError):
            wizard.action_submit()

    def test_successful_response_advances_status(self):
        """A complete response moves the finding to responded."""
        finding = self._submit_response(self.category_major)
        self.assertEqual(finding.state, "responded")
        self.assertEqual(finding.responded_by_id, self.user_auditee)
        self.assertEqual(finding.response_date, self.today)

    def test_rejected_response_returns_to_open(self):
        """Rejecting a response sends the finding back to the auditee."""
        finding = self._submit_response(self.category_major)
        finding.with_user(self.user_lead).action_reject_response()
        self.assertEqual(finding.state, "open")

    def test_accept_response_starts_action_phase(self):
        """Accepting a complete response starts the action phase."""
        finding = self._submit_response(self.category_major)
        finding.with_user(self.user_lead).action_accept_response()
        self.assertEqual(finding.state, "in_progress")

    def test_close_requires_documented_verification(self):
        """A finding cannot close without documented verification."""
        finding = self._submit_response(self.category_major)
        finding.with_user(self.user_lead).action_accept_response()
        finding.action_request_verification()
        with self.assertRaises(UserError):
            finding.with_user(self.user_lead).action_verify_and_close()

    def test_full_lifecycle_to_closed(self):
        """A finding closes once verification is documented."""
        finding = self._submit_response(self.category_major)
        finding.with_user(self.user_lead).action_accept_response()
        finding.action_request_verification()
        finding.write(
            {
                "verification_method": "Re-inspection after 30 days.",
                "verification_result": "No recurrence observed.",
            }
        )
        finding.with_user(self.user_lead).action_verify_and_close()
        self.assertEqual(finding.state, "closed")
        self.assertEqual(finding.closure_date, self.today)
        self.assertTrue(finding.verified_by_id)

    def test_closed_finding_is_read_only(self):
        """A closed finding refuses further modification."""
        finding = self._submit_response(self.category_major)
        finding.with_user(self.user_lead).action_accept_response()
        finding.action_request_verification()
        finding.write(
            {
                "verification_method": "Re-inspection.",
                "verification_result": "Effective.",
            }
        )
        finding.with_user(self.user_lead).action_verify_and_close()
        with self.assertRaises(UserError):
            finding.name = "Renamed after closure"

    def test_issued_finding_cannot_be_deleted(self):
        """An issued finding cannot be deleted."""
        finding = self._create_finding()
        finding.action_issue()
        with self.assertRaises(UserError):
            finding.unlink()

    def test_draft_finding_can_be_deleted(self):
        """A draft finding can still be deleted."""
        finding = self._create_finding()
        finding.unlink()
        self.assertFalse(finding.exists())

    def test_overdue_flag_and_search(self):
        """The overdue flag is computed and searchable."""
        finding = self._create_finding()
        finding.action_issue()
        finding.response_due_date = self.today - relativedelta(days=1)
        self.assertTrue(finding.is_overdue)
        overdue = self.env["ls.audit.finding"].search(
            [("is_overdue", "=", True)]
        )
        self.assertIn(finding, overdue)

    def test_days_open_is_computed(self):
        """Days open is measured from the issue date."""
        finding = self._create_finding()
        finding.action_issue()
        self.assertEqual(finding.days_open, 0)

    def test_adverse_response_requires_evidence(self):
        """A non-conform assessment without evidence is refused."""
        audit = self._create_audit(name="Evidence Audit")
        # Responses are only editable while the audit is in progress.
        self._bring_audit_to_in_progress(audit)
        with self.assertRaises(ValidationError):
            audit.response_ids[0].write({"result": "nonconform"})

    def test_finding_can_be_raised_from_a_response(self):
        """A response can open a pre-filled finding form."""
        audit = self._create_audit(name="Raise Audit")
        self._bring_audit_to_in_progress(audit)
        response = audit.response_ids[0]
        response.write(
            {"result": "nonconform", "evidence": "Observed at line 1."}
        )
        action = response.action_create_finding()
        self.assertEqual(action["res_model"], "ls.audit.finding")
        self.assertEqual(
            action["context"]["default_response_id"], response.id
        )

    def test_finding_creation_links_back_to_response(self):
        """Creating a finding from a response links the two records."""
        audit = self._create_audit(name="Link Audit")
        self._bring_audit_to_in_progress(audit)
        response = audit.response_ids[0]
        response.write(
            {"result": "nonconform", "evidence": "Observed at line 1."}
        )
        audit.response_ids.filtered("is_mandatory").filtered(
            lambda item: item.result == "pending"
        ).write({"result": "conform"})
        audit.action_complete()
        finding = self._create_finding(audit=audit, response_id=response.id)
        self.assertEqual(response.finding_id, finding)

    def _submit_response(self, category):
        """Create, issue and answer a finding of ``category``.

        :param category: finding category to use.
        :return: the finding in the responded status.
        :rtype: recordset
        """
        finding = self._create_finding(category=category)
        finding.action_issue()
        wizard = self.env["ls.audit.finding.response"].create(
            {
                "finding_id": finding.id,
                "root_cause": "Withdrawal step missing.",
                "correction": "Obsolete copy removed.",
                "corrective_action": "Procedure revised.",
                "capa_reference": "CAPA/2026/0007",
                "action_due_date": self.today + relativedelta(days=30),
            }
        )
        wizard.with_user(self.user_auditee).action_submit()
        return finding
