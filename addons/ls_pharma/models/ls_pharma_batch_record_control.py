# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""In-process and laboratory control results of a batch record."""

from odoo import api, fields, models
from odoo.exceptions import ValidationError

CONTROL_TYPES = [
    ("in_process", "In-Process Control"),
    ("laboratory", "Laboratory Control"),
]

RESULT_TYPES = [
    ("numeric", "Numeric"),
    ("text", "Text or Attribute"),
]


class LsPharmaBatchRecordControl(models.Model):
    """An in-process or laboratory control result.

    21 CFR 211.188(b)(5) requires that in-process and laboratory control
    results be documented in the batch production and control record.
    21 CFR 211.165 requires that acceptance criteria be adequate to support
    the release of the product for distribution; conformity of each control
    against its acceptance criterion is therefore computed and stored.
    """

    _name = "ls.pharma.batch_record.control"
    _description = "Batch Record Control Result"
    _order = "record_id, sequence, id"

    sequence = fields.Integer(default=10)
    record_id = fields.Many2one(
        comodel_name="ls.pharma.batch_record",
        string="Batch Record",
        required=True,
        ondelete="cascade",
        index=True,
    )
    company_id = fields.Many2one(comodel_name="res.company", related="record_id.company_id",
                                 store=True,
                                 index=True,)
    name = fields.Char(string="Test", required=True)
    control_type = fields.Selection(selection=CONTROL_TYPES, required=True,
                                    default="in_process",)
    method_reference = fields.Char(help="Identifier of the approved analytical or in-process method applied.",)
    result_type = fields.Selection(selection=RESULT_TYPES, required=True,
                                   default="numeric",)
    specification_text = fields.Char(
        string="Acceptance Criterion",
        help="Acceptance criterion as written in the approved specification.",
    )
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
        help=(
            "Conformity of the result against its acceptance criterion. For a "
            "numeric result the value is computed from the minimum and "
            "maximum; for a textual result it is set manually by the analyst."
        ),
    )
    performed_by_user_id = fields.Many2one(
        comodel_name="res.users", string="Performed By"
    )
    date_performed = fields.Datetime()
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
        """Compute the conformity of a numeric result.

        A textual result is left untouched so that the manual value entered by
        the analyst is preserved.
        """
        for control in self:
            if control.result_type != "numeric":
                continue
            conform = True
            if control.has_minimum and control.result_value < control.specification_min:
                conform = False
            if control.has_maximum and control.result_value > control.specification_max:
                conform = False
            control.is_conform = conform

    @api.constrains(
        "has_minimum", "has_maximum", "specification_min", "specification_max"
    )
    def _check_specification_range(self):
        """Reject an acceptance range whose minimum exceeds its maximum."""
        for control in self:
            if (
                control.has_minimum
                and control.has_maximum
                and control.specification_min > control.specification_max
            ):
                raise ValidationError(
                    self.env._(
                        "The minimum of test %(name)s cannot exceed its "
                        "maximum.",
                        name=control.name,
                    )
                )

    @api.constrains("result_type", "result_text")
    def _check_textual_result(self):
        """Require a value for a textual result that has been attributed."""
        for control in self:
            if (
                control.result_type == "text"
                and control.date_performed
                and not control.result_text
            ):
                raise ValidationError(
                    self.env._(
                        "Test %(name)s has been performed but carries no "
                        "result.",
                        name=control.name,
                    )
                )
