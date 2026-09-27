"""P2 - Permissions with realistic users (Internal User + business role)."""

from odoo.exceptions import AccessError
from odoo.tests import tagged
from odoo.tests.common import new_test_user

import logging

from .common import ProbeCommon

_logger = logging.getLogger(__name__)


@tagged("post_install", "-at_install", "ls_audit_probe")
class TestP2Permissions(ProbeCommon):

    def test_F01_contact_form_readable_by_sales_user(self):
        """F-01: a sales user with no qualification role can open a contact."""
        user = new_test_user(
            self.env, login="probe_sales",
            groups="base.group_user,sales_team.group_sale_salesman",
        )
        partner = self.env["res.partner"].create({"name": "Probe Supplier"})
        views = self.env["res.partner"].with_user(user).get_views([(False, "form")])
        arch = views["views"]["form"]["arch"]
        # Since the F-01 fix the invisible fields carry groups=, so the form of
        # a user without a qualification role may no longer contain them. The
        # read below is performed in every case and must not raise.
        _logger.info(
            "PROBE F-01 diagnostic: field in the form arch of the sales user = %s",
            "ls_is_approved_supplier" in arch,
        )
        acl = self.env["ls.supplier.qualification"].with_user(user).has_access("read")
        _logger.info("PROBE F-01 diagnostic: sales user read access on ls.supplier.qualification = %s", acl)
        self.env.invalidate_all()
        try:
            partner.with_user(user).read(["ls_is_approved_supplier", "ls_qualification_id"])
        except AccessError as error:
            self.fail(f"PROBE F-01 reproduced: contact form fields raise AccessError for a sales user: {error}")

    def test_F01c_contact_form_readable_by_plain_internal_user(self):
        """F-01: an internal user with no other right can open a contact."""
        user = new_test_user(self.env, login="probe_plain", groups="base.group_user")
        partner = self.env["res.partner"].create({"name": "Probe Supplier C"})
        self.env.invalidate_all()
        try:
            partner.with_user(user).read(["ls_is_approved_supplier", "ls_qualification_id"])
        except AccessError as error:
            self.fail(f"PROBE F-01 reproduced for a plain internal user: {error}")

    def test_F01b_purchase_form_readable_by_purchase_user(self):
        """F-01: a purchase user with no qualification role can open a PO."""
        user = new_test_user(
            self.env, login="probe_buyer",
            groups="base.group_user,purchase.group_purchase_user",
        )
        vendor = self.env["res.partner"].create({"name": "Probe Vendor"})
        order = self.env["purchase.order"].create({
            "partner_id": vendor.id,
            "order_line": [self.cmd().create({
                "product_id": self.product_plain.id, "product_qty": 1, "price_unit": 1,
            })],
        })
        try:
            order.with_user(user).read(["ls_qualification_warning"])
        except AccessError as error:
            self.fail(f"PROBE F-01 reproduced on purchase.order: {error}")

    def test_F03_lot_form_readable_by_inventory_user(self):
        """F-03: an inventory user with no recall role can open a lot."""
        user = new_test_user(
            self.env, login="probe_stock",
            groups="base.group_user,stock.group_stock_user",
        )
        lot = self._lot(self.product_lot, "PROBE-F03")
        self.env["ls.recall.execution"].create({
            "action_type": "recall",
            "product_id": self.product_lot.id,
            "lot_ids": [(6, 0, lot.ids)],
            "classification": "class_ii",
            "depth": "retail",
            "reason": "Probe.",
            "health_hazard_evaluation": "<p>Probe.</p>",
            "responsible_user_id": self.env.user.id,
            "effectiveness_level": "a",
        })
        lot_user = lot.with_user(user)
        lot_user.invalidate_recordset()
        try:
            lot_user.read(["ls_recall_open"])
        except AccessError as error:
            self.fail(f"PROBE F-03 reproduced: lot form raises AccessError for an inventory user: {error}")

    def test_F14_folder_rule_honours_implied_groups(self):
        """F-14: access granted through an implied group is honoured."""
        group_base = self.env["res.groups"].create({"name": "Probe QA Staff"})
        group_sub = self.env["res.groups"].create({
            "name": "Probe QA Lead",
            "implied_ids": [(4, group_base.id)],
        })
        user = new_test_user(
            self.env, login="probe_doc_reader",
            groups="base.group_user,ls_document_management.group_ls_document_viewer",
        )
        user.write({"group_ids": [(4, group_sub.id)]})
        folder = self.env["ls.document.folder"].create({
            "name": "Probe restricted folder",
            "group_read_ids": [(6, 0, group_base.ids)],
        })
        document = self.env["ls.document.document"].create({
            "name": "Probe restricted document",
            "folder_id": folder.id,
        })
        found = self.env["ls.document.document"].with_user(user).search([("id", "=", document.id)])
        self.assertTrue(
            found,
            "PROBE F-14 reproduced: a user holding the folder read group through an implied group cannot see the document",
        )

    def test_F27_role_only_user_vs_internal_user(self):
        """F-27 / F-33: internal users can draw sequences; role-only users cannot."""
        internal = new_test_user(
            self.env, login="probe_lab_internal",
            groups="base.group_user,ls_lab.ls_lab_group_analyst",
        )
        role_only = new_test_user(
            self.env, login="probe_lab_role_only",
            groups="ls_lab.ls_lab_group_analyst",
        )
        # Must succeed: this is the production situation.
        self.env["ir.sequence"].with_user(internal).next_by_code("ls.lab.oos")
        # F-27 fixed: the role group implies Internal User, so a user given
        # only the role is an internal user and can draw the sequence too.
        self.assertTrue(
            role_only.has_group("base.group_user"),
            "PROBE F-27 reproduced: the role group does not imply base.group_user",
        )
        self.env["ir.sequence"].with_user(role_only).next_by_code("ls.lab.oos")
