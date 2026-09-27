# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Transient model collecting the mandatory justification of a decision."""

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class LsChangeControlDecisionWizard(models.TransientModel):
    """Collect the reason of a closure, rejection or cancellation.

    A single wizard serves the three decisions because the data collected and
    the confirmation pattern are identical. The decision itself is always
    delegated to the corresponding method of the change request, which keeps
    the workflow rules in a single place.
    """

    _name = "ls.change_control.decision_wizard"
    _description = "Change Control Decision Wizard"

    request_id = fields.Many2one(
        comodel_name="ls.change_control.request",
        string="Change Request",
        required=True,
        ondelete="cascade",
        readonly=True,
    )
    mode = fields.Selection(
        selection=[
            ("close", "Close"),
            ("reject", "Reject"),
            ("cancel", "Cancel"),
        ],
        string="Decision",
        required=True,
        readonly=True,
    )
    request_state = fields.Selection(
        related="request_id.state",
        string="Current Status",
        readonly=True,
    )
    reason = fields.Text(
        string="Justification",
        required=True,
        help="Justification of the decision. It is written on the change "
             "request and cannot be modified afterwards.",
    )

    @api.constrains("reason")
    def _check_reason_not_blank(self):
        """Reject a justification made only of whitespace."""
        for wizard in self:
            if not wizard.reason or not wizard.reason.strip():
                raise ValidationError(_("The justification cannot be empty."))

    def action_confirm(self):
        """Apply the decision to the change request."""
        self.ensure_one()
        if self.mode == "close":
            self.request_id.action_close(self.reason)
        elif self.mode == "reject":
            self.request_id.action_reject(self.reason)
        else:
            self.request_id.action_cancel(self.reason)
        return {"type": "ir.actions.act_window_close"}
