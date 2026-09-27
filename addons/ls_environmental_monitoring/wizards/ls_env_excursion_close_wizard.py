# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Wizard that records the justification for closing an excursion."""

from odoo import fields, models


class LsEnvExcursionCloseWizard(models.TransientModel):
    """Capture a mandatory justification before an excursion is closed."""

    _name = "ls.env.excursion.close.wizard"
    _description = "Close Environmental Monitoring Excursion"

    excursion_id = fields.Many2one(comodel_name="ls.env.excursion", required=True,
                                   ondelete="cascade",)
    justification = fields.Text(
        string="Closure Justification",
        required=True,
        help="Basis on which the excursion is considered resolved.",
    )

    def action_close(self):
        """Close the excursion with the supplied justification."""
        self.ensure_one()
        self.excursion_id.close(self.justification)
        return {"type": "ir.actions.act_window_close"}
