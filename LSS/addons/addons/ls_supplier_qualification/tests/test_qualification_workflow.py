# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Tests for the qualification dossier state machine."""
from dateutil.relativedelta import relativedelta

from odoo.exceptions import UserError
from odoo.tests import tagged

from .common import SupplierQualificationCommon


@tagged("post_install", "-at_install")
class TestQualificationWorkflow(SupplierQualificationCommon):
    """Cover the dossier lifecycle from registration to disqualification."""

    def test_sequence_assigned_on_creation(self):
        """A new dossier receives a reference from the company sequence."""
        self.assertNotEqual(self.qualification.name, "/")
        self.assertTrue(self.qualification.name.startswith("SQ/"))

    def test_criticality_inherited_from_category(self):
        """The dossier inherits the criticality of its category."""
        self.assertEqual(self.qualification.criticality, "major")
        self.qualification.category_id = self.category_with_audit
        self.assertEqual(self.qualification.criticality, "critical")

    def test_blocking_reasons_listed_in_draft(self):
        """A fresh dossier lists the prerequisites it does not meet."""
        self.assertFalse(self.qualification.is_ready_for_approval)
        self.assertIn("assessment", self.qualification.blocking_reasons)
        self.assertIn("scope", self.qualification.blocking_reasons)

    def test_cannot_submit_without_evidence(self):
        """Submitting a dossier without evidence is refused."""
        self.qualification.action_start_assessment()
        with self.assertRaises(UserError):
            self.qualification.action_submit_for_approval()

    def test_happy_path_to_approval(self):
        """A dossier with an assessment and a scope reaches approval."""
        self.qualification.action_start_assessment()
        self._create_assessment(self.qualification)
        self._create_material(self.qualification, self.product)
        self.assertTrue(self.qualification.is_ready_for_approval)
        self.qualification.action_submit_for_approval()
        self.assertEqual(self.qualification.state, "approval")
        self._approve(self.qualification)
        self.assertEqual(self.qualification.state, "approved")
        self.assertEqual(self.qualification.approved_by_id, self.user_manager)
        self.assertTrue(self.qualification.expiry_date)

    def test_audit_required_blocks_approval(self):
        """A category requiring an audit blocks approval until one is closed."""
        dossier = self.env["ls.supplier.qualification"].create({
            "partner_id": self.partner_two.id,
            "category_id": self.category_with_audit.id,
            "responsible_id": self.user_manager.id,
        })
        dossier.action_start_assessment()
        self._create_assessment(dossier)
        self._create_material(dossier)
        self.assertFalse(dossier.is_ready_for_approval)
        self.assertIn("audit", dossier.blocking_reasons)
        self._create_closed_audit(dossier)
        dossier.invalidate_recordset()
        self.assertTrue(dossier.is_ready_for_approval)

    def test_open_critical_finding_blocks_approval(self):
        """An open critical finding prevents submission for approval."""
        self.qualification.action_start_assessment()
        self._create_assessment(self.qualification)
        self._create_material(self.qualification)
        audit = self.env["ls.supplier.audit"].create({
            "qualification_id": self.qualification.id,
            "audit_type": "on_site",
            "audit_scope": "Scope defined by the test suite.",
            "planned_date": self.today,
            "lead_auditor_id": self.user_assessor.id,
        })
        self.env["ls.supplier.audit.finding"].create({
            "audit_id": audit.id,
            "name": "F-CRIT",
            "severity": "critical",
            "description": "Critical finding raised by the test suite.",
        })
        self.qualification.invalidate_recordset()
        self.assertEqual(self.qualification.open_critical_finding_count, 1)
        self.assertFalse(self.qualification.is_ready_for_approval)

    def test_suspend_and_reinstate(self):
        """An approved dossier can be suspended and reinstated."""
        self._reach_approved()
        wizard = self.env["ls.supplier.status.wizard"].with_user(
            self.user_manager
        ).create({
            "qualification_id": self.qualification.id,
            "action_type": "suspend",
            "reason": "Suspension justified by the test suite.",
            "signature_login": self.user_manager.login,
        })
        wizard.action_confirm()
        self.assertEqual(self.qualification.state, "suspended")
        wizard_back = self.env["ls.supplier.status.wizard"].with_user(
            self.user_manager
        ).create({
            "qualification_id": self.qualification.id,
            "action_type": "reinstate",
            "reason": "Reinstatement justified by the test suite.",
            "signature_login": self.user_manager.login,
        })
        wizard_back.action_confirm()
        self.assertEqual(self.qualification.state, "approved")
        self.assertFalse(self.qualification.suspension_reason)

    def test_disqualify(self):
        """A dossier can be disqualified with a recorded reason."""
        self._reach_approved()
        wizard = self.env["ls.supplier.status.wizard"].with_user(
            self.user_manager
        ).create({
            "qualification_id": self.qualification.id,
            "action_type": "disqualify",
            "reason": "Disqualification justified by the test suite.",
            "signature_login": self.user_manager.login,
        })
        wizard.action_confirm()
        self.assertEqual(self.qualification.state, "disqualified")
        self.assertTrue(self.qualification.disqualification_reason)

    def test_requalify_from_expired(self):
        """An expired dossier returns to the assessment stage."""
        self._reach_approved()
        self.qualification.state = "expired"
        self.qualification.action_requalify()
        self.assertEqual(self.qualification.state, "assessment")
        self.assertFalse(self.qualification.approval_date)
        self.assertFalse(self.qualification.expiry_date)

    def test_identification_locked_after_assessment(self):
        """The supplier cannot be changed once the dossier is under audit."""
        self.qualification.action_start_assessment()
        self.qualification.action_start_audit()
        with self.assertRaises(UserError):
            self.qualification.partner_id = self.partner_two

    def test_only_draft_dossier_can_be_deleted(self):
        """Deleting a dossier that left the draft status is refused."""
        self.qualification.action_start_assessment()
        with self.assertRaises(UserError):
            self.qualification.unlink()

    def test_copy_resets_approval(self):
        """Duplicating an approved dossier produces a fresh draft."""
        self._reach_approved()
        self.qualification.state = "disqualified"
        copy = self.qualification.copy()
        self.assertEqual(copy.state, "draft")
        self.assertFalse(copy.approval_date)
        self.assertFalse(copy.approved_by_id)
        self.assertNotEqual(copy.name, self.qualification.name)

    def test_next_dates_computed_after_approval(self):
        """Approval schedules the next audit and the next review."""
        dossier = self.env["ls.supplier.qualification"].create({
            "partner_id": self.partner_two.id,
            "category_id": self.category_with_audit.id,
            "responsible_id": self.user_manager.id,
        })
        dossier.action_start_assessment()
        self._create_assessment(dossier)
        self._create_material(dossier)
        self._create_closed_audit(dossier)
        dossier.action_submit_for_approval()
        self._approve(dossier)
        self.assertTrue(dossier.next_review_date)
        self.assertTrue(dossier.next_audit_date)

    def test_risk_level_rises_with_poor_evidence(self):
        """A failing assessment raises the computed risk level."""
        self.qualification.action_start_assessment()
        self._create_assessment(self.qualification, scores=(0, 0))
        self.qualification.invalidate_recordset()
        self.assertEqual(self.qualification.latest_assessment_result, "fail")
        self.assertEqual(self.qualification.risk_level, "high")

    def test_expiry_status_transitions(self):
        """The expiry status reflects the remaining validity."""
        self._reach_approved()
        self.qualification.expiry_date = self.today + relativedelta(days=5)
        self.qualification.invalidate_recordset()
        self.assertEqual(self.qualification.expiry_status, "expiring")
        # Approved two years ago, so that an elapsed expiry is consistent.
        self.qualification.write({
            "approval_date": self.today - relativedelta(years=2),
            "expiry_date": self.today - relativedelta(days=1),
        })
        self.qualification.invalidate_recordset()
        self.assertEqual(self.qualification.expiry_status, "expired")

    def _reach_approved(self):
        """Bring the shared dossier to the approved status."""
        self.qualification.action_start_assessment()
        self._create_assessment(self.qualification)
        self._create_material(self.qualification, self.product)
        self.qualification.action_submit_for_approval()
        self._approve(self.qualification)
