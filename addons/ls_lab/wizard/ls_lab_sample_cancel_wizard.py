# Part of the Life Sciences Suite. See LICENSE file for full copyright and licensing details.
"""Wizard collecting a mandatory reason before a sample is cancelled."""

from odoo import fields, models
from odoo.exceptions import UserError

CANCELLABLE_SAMPLE_STATES = (
    "received",
    "in_progress",
    "testing",
    "results_recorded",
    "reviewed",
)


class LsLabSampleCancelWizard(models.TransientModel):
    """Collects the cancellation reason required by business rule BRU-26."""

    _name = "ls.lab.sample_cancel_wizard"
    _description = "Laboratory Sample Cancellation Wizard"

    sample_id = fields.Many2one(comodel_name="ls.lab.sample", required=True,
                                readonly=True,)
    sample_state = fields.Selection(
        related="sample_id.state", string="Current Status", readonly=True
    )
    reason = fields.Text(
        string="Cancellation Reason",
        required=True,
        help="Recorded on the sample so that the cancellation is never "
             "undocumented.",
    )

    def action_confirm(self):
        """Cancel the sample and record who cancelled it and why."""
        self.ensure_one()
        sample = self.sample_id
        if sample.state not in CANCELLABLE_SAMPLE_STATES:
            raise UserError(
                self.env._(
                    "Sample '%(sample)s' is in status '%(state)s' and can no "
                    "longer be cancelled.",
                    sample=sample.name,
                    state=sample.state,
                )
            )
        sample.write({
            "state": "cancelled",
            "cancel_reason": self.reason,
            "cancelled_by_id": self.env.user.id,
        })
        sample.message_post(
            body=self.env._(
                "Sample cancelled. Reason: %(reason)s", reason=self.reason
            )
        )
        return {"type": "ir.actions.act_window_close"}
