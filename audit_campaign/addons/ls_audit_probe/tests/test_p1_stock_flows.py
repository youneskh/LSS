"""P1 - Standard stock workflows with all custom modules installed.

The same scenarios run twice: once as installed, and once with the audit
trail recording every field of stock.picking, stock.move, stock.move.line and
stock.quant (the configuration that exercises the ``base`` create/write/unlink
overrides of ls_audit_trail on the stock engine).
"""

from odoo.tests import tagged

from .common import ProbeCommon


class StockFlowsMixin:
    """Scenarios. ``AUDITED`` switches the audit rules on."""

    AUDITED = False

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        if cls.AUDITED:
            cls._audit_all_stock_models(cls)

    def _check_chain(self):
        if not self.AUDITED:
            return
        outcome = self.env["ls.audit_trail.log"]._ls_verify_chain(self.company)
        self.assertTrue(
            outcome["passed"],
            f"PROBE audit chain does not verify after stock operations: {outcome.get('details')}",
        )
        entries = self.env["ls.audit_trail.log"].sudo().search_count(
            [("model_name", "in", ["stock.move", "stock.quant"])]
        )
        self.assertGreater(entries, 0, "PROBE no audit entry recorded for stock models")

    def test_S01_receipt_lot_partial_with_backorder(self):
        picking = self._picking(
            self.warehouse.in_type_id, self.supplier_location, self.stock_location,
            [(self.product_lot, 10)],
        )
        picking.action_confirm()
        picking.action_assign()
        move = picking.move_ids
        move.move_line_ids.write({"lot_name": "PROBE-R1", "quantity": 6})
        self._validate(picking, backorder=True)
        self.assertEqual(picking.state, "done")
        backorder = self.env["stock.picking"].search([("backorder_id", "=", picking.id)])
        self.assertEqual(len(backorder), 1, "PROBE receipt backorder not created")
        self.assertEqual(sum(backorder.move_ids.mapped("product_uom_qty")), 4)
        lot = self.env["stock.lot"].search(
            [("name", "=", "PROBE-R1"), ("product_id", "=", self.product_lot.id)]
        )
        self.assertEqual(self._qty(self.product_lot, self.stock_location, lot), 6)
        self._check_chain()

    def test_S02_delivery_reservation_partial_backorder_and_return(self):
        lot = self._lot(self.product_lot, "PROBE-D1")
        self._add_stock(self.product_lot, 10, lot)
        picking = self._picking(
            self.warehouse.out_type_id, self.stock_location, self.customer_location,
            [(self.product_lot, 8)],
        )
        picking.action_confirm()
        picking.action_assign()
        self.assertEqual(picking.state, "assigned")
        quant = self.env["stock.quant"]._gather(self.product_lot, self.stock_location, lot_id=lot, strict=True)
        self.assertEqual(sum(quant.mapped("reserved_quantity")), 8)
        picking.move_ids.quantity = 5
        self._validate(picking, backorder=True)
        self.assertEqual(self._qty(self.product_lot, self.stock_location, lot), 5)
        self.assertEqual(self._qty(self.product_lot, self.customer_location, lot), 5)
        backorder = self.env["stock.picking"].search([("backorder_id", "=", picking.id)])
        self.assertEqual(sum(backorder.move_ids.mapped("product_uom_qty")), 3)
        # Return 2 units of the delivered lot.
        wizard = self.env["stock.return.picking"].with_context(
            active_id=picking.id, active_ids=picking.ids, active_model="stock.picking"
        ).create({})
        wizard.product_return_moves.quantity = 2
        res = wizard.action_create_returns()
        ret = self.env["stock.picking"].browse(res["res_id"])
        ret.action_assign()
        for ml in ret.move_ids.move_line_ids:
            ml.lot_id = lot
        self._validate(ret)
        self.assertEqual(ret.state, "done")
        self.assertEqual(self._qty(self.product_lot, self.stock_location, lot), 7)
        self.assertEqual(self._qty(self.product_lot, self.customer_location, lot), 3)
        self._check_chain()

    def test_S03_internal_transfer(self):
        shelf = self.env["stock.location"].create(
            {"name": "Probe Shelf", "location_id": self.stock_location.id}
        )
        self._add_stock(self.product_plain, 9)
        picking = self._picking(
            self.warehouse.int_type_id, self.stock_location, shelf, [(self.product_plain, 5)]
        )
        picking.action_confirm()
        picking.action_assign()
        self._validate(picking)
        self.assertEqual(self._qty(self.product_plain, shelf), 5)
        self.assertEqual(self._qty(self.product_plain, self.stock_location), 4)
        self._check_chain()

    def test_S04_inventory_adjustment(self):
        lot = self._lot(self.product_lot, "PROBE-I1")
        self.env["stock.quant"].with_context(inventory_mode=True).create({
            "product_id": self.product_lot.id,
            "location_id": self.stock_location.id,
            "lot_id": lot.id,
            "inventory_quantity": 12,
        }).action_apply_inventory()
        self.assertEqual(self._qty(self.product_lot, self.stock_location, lot), 12)
        self._check_chain()

    def test_S05_serial_uniqueness_enforced(self):
        self._lot(self.product_serial, "PROBE-SN-1")
        with self.assertRaises(Exception):
            with self.env.cr.savepoint():
                self._lot(self.product_serial, "PROBE-SN-1")

    def test_S06_cancel_releases_reservation(self):
        self._add_stock(self.product_plain, 4)
        picking = self._picking(
            self.warehouse.out_type_id, self.stock_location, self.customer_location,
            [(self.product_plain, 4)],
        )
        picking.action_confirm()
        picking.action_assign()
        picking.action_cancel()
        self.assertEqual(picking.state, "cancel")
        quants = self.env["stock.quant"]._gather(self.product_plain, self.stock_location, strict=True)
        self.assertEqual(sum(quants.mapped("reserved_quantity")), 0)
        self._check_chain()

    def test_S07_scrap(self):
        self._add_stock(self.product_plain, 3)
        scrap = self.env["stock.scrap"].create({
            "product_id": self.product_plain.id,
            "scrap_qty": 1,
            "location_id": self.stock_location.id,
        })
        scrap.action_validate()
        self.assertEqual(self._qty(self.product_plain, self.stock_location), 2)
        self._check_chain()

    def test_S08_sale_order_to_delivery(self):
        self._add_stock(self.product_plain, 5)
        order = self.env["sale.order"].create({
            "partner_id": self.partner.id,
            "order_line": [self.cmd().create({
                "product_id": self.product_plain.id,
                "product_uom_qty": 3,
            })],
        })
        order.action_confirm()
        picking = order.picking_ids
        self.assertEqual(len(picking), 1)
        picking.action_assign()
        self._validate(picking)
        self.assertEqual(order.order_line.qty_delivered, 3)
        self.assertEqual(self._qty(self.product_plain, self.stock_location), 2)
        self._check_chain()


@tagged("post_install", "-at_install", "ls_audit_probe")
class TestP1StockFlowsPlain(StockFlowsMixin, ProbeCommon):
    AUDITED = False
    allow_inherited_tests_method = True


@tagged("post_install", "-at_install", "ls_audit_probe")
class TestP1StockFlowsAudited(StockFlowsMixin, ProbeCommon):
    AUDITED = True
    allow_inherited_tests_method = True
