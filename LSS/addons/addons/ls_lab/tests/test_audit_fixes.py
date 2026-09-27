# Part of the Life Sciences Suite. See LICENSE file for full copyright and licensing details.
"""Regression tests for the findings of the 2026-09-25 audit.

F-06 customer delivery of a lot held by an OOS investigation is refused,
F-16 a sample cannot reference the lot of another product, and an analyst
entering a failing result opens the investigation.
"""
from odoo.exceptions import UserError, ValidationError
from odoo.tests import tagged

from .common import LsLabCommon


@tagged("post_install", "-at_install")
class TestAuditFixes(LsLabCommon):
    """Behaviour restored by the 2026-09-25 remediation."""

    @classmethod
    def setUpClass(cls):
        """Create a lot-tracked product and one of its lots."""
        super().setUpClass()
        cls.tracked = cls._tracked_product("Tracked lab product")
        cls.lot = cls.env["stock.lot"].create(
            {"name": "LAB-FIX-1", "product_id": cls.tracked.id}
        )

    @classmethod
    def _tracked_product(cls, name):
        """Create a lot-tracked storable product."""
        values = {"name": name, "type": "consu", "tracking": "lot"}
        if "is_storable" in cls.env["product.template"]._fields:
            values["is_storable"] = True
        return cls.env["product.product"].create(values)

    def _deliver(self, product, lot, quantity):
        """Deliver ``quantity`` of ``lot`` to a customer.

        :return: the validated picking.
        """
        warehouse = self.env["stock.warehouse"].search(
            [("company_id", "=", self.env.company.id)], limit=1
        )
        customer_location = self.env.ref("stock.stock_location_customers")
        self.env["stock.quant"]._update_available_quantity(
            product, warehouse.lot_stock_id, quantity, lot_id=lot
        )
        picking = self.env["stock.picking"].create(
            {
                "partner_id": self.env["res.partner"].create({"name": "Customer"}).id,
                "picking_type_id": warehouse.out_type_id.id,
                "location_id": warehouse.lot_stock_id.id,
                "location_dest_id": customer_location.id,
            }
        )
        self.env["stock.move"].create(
            {
                "product_id": product.id,
                "product_uom_qty": quantity,
                "product_uom": product.uom_id.id,
                "picking_id": picking.id,
                "location_id": warehouse.lot_stock_id.id,
                "location_dest_id": customer_location.id,
            }
        )
        picking.action_confirm()
        picking.action_assign()
        picking.move_ids.move_line_ids.lot_id = lot
        picking.move_ids.picked = True
        picking.button_validate()
        return picking

    def _investigation_on_lot(self, **values):
        """Create an investigation on a sample of the tracked lot."""
        specification = self._create_approved_specification()
        sample = self.env["ls.lab.sample"].create({
            "product_id": self.tracked.id,
            "lot_id": self.lot.id,
            "specification_id": specification.id,
            "sample_type": "finished_product",
        })
        sample.action_start()
        sample.action_start_testing()
        result = sample.result_ids[0]
        result.with_user(self.analyst).write({"result_numeric": 80.0})
        result.with_user(self.analyst).action_enter()
        investigation = result.oos_id
        if values:
            self.env.flush_all()
            investigation.sudo().write(values)
        return investigation

    # F-06 ---------------------------------------------------------------
    def test_lot_under_open_investigation_cannot_be_delivered(self):
        """A lot under an open investigation is refused at delivery."""
        investigation = self._investigation_on_lot()
        self.assertEqual(investigation.investigator_id, self.analyst)
        with self.assertRaises(UserError):
            self._deliver(self.tracked, self.lot, 5.0)

    def test_lot_released_by_the_investigation_can_be_delivered(self):
        """A closed investigation with a release disposition frees the lot."""
        self._investigation_on_lot(state="closed", product_disposition="release")
        picking = self._deliver(self.tracked, self.lot, 5.0)
        self.assertEqual(picking.state, "done")

    def test_lot_rejected_by_the_investigation_cannot_be_delivered(self):
        """A reject disposition keeps the lot out of distribution."""
        self._investigation_on_lot(state="closed", product_disposition="reject")
        with self.assertRaises(UserError):
            self._deliver(self.tracked, self.lot, 5.0)

    # F-16 ---------------------------------------------------------------
    def test_sample_refuses_the_lot_of_another_product(self):
        """The lot of a sample must belong to the sample product."""
        with self.assertRaises(ValidationError):
            self.env["ls.lab.sample"].create({
                "product_id": self.product.id,
                "lot_id": self.lot.id,
                "specification_id": self._create_approved_specification().id,
                "sample_type": "finished_product",
            })
