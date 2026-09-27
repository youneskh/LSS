# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Wizard collecting the information required to close a complaint."""

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


class LsComplaintCloseWizard(models.TransientModel):
    """Transient model used to close a complaint with a documented review."""

    _name = "ls.complaint.close.wizard"
    _description = "Close Complaint Wizard"

    complaint_id = fields.Many2one(comodel_name="ls.complaint", required=True,
                                   ondelete="cascade",)
    complaint_state = fields.Selection(
        related="complaint_id.state",
        string="Current Status",
        readonly=True,
    )
    owner_id = fields.Many2one(
        related="complaint_id.owner_id",
        string="Responsible",
        readonly=True,
    )
    closure_summary = fields.Text(required=True)
    reviewer_id = fields.Many2one(comodel_name="res.users", required=True,
                                  help="User performing the closure review. Must differ from the "
                                  "responsible user.",)
    effectiveness_confirmed = fields.Boolean(
        string="Resolution Effectiveness Confirmed",
        help="Confirms that the resolution actions were verified as effective.",
    )
    customer_notified = fields.Boolean(
        string="Complainant Informed",
    )

    @api.constrains("reviewer_id", "owner_id")
    def _check_reviewer(self):
        """The reviewer cannot be the responsible user."""
        for wizard in self:
            if wizard.reviewer_id and wizard.reviewer_id == wizard.owner_id:
                raise ValidationError(
                    _(
                        "The reviewer must be different from the responsible "
                        "user (segregation of duties)."
                    )
                )

    def action_confirm(self):
        """Apply the closure on the related complaint.

        :return: an action closing the wizard dialog
        :raises UserError: when the effectiveness confirmation is missing
        """
        self.ensure_one()
        if not self.effectiveness_confirmed:
            raise UserError(
                _(
                    "The effectiveness of the resolution must be confirmed "
                    "before the complaint can be closed."
                )
            )
        self.complaint_id.action_close(
            closure_summary=self.closure_summary,
            reviewer=self.reviewer_id,
            customer_notified=self.customer_notified,
        )
        return {"type": "ir.actions.act_window_close"}
