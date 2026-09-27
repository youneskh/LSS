# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Co-products obtained from a manufacturing batch."""

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class LsPharmaBatchCoproduct(models.Model):
    """An additional product obtained from the same manufacturing run.

    The functional specification lists co-product manufacturing, described as
    multiple products obtained from one manufacturing order, among the
    features of the pharmaceutical module.  Each co-product line carries its
    own quantity and its own inventory lot so that the co-product remains
    traceable independently of the main product of the batch.
    """

    _name = "ls.pharma.batch.coproduct"
    _description = "Batch Co-Product"
    _check_company_auto = True
    _order = "batch_id, sequence, id"

    sequence = fields.Integer(default=10)
    batch_id = fields.Many2one(comodel_name="ls.pharma.batch", required=True,
                               ondelete="cascade",
                               index=True,)
    company_id = fields.Many2one(comodel_name="res.company", related="batch_id.company_id",
                                 store=True,
                                 index=True,)
    product_id = fields.Many2one(
        comodel_name="product.product",
        string="Co-Product",
        required=True,
    )
    lot_id = fields.Many2one(
        comodel_name="stock.lot",
        string="Inventory Lot",
        check_company=True,
    )
    quantity = fields.Float(
        string="Quantity Obtained",
        digits="Product Unit of Measure",
        required=True,
    )
    uom_id = fields.Many2one(
        comodel_name="uom.uom",
        string="Unit of Measure",
        required=True,
    )
    note = fields.Char(string="Remark")

    @api.constrains("quantity")
    def _check_quantity(self):
        """Reject a co-product quantity that is not strictly positive."""
        for coproduct in self:
            if coproduct.quantity <= 0.0:
                raise ValidationError(
                    self.env._(
                        "The quantity obtained for co-product %(name)s must "
                        "be strictly positive.",
                        name=coproduct.product_id.display_name,
                    )
                )

    @api.onchange("product_id")
    def _onchange_product_id(self):
        """Default the unit of measure from the selected co-product."""
        for coproduct in self:
            if coproduct.product_id:
                coproduct.uom_id = coproduct.product_id.uom_id

    @api.constrains("lot_id", "product_id")
    def _check_lot_id_matches_product(self):
        """The lot must belong to the product of the record.

        :raise ValidationError: when the lot was created for another product.
        """
        for record in self:
            product = record.product_id
            if record.lot_id and product and record.lot_id.product_id != product:
                raise ValidationError(
                    self.env._(
                        "Lot %(lot)s belongs to product %(lot_product)s, not to "
                        "%(product)s.",
                        lot=record.lot_id.display_name,
                        lot_product=record.lot_id.product_id.display_name,
                        product=product.display_name,
                    )
                )
