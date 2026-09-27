# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Material consumption lines of a moulding run.

These lines are the traceability link between a moulded component and the
resin and masterbatch lots it was made from. They are a quality record: the
authoritative inventory movement remains the stock move of the manufacturing
order.
"""

from odoo import api, fields, models
from odoo.exceptions import ValidationError

from ..constants import MATERIAL_USABLE_STATES, QUANTITY_DIGITS


class LsMpInjectionMoldingMaterial(models.Model):
    """One material grade and lot consumed by a moulding run."""

    _name = "ls.mp.injection_molding.material"
    _description = "Medical Plastics Moulding Material Consumption"
    _check_company_auto = True
    _order = "run_id, id"

    run_id = fields.Many2one(
        comodel_name="ls.mp.injection_molding",
        string="Moulding Run",
        required=True,
        ondelete="cascade",
        index=True,
    )
    material_grade_id = fields.Many2one(comodel_name="ls.mp.material.grade", required=True,
                                        ondelete="restrict",
                                        index=True,)
    product_id = fields.Many2one(comodel_name="product.product", ondelete="restrict",
                                 help="Inventory product consumed, defaulted from the material grade.",)
    lot_id = fields.Many2one(
        comodel_name="stock.lot",
        string="Material Lot",
        ondelete="restrict",
        index=True,
        help="Supplier lot of resin or masterbatch consumed.",
        check_company=True,
    )
    supplier_lot_reference = fields.Char(help=(
            "Lot reference printed on the supplier packaging, when it is not "
            "registered as an inventory lot."),
    )
    quantity = fields.Float(
        string="Quantity Consumed",
        digits=QUANTITY_DIGITS,
        required=True,
    )
    quantity_uom = fields.Char(
        string="Unit",
        required=True,
        default="kg",
        help=(
            "Unit label recorded as free text, defaulted from the consumption "
            "unit configured on the material grade."
        ),
    )
    is_regrind = fields.Boolean(
        string="Regrind",
        help="The material consumed is reprocessed material rather than virgin resin.",
    )
    drug_contact = fields.Boolean(
        string="Direct Drug Contact",
        related="material_grade_id.drug_contact",
        store=True,
        readonly=True,
    )
    company_id = fields.Many2one(comodel_name="res.company", related="run_id.company_id",
                                 store=True,
                                 index=True,
                                 readonly=True,)

    _quantity_positive = models.Constraint(
        "CHECK(quantity > 0)",
        "The consumed quantity must be strictly positive.",
    )

    @api.onchange("material_grade_id")
    def _onchange_material_grade_id(self):
        """Default the product and consumption unit from the selected grade."""
        if self.material_grade_id:
            self.product_id = self.material_grade_id.product_id
            self.quantity_uom = self.material_grade_id.default_quantity_uom

    @api.depends("material_grade_id.code", "lot_id.name")
    def _compute_display_name(self):
        """Render the line as ``GRADE / LOT``."""
        for line in self:
            grade = line.material_grade_id.code or ""
            lot = line.lot_id.name or line.supplier_lot_reference or ""
            line.display_name = f"{grade} / {lot}" if lot else grade

    @api.constrains("material_grade_id")
    def _check_grade_is_usable(self):
        """Only qualified grades may be consumed."""
        for line in self:
            state = line.material_grade_id.qualification_state
            if state not in MATERIAL_USABLE_STATES:
                raise ValidationError(
                    self.env._(
                        "Material grade %(grade)s is not qualified and cannot be "
                        "consumed.",
                        grade=line.material_grade_id.display_name,
                    )
                )

    @api.constrains("material_grade_id", "run_id")
    def _check_grade_approved_for_component(self):
        """The grade must be approved for the component being moulded."""
        for line in self:
            component = line.run_id.component_id
            if component and line.material_grade_id not in component.material_grade_ids:
                raise ValidationError(
                    self.env._(
                        "Material grade %(grade)s is not approved for component "
                        "%(component)s.",
                        grade=line.material_grade_id.display_name,
                        component=component.display_name,
                    )
                )

    @api.constrains("lot_id", "supplier_lot_reference", "drug_contact")
    def _check_lot_recorded_for_drug_contact(self):
        """Grades in direct drug contact must be traceable to a lot."""
        for line in self:
            if line.drug_contact and not (line.lot_id or line.supplier_lot_reference):
                raise ValidationError(
                    self.env._(
                        "Material grade %(grade)s is in direct drug contact and "
                        "requires a lot reference for traceability.",
                        grade=line.material_grade_id.display_name,
                    )
                )

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
