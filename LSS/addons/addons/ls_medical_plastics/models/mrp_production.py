# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Extension of the manufacturing order with moulding run visibility.

The manufacturing order remains the authoritative material and inventory
document. This extension only surfaces the moulding runs attached to it so
that a production supervisor can navigate from the order to the moulding
records without leaving the manufacturing application.
"""

from odoo import api, fields, models


class MrpProduction(models.Model):
    """Add moulding run navigation to manufacturing orders."""

    _inherit = "mrp.production"

    mp_run_ids = fields.One2many(
        comodel_name="ls.mp.injection_molding",
        inverse_name="production_id",
        string="Moulding Runs",
    )
    mp_run_count = fields.Integer(
        string="Moulding Run Count",
        compute="_compute_mp_run_count",
    )
    mp_open_run_count = fields.Integer(
        string="Open Moulding Runs",
        compute="_compute_mp_run_count",
    )

    @api.depends("mp_run_ids", "mp_run_ids.state")
    def _compute_mp_run_count(self):
        """Count attached moulding runs and those not yet closed."""
        for production in self:
            production.mp_run_count = len(production.mp_run_ids)
            production.mp_open_run_count = len(
                production.mp_run_ids.filtered(
                    lambda run: run.state not in ("closed", "cancelled")
                )
            )

    def action_view_mp_runs(self):
        """Open the moulding runs attached to this manufacturing order."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": self.env._("Moulding Runs"),
            "res_model": "ls.mp.injection_molding",
            "view_mode": "list,form",
            "domain": [("production_id", "=", self.id)],
            "context": {"default_production_id": self.id},
        }
