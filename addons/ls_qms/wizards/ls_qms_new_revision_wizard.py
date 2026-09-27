# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0.html).
"""Wizard creating the next revision of a published controlled document."""

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class LsQmsNewRevisionWizard(models.TransientModel):
    """Collect the reason for change before a new revision is created."""

    _name = "ls.qms.new.revision.wizard"
    _description = "Create a New Document Revision"

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
    reason_for_change = fields.Text(required=True,
                                    help="Justification recorded on the new revision and in the message"
                                    " log of the current one.",)
    date_effective = fields.Date(
        string="Planned Effective Date",
    )

    @api.model
    def default_get(self, fields_list):
        """Read the source document from the action context.

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

    def action_create_revision(self):
        """Create the revision and open it.

        :rtype: dict
        """
        self.ensure_one()
        document = self.env[self.res_model].browse(self.res_id)
        new_revision = document.create_new_revision(
            self.reason_for_change,
            date_effective=self.date_effective,
        )
        return {
            "type": "ir.actions.act_window",
            "name": _("New Revision"),
            "res_model": self.res_model,
            "res_id": new_revision.id,
            "view_mode": "form",
            "target": "current",
        }
