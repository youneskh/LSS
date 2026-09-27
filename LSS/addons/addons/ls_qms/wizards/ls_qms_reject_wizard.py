# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0.html).
"""Wizard returning a document under review to its author."""

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class LsQmsRejectWizard(models.TransientModel):
    """Collect the rejection reason before a document returns to draft."""

    _name = "ls.qms.reject.wizard"
    _description = "Reject a Quality Document"

    res_model = fields.Char(
        string="Document Model",
        required=True,
        readonly=True,
    )
    res_id = fields.Integer(
        string="Document Identifier",
        required=True,
        readonly=True,
    )
    document_name = fields.Char(
        string="Document",
        readonly=True,
    )
    reason = fields.Text(
        string="Rejection Reason",
        required=True,
        help="Reason communicated to the author and written to the message"
        " log of the document.",
    )

    @api.model
    def default_get(self, fields_list):
        """Read the rejected document from the action context.

        :param list fields_list: fields requested by the client.
        :rtype: dict
        """
        result = super().default_get(fields_list)
        model_name = self.env.context.get("active_model")
        active_id = self.env.context.get("active_id")
        if not model_name or not active_id:
            raise UserError(
                _("Open this wizard from a controlled document.")
            )
        allowed_models = self.env[
            "ls.qms.document.mixin"
        ]._ls_qms_document_models()
        if model_name not in allowed_models:
            raise UserError(
                _(
                    "Model %(model)s is not a controlled document of the "
                    "quality management system.",
                    model=model_name,
                )
            )
        document = self.env[model_name].browse(active_id)
        document.check_access("write")
        result.update(
            {
                "res_model": model_name,
                "res_id": active_id,
                "document_name": document.display_name,
            }
        )
        return result

    def action_reject(self):
        """Return the document to its author.

        :rtype: bool
        """
        self.ensure_one()
        document = self.env[self.res_model].browse(self.res_id)
        document.ls_qms_reject(self.reason)
        return {"type": "ir.actions.act_window_close"}
