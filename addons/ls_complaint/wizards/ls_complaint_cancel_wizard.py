# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Wizard collecting the justification required to cancel a complaint."""

from odoo import fields, models


class LsComplaintCancelWizard(models.TransientModel):
    """Transient model used to cancel a complaint with a documented reason."""

    _name = "ls.complaint.cancel.wizard"
    _description = "Cancel Complaint Wizard"

    complaint_id = fields.Many2one(comodel_name="ls.complaint", required=True,
                                   ondelete="cascade",)
    reason = fields.Text(
        string="Cancellation Reason",
        required=True,
    )

    def action_confirm(self):
        """Apply the cancellation on the related complaint.

        :return: an action closing the wizard dialog
        """
        self.ensure_one()
        self.complaint_id.action_cancel(reason=self.reason)
        return {"type": "ir.actions.act_window_close"}
