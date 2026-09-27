# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Components charged into a manufacturing batch."""

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class LsPharmaBatchComponent(models.Model):
    """A component or in-process material charged into a batch.

    This model implements two distinct regulatory requirements.

    21 CFR 211.188(b)(3) and 21 CFR 211.188(b)(4) require the batch
    production and control record to carry the specific identification of
    each batch of component used and the weights and measures of the
    components used in the course of processing.

    21 CFR 211.101(d) requires that each component be added to the batch by
    one person and verified by a second person, or, where the component is
    added by automated equipment, verified by one person.  The model
    therefore records the person who charged the component and the person who
    verified the charge, and refuses to accept the same user in both roles
    unless the charge was performed by automated equipment.
    """

    _name = "ls.pharma.batch.component"
    _description = "Batch Component Charge"
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
        string="Component",
        required=True,
    )
    api_id = fields.Many2one(
        comodel_name="ls.pharma.api",
        string="Active Ingredient",
        help=(
            "Active ingredient master record, completed when the component is "
            "an active pharmaceutical ingredient."
        ),
    )
    excipient_id = fields.Many2one(comodel_name="ls.pharma.excipient", help="Excipient master record, completed when the component is an excipient.",)
    component_lot_id = fields.Many2one(comodel_name="stock.lot", help=(
            "Inventory lot of the component consumed. It provides the "
            "specific identification required by 21 CFR 211.188(b)(3)."
        ),
        check_company=True,
    )
    component_lot_reference = fields.Char(help=(
            "Free-text lot reference, used when the component lot is not held "
            "as an inventory lot in this database."),
    )
    quantity = fields.Float(
        string="Quantity Charged",
        digits="Product Unit of Measure",
        required=True,
    )
    uom_id = fields.Many2one(
        comodel_name="uom.uom",
        string="Unit of Measure",
        required=True,
    )
    assay_percentage = fields.Float(
        string="Assay (%)",
        digits=(16, 4),
        help=(
            "Assay of the consignment actually used. It is compared with the "
            "label assay of the active ingredient to compute the "
            "potency-compensated quantity."
        ),
    )
    compensated_quantity = fields.Float(
        string="Potency-Compensated Quantity",
        compute="_compute_compensated_quantity",
        store=True,
        digits="Product Unit of Measure",
        help=(
            "Quantity that would deliver the same amount of active ingredient "
            "at the label assay. It is computed only when both the assay of "
            "the consignment and the label assay of the ingredient are known."
        ),
    )
    is_active_ingredient = fields.Boolean(
        string="Active Ingredient",
        compute="_compute_is_active_ingredient",
        store=True,
    )
    charged_by_user_id = fields.Many2one(
        comodel_name="res.users",
        string="Charged By",
        help="User who added the component to the batch.",
    )
    verified_by_user_id = fields.Many2one(
        comodel_name="res.users",
        string="Verified By",
        help=(
            "Second user who verified the charge, as required by "
            "21 CFR 211.101(d)."
        ),
    )
    is_automated_charge = fields.Boolean(
        string="Charged by Automated Equipment",
        help=(
            "Set when the component was added by automated equipment. "
            "21 CFR 211.101(d) then requires verification by one person only."
        ),
    )
    date_charged = fields.Datetime(string="Charge Date and Time")
    note = fields.Char(string="Remark")

    @api.depends("api_id")
    def _compute_is_active_ingredient(self):
        """Flag the lines that carry an active pharmaceutical ingredient."""
        for component in self:
            component.is_active_ingredient = bool(component.api_id)

    @api.depends("quantity", "assay_percentage", "api_id.label_assay_percentage")
    def _compute_compensated_quantity(self):
        """Compute the potency-compensated charge quantity."""
        for component in self:
            label_assay = component.api_id.label_assay_percentage
            if component.assay_percentage > 0.0 and label_assay > 0.0:
                component.compensated_quantity = (
                    component.quantity * label_assay / component.assay_percentage
                )
            else:
                component.compensated_quantity = component.quantity

    @api.constrains("quantity")
    def _check_quantity(self):
        """Reject a charge quantity that is not strictly positive."""
        for component in self:
            if component.quantity <= 0.0:
                raise ValidationError(
                    self.env._(
                        "The quantity charged for component %(name)s must be "
                        "strictly positive.",
                        name=component.product_id.display_name,
                    )
                )

    @api.constrains("assay_percentage")
    def _check_assay(self):
        """Reject a negative assay."""
        for component in self:
            if component.assay_percentage < 0.0:
                raise ValidationError(self.env._("The assay cannot be negative."))

    @api.constrains(
        "charged_by_user_id", "verified_by_user_id", "is_automated_charge"
    )
    def _check_second_person_verification(self):
        """Enforce the second-person verification of 21 CFR 211.101(d)."""
        for component in self:
            if component.is_automated_charge:
                continue
            charged = component.charged_by_user_id
            verified = component.verified_by_user_id
            if charged and verified and charged.id == verified.id:
                raise ValidationError(
                    self.env._(
                        "Component %(name)s was charged and verified by the "
                        "same user. 21 CFR 211.101(d) requires that a "
                        "component added by one person be verified by a "
                        "second person.",
                        name=component.product_id.display_name,
                    )
                )

    @api.constrains("api_id", "excipient_id")
    def _check_material_exclusivity(self):
        """Reject a component that is both an active ingredient and an excipient."""
        for component in self:
            if component.api_id and component.excipient_id:
                raise ValidationError(
                    self.env._(
                        "A component cannot be linked to an active ingredient "
                        "and to an excipient at the same time."
                    )
                )

    @api.onchange("product_id")
    def _onchange_product_id(self):
        """Default the unit of measure from the selected component."""
        for component in self:
            if component.product_id:
                component.uom_id = component.product_id.uom_id

    @api.constrains("component_lot_id", "product_id")
    def _check_component_lot_id_matches_product(self):
        """The lot must belong to the product of the record.

        :raise ValidationError: when the lot was created for another product.
        """
        for record in self:
            product = record.product_id
            if record.component_lot_id and product and record.component_lot_id.product_id != product:
                raise ValidationError(
                    self.env._(
                        "Lot %(lot)s belongs to product %(lot_product)s, not to "
                        "%(product)s.",
                        lot=record.component_lot_id.display_name,
                        lot_product=record.component_lot_id.product_id.display_name,
                        product=product.display_name,
                    )
                )
