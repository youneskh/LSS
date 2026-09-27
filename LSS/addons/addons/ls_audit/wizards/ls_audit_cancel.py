# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Cancellation wizard.

Cancellation of a quality record is never silent: the wizard forces a written
justification, records it on the cancelled record and posts it to the record
message thread, so that the reason remains part of the traceable history.
"""

from odoo import _, api, fields, models
from odoo.exceptions import UserError

#: Models that can be cancelled through this wizard, mapped to the statuses
#: from which cancellation is refused because the record is already final.
CANCELLABLE_MODELS = {
    "ls.audit.program": ("closed", "cancelled"),
    "ls.audit.schedule": ("closed", "cancelled"),
    "ls.audit.finding": ("closed", "cancelled"),
    "ls.audit.report": ("issued", "cancelled"),
}


class LsAuditCancel(models.TransientModel):
    """Wizard capturing the justification of a cancellation."""

    _name = "ls.audit.cancel"
    _description = "Cancel Audit Record"

    res_model = fields.Selection(
        selection=[
            ("ls.audit.program", "Audit Programme"),
            ("ls.audit.schedule", "Audit"),
            ("ls.audit.finding", "Audit Finding"),
            ("ls.audit.report", "Audit Report"),
        ],
        string="Record Type",
        required=True,
        readonly=True,
        help="Model of the record being cancelled.",
    )
    res_id = fields.Integer(
        string="Record",
        required=True,
        readonly=True,
        help="Database identifier of the record being cancelled.",
    )
    record_name = fields.Char(
        string="Record Reference",
        compute="_compute_record_name",
        help="Reference of the record being cancelled.",
    )
    reason = fields.Text(
        string="Cancellation Reason",
        required=True,
        help="Justification for the cancellation. This text is written onto "
             "the record and posted to its message thread.",
    )

    @api.depends("res_model", "res_id")
    def _compute_record_name(self):
        """Resolve the display name of the targeted record."""
        for wizard in self:
            record = wizard._get_target_record(check_access=False)
            wizard.record_name = record.display_name if record else ""

    def _get_target_record(self, check_access=True):
        """Return the record targeted by the wizard.

        :param check_access: when ``True``, access rights are enforced by the
            ORM as usual; when ``False``, a missing record yields an empty
            recordset instead of an error.
        :return: the targeted recordset, possibly empty.
        :rtype: recordset
        :raise UserError: when the model is not cancellable.
        """
        self.ensure_one()
        if self.res_model not in CANCELLABLE_MODELS:
            raise UserError(
                _(
                    "Records of type '%(model)s' cannot be cancelled through "
                    "this wizard.",
                    model=self.res_model,
                )
            )
        record = self.env[self.res_model].browse(self.res_id)
        if not check_access:
            return record.exists()
        return record

    def action_cancel(self):
        """Cancel the targeted record and record the justification.

        :return: an action closing the wizard window.
        :rtype: dict
        :raise UserError: when the record no longer exists or has already
            reached a final status.
        """
        self.ensure_one()
        record = self._get_target_record()
        if not record.exists():
            raise UserError(
                _("The record to cancel no longer exists.")
            )
        forbidden_states = CANCELLABLE_MODELS[self.res_model]
        if record.state in forbidden_states:
            raise UserError(
                _(
                    "Record %(name)s is in status '%(state)s' and can no "
                    "longer be cancelled.",
                    name=record.display_name,
                    state=record.state,
                )
            )
        record.write(
            {"state": "cancelled", "cancellation_reason": self.reason}
        )
        record.message_post(
            body=_(
                "Cancelled by %(user)s. Reason: %(reason)s",
                user=self.env.user.name,
                reason=self.reason,
            )
        )
        return {"type": "ir.actions.act_window_close"}
