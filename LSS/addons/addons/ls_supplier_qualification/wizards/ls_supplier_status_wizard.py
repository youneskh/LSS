# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Wizard used to suspend, reinstate or disqualify a supplier."""
from odoo import _, api, fields, models
from odoo.exceptions import UserError

ACTION_SELECTION = [
    ("suspend", "Suspend"),
    ("reinstate", "Reinstate"),
    ("disqualify", "Disqualify"),
]

MEANING_BY_ACTION = {
    "suspend": "suspended",
    "reinstate": "reinstated",
    "disqualify": "disqualified",
}


class LsSupplierStatusWizard(models.TransientModel):
    """Collect the status change, its justification and its signature."""

    _name = "ls.supplier.status.wizard"
    _description = "Life Sciences Supplier Qualification Status Wizard"

    qualification_id = fields.Many2one(
        comodel_name="ls.supplier.qualification",
        required=True,
        ondelete="cascade",
        readonly=True,
    )
    partner_id = fields.Many2one(
        related="qualification_id.partner_id",
        readonly=True,
    )
    current_state = fields.Selection(
        related="qualification_id.state",
        readonly=True,
    )
    action_type = fields.Selection(
        selection=ACTION_SELECTION,
        string="Action",
        required=True,
        compute="_compute_action_type",
        store=True,
        precompute=True,
        readonly=False,
    )
    reason = fields.Text(
        string="Justification",
        required=True,
        help="Recorded on the dossier and verbatim in the signature log.",
    )
    signature_login = fields.Char(
        string="Confirm Your Login",
        required=True,
    )

    @api.depends("qualification_id")
    def _compute_action_type(self):
        """Propose the action that matches the current dossier status."""
        for wizard in self:
            if wizard.qualification_id.state == "suspended":
                wizard.action_type = "reinstate"
            else:
                wizard.action_type = "suspend"

    def action_confirm(self):
        """Validate the input and apply the status change."""
        self.ensure_one()
        if self.signature_login != self.env.user.login:
            raise UserError(
                _("The login you entered does not match the login of the "
                  "connected user.")
            )
        qualification = self.qualification_id
        if self.action_type == "suspend":
            if qualification.state not in ("approved", "conditional"):
                raise UserError(
                    _("Only an approved dossier can be suspended "
                      "(dossier %s).", qualification.name)
                )
            qualification.write({
                "state": "suspended",
                "suspension_reason": self.reason,
            })
            body = _("Qualification suspended: %s", self.reason)
        elif self.action_type == "reinstate":
            if qualification.state != "suspended":
                raise UserError(
                    _("Only a suspended dossier can be reinstated "
                      "(dossier %s).", qualification.name)
                )
            if (
                qualification.expiry_date
                and qualification.expiry_date <= fields.Date.context_today(self)
            ):
                raise UserError(
                    _("The approval of dossier %s has expired. Requalify the "
                      "supplier instead of reinstating it.",
                      qualification.name)
                )
            qualification.write({
                "state": (
                    "conditional" if qualification.approval_conditions
                    else "approved"
                ),
                "suspension_reason": False,
            })
            body = _("Qualification reinstated: %s", self.reason)
        else:
            if qualification.state == "disqualified":
                raise UserError(
                    _("Dossier %s is already disqualified.",
                      qualification.name)
                )
            qualification.write({
                "state": "disqualified",
                "disqualification_reason": self.reason,
            })
            body = _("Supplier disqualified: %s", self.reason)
        qualification.message_post(body=body)
        self.env["ls.supplier.signature"].sign(
            record=qualification,
            meaning=MEANING_BY_ACTION[self.action_type],
            reason=self.reason,
            login=self.signature_login,
            payload={
                "state": qualification.state,
                "expiry_date": qualification.expiry_date,
            },
        )
        return {"type": "ir.actions.act_window_close"}
