# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Wizard used to upload a new version of a controlled document."""

from odoo import _, fields, models
from odoo.exceptions import UserError


class LsDocumentNewVersionWizard(models.TransientModel):
    """Collect the file and the change description of a new version."""

    _name = "ls.document.new.version.wizard"
    _description = "Life Sciences Document New Version Wizard"

    document_id = fields.Many2one(comodel_name="ls.document.document", required=True,
                                  ondelete="cascade",)
    document_state = fields.Selection(
        related="document_id.state",
        string="Document Status",
    )
    content = fields.Binary(
        string="File",
        required=True,
    )
    filename = fields.Char(
        string="File Name",
        required=True,
    )
    change_summary = fields.Text(
        string="Summary of Change",
        required=True,
    )
    change_reason = fields.Text(string="Reason for Change")

    def action_create_version(self):
        """Create the new version and return to the document form.

        :return: an ``ir.actions.act_window_close`` action.
        :raises UserError: when the document is not in the Draft status.
        """
        self.ensure_one()
        document = self.document_id
        if document.state != "draft":
            raise UserError(
                _(
                    "A new version can only be added while document "
                    "'%(reference)s' is in draft status. Start a revision "
                    "first.",
                    reference=document.reference,
                )
            )
        version = self.env["ls.document.version"].create(
            {
                "document_id": document.id,
                "content": self.content,
                "filename": self.filename,
                "change_summary": self.change_summary,
                "change_reason": self.change_reason,
            }
        )
        document.message_post(
            body=_(
                "Version %(version)s created: %(summary)s",
                version=version.version_number,
                summary=self.change_summary,
            )
        )
        return {"type": "ir.actions.act_window_close"}
