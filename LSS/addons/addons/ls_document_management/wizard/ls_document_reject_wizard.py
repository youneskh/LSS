# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Wizard capturing the mandatory reason when an approval is refused."""

from odoo import _, fields, models
from odoo.exceptions import UserError


class LsDocumentRejectWizard(models.TransientModel):
    """Collect the rejection reason of the current approver."""

    _name = "ls.document.reject.wizard"
    _description = "Life Sciences Document Rejection Wizard"

    document_id = fields.Many2one(comodel_name="ls.document.document", required=True,
                                  ondelete="cascade",)
    reason = fields.Text(
        string="Reason for Rejection",
        required=True,
    )

    def action_confirm_rejection(self):
        """Record the rejection on the approval of the current user.

        :return: an ``ir.actions.act_window_close`` action.
        :raises UserError: when the current user has no pending approval on
            the document.
        """
        self.ensure_one()
        document = self.document_id
        approval = document.approval_ids.filtered(
            lambda item: item.state == "pending"
            and item.approver_id == self.env.user
        )
        if not approval:
            raise UserError(
                _(
                    "You have no pending approval on document "
                    "'%(reference)s'.",
                    reference=document.reference,
                )
            )
        approval[0].write({"comment": self.reason})
        approval[0].action_reject()
        return {"type": "ir.actions.act_window_close"}
