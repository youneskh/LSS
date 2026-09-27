"""P4 - Quality decisions and recall traceability against real stock moves."""

from odoo import Command
from odoo.exceptions import UserError, ValidationError
from odoo.tests import Form, tagged

from .common import ProbeCommon

RECALL_DEFAULTS = {
    "action_type": "recall",
    "classification": "class_ii",
    "depth": "retail",
    "reason": "Probe.",
    "health_hazard_evaluation": "<p>Probe.</p>",
    "effectiveness_level": "a",
}


@tagged("post_install", "-at_install", "ls_audit_probe")
class TestP4QualityStock(ProbeCommon):

    def _recall(self, product, lots):
        return self.env["ls.recall.execution"].create(dict(
            RECALL_DEFAULTS,
            product_id=product.id,
            lot_ids=[(6, 0, lots.ids)],
            responsible_user_id=self.env.user.id,
        ))

    # ------------------------------------------------------------------
    def test_F06a_rejected_batch_lot_cannot_be_delivered(self):
        """F-06: a lot whose pharmaceutical batch is rejected is blocked."""
        lot = self._lot(self.product_lot, "PROBE-F06A")
        self._add_stock(self.product_lot, 5, lot)
        try:
            batch = self.env["ls.pharma.batch"].create({
                "product_id": self.product_lot.id,
                "batch_type": "finished",
                "uom_id": self.uom_unit.id,
                "planned_qty": 5.0,
                "theoretical_yield_qty": 5.0,
                "yield_min_percentage": 95.0,
                "yield_max_percentage": 102.0,
                "shelf_life_months": 24,
                "lot_id": lot.id,
            })
        except Exception as error:  # noqa: BLE001
            self.skipTest(f"SETUP batch cannot be created: {error}")
        self.env.cr.execute("UPDATE ls_pharma_batch SET state = 'rejected' WHERE id = %s", (batch.id,))
        self.env.invalidate_all()
        try:
            with self.env.cr.savepoint():
                picking = self._deliver_lot(self.product_lot, lot, 5)
                delivered = picking.state == "done"
        except (UserError, ValidationError):
            delivered = False
        self.assertFalse(delivered, "PROBE F-06 reproduced: a lot of a REJECTED batch was delivered to a customer")

    def test_F06b_lot_under_open_recall_cannot_be_delivered(self):
        """F-06: a lot named in an initiated recall is blocked."""
        lot = self._lot(self.product_lot, "PROBE-F06B")
        self._add_stock(self.product_lot, 5, lot)
        execution = self._recall(self.product_lot, lot)
        try:
            execution.action_initiate()
        except Exception as error:  # noqa: BLE001
            self.skipTest(f"SETUP recall cannot be initiated: {error}")
        self.assertTrue(lot.ls_recall_open, "SETUP lot not flagged as under recall")
        try:
            with self.env.cr.savepoint():
                picking = self._deliver_lot(self.product_lot, lot, 5)
                delivered = picking.state == "done"
        except (UserError, ValidationError):
            delivered = False
        self.assertFalse(delivered, "PROBE F-06 reproduced: a lot under an open recall was delivered to a customer")

    # ------------------------------------------------------------------
    def test_F07_recall_of_component_reaches_finished_goods_consignee(self):
        """F-07: recalling a component lot finds the customers of the
        finished lots made from it."""
        component = self._product("Probe API component", "lot")
        finished = self._product("Probe finished tablets", "lot")
        comp_lot = self._lot(component, "PROBE-COMP-1")
        self._add_stock(component, 10, comp_lot)
        consignee = self.env["res.partner"].create({"name": "Probe pharmacy"})
        try:
            bom = self.env["mrp.bom"].create({
                "product_id": finished.id,
                "product_tmpl_id": finished.product_tmpl_id.id,
                "product_qty": 1.0,
                "type": "normal",
                "bom_line_ids": [Command.create({"product_id": component.id, "product_qty": 1})],
            })
            mo_form = Form(self.env["mrp.production"])
            mo_form.product_id = finished
            mo_form.bom_id = bom
            mo_form.product_qty = 2
            mo = mo_form.save()
            mo.action_confirm()
            mo.action_assign()
            fin_lot = self._lot(finished, "PROBE-FIN-1")
            mo_form = Form(mo)
            if "lot_producing_ids" in mo._fields:
                mo_form.lot_producing_ids.set(fin_lot)
            else:
                mo_form.lot_producing_id = fin_lot
            mo_form.qty_producing = 2
            mo = mo_form.save()
            for ml in mo.move_raw_ids.move_line_ids:
                ml.lot_id = comp_lot
            mo.move_raw_ids.picked = True
            mo.button_mark_done()
            self.assertEqual(mo.state, "done")
            self._deliver_lot(finished, fin_lot, 2, partner=consignee)
        except Exception as error:  # noqa: BLE001
            self.skipTest(f"SETUP manufacturing or delivery scenario failed: {error}")
        execution = self._recall(component, comp_lot)
        execution.action_trace_distribution()
        self.assertIn(
            consignee, execution.line_ids.mapped("partner_id"),
            "PROBE F-07 reproduced: recall of a component lot does not reach the consignee of the finished lot made from it",
        )

    # ------------------------------------------------------------------
    def test_F17_traced_quantity_is_in_product_uom(self):
        """F-17: 2 dozen delivered are traced as 24 units."""
        lot = self._lot(self.product_lot, "PROBE-F17")
        self._add_stock(self.product_lot, 24, lot)
        consignee = self.env["res.partner"].create({"name": "Probe wholesaler"})
        try:
            self._deliver_lot(self.product_lot, lot, 2, partner=consignee, uom=self.uom_dozen)
        except Exception as error:  # noqa: BLE001
            self.skipTest(f"SETUP delivery in dozens failed: {error}")
        self.assertEqual(self._qty(self.product_lot, self.customer_location, lot), 24, "SETUP stock not moved")
        execution = self._recall(self.product_lot, lot)
        execution.action_trace_distribution()
        shipped = sum(execution.line_ids.mapped("qty_shipped"))
        self.assertEqual(shipped, 24, f"PROBE F-17 reproduced: traced quantity is {shipped}, expected 24 units")

    # ------------------------------------------------------------------
    def test_F35_generate_effectiveness_checks_button(self):
        """F-35: the 'Generate effectiveness checks' action works after a trace."""
        lot = self._lot(self.product_lot, "PROBE-F35")
        self._add_stock(self.product_lot, 3, lot)
        consignee = self.env["res.partner"].create({"name": "Probe clinic"})
        self._deliver_lot(self.product_lot, lot, 3, partner=consignee)
        execution = self._recall(self.product_lot, lot)
        execution.action_trace_distribution()
        self.assertTrue(execution.line_ids, "SETUP trace produced no consignee line")
        try:
            with self.env.cr.savepoint():
                execution.action_generate_effectiveness_checks()
        except Exception as error:  # noqa: BLE001
            self.fail(f"PROBE F-35 reproduced: effectiveness checks cannot be generated: {error}")
