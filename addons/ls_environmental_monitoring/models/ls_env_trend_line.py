# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Trend analysis line."""

from odoo import fields, models

from .constants import TREND_DIRECTION_INSUFFICIENT, TREND_DIRECTIONS


class LsEnvTrendLine(models.Model):
    """Aggregated figures for one sampling point and parameter.

    Each statistic is paired with an availability flag. A statistic that is
    undefined for the underlying data, such as a standard deviation over a
    single value, is reported as unavailable rather than as zero, so that the
    reader is not shown a number the data does not support.
    """

    _name = "ls.env.trend.line"
    _description = "Environmental Monitoring Trend Line"
    _order = "trend_id, sampling_point_id, parameter_id"

    trend_id = fields.Many2one(
        comodel_name="ls.env.trend",
        string="Analysis",
        required=True,
        index=True,
        ondelete="cascade",
    )
    sampling_point_id = fields.Many2one(comodel_name="ls.env.sampling_point", required=True,
                                        index=True,
                                        ondelete="restrict",)
    area_id = fields.Many2one(comodel_name="ls.env.area", related="sampling_point_id.area_id",
                              store=True,)
    parameter_id = fields.Many2one(comodel_name="ls.env.parameter", required=True,
                                   index=True,
                                   ondelete="restrict",)
    result_count = fields.Integer(string="Results", readonly=True)
    numeric_count = fields.Integer(string="Numeric Values", readonly=True)
    alert_count = fields.Integer(string="Alert Exceedances", readonly=True)
    action_count = fields.Integer(string="Action Exceedances", readonly=True)
    spec_count = fields.Integer(string="Specification Exceedances", readonly=True)
    exceedance_ratio = fields.Float(
        string="Exceedance Rate",
        digits=(16, 4),
        readonly=True,
        help="Proportion of results that breached any threshold, expressed as "
        "a ratio between zero and one.",
    )
    value_min = fields.Float(string="Minimum", digits=(16, 4), readonly=True)
    value_min_available = fields.Boolean(readonly=True)
    value_max = fields.Float(string="Maximum", digits=(16, 4), readonly=True)
    value_max_available = fields.Boolean(readonly=True)
    value_mean = fields.Float(string="Mean", digits=(16, 4), readonly=True)
    value_mean_available = fields.Boolean(readonly=True)
    value_median = fields.Float(string="Median", digits=(16, 4), readonly=True)
    value_median_available = fields.Boolean(readonly=True)
    value_stdev = fields.Float(
        string="Standard Deviation", digits=(16, 4), readonly=True
    )
    value_stdev_available = fields.Boolean(readonly=True)
    direction = fields.Selection(selection=TREND_DIRECTIONS, default=TREND_DIRECTION_INSUFFICIENT,
                                 readonly=True,
                                 help="Descriptive comparison of the later half of the series with the "
                                 "earlier half. Not a test of statistical significance.",)
    company_id = fields.Many2one(comodel_name="res.company", related="trend_id.company_id",
                                 store=True,
                                 index=True,)

    _trend_point_parameter_unique = models.Constraint(
        "UNIQUE(trend_id, sampling_point_id, parameter_id)",
        "An analysis may contain only one line per sampling point and parameter.",
    )
    _counts_not_negative = models.Constraint(
        "CHECK(result_count >= 0 AND alert_count >= 0 AND action_count >= 0 "
        "AND spec_count >= 0)",
        "Result counts must not be negative.",
    )
