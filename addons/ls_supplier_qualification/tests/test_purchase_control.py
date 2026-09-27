# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Tests for the purchase order qualification control."""
from dateutil.relativedelta import relativedelta

from odoo.exceptions import UserError
from odoo.tests import tagged

from .common import SupplierQualificationCommon


@tagged("post_install", "-at_install")
class TestPurchaseControl(SupplierQualificationCommon):
    """Verify the three control levels and the scope check."""

    def setUp(self):
        """Create a purchase order for the shared supplier."""
        super().setUp()
        self.order = self.env["purchase.order"].create({
            "partner_id": self.partner.id,
            "order_line": [
                (0, 0, {
                    "product_id": self.product.id,
                    "product_qty": 10.0,
                    "name": self.product.name,
                    "price_unit": 5.0,
                }),
            ],
        })

    def _approve_supplier(self):
        """Bring the shared dossier to the approved status."""
        self.qualification.action_start_assessment()
        self._create_assessment(self.qualification)
        self._create_material(self.qualification, self.product)
        self.qualification.action_submit_for_approval()
        self._approve(self.qualification)

    def test_control_none_allows_confirmation(self):
        """With the control disabled the order confirms normally."""
        self.company.ls_po_control_level = "none"
        self.order.button_confirm()
        self.assertIn(self.order.state, ("purchase", "to approve"))

    def test_control_block_refuses_unapproved_supplier(self):
        """With the blocking level an unapproved supplier stops the order."""
        self.company.ls_po_control_level = "block"
        with self.assertRaises(UserError):
            self.order.button_confirm()

    def test_control_warn_posts_message(self):
        """With the warning level the issue is logged and the order confirms."""
        self.company.ls_po_control_level = "warn"
        before = len(self.order.message_ids)
        self.order.button_confirm()
        self.assertGreater(len(self.order.message_ids), before)
        self.assertIn(self.order.state, ("purchase", "to approve"))

    def test_approved_supplier_passes_control(self):
        """An approved supplier confirms even at the blocking level."""
        self._approve_supplier()
        self.company.ls_po_control_level = "block"
        self.order.button_confirm()
        self.assertIn(self.order.state, ("purchase", "to approve"))

    def test_expired_approval_blocks_confirmation(self):
        """An expired approval blocks the confirmation."""
        self._approve_supplier()
        # Approved two years ago, so that an elapsed expiry is consistent.
        self.qualification.write({
            "approval_date": self.today - relativedelta(years=2),
            "expiry_date": self.today - relativedelta(days=1),
        })
        self.company.ls_po_control_level = "block"
        with self.assertRaises(UserError):
            self.order.button_confirm()

    def test_scope_check_blocks_product_outside_scope(self):
        """With the scope check on, an unqualified product blocks the order."""
        self._approve_supplier()
        self.company.write({
            "ls_po_control_level": "block",
            "ls_po_check_scope": True,
        })
        order = self.env["purchase.order"].create({
            "partner_id": self.partner.id,
            "order_line": [
                (0, 0, {
                    "product_id": self.product_off_scope.id,
                    "product_qty": 1.0,
                    "name": self.product_off_scope.name,
                    "price_unit": 1.0,
                }),
            ],
        })
        with self.assertRaises(UserError):
            order.button_confirm()

    def test_warning_field_exposed_on_order(self):
        """The order form shows the qualification issue."""
        self.assertTrue(self.order.ls_qualification_warning)
        self._approve_supplier()
        self.order.invalidate_recordset()
        self.assertFalse(self.order.ls_qualification_warning)

    def test_partner_approval_flag_and_search(self):
        """The partner exposes and can be searched on its approval status."""
        self.assertFalse(self.partner.ls_is_approved_supplier)
        self._approve_supplier()
        self.partner.invalidate_recordset()
        self.assertTrue(self.partner.ls_is_approved_supplier)
        found = self.env["res.partner"].search([
            ("ls_is_approved_supplier", "=", True),
        ])
        self.assertIn(self.partner, found)
        not_found = self.env["res.partner"].search([
            ("ls_is_approved_supplier", "=", False),
        ])
        self.assertIn(self.partner_two, not_found)
