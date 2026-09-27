# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Regression tests for the findings of the 2026-09-25 audit.

F-06 customer delivery of a lot whose batch is not released is refused,
F-16 a batch cannot reference the lot of another product.
"""
from odoo.exceptions import UserError, ValidationError
from odoo.tests import tagged

from .common import LsPharmaCommon


@tagged("post_install", "-at_install")
class TestAuditFixes(LsPharmaCommon):
    """Behaviour restored by the 2026-09-25 remediation."""

    @classmethod
    def setUpClass(cls):
        """Create a lot-tracked product and one of its lots."""
        super().setUpClass()
        cls.tracked = cls._tracked_product("Tracked tablets")
        cls.lot = cls.env["stock.lot"].create(
            {"name": "PHARMA-FIX-1", "product_id": cls.tracked.id}
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

    def _batch_in_state(self, state):
        """Create a batch of the tracked lot and force its status."""
        batch = self._create_batch(product_id=self.tracked.id, lot_id=self.lot.id)
        self.env.flush_all()
        self.env.cr.execute(
            "UPDATE ls_pharma_batch SET state = %s WHERE id = %s", (state, batch.id)
        )
        self.env.invalidate_all()
        return batch

    # F-06 ---------------------------------------------------------------
    def test_rejected_batch_lot_cannot_be_delivered(self):
        """A lot of a rejected batch is refused at delivery."""
        self._batch_in_state("rejected")
        with self.assertRaises(UserError):
            self._deliver(self.tracked, self.lot, 5.0)

    def test_batch_under_review_lot_cannot_be_delivered(self):
        """A lot of a batch awaiting its release decision is refused."""
        self._batch_in_state("under_review")
        with self.assertRaises(UserError):
            self._deliver(self.tracked, self.lot, 5.0)

    def test_released_batch_lot_can_be_delivered(self):
        """A lot of a released batch is delivered normally."""
        self._batch_in_state("released")
        picking = self._deliver(self.tracked, self.lot, 5.0)
        self.assertEqual(picking.state, "done")

    def test_lot_without_batch_can_be_delivered(self):
        """A lot that no batch names is not affected."""
        picking = self._deliver(self.tracked, self.lot, 5.0)
        self.assertEqual(picking.state, "done")

    # F-16 ---------------------------------------------------------------
    def test_batch_refuses_the_lot_of_another_product(self):
        """The lot of a batch must belong to the batch product."""
        with self.assertRaises(ValidationError):
            self._create_batch(lot_id=self.lot.id)
