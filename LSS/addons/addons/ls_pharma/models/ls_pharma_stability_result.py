# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Analytical results recorded at a stability time point."""

from odoo import api, fields, models
from odoo.exceptions import ValidationError

RESULT_TYPES = [
    ("numeric", "Numeric"),
    ("text", "Text or Attribute"),
]


class LsPharmaStabilityResult(models.Model):
    """One analytical result obtained at a stability time point.

    ICH Q1A(R2) states that a significant change is a failure of the product
    to meet its specification.  The significant change flag is therefore
    computed from the conformity of the result and may then be confirmed or
    overridden by the analyst, because the guideline also defines
    product-specific significant change criteria, such as a change in
    dissolution or in physical attributes, that this module cannot evaluate
    on its own.
    """

    _name = "ls.pharma.stability.result"
    _description = "Stability Test Result"
    _order = "timepoint_id, sequence, id"

    sequence = fields.Integer(default=10)
    timepoint_id = fields.Many2one(
        comodel_name="ls.pharma.stability.timepoint",
        string="Time Point",
        required=True,
        ondelete="cascade",
        index=True,
    )
    company_id = fields.Many2one(comodel_name="res.company", related="timepoint_id.company_id",
                                 store=True,
                                 index=True,)
    study_id = fields.Many2one(comodel_name="ls.pharma.stability_study", related="timepoint_id.study_id",
                               store=True,
                               index=True,)
    name = fields.Char(string="Test", required=True)
    method_reference = fields.Char()
    result_type = fields.Selection(selection=RESULT_TYPES, required=True,
                                   default="numeric",)
    specification_text = fields.Char(string="Acceptance Criterion")
    specification_min = fields.Float(string="Minimum", digits=(16, 6))
    specification_max = fields.Float(string="Maximum", digits=(16, 6))
    has_minimum = fields.Boolean(string="Minimum Applies")
    has_maximum = fields.Boolean(string="Maximum Applies")
    result_value = fields.Float(string="Result", digits=(16, 6))
    result_text = fields.Char(string="Result (Text)")
    result_uom = fields.Char(string="Result Unit")
    is_conform = fields.Boolean(
        string="Conforms",
        compute="_compute_is_conform",
        store=True,
        readonly=False,
    )
    is_significant_change = fields.Boolean(
        string="Significant Change",
        help=(
            "Set when the result constitutes a significant change within the "
            "meaning of ICH Q1A(R2). A non-conforming result is proposed as a "
            "significant change; the analyst confirms or overrides the "
            "proposal."
        ),
    )
    tested_by_user_id = fields.Many2one(
        comodel_name="res.users", string="Tested By"
    )
    date_tested = fields.Date(string="Tested On")
    remark = fields.Text()

    @api.depends(
        "result_type",
        "result_value",
        "specification_min",
        "specification_max",
        "has_minimum",
        "has_maximum",
    )
    def _compute_is_conform(self):
        """Compute the conformity of a numeric result."""
        for result in self:
            if result.result_type != "numeric":
                continue
            conform = True
            if result.has_minimum and result.result_value < result.specification_min:
                conform = False
            if result.has_maximum and result.result_value > result.specification_max:
                conform = False
            result.is_conform = conform

    @api.onchange("is_conform")
    def _onchange_is_conform(self):
        """Propose a non-conforming result as a significant change."""
        for result in self:
            if not result.is_conform:
                result.is_significant_change = True

    @api.constrains(
        "has_minimum", "has_maximum", "specification_min", "specification_max"
    )
    def _check_specification_range(self):
        """Reject an acceptance range whose minimum exceeds its maximum."""
        for result in self:
            if (
                result.has_minimum
                and result.has_maximum
                and result.specification_min > result.specification_max
            ):
                raise ValidationError(
                    self.env._(
                        "The minimum of test %(name)s cannot exceed its "
                        "maximum.",
                        name=result.name,
                    )
                )
