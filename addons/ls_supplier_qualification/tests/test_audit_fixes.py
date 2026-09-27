# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Regression tests for the findings of the 2026-09-25 audit.

F-01 contact and purchase order readable without a qualification role,
F-13 purchase control evaluated in the company of the order, F-36 dossier
created by code without its computed values, Odoo 19 search normalisation
of the approved-supplier filter.
"""
from odoo.exceptions import UserError
from odoo.tests import tagged
from odoo.tests.common import new_test_user

from .common import SupplierQualificationCommon


@tagged("post_install", "-at_install")
class TestAuditFixes(SupplierQualificationCommon):
    """Behaviour restored by the 2026-09-25 remediation."""

    def _approve_shared_dossier(self):
        """Bring the shared dossier of ``self.partner`` to approved."""
        self.qualification.action_start_assessment()
        self._create_assessment(self.qualification)
        self._create_material(self.qualification, self.product)
        self.qualification.action_submit_for_approval()
        self._approve(self.qualification)

    def _order(self, company=None):
        """Create a purchase order for the shared supplier."""
        order_model = self.env["purchase.order"]
        if company:
            order_model = order_model.with_company(company)
        return order_model.create({
            "partner_id": self.partner.id,
            "company_id": (company or self.company).id,
            "order_line": [
                (0, 0, {
                    "product_id": self.product.id,
                    "product_qty": 1.0,
                    "name": self.product.name,
                    "price_unit": 1.0,
                }),
            ],
        })

    # F-01 ---------------------------------------------------------------
    def test_contact_readable_by_user_without_qualification_role(self):
        """Every internal user can read the qualification status of a contact."""
        self._approve_shared_dossier()
        user = new_test_user(self.env, login="sq_fix_plain", groups="base.group_user")
        self.env.invalidate_all()
        values = self.partner.with_user(user).read(
            ["ls_is_approved_supplier", "ls_qualification_state"]
        )[0]
        self.assertTrue(values["ls_is_approved_supplier"])
        self.assertEqual(values["ls_qualification_state"], self.qualification.state)

    def test_order_warning_readable_by_purchase_user(self):
        """A purchase user without qualification role reads the order warning."""
        user = new_test_user(
            self.env,
            login="sq_fix_buyer",
            groups="base.group_user,purchase.group_purchase_user",
        )
        order = self._order()
        self.env.invalidate_all()
        warning = order.with_user(user).ls_qualification_warning
        self.assertTrue(warning)

    # F-13 ---------------------------------------------------------------
    def test_control_uses_the_company_of_the_order(self):
        """A company B order is checked against the company B dossier."""
        company_b = self.env["res.company"].create({"name": "SQ Fix Company B"})
        self.env.user.write({"company_ids": [(4, company_b.id)]})
        company_b.write({"ls_po_control_level": "block", "ls_po_check_scope": False})
        self.company.write({"ls_po_control_level": "block", "ls_po_check_scope": False})
        category_b = self.env["ls.supplier.category"].with_company(company_b).create({
            "name": "SQ Fix category B",
            "code": "SQFIX-B",
            "criticality": "major",
            "requires_assessment": True,
            "requires_initial_audit": False,
            "requires_periodic_audit": False,
            "requalification_interval_months": 36,
            "review_interval_months": 12,
            "company_id": company_b.id,
        })
        dossier_b = self.env["ls.supplier.qualification"].with_company(company_b).create({
            "partner_id": self.partner.id,
            "category_id": category_b.id,
            "responsible_id": self.user_manager.id,
            "company_id": company_b.id,
        })
        self.env.flush_all()
        self.env.cr.execute(
            "UPDATE ls_supplier_qualification SET state = 'approved', "
            "expiry_date = NULL WHERE id = %s",
            (dossier_b.id,),
        )
        self.env.invalidate_all()
        order_b = self._order(company=company_b)
        # Company A active (it has no approved dossier for this supplier):
        # the order of company B is evaluated with the dossier of company B.
        order_b.with_context(
            allowed_company_ids=[self.company.id, company_b.id]
        ).button_confirm()
        self.assertIn(order_b.state, ("purchase", "done"))

    def test_status_is_recomputed_per_company(self):
        """The partner status depends on the active company."""
        self._approve_shared_dossier()
        company_b = self.env["res.company"].create({"name": "SQ Fix Company C"})
        self.env.user.write({"company_ids": [(4, company_b.id)]})
        partner_a = self.partner.with_company(self.company)
        partner_b = self.partner.with_company(company_b)
        self.assertTrue(partner_a.ls_is_approved_supplier)
        self.assertFalse(partner_b.ls_is_approved_supplier)

    # F-36 ---------------------------------------------------------------
    def test_dossier_created_without_computed_values(self):
        """Criticality and interval are computed before the row is inserted."""
        dossier = self.env["ls.supplier.qualification"].create({
            "partner_id": self.partner_two.id,
            "category_id": self.category_with_audit.id,
            "responsible_id": self.user_manager.id,
        })
        self.assertEqual(dossier.criticality, self.category_with_audit.criticality)
        self.assertEqual(
            dossier.requalification_interval_months,
            self.category_with_audit.requalification_interval_months,
        )

    # Odoo 19 search normalisation --------------------------------------
    def test_approved_supplier_filter(self):
        """The filter works with the operators Odoo 19 sends."""
        self._approve_shared_dossier()
        partner_model = self.env["res.partner"]
        self.assertIn(
            self.partner,
            partner_model.search([("ls_is_approved_supplier", "=", True)]),
        )
        self.assertNotIn(
            self.partner,
            partner_model.search([("ls_is_approved_supplier", "!=", True)]),
        )
        self.assertIn(
            self.partner_two,
            partner_model.search([("ls_is_approved_supplier", "=", False)]),
        )

    def test_unsupported_operator_is_refused(self):
        """The search method refuses an operator it does not implement."""
        with self.assertRaises(UserError):
            self.env["res.partner"]._search_ls_is_approved_supplier("in", [True])
