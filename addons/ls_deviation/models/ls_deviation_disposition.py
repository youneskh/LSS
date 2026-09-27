# Copyright 2026 Life Sciences Suite
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Product disposition decisions taken as a result of a deviation."""

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

DISPOSITION_DECISION_SELECTION = [
    ("use_as_is", "Use As Is"),
    ("rework", "Rework"),
    ("reprocess", "Reprocess"),
    ("quarantine", "Quarantine"),
    ("reject", "Reject"),
    ("destroy", "Destroy"),
    ("return_supplier", "Return to Supplier"),
]

DISPOSITION_STATE_SELECTION = [
    ("draft", "Draft"),
    ("approved", "Approved"),
    ("rejected", "Rejected"),
]


class LsDeviationDisposition(models.Model):
    """Decision on the fate of material affected by a deviation."""

    _name = "ls.deviation.disposition"
    _description = "Deviation Product Disposition"
    _inherit = ["mail.thread"]
    _order = "id desc"
    _check_company_auto = True

    deviation_id = fields.Many2one(
        comodel_name="ls.deviation",
        required=True,
        ondelete="cascade",
        index=True,
    )
    company_id = fields.Many2one(
        related="deviation_id.company_id",
        store=True,
        index=True,
    )
    product_id = fields.Many2one(comodel_name="product.product", required=True,
                                 ondelete="restrict",
                                 check_company=True,)
    lot_id = fields.Many2one(
        comodel_name="stock.lot",
        string="Lot/Serial",
        ondelete="restrict",
        check_company=True,
    )
    quantity = fields.Float(
        digits="Product Unit of Measure",
        required=True,
    )
    product_uom_id = fields.Many2one(
        comodel_name="uom.uom",
        string="Unit of Measure",
        compute="_compute_product_uom_id",
        store=True,
        readonly=True,
    )
    decision = fields.Selection(
        selection=DISPOSITION_DECISION_SELECTION,
        required=True,
        tracking=True,
    )
    justification = fields.Text(
        required=True,
        tracking=True,
        help="Scientific and quality rationale supporting the decision. A "
        "Use As Is decision requires a rationale demonstrating that product "
        "quality, safety and efficacy are not adversely affected.",
    )
    approved_by_id = fields.Many2one(comodel_name="res.users", readonly=True,
                                     copy=False,
                                     ondelete="restrict",)
    approval_date = fields.Datetime(readonly=True, copy=False)
    state = fields.Selection(
        selection=DISPOSITION_STATE_SELECTION,
        required=True,
        default="draft",
        tracking=True,
    )

    _quantity_positive = models.Constraint(
        "CHECK(quantity > 0)",
        "The disposition quantity must be strictly positive.",
    )

    @api.depends("product_id")
    def _compute_product_uom_id(self):
        """Mirror the product unit of measure onto the disposition."""
        for record in self:
            record.product_uom_id = record.product_id.uom_id

    @api.constrains("lot_id", "product_id")
    def _check_lot_product(self):
        """The lot, where given, must belong to the dispositioned product."""
        for record in self:
            if record.lot_id and record.lot_id.product_id != record.product_id:
                raise ValidationError(
                    _(
                        "Lot %(lot)s does not belong to product %(product)s.",
                        lot=record.lot_id.display_name,
                        product=record.product_id.display_name,
                    )
                )

    def action_approve(self):
        """Approve the disposition.

        Approval is restricted to the deviation manager group because a
        disposition determines whether affected material may be released.
        """
        if not self.env.user.has_group("ls_deviation.group_ls_deviation_manager"):
            raise UserError(
                _("Only a Deviation Manager may approve a product disposition.")
            )
        for record in self:
            if record.state != "draft":
                raise UserError(
                    _("Only a draft disposition can be approved.")
                )
        return self.write(
            {
                "state": "approved",
                "approved_by_id": self.env.user.id,
                "approval_date": fields.Datetime.now(),
            }
        )

    def action_reject(self):
        """Reject the proposed disposition."""
        if not self.env.user.has_group("ls_deviation.group_ls_deviation_manager"):
            raise UserError(
                _("Only a Deviation Manager may reject a product disposition.")
            )
        return self.write({"state": "rejected"})
