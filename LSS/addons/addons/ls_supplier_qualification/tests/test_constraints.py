# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Tests for the cross-model constraints of the module."""
from dateutil.relativedelta import relativedelta

from odoo.exceptions import UserError, ValidationError
from odoo.tests import tagged

from .common import SupplierQualificationCommon


@tagged("post_install", "-at_install")
class TestConstraints(SupplierQualificationCommon):
    """Cover uniqueness, completeness and segregation-of-duties rules."""

    def test_single_active_dossier_per_supplier(self):
        """A supplier cannot hold two live dossiers in one company."""
        with self.assertRaises(ValidationError):
            self.env["ls.supplier.qualification"].create({
                "partner_id": self.partner.id,
                "category_id": self.category_no_audit.id,
            })

    def test_second_dossier_allowed_after_disqualification(self):
        """A new dossier is allowed once the previous one is disqualified."""
        self.qualification.state = "disqualified"
        second = self.env["ls.supplier.qualification"].create({
            "partner_id": self.partner.id,
            "category_id": self.category_no_audit.id,
        })
        self.assertTrue(second)

    def test_approved_dossier_requires_full_approval_record(self):
        """An approved dossier without approval data is rejected."""
        with self.assertRaises(ValidationError):
            self.qualification.state = "approved"

    def test_conditional_approval_requires_conditions(self):
        """A conditional approval without conditions is rejected."""
        self.qualification.action_start_assessment()
        self._create_assessment(self.qualification)
        self._create_material(self.qualification)
        self.qualification.action_submit_for_approval()
        with self.assertRaises(ValidationError):
            self.qualification.write({
                "state": "conditional",
                "approval_date": self.today,
                "approved_by_id": self.user_manager.id,
                "expiry_date": self.today + relativedelta(months=12),
            })

    def test_expiry_after_approval_date(self):
        """The validity end must follow the approval date."""
        with self.assertRaises(ValidationError):
            self.qualification.write({
                "approval_date": self.today,
                "expiry_date": self.today,
            })

    def test_segregation_of_duties_blocks_assessor_approval(self):
        """An assessor of the dossier cannot approve it."""
        self.qualification.action_start_assessment()
        self._create_assessment(self.qualification, assessor=self.user_manager)
        self._create_material(self.qualification)
        self.qualification.action_submit_for_approval()
        with self.assertRaises(UserError):
            self._approve(self.qualification, approver=self.user_manager)

    def test_segregation_of_duties_can_be_disabled(self):
        """Disabling the company flag allows the assessor to approve."""
        self.company.ls_enforce_sod = False
        self.qualification.action_start_assessment()
        self._create_assessment(self.qualification, assessor=self.user_manager)
        self._create_material(self.qualification)
        self.qualification.action_submit_for_approval()
        self._approve(self.qualification, approver=self.user_manager)
        self.assertEqual(self.qualification.state, "approved")

    def test_wizard_rejects_wrong_login(self):
        """The approval wizard rejects a login that is not the signer's."""
        self.qualification.action_start_assessment()
        self._create_assessment(self.qualification)
        self._create_material(self.qualification)
        self.qualification.action_submit_for_approval()
        wizard = self.env["ls.supplier.approve.wizard"].with_user(
            self.user_manager
        ).create({
            "qualification_id": self.qualification.id,
            "decision": "approved",
            "expiry_date": self.today + relativedelta(months=12),
            "reason": "Justification recorded by the test suite.",
            "signature_login": "not-the-right-login",
        })
        with self.assertRaises(UserError):
            wizard.action_confirm()

    def test_wizard_rejects_past_expiry_date(self):
        """The approval wizard rejects a validity end in the past."""
        self.qualification.action_start_assessment()
        self._create_assessment(self.qualification)
        self._create_material(self.qualification)
        self.qualification.action_submit_for_approval()
        wizard = self.env["ls.supplier.approve.wizard"].with_user(
            self.user_manager
        ).create({
            "qualification_id": self.qualification.id,
            "decision": "approved",
            "expiry_date": self.today - relativedelta(days=1),
            "reason": "Justification recorded by the test suite.",
            "signature_login": self.user_manager.login,
        })
        with self.assertRaises(UserError):
            wizard.action_confirm()

    def test_company_performance_thresholds_ordered(self):
        """Company rating thresholds must decrease from A to C."""
        with self.assertRaises(ValidationError):
            self.company.ls_perf_threshold_a = 50.0

    def test_company_weights_cannot_all_be_zero(self):
        """At least one performance weight must be strictly positive."""
        with self.assertRaises(ValidationError):
            self.company.write({
                "ls_perf_weight_otd": 0.0,
                "ls_perf_weight_quality": 0.0,
                "ls_perf_weight_documentation": 0.0,
                "ls_perf_weight_responsiveness": 0.0,
            })

    def test_company_lead_times_non_negative(self):
        """Lead times cannot be negative."""
        with self.assertRaises(ValidationError):
            self.company.ls_expiry_reminder_days = -1
