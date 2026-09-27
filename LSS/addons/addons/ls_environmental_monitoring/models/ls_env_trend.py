# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Trend analysis run."""

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError

from .constants import (
    EVAL_ACTION,
    EVAL_ALERT,
    EVAL_SPEC,
    RESULT_TYPE_QUANTITATIVE,
    TREND_COMPUTED,
    TREND_DEFAULT_CHANGE_THRESHOLD,
    TREND_DRAFT,
    TREND_REVIEWED,
    TREND_STATES,
)
from .evaluation import exceedance_rate, summarise, trend_direction


class LsEnvTrend(models.Model):
    """A trend analysis over a defined period and scope.

    The analysis is descriptive. It reports counts, exceedance rates and
    summary statistics over the selected results, together with an indication
    of direction obtained by comparing the two halves of the series. It does
    not perform a statistical hypothesis test and makes no claim of
    significance.
    """

    _name = "ls.env.trend"
    _description = "Environmental Monitoring Trend Analysis"
    _inherit = ["mail.thread"]
    _order = "date_to desc, id desc"

    name = fields.Char(string="Analysis", required=True, tracking=True)
    date_from = fields.Date(string="From", required=True, tracking=True)
    date_to = fields.Date(string="To", required=True, tracking=True)
    area_ids = fields.Many2many(
        comodel_name="ls.env.area",
        string="Areas",
        help="Restrict the analysis to these areas. Leave empty for all.",
    )
    sampling_point_ids = fields.Many2many(
        comodel_name="ls.env.sampling_point",
        string="Sampling Points",
        help="Restrict the analysis to these points. Leave empty for all.",
    )
    parameter_ids = fields.Many2many(
        comodel_name="ls.env.parameter",
        string="Parameters",
        help="Restrict the analysis to these parameters. Leave empty for all.",
    )
    change_threshold = fields.Float(
        string="Direction Threshold",
        digits=(16, 4),
        default=TREND_DEFAULT_CHANGE_THRESHOLD,
        help="Relative change between the earlier and later half of a series, "
        "above which the series is reported as increasing or decreasing. "
        "Expressed as a ratio, so 0.20 corresponds to a change of one fifth. "
        "This is an operational setting, not a regulatory value.",
    )
    state = fields.Selection(
        selection=TREND_STATES,
        string="Status",
        default=TREND_DRAFT,
        required=True,
        readonly=True,
        copy=False,
        tracking=True,
    )
    line_ids = fields.One2many(
        comodel_name="ls.env.trend.line",
        inverse_name="trend_id",
        string="Trend Lines",
        readonly=True,
    )
    line_count = fields.Integer(string="Lines", compute="_compute_line_count")
    computed_by_id = fields.Many2one(comodel_name="res.users", readonly=True, copy=False)
    computed_datetime = fields.Datetime(
        string="Computed On", readonly=True, copy=False
    )
    reviewed_by_id = fields.Many2one(comodel_name="res.users", readonly=True, copy=False)
    review_datetime = fields.Datetime(string="Reviewed On", readonly=True, copy=False)
    conclusion = fields.Text(tracking=True,
                             help="Reviewer's interpretation of the figures and any action arising.",)
    company_id = fields.Many2one(comodel_name="res.company", required=True,
                                 default=lambda self: self.env.company,
                                 index=True,)

    _change_threshold_positive = models.Constraint(
        "CHECK(change_threshold >= 0)",
        "The direction threshold must not be negative.",
    )

    @api.depends("line_ids")
    def _compute_line_count(self):
        """Count the lines produced by each analysis."""
        for record in self:
            record.line_count = len(record.line_ids)

    @api.constrains("date_from", "date_to")
    def _check_period(self):
        """Reject a period whose end precedes its start."""
        for record in self:
            if record.date_from > record.date_to:
                raise ValidationError(
                    self.env._("The end of the period must not precede its start.")
                )

    def _result_domain(self):
        """Build the domain selecting the results in scope.

        Only results on approved samples are included, so that the analysis
        reflects released data rather than values still under review.
        """
        self.ensure_one()
        domain = [
            ("company_id", "=", self.company_id.id),
            ("sample_state", "=", "approved"),
            ("collection_datetime", ">=", fields.Datetime.to_datetime(self.date_from)),
            ("collection_datetime", "<=", fields.Datetime.to_datetime(self.date_to)),
        ]
        if self.sampling_point_ids:
            domain.append(("sampling_point_id", "in", self.sampling_point_ids.ids))
        elif self.area_ids:
            domain.append(("area_id", "child_of", self.area_ids.ids))
        if self.parameter_ids:
            domain.append(("parameter_id", "in", self.parameter_ids.ids))
        return domain

    def action_compute(self):
        """Recompute the analysis, replacing any previously produced lines."""
        line_model = self.env["ls.env.trend.line"]
        for record in self:
            if record.state == TREND_REVIEWED:
                raise UserError(
                    self.env._(
                        "A reviewed analysis cannot be recomputed. Create a new "
                        "analysis instead."
                    )
                )
            record.line_ids.unlink()
            results = self.env["ls.env.result"].search(
                record._result_domain(), order="collection_datetime asc"
            )
            grouped = {}
            for result in results:
                key = (result.sampling_point_id.id, result.parameter_id.id)
                grouped.setdefault(key, []).append(result)
            line_values = []
            for (point_id, parameter_id), group in grouped.items():
                line_values.append(
                    record._prepare_line(point_id, parameter_id, group)
                )
            if line_values:
                line_model.create(line_values)
            record.write(
                {
                    "state": TREND_COMPUTED,
                    "computed_by_id": self.env.user.id,
                    "computed_datetime": fields.Datetime.now(),
                }
            )
        return True

    def _prepare_line(self, point_id, parameter_id, results):
        """Build the values of one trend line.

        :param int point_id: sampling point identifier
        :param int parameter_id: parameter identifier
        :param results: results for that combination, oldest first
        :rtype: dict
        """
        self.ensure_one()
        total = len(results)
        alert_count = sum(1 for r in results if r.evaluation == EVAL_ALERT)
        action_count = sum(1 for r in results if r.evaluation == EVAL_ACTION)
        spec_count = sum(1 for r in results if r.evaluation == EVAL_SPEC)
        numeric_values = [
            r.value_numeric
            for r in results
            if r.result_type == RESULT_TYPE_QUANTITATIVE and r.value_set
        ]
        statistics = summarise(numeric_values)
        values = {
            "trend_id": self.id,
            "sampling_point_id": point_id,
            "parameter_id": parameter_id,
            "result_count": total,
            "alert_count": alert_count,
            "action_count": action_count,
            "spec_count": spec_count,
            "exceedance_ratio": exceedance_rate(
                total, alert_count + action_count + spec_count
            ),
            "numeric_count": statistics["count"],
            "direction": trend_direction(numeric_values, self.change_threshold),
        }
        for field_name, key in (
            ("value_min", "minimum"),
            ("value_max", "maximum"),
            ("value_mean", "mean"),
            ("value_median", "median"),
            ("value_stdev", "standard_deviation"),
        ):
            statistic = statistics[key]
            values[field_name] = statistic if statistic is not None else 0.0
            values["%s_available" % field_name] = statistic is not None
        return values

    def action_review(self):
        """Record review of the analysis and its conclusion."""
        for record in self:
            if record.state != TREND_COMPUTED:
                raise UserError(
                    self.env._("Only a computed analysis can be reviewed.")
                )
            if not record.conclusion:
                raise UserError(
                    self.env._(
                        "A conclusion must be recorded before the analysis is "
                        "marked as reviewed."
                    )
                )
            record.write(
                {
                    "state": TREND_REVIEWED,
                    "reviewed_by_id": self.env.user.id,
                    "review_datetime": fields.Datetime.now(),
                }
            )
        return True
