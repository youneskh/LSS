# Part of the Life Sciences Suite. See LICENSE file for full copyright and licensing details.
"""Signature-intent confirmation wizard.

IMPORTANT LIMITATION. This wizard records the identity of the signing user, a
UTC timestamp and the declared meaning of the signature. It does NOT
re-authenticate the user at the moment of signing, does not implement two
distinct identification components, and does not cryptographically bind the
signature to the record. FDA 21 CFR Part 11 compliance is NOT claimed for this
functionality. Organisations requiring Part 11 electronic signatures must
implement re-authentication at platform level and validate it.
"""

from odoo import api, fields, models
from odoo.exceptions import UserError

SIGNABLE_MODELS = ("ls.lab.sample", "ls.lab.coa")


class LsLabSignatureWizard(models.TransientModel):
    """Records signature intent before a controlled action is performed."""

    _name = "ls.lab.signature_wizard"
    _description = "Laboratory Signature Intent Wizard"

    res_model = fields.Char(string="Target Model", required=True, readonly=True)
    res_id = fields.Integer(string="Target Record", required=True, readonly=True)
    record_label = fields.Char(
        string="Record", compute="_compute_record_label", readonly=True
    )
    meaning = fields.Selection(
        selection=[
            ("reviewed", "Reviewed"),
            ("approved", "Approved"),
            ("issued", "Issued"),
            ("authorised", "Authorised"),
        ],
        string="Meaning Of Signature",
        required=True,
        help="The meaning attributed to this signature intent, recorded on the "
             "target record.",
    )
    limitation_notice = fields.Text(
        string="Limitation",
        readonly=True,
        default=lambda self: self._default_limitation_notice(),
    )
    acknowledged = fields.Boolean(
        string="I confirm this action",
        help="Confirms that the signing user intends to perform this action.",
    )

    def _default_limitation_notice(self):
        """Return the limitation text shown on the wizard."""
        return self.env._(
            "This confirmation records your user identity, the current "
            "timestamp and the meaning selected above. It does not "
            "re-authenticate you and is not an FDA 21 CFR Part 11 electronic "
            "signature. Your organisation's procedures determine the "
            "evidentiary weight of this record."
        )

    @api.depends("res_model", "res_id")
    def _compute_record_label(self):
        """Show the display name of the record being signed."""
        for wizard in self:
            if wizard.res_model and wizard.res_id:
                record = self.env[wizard.res_model].browse(wizard.res_id)
                wizard.record_label = record.display_name
            else:
                wizard.record_label = ""

    def action_confirm(self):
        """Record the signature intent and run the authorised action."""
        self.ensure_one()
        if not self.acknowledged:
            raise UserError(
                self.env._(
                    "Tick the confirmation box to record your signature intent."
                )
            )
        if self.res_model not in SIGNABLE_MODELS:
            raise UserError(
                self.env._(
                    "Model '%(model)s' does not support signature intent.",
                    model=self.res_model,
                )
            )
        record = self.env[self.res_model].browse(self.res_id)
        if not record.exists():
            raise UserError(
                self.env._("The record to be signed no longer exists.")
            )
        meaning_label = dict(
            self._fields["meaning"]._description_selection(self.env)
        ).get(self.meaning, self.meaning)
        record.action_signature_apply(meaning_label)
        return {"type": "ir.actions.act_window_close"}
