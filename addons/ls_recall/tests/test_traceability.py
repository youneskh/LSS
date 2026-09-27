# Part of the Life Sciences Suite for Odoo 19 Community Edition.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Tests for distribution tracing from stock movements.

These are integration tests: they drive real deliveries through the
stock module and then ask the recall to trace them. They are the tests
most tightly coupled to stock internals and therefore the ones to run
first when validating the module on a new Odoo build.
"""

from odoo.exceptions import UserError
from odoo.tests import tagged

from .common import RecallCommon


@tagged("post_install", "-at_install")
class TestTraceability(RecallCommon):
    """Consignee lines are built from completed outgoing movements."""

    @classmethod
    def setUpClass(cls):
        """Add the warehouse locations used to build deliveries."""
        super().setUpClass()
        cls.warehouse = cls.env["stock.warehouse"].search(
            [("company_id", "=", cls.company.id)], limit=1
        )
        cls.stock_location = cls.warehouse.lot_stock_id
        cls.customer_location = cls.env.ref("stock.stock_location_customers")

    def _deliver(self, partner, lot, quantity):
        """Ship a quantity of one lot to one consignee.

        :param partner: the consignee.
        :param lot: the lot shipped.
        :param float quantity: the quantity shipped.
        :return: the validated picking.
        """
        self.env["stock.quant"]._update_available_quantity(
            self.product, self.stock_location, quantity, lot_id=lot
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
                "picking_id": picking.id,
                "location_id": self.stock_location.id,
                "location_dest_id": self.customer_location.id,
            }
        )
        picking.action_confirm()
        picking.action_assign()
        for move in picking.move_ids:
            move.picked = True
        picking.button_validate()
        return picking

    def test_trace_creates_one_line_per_consignee_and_lot(self):
        """Each consignee and lot combination yields exactly one line."""
        self._deliver(self.partner_a, self.lot_1, 30.0)
        self._deliver(self.partner_b, self.lot_1, 20.0)
        execution = self._create_execution()
        execution.action_trace_distribution()
        self.assertEqual(len(execution.line_ids), 2)
        self.assertEqual(execution.qty_distributed, 50.0)
        self.assertEqual(execution.consignee_count, 2)

    def test_repeated_shipments_are_summed(self):
        """Two deliveries to one consignee produce one aggregated line."""
        self._deliver(self.partner_a, self.lot_1, 10.0)
        self._deliver(self.partner_a, self.lot_1, 15.0)
        execution = self._create_execution()
        execution.action_trace_distribution()
        self.assertEqual(len(execution.line_ids), 1)
        self.assertEqual(execution.line_ids.qty_shipped, 25.0)

    def test_only_named_lots_are_traced(self):
        """A lot outside the recall scope is not picked up."""
        self._deliver(self.partner_a, self.lot_1, 10.0)
        self._deliver(self.partner_b, self.lot_2, 40.0)
        execution = self._create_execution(lot_ids=[(6, 0, self.lot_1.ids)])
        execution.action_trace_distribution()
        self.assertEqual(len(execution.line_ids), 1)
        self.assertEqual(execution.line_ids.partner_id, self.partner_a)

    def test_retracing_preserves_user_entered_returns(self):
        """Tracing again refreshes shipments without erasing responses.

        Both shipments precede the recall: once a recall names the lot,
        further customer deliveries of that lot are refused.
        """
        self._deliver(self.partner_a, self.lot_1, 40.0)
        self._deliver(self.partner_a, self.lot_1, 10.0)
        execution = self._create_execution()
        execution.action_trace_distribution()
        line = execution.line_ids
        line.qty_returned = 25.0
        execution.action_trace_distribution()
        self.assertEqual(len(execution.line_ids), 1)
        self.assertEqual(execution.line_ids.qty_shipped, 50.0)
        self.assertEqual(execution.line_ids.qty_returned, 25.0)

    def test_source_transfers_recorded(self):
        """The line keeps a link to the transfers it was traced from."""
        picking = self._deliver(self.partner_a, self.lot_1, 12.0)
        execution = self._create_execution()
        execution.action_trace_distribution()
        self.assertIn(picking, execution.line_ids.picking_ids)

    def test_tracing_blocked_on_finalised_recall(self):
        """A closed or cancelled recall cannot be re-traced."""
        execution = self._create_execution()
        execution.action_initiate()
        wizard = self.env["ls.recall.close.wizard"].create(
            {
                "execution_id": execution.id,
                "mode": "cancel",
                "justification": "Not required.",
            }
        )
        wizard.action_confirm()
        with self.assertRaises(UserError):
            execution.action_trace_distribution()

    def test_lot_shows_recall_indicator(self):
        """A lot named in an open recall is flagged on the lot record."""
        execution = self._create_execution()
        execution.action_initiate()
        self.lot_1.invalidate_recordset()
        self.assertTrue(self.lot_1.ls_recall_open)
        self.assertEqual(self.lot_1.ls_recall_count, 1)
        self.assertNotIn(execution, self.lot_2.ls_recall_execution_ids)
