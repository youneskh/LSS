"""Shared helpers for the audit probes.

Conventions used by every probe:

* A test named ``test_Fxx_...`` checks the CORRECT behaviour expected for
  finding F-xx. A PASS means the finding is NOT reproduced; a FAIL or ERROR
  whose message starts with ``PROBE`` means the finding IS reproduced.
* When the scenario itself cannot be built (setup problem unrelated to the
  finding), the test is skipped with a message starting with ``SETUP``, so a
  setup problem is never reported as a finding.
"""

import logging

from odoo import Command
from odoo.tests import Form
from odoo.tests.common import TransactionCase

_logger = logging.getLogger(__name__)


class ProbeCommon(TransactionCase):
    """Warehouse, locations, products and stock helpers."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.company = cls.env.company
        cls.warehouse = cls.env["stock.warehouse"].search(
            [("company_id", "=", cls.company.id)], limit=1
        )
        cls.stock_location = cls.warehouse.lot_stock_id
        cls.customer_location = cls.env.ref("stock.stock_location_customers")
        cls.supplier_location = cls.env.ref("stock.stock_location_suppliers")
        cls.uom_unit = cls.env.ref("uom.product_uom_unit")
        cls.uom_dozen = cls.env.ref("uom.product_uom_dozen")
        cls.partner = cls.env["res.partner"].create({"name": "Probe Customer"})
        cls.product_lot = cls._product("Probe Lot Product", "lot")
        cls.product_serial = cls._product("Probe Serial Product", "serial")
        cls.product_plain = cls._product("Probe Plain Product", "none")

    @classmethod
    def _product(cls, name, tracking):
        values = {"name": name, "type": "consu", "tracking": tracking}
        if "is_storable" in cls.env["product.template"]._fields:
            values["is_storable"] = True
        return cls.env["product.product"].create(values)

    def _lot(self, product, name):
        return self.env["stock.lot"].create({"name": name, "product_id": product.id})

    def _add_stock(self, product, qty, lot=None, location=None):
        self.env["stock.quant"]._update_available_quantity(
            product, location or self.stock_location, qty, lot_id=lot
        )

    def _qty(self, product, location, lot=None):
        quants = self.env["stock.quant"]._gather(
            product, location, lot_id=lot, strict=True
        )
        return sum(quants.mapped("quantity"))

    def _picking(self, picking_type, src, dst, lines, partner=None):
        picking = self.env["stock.picking"].create({
            "picking_type_id": picking_type.id,
            "location_id": src.id,
            "location_dest_id": dst.id,
            "partner_id": (partner or self.partner).id,
        })
        for line in lines:
            product, qty = line[0], line[1]
            uom = line[2] if len(line) > 2 else product.uom_id
            self.env["stock.move"].create({
                "product_id": product.id,
                "product_uom_qty": qty,
                "product_uom": uom.id,
                "picking_id": picking.id,
                "location_id": src.id,
                "location_dest_id": dst.id,
            })
        return picking

    def _validate(self, picking, backorder=True):
        """Validate, answering the backorder wizard if it appears."""
        picking.move_ids.picked = True
        res = picking.button_validate()
        if isinstance(res, dict) and res.get("res_model") == "stock.backorder.confirmation":
            wizard = Form(
                self.env[res["res_model"]].with_context(res["context"])
            ).save()
            if backorder:
                wizard.process()
            else:
                wizard.process_cancel_backorder()
        return picking

    def _deliver_lot(self, product, lot, qty, partner=None, uom=None):
        """Deliver ``qty`` (in ``uom``) of ``lot`` to ``partner``."""
        picking = self._picking(
            self.warehouse.out_type_id, self.stock_location, self.customer_location,
            [(product, qty, uom or product.uom_id)], partner=partner,
        )
        picking.action_confirm()
        picking.action_assign()
        for ml in picking.move_ids.move_line_ids:
            ml.lot_id = lot
        return self._validate(picking)

    def _audit_all_stock_models(self):
        """Create audit rules on the four stock models, every field."""
        rules = self.env["ls.audit_trail.rule"]
        for model in ("stock.picking", "stock.move", "stock.move.line", "stock.quant"):
            rules |= rules.create({
                "name": f"Probe rule {model}",
                "model_id": self.env["ir.model"]._get(model).id,
                "log_create": True,
                "log_write": True,
                "log_unlink": True,
            })
        return rules

    @staticmethod
    def cmd():
        return Command
