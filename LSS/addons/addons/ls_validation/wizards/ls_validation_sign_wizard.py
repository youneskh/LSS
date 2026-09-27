# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Wizard capturing an electronic signature before a controlled transition.

The wizard re-authenticates the connected user, records the signature with its
meaning in the append-only signature log, and only then executes the callback
declared by the signed record. The callback name is validated against the
whitelist of the target model, so a forged context cannot execute an arbitrary
method.
"""

from odoo import _, api, fields, models
from odoo.exceptions import UserError

from ..models.ls_validation_signature import SIGNATURE_MEANINGS


class LsValidationSignWizard(models.TransientModel):
    """Transient model collecting the credentials and the reason of a signature."""

    _name = "ls.validation.sign.wizard"
    _description = "Validation Electronic Signature Wizard"

    res_model = fields.Char(string="Model", required=True, readonly=True)
    res_id = fields.Integer(string="Record", required=True, readonly=True)
    record_label = fields.Char(
        string="Record", compute="_compute_record_label", readonly=True
    )
    meaning = fields.Selection(
        selection=SIGNATURE_MEANINGS,
        string="Meaning of Signature",
        required=True,
        readonly=True,
    )
    callback = fields.Char(required=True, readonly=True)
    login = fields.Char(required=True,
                        default=lambda self: self.env.user.login,)
    password = fields.Char()
    password_required = fields.Boolean(default=lambda self: self.env[
            "ls.validation.signature.mixin"
        ]._ls_password_required(),
        readonly=True,
    )
    reason = fields.Char(string="Reason / Comment")

    @api.depends("res_model", "res_id")
    def _compute_record_label(self):
        """Resolve the display name of the record being signed."""
        for wizard in self:
            label = False
            if wizard.res_model and wizard.res_model in self.env and wizard.res_id:
                record = self.env[wizard.res_model].browse(wizard.res_id).exists()
                label = record.display_name if record else False
            wizard.record_label = label

    def _get_target_record(self):
        """Return the record being signed after checking it still exists."""
        self.ensure_one()
        if self.res_model not in self.env:
            raise UserError(_("The signed model no longer exists."))
        record = self.env[self.res_model].browse(self.res_id).exists()
        if not record:
            raise UserError(_("The record to sign no longer exists."))
        if not hasattr(record, "_ls_create_signature"):
            raise UserError(
                _("Model %s does not support electronic signatures.")
                % self.res_model
            )
        return record

    def action_sign(self):
        """Verify the credentials, record the signature and run the callback.

        Access rights and record rules are enforced by the ORM when the
        callback writes on the record, so no version specific access check API
        is called here.

        :return: the result of the callback, usually ``True``.
        :raise ValidationError: when the credentials are not valid.
        :raise UserError: when the callback is not whitelisted by the model.
        """
        self.ensure_one()
        record = self._get_target_record()
        record._ls_verify_credentials(self.login, self.password)
        record._ls_create_signature(meaning=self.meaning, reason=self.reason)
        return record._ls_execute_signed_callback(self.callback)
