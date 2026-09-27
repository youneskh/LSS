# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Wizard used to record a justified change of device lifecycle status.

Status changes that affect market availability are the ones an inspector is
most likely to ask about, so this wizard forces a justification to be captured
at the moment of the change rather than reconstructed afterwards.
"""

from odoo import api, fields, models
from odoo.exceptions import UserError

from ..models import constants


class LsMdDeviceStateWizard(models.TransientModel):
    """Transient record collecting the target status and its justification."""

    _name = "ls.md.device.state.wizard"
    _description = "Medical Device Status Change Wizard"

    device_id = fields.Many2one(comodel_name="ls.md.device", required=True,
                                ondelete="cascade",)
    current_state = fields.Selection(
        selection=constants.DEVICE_STATE_SELECTION,
        string="Current Status",
        related="device_id.state",
        readonly=True,
    )
    target_state = fields.Selection(
        selection=constants.DEVICE_STATE_SELECTION,
        string="New Status",
        required=True,
    )
    reason = fields.Text(
        string="Justification",
        required=True,
        help="Justification recorded on the device and in its message history.",
    )
    effective_date = fields.Date(required=True,
                                 default=fields.Date.context_today,)

    @api.onchange("device_id")
    def _onchange_device_id(self):
        """Reset the target status when it is not reachable from the current one."""
        for wizard in self:
            allowed = constants.DEVICE_ALLOWED_TRANSITIONS.get(
                wizard.device_id.state, ()
            )
            if wizard.target_state not in allowed:
                wizard.target_state = allowed[0] if allowed else False

    def action_apply(self):
        """Apply the requested transition through the device business methods."""
        self.ensure_one()
        device = self.device_id
        allowed = constants.DEVICE_ALLOWED_TRANSITIONS.get(device.state, ())
        if self.target_state not in allowed:
            raise UserError(
                self.env._(
                    "Device '%(device)s' cannot move from status "
                    "'%(current)s' to status '%(target)s'.",
                    device=device.display_name,
                    current=dict(constants.DEVICE_STATE_SELECTION).get(device.state),
                    target=dict(constants.DEVICE_STATE_SELECTION).get(
                        self.target_state
                    ),
                )
            )
        handlers = {
            "development": device.action_start_development,
            "conformity_assessment": device.action_start_conformity_assessment,
            "on_market": (
                device.action_resume
                if device.state == "suspended"
                else device.action_place_on_market
            ),
            "suspended": device.action_suspend,
            "withdrawn": device.action_withdraw,
        }
        handler = handlers.get(self.target_state)
        if handler is None:
            raise UserError(
                self.env._(
                    "No transition is implemented towards status '%(target)s'.",
                    target=self.target_state,
                )
            )
        if self.target_state == "on_market" and device.state != "suspended":
            device.market_placement_date = self.effective_date
        if self.target_state == "withdrawn":
            device.market_withdrawal_date = self.effective_date
        handler()
        device.state_change_reason = self.reason
        device.message_post(
            body=self.env._(
                "Status change justification recorded: %(reason)s",
                reason=self.reason,
            )
        )
        return {"type": "ir.actions.act_window_close"}
