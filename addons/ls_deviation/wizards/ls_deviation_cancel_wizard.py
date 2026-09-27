# Copyright 2026 Life Sciences Suite
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Wizard cancelling a deviation or sending it back one workflow step."""

from odoo import _, fields, models
from odoo.exceptions import UserError

from ..models.ls_deviation import STATE_SELECTION

#: Mapping used to determine the previous state for a send-back.
PREVIOUS_STATE = {
    "assessed": "reported",
    "investigation": "assessed",
    "disposition": "investigation",
    "capa_required": "disposition",
}


class LsDeviationCancelWizard(models.TransientModel):
    """Capture the mandatory reason for a cancellation or a send-back."""

    _name = "ls.deviation.cancel.wizard"
    _description = "Cancel or Send Back Deviation Wizard"

    deviation_id = fields.Many2one(
        comodel_name="ls.deviation",
        required=True,
        ondelete="cascade",
    )
    mode = fields.Selection(
        selection=[("cancel", "Cancel"), ("send_back", "Send Back")],
        required=True,
        default="cancel",
    )
    reason = fields.Text(required=True)

    def action_confirm(self):
        """Apply the cancellation or the send-back transition."""
        self.ensure_one()
        deviation = self.deviation_id
        if self.mode == "cancel":
            deviation.write({"cancel_reason": self.reason})
            deviation._apply_transition("cancelled", self.reason)
            return {"type": "ir.actions.act_window_close"}

        target = PREVIOUS_STATE.get(deviation.state)
        if not target:
            state_labels = dict(STATE_SELECTION)
            raise UserError(
                _(
                    "Deviation %(ref)s is %(state)s and cannot be sent back.",
                    ref=deviation.name,
                    state=state_labels.get(deviation.state, deviation.state),
                )
            )
        deviation._apply_transition(target, self.reason)
        return {"type": "ir.actions.act_window_close"}
