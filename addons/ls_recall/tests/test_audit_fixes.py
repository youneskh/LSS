# Part of the Life Sciences Suite for Odoo 19 Community Edition.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Regression tests for the findings of the 2026-09-25 audit.

F-03 lot form readable without a recall role, F-06 delivery of a recalled
lot refused, F-07 recall reaching the lots produced from a recalled lot,
F-17 traced quantity in the unit of measure of the product and tracing by a
coordinator without inventory rights, F-35 generation of the effectiveness
checks.
"""

from odoo.exceptions import UserError
from odoo.tests import tagged
from odoo.tests.common import new_test_user

from .common import RecallCommon


@tagged("post_install", "-at_install")
class TestAuditFixes(RecallCommon):
    """Behaviour restored by the 2026-09-25 remediation."""

    @classmethod
    def setUpClass(cls):
        """Add the stock locations used to build real movements."""
        super().setUpClass()
        cls.warehouse = cls.env["stock.warehouse"].search(
            [("company_id", "=", cls.company.id)], limit=1
        )
        cls.stock_location = cls.warehouse.lot_stock_id
        cls.customer_location = cls.env.ref("stock.stock_location_customers")
        cls.production_location = cls.env["stock.location"].search(
            [("usage", "=", "production"), ("company_id", "in", [cls.company.id, False])],
            limit=1,
        )
        cls.uom_dozen = cls.env.ref("uom.product_uom_dozen")

    def _deliver(self, partner, lot, quantity, uom=None):
        """Ship ``quantity`` (in ``uom``) of ``lot`` to ``partner``.

        :return: the picking, validated.
        """
        self.env["stock.quant"]._update_available_quantity(
            self.product, self.stock_location, 1000.0, lot_id=lot
        )
        picking = self.env["stock.picking"].create(
            {
                "partner_id": partner.id,
                "picking_type_id": self.warehouse.out_type_id.id,
                "location_id": self.stock_location.id,
                "location_dest_id": self.customer_location.id,
            }
        )
        self.env["stock.move"].create(
            {
                "product_id": self.product.id,
                "product_uom_qty": quantity,
                "product_uom": (uom or self.product.uom_id).id,
                "picking_id": picking.id,
                "location_id": self.stock_location.id,
                "location_dest_id": self.customer_location.id,
            }
        )
        picking.action_confirm()
        picking.action_assign()
        picking.move_ids.move_line_ids.lot_id = lot
        picking.move_ids.picked = True
        picking.button_validate()
        return picking

    def _done_move_line(self, product, lot, quantity, source, destination):
        """Record a completed internal movement of one lot.

        :return: the ``stock.move.line`` of the movement.
        """
        move = self.env["stock.move"].create(
            {
                "product_id": product.id,
                "product_uom_qty": quantity,
                "product_uom": product.uom_id.id,
                "location_id": source.id,
                "location_dest_id": destination.id,
            }
        )
        move._action_confirm()
        move._action_assign()
        if not move.move_line_ids:
            self.env["stock.move.line"].create(
                {
                    "move_id": move.id,
                    "product_id": product.id,
                    "location_id": source.id,
                    "location_dest_id": destination.id,
                    "quantity": quantity,
                }
            )
        move.move_line_ids.write({"lot_id": lot.id, "quantity": quantity})
        move.picked = True
        move._action_done()
        return move.move_line_ids

    # F-03 ---------------------------------------------------------------
    def test_lot_indicator_readable_by_inventory_user(self):
        """An inventory user without recall role reads the recall indicator."""
        user = new_test_user(
            self.env, login="recall_fix_stock_user", groups="stock.group_stock_user"
        )
        self._create_execution().action_initiate()
        self.env.invalidate_all()
        lot = self.lot_1.with_user(user)
        self.assertTrue(lot.ls_recall_open)
        self.assertEqual(lot.ls_recall_count, 1)

    # F-06 ---------------------------------------------------------------
    def test_lot_under_open_recall_cannot_be_delivered(self):
        """A lot named in an open recall is refused at delivery."""
        self._create_execution().action_initiate()
        with self.assertRaises(UserError):
            self._deliver(self.partner_a, self.lot_1, 5.0)

    def test_lot_of_rehearsal_can_be_delivered(self):
        """A mock recall does not hold the lot back."""
        self._create_execution(
            action_type="mock_recall",
            classification="not_classified",
            health_hazard_evaluation=False,
            depth=False,
        ).action_initiate()
        picking = self._deliver(self.partner_a, self.lot_1, 5.0)
        self.assertEqual(picking.state, "done")

    # F-07 ---------------------------------------------------------------
    def test_recall_follows_lots_produced_from_the_recalled_lot(self):
        """The consignee of a finished lot made from a recalled lot is traced."""
        component_lot = self.lot_2
        finished_lot = self.env["stock.lot"].create(
            {"name": "LOT-FINISHED", "product_id": self.product.id}
        )
        self.env["stock.quant"]._update_available_quantity(
            self.product, self.stock_location, 10.0, lot_id=component_lot
        )
        consumed = self._done_move_line(
            self.product, component_lot, 10.0,
            self.stock_location, self.production_location,
        )
        produced = self._done_move_line(
            self.product, finished_lot, 10.0,
            self.production_location, self.stock_location,
        )
        # The link recorded by manufacturing between consumed and produced
        # move lines (stock.move.line.produce_line_ids).
        consumed.produce_line_ids = [(6, 0, produced.ids)]
        self._deliver(self.partner_b, finished_lot, 4.0)
        execution = self._create_execution(lot_ids=[(6, 0, component_lot.ids)])
        execution.action_trace_distribution()
        line = execution.line_ids.filtered(lambda item: item.lot_id == finished_lot)
        self.assertEqual(line.partner_id, self.partner_b)
        self.assertEqual(line.qty_shipped, 4.0)

    # F-17 ---------------------------------------------------------------
    def test_traced_quantity_is_in_the_product_unit(self):
        """Two dozen delivered are traced as 24 units."""
        self._deliver(self.partner_a, self.lot_1, 2.0, uom=self.uom_dozen)
        execution = self._create_execution()
        execution.action_trace_distribution()
        self.assertEqual(execution.line_ids.qty_shipped, 24.0)

    def test_coordinator_without_inventory_rights_can_trace(self):
        """Tracing reads stock data on behalf of the recall coordinator."""
        self._deliver(self.partner_a, self.lot_1, 3.0)
        execution = self._create_execution().with_user(self.user_coordinator)
        execution.action_trace_distribution()
        self.assertEqual(execution.line_ids.partner_id, self.partner_a)

    # F-35 ---------------------------------------------------------------
    def test_effectiveness_checks_are_generated_after_a_trace(self):
        """One check per consignee line is created with its consignee."""
        self._deliver(self.partner_a, self.lot_1, 3.0)
        execution = self._create_execution()
        execution.action_trace_distribution()
        execution.action_generate_effectiveness_checks()
        self.assertEqual(
            execution.effectiveness_ids.mapped("partner_id"), self.partner_a
        )
