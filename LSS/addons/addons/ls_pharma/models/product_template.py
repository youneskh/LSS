# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Pharmaceutical attributes added to the product template."""

from odoo import api, fields, models
from odoo.exceptions import ValidationError

from .. import gs1
from ..constants import DOSAGE_FORMS


class ProductTemplate(models.Model):
    """Pharmaceutical attributes of a product.

    The attributes are added to the product template rather than to a
    separate model so that they follow the product through the existing
    inventory and manufacturing applications without any further mapping.
    """

    _inherit = "product.template"

    is_pharmaceutical = fields.Boolean(
        string="Pharmaceutical Product",
        help=(
            "Marks a product that is subject to the pharmaceutical controls "
            "of this module."
        ),
    )
    pharma_dosage_form = fields.Selection(
        selection=DOSAGE_FORMS,
        string="Dosage Form",
    )
    pharma_strength = fields.Char(
        string="Strength",
        help="Strength as declared on the approved product information.",
    )
    pharma_gtin14 = fields.Char(
        string="Product Code (GTIN-14)",
        help=(
            "Product code used as GS1 Application Identifier (01) when "
            "serialised units are generated for this product."
        ),
    )
    pharma_national_number = fields.Char(
        string="National Reimbursement Number",
        help=(
            "National reimbursement or identification number required by the "
            "Member State of destination, where one is required."
        ),
    )
    pharma_marketing_auth_number = fields.Char(
        string="Marketing Authorisation Number",
    )
    pharma_marketing_auth_holder_id = fields.Many2one(
        comodel_name="res.partner",
        string="Marketing Authorisation Holder",
    )
    pharma_shelf_life_months = fields.Integer(
        string="Shelf Life (Months)",
        help="Approved shelf life, used to default the expiry date of a batch.",
    )
    pharma_storage_condition = fields.Char(
        string="Storage Condition",
        help="Storage condition as declared on the approved product information.",
    )
    pharma_requires_serialization = fields.Boolean(
        string="Requires Serialisation",
        help=(
            "Marks a product whose saleable units must carry a unique "
            "identifier."
        ),
    )
    pharma_theoretical_yield_qty = fields.Float(
        string="Theoretical Yield",
        digits="Product Unit of Measure",
        help="Theoretical yield of one standard batch of this product.",
    )
    pharma_yield_min_percentage = fields.Float(
        string="Minimum Yield (%)",
        digits=(16, 2),
        help=(
            "Lower percentage of theoretical yield beyond which "
            "21 CFR 211.192 requires an investigation. The value is a "
            "percentage between 0 and 100."
        ),
    )
    pharma_yield_max_percentage = fields.Float(
        string="Maximum Yield (%)",
        digits=(16, 2),
        help=(
            "Upper percentage of theoretical yield beyond which "
            "21 CFR 211.192 requires an investigation. The value is a "
            "percentage between 0 and 100."
        ),
    )

    @api.constrains("pharma_gtin14")
    def _check_pharma_gtin14(self):
        """Reject a product code that is not a valid GTIN-14."""
        for template in self:
            if template.pharma_gtin14 and not gs1.is_valid_gtin14(
                template.pharma_gtin14
            ):
                raise ValidationError(
                    self.env._(
                        "The product code %(gtin)s of %(name)s is not a valid "
                        "GTIN-14.",
                        gtin=template.pharma_gtin14,
                        name=template.name,
                    )
                )

    @api.constrains("pharma_yield_min_percentage", "pharma_yield_max_percentage")
    def _check_pharma_yield_limits(self):
        """Reject yield limits that cannot describe an acceptance range."""
        for template in self:
            minimum = template.pharma_yield_min_percentage
            maximum = template.pharma_yield_max_percentage
            if minimum < 0.0 or maximum < 0.0:
                raise ValidationError(
                    self.env._("Yield limits cannot be negative.")
                )
            if minimum and maximum and minimum > maximum:
                raise ValidationError(
                    self.env._(
                        "The minimum yield of %(name)s cannot exceed its "
                        "maximum yield.",
                        name=template.name,
                    )
                )

    @api.constrains("pharma_shelf_life_months")
    def _check_pharma_shelf_life(self):
        """Reject a negative shelf life."""
        for template in self:
            if template.pharma_shelf_life_months < 0:
                raise ValidationError(
                    self.env._("The shelf life cannot be negative.")
                )

    @api.constrains(
        "pharma_requires_serialization", "pharma_gtin14", "is_pharmaceutical"
    )
    def _check_serialization_requirements(self):
        """Require a product code on a product that must be serialised."""
        for template in self:
            if template.pharma_requires_serialization and not template.pharma_gtin14:
                raise ValidationError(
                    self.env._(
                        "Product %(name)s requires serialisation and must "
                        "therefore carry a product code.",
                        name=template.name,
                    )
                )
