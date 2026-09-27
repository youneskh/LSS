# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Monitored parameter definition."""

from odoo import api, fields, models

from .constants import PARAMETER_TYPES, RESULT_TYPE_QUANTITATIVE, RESULT_TYPES


class LsEnvParameter(models.Model):
    """A measurable environmental characteristic.

    A parameter defines what is measured and how the value is expressed. It
    carries no acceptance criteria: thresholds are configured per sampling
    point on ``ls.env.limit`` so that the same parameter can be monitored
    against different criteria in different areas.
    """

    _name = "ls.env.parameter"
    _description = "Environmental Monitoring Parameter"
    _order = "sequence, name"

    name = fields.Char(
        string="Parameter",
        required=True,
        translate=True,
        help="Name of the measured characteristic.",
    )
    code = fields.Char(required=True,
                       help="Short unique code used in result tables and reports.",)
    sequence = fields.Integer(default=10)
    parameter_type = fields.Selection(selection=PARAMETER_TYPES, required=True,
                                      default="other",
                                      help="Classification used to group parameters in reports and to "
                                      "filter monitoring plans.",)
    result_type = fields.Selection(selection=RESULT_TYPES, required=True,
                                   default=RESULT_TYPE_QUANTITATIVE,
                                   help="Quantitative parameters record a numeric value evaluated "
                                   "against thresholds. Qualitative parameters record a pass or fail "
                                   "outcome.",)
    uom_label = fields.Char(
        string="Unit of Measure",
        help="Unit in which results for this parameter are expressed, for "
        "example a count per plate or a count per cubic metre. Recorded as "
        "free text so that units specific to environmental monitoring can be "
        "used without extending the general unit of measure configuration.",
    )
    decimal_precision = fields.Integer(
        string="Displayed Decimals",
        default=2,
        help="Number of decimal places shown for results of this parameter.",
    )
    incubation_required = fields.Boolean(
        string="Requires Incubation",
        help="Indicates that samples for this parameter are incubated before "
        "a result can be read. Used to distinguish microbiological "
        "parameters in the sample workflow.",
    )
    description = fields.Text(translate=True)
    active = fields.Boolean(default=True)
    company_id = fields.Many2one(comodel_name="res.company", required=True,
                                 default=lambda self: self.env.company,
                                 index=True,)

    _code_company_unique = models.Constraint(
        "UNIQUE(code, company_id)",
        "The parameter code must be unique per company.",
    )
    _decimal_precision_positive = models.Constraint(
        "CHECK(decimal_precision >= 0 AND decimal_precision <= 10)",
        "Displayed decimals must be between 0 and 10.",
    )

    @property
    def is_quantitative(self):
        """Return whether this parameter records a numeric value."""
        self.ensure_one()
        return self.result_type == RESULT_TYPE_QUANTITATIVE

    @api.depends("code", "name")
    def _compute_display_name(self):
        """Show the code alongside the parameter name."""
        for record in self:
            record.display_name = "[%s] %s" % (record.code or "", record.name or "")
