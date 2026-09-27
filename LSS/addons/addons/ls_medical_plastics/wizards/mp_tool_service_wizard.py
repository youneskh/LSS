# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Wizard used to return a moulding tool to service after maintenance.

Returning a tool to production is a controlled step: the cavity register must
be confirmed, and where the intervention required requalification the tool
cannot re-enter service until the qualification date has been updated.
"""

from odoo import api, fields, models
from odoo.exceptions import ValidationError

from ..constants import TOOL_PRODUCTION_STATE


class LsMpToolServiceWizard(models.TransientModel):
    """Confirm the conditions for returning a tool to production."""

    _name = "ls.mp.tool.service.wizard"
    _description = "Return Moulding Tool to Service"

    tool_id = fields.Many2one(comodel_name="ls.mp.tool", required=True,
                              ondelete="cascade",)
    tool_state = fields.Selection(
        related="tool_id.state", string="Current Status", readonly=True
    )
    cavity_ids = fields.Many2many(
        comodel_name="ls.mp.tool.cavity",
        relation="ls_mp_service_wizard_cavity_rel",
        column1="wizard_id",
        column2="cavity_id",
        string="Cavities Confirmed Active",
    )
    blocked_cavity_ids = fields.Many2many(
        comodel_name="ls.mp.tool.cavity",
        relation="ls_mp_service_wizard_blocked_rel",
        column1="wizard_id",
        column2="cavity_id",
        string="Cavities Remaining Blocked",
        readonly=True,
    )
    requalification_performed = fields.Boolean()
    qualification_date = fields.Date(default=fields.Date.context_today,
                                     help="Date of the qualification or requalification supporting the return.",)
    reset_maintenance_baseline = fields.Boolean(default=True,
                                                help="Set the shots-since-maintenance baseline to the current shot count.",)
    confirmation_note = fields.Text()

    @api.onchange("tool_id")
    def _onchange_tool_id(self):
        """Pre-select the currently active cavities of the tool."""
        if not self.tool_id:
            return
        cavities = self.tool_id.cavity_ids
        self.cavity_ids = cavities.filtered(lambda cavity: cavity.state == "active")
        self.blocked_cavity_ids = cavities.filtered(
            lambda cavity: cavity.state == "blocked"
        )

    def action_return_to_service(self):
        """Return the tool to production after validating the conditions.

        :return: an action closing the wizard window.
        :rtype: dict
        """
        self.ensure_one()
        tool = self.tool_id
        if tool.state not in ("maintenance", "quarantined"):
            raise ValidationError(
                self.env._(
                    "Tool %(tool)s is in status %(state)s and is not awaiting return "
                    "to service.",
                    tool=tool.display_name,
                    state=tool.state,
                )
            )
        if not self.cavity_ids:
            raise ValidationError(
                self.env._(
                    "At least one cavity must be confirmed active to return tool "
                    "%(tool)s to service.",
                    tool=tool.display_name,
                )
            )
        if tool.state == "quarantined" and not self.requalification_performed:
            raise ValidationError(
                self.env._(
                    "Tool %(tool)s is quarantined and requires a recorded "
                    "requalification before returning to service.",
                    tool=tool.display_name,
                )
            )
        if self.requalification_performed and not self.qualification_date:
            raise ValidationError(
                self.env._("A qualification date is required to record requalification.")
            )

        self.cavity_ids.filtered(lambda cavity: cavity.state == "blocked").action_unblock()

        tool_values = {"state": TOOL_PRODUCTION_STATE}
        if self.requalification_performed:
            tool_values["qualification_date"] = self.qualification_date
        if self.reset_maintenance_baseline:
            tool_values["shot_count_at_last_maintenance"] = tool.total_shot_count
            tool_values["last_maintenance_date"] = fields.Date.context_today(self)
        tool.write(tool_values)
        tool.message_post(
            body=self.env._(
                "Tool returned to service with %(count)s active cavities. %(note)s",
                count=len(self.cavity_ids),
                note=self.confirmation_note or "",
            )
        )
        return {"type": "ir.actions.act_window_close"}
