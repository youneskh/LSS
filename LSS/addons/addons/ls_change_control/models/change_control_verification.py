# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Verification that an implemented change achieved its objective."""

from odoo import _, api, fields, models
from odoo.exceptions import AccessError, UserError


class LsChangeControlVerification(models.Model):
    """Effectiveness verification of an implemented change."""

    _name = "ls.change_control.verification"
    _description = "Change Control Effectiveness Verification"
    _inherit = ["mail.thread"]
    _order = "request_id, date_planned, id"

    request_id = fields.Many2one(
        comodel_name="ls.change_control.request",
        string="Change Request",
        required=True,
        ondelete="cascade",
        index=True,
    )
    company_id = fields.Many2one(comodel_name="res.company", related="request_id.company_id",
                                 store=True,
                                 index=True,)
    request_state = fields.Selection(
        related="request_id.state",
        string="Request Status",
        store=True,
        index=True,
    )
    name = fields.Char(
        string="Verification",
        required=True,
        help="Short description of what is verified.",
    )
    method = fields.Selection(
        selection=[
            ("document_review", "Document Review"),
            ("record_review", "Record Review"),
            ("data_trend_review", "Data Trend Review"),
            ("training_record_review", "Training Record Review"),
            ("physical_inspection", "Physical Inspection"),
            ("testing", "Testing"),
            ("internal_audit", "Internal Audit"),
        ],
        string="Verification Method",
        required=True,
    )
    verifier_id = fields.Many2one(comodel_name="res.users", required=True,
                                  tracking=True,
                                  domain="[('share', '=', False)]",
                                  )
    date_planned = fields.Date(
        string="Planned Date",
        required=True,
        tracking=True,
    )
    date_done = fields.Date(
        string="Verification Date",
        readonly=True,
        copy=False,
    )
    acceptance_criteria = fields.Text(required=True,
                                      help="Criteria defined before the verification is performed, against "
                                      "which effectiveness is judged.",)
    conclusion = fields.Text(help="Outcome of the verification against the acceptance criteria.",)
    result = fields.Selection(
        selection=[
            ("pending", "Pending"),
            ("effective", "Effective"),
            ("not_effective", "Not Effective"),
        ],
        default="pending",
        required=True,
        readonly=True,
        copy=False,
        tracking=True,
    )
    state = fields.Selection(
        selection=[
            ("draft", "Planned"),
            ("completed", "Completed"),
        ],
        string="Status",
        default="draft",
        required=True,
        readonly=True,
        copy=False,
        tracking=True,
    )
    follow_up_required = fields.Boolean(
        string="Follow-up Required",
        help="A corrective action is required because the change was not "
             "effective. The corrective action itself is managed outside "
             "this module.",
    )
    follow_up_reference = fields.Char(
        string="Follow-up Reference",
        help="Reference of the corrective action record opened as a "
             "consequence of the verification.",
    )
    completed_by_id = fields.Many2one(comodel_name="res.users", readonly=True,
                                      copy=False,)

    @api.depends("name", "request_id")
    def _compute_display_name(self):
        """Show the request reference and the verification name."""
        for verification in self:
            verification.display_name = "%s / %s" % (
                verification.request_id.name or "",
                verification.name or "",
            )

    def write(self, vals):
        """Protect the workflow fields and freeze completed verifications."""
        if not self.env.su:
            protected = {
                "state",
                "result",
                "date_done",
                "completed_by_id",
            }
            forbidden = sorted(set(vals) & protected)
            if forbidden:
                raise AccessError(
                    _(
                        "The following fields are maintained by the "
                        "verification workflow and cannot be written "
                        "directly: %(fields)s.",
                        fields=", ".join(forbidden),
                    )
                )
            completed = self.filtered(lambda v: v.state == "completed")
            if completed:
                raise UserError(
                    _(
                        "Verification %(name)s is completed and can no "
                        "longer be modified.",
                        name=completed[0].display_name,
                    )
                )
        return super().write(vals)

    @api.ondelete(at_uninstall=False)
    def _ls_unlink_check_ls_change_control_verification(self):
        """Forbid the deletion of a completed verification."""
        completed = self.filtered(lambda v: v.state == "completed")
        if completed:
            raise UserError(
                _(
                    "Verification %(name)s is completed and cannot be "
                    "deleted.",
                    name=completed[0].display_name,
                )
            )

    def _check_can_complete(self, result):
        """Validate that the verification may be completed with this result.

        :param result: ``effective`` or ``not_effective``.
        """
        is_manager = self.env.user.has_group(
            "ls_change_control.group_ls_change_control_manager"
        )
        for verification in self:
            if verification.state == "completed":
                raise UserError(
                    _("Verification %(name)s is already completed.",
                      name=verification.display_name)
                )
            if verification.request_state != "implementation":
                raise UserError(
                    _(
                        "Verifications can only be completed while request "
                        "%(name)s is in the Implementation state.",
                        name=verification.request_id.name,
                    )
                )
            if verification.verifier_id != self.env.user and not is_manager:
                raise AccessError(
                    _(
                        "Only %(user)s or a Change Control Manager may "
                        "complete verification %(name)s.",
                        user=verification.verifier_id.name,
                        name=verification.display_name,
                    )
                )
            if not verification.conclusion or not verification.conclusion.strip():
                raise UserError(
                    _(
                        "A conclusion is required before completing "
                        "verification %(name)s.",
                        name=verification.display_name,
                    )
                )
            if result == "not_effective" and not verification.follow_up_required:
                raise UserError(
                    _(
                        "Verification %(name)s concludes that the change is "
                        "not effective. A follow-up must be requested.",
                        name=verification.display_name,
                    )
                )

    def _complete(self, result):
        """Write the completion values and trace the outcome.

        :param result: ``effective`` or ``not_effective``.
        """
        self._check_can_complete(result)
        self.sudo().write(
            {
                "state": "completed",
                "result": result,
                "date_done": fields.Date.context_today(self),
                "completed_by_id": self.env.user.id,
            }
        )
        labels = dict(self._fields["result"].selection)
        for verification in self:
            verification.request_id.message_post(
                body=_(
                    "Effectiveness verification '%(name)s' completed by "
                    "%(user)s with result '%(result)s'.",
                    name=verification.name,
                    user=self.env.user.name,
                    result=labels.get(result, result),
                ),
                subtype_xmlid="mail.mt_note",
            )
        return True

    def action_complete_effective(self):
        """Complete the verification with an Effective result."""
        return self._complete("effective")

    def action_complete_not_effective(self):
        """Complete the verification with a Not Effective result."""
        return self._complete("not_effective")
