# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Wizard that creates and runs a trend analysis."""

from odoo import fields, models
from odoo.exceptions import UserError

from ..models.constants import TREND_DEFAULT_CHANGE_THRESHOLD


class LsEnvTrendWizard(models.TransientModel):
    """Collect the scope of a trend analysis and run it."""

    _name = "ls.env.trend.wizard"
    _description = "Run Environmental Monitoring Trend Analysis"

    name = fields.Char(string="Analysis Name", required=True)
    date_from = fields.Date(string="From", required=True)
    date_to = fields.Date(
        string="To", required=True, default=fields.Date.context_today
    )
    area_ids = fields.Many2many(comodel_name="ls.env.area", string="Areas")
    sampling_point_ids = fields.Many2many(
        comodel_name="ls.env.sampling_point", string="Sampling Points"
    )
    parameter_ids = fields.Many2many(
        comodel_name="ls.env.parameter", string="Parameters"
    )
    change_threshold = fields.Float(
        string="Direction Threshold",
        digits=(16, 4),
        default=TREND_DEFAULT_CHANGE_THRESHOLD,
        help="Relative change between the earlier and later half of a series "
        "above which a direction is reported. Expressed as a ratio.",
    )

    def action_run(self):
        """Create the analysis record, compute it and open the result."""
        self.ensure_one()
        if self.date_from > self.date_to:
            raise UserError(
                self.env._("The end of the period must not precede its start.")
            )
        analysis = self.env["ls.env.trend"].create(
            {
                "name": self.name,
                "date_from": self.date_from,
                "date_to": self.date_to,
                "area_ids": [(6, 0, self.area_ids.ids)],
                "sampling_point_ids": [(6, 0, self.sampling_point_ids.ids)],
                "parameter_ids": [(6, 0, self.parameter_ids.ids)],
                "change_threshold": self.change_threshold,
            }
        )
        analysis.action_compute()
        return {
            "type": "ir.actions.act_window",
            "name": self.env._("Trend Analysis"),
            "res_model": "ls.env.trend",
            "res_id": analysis.id,
            "view_mode": "form",
            "target": "current",
        }
