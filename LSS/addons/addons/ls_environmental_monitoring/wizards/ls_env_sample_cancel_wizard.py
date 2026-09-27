# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Wizard that records the reason for cancelling a sample."""

from odoo import fields, models


class LsEnvSampleCancelWizard(models.TransientModel):
    """Capture a mandatory reason before a sample is cancelled."""

    _name = "ls.env.sample.cancel.wizard"
    _description = "Cancel Environmental Monitoring Sample"

    sample_id = fields.Many2one(comodel_name="ls.env.sample", required=True,
                                ondelete="cascade",)
    reason = fields.Text(
        string="Reason for Cancellation",
        required=True,
        help="Explanation of why this scheduled sample was not taken or is "
        "being withdrawn. Retained on the sample record.",
    )

    def action_cancel(self):
        """Cancel the sample, passing the reason through the context."""
        self.ensure_one()
        self.sample_id.with_context(
            cancellation_reason=self.reason
        ).action_cancel()
        return {"type": "ir.actions.act_window_close"}
