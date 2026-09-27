# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Approval of a change request by a named function."""

from odoo import _, api, fields, models
from odoo.exceptions import AccessError, UserError

from .change_control_approval_template import APPROVAL_ROLES


class LsChangeControlApproval(models.Model):
    """A decision that one function must take on a change request.

    Electronic signature
    --------------------
    The module records the identity of the approver, the date and time in
    UTC, the meaning of the decision and the decision comment, and makes the
    record immutable once the decision is taken.

    It does not implement re-authentication of the approver at the moment of
    signing. In the architecture of the Life Sciences Suite, binding
    electronic signatures are the responsibility of the ``ls_electronic_
    signature`` module. The method ``_apply_signature`` is the documented
    extension point where that module plugs its own signing procedure.
    """

    _name = "ls.change_control.approval"
    _description = "Change Control Approval"
    _inherit = ["mail.thread"]
    _order = "request_id, sequence, id"

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
    sequence = fields.Integer(default=10,)
    approval_role = fields.Selection(selection=APPROVAL_ROLES, required=True,
                                     help="Function that must take the decision.",)
    user_id = fields.Many2one(
        comodel_name="res.users",
        string="Approver",
        tracking=True,
        domain="[('share', '=', False)]",
        help="User who must take the decision. It must be assigned before "
             "the impact assessment starts.",
    )
    mandatory = fields.Boolean(default=True,
                               help="A mandatory approval blocks the transition to Approved until "
                               "it is granted.",)
    state = fields.Selection(
        selection=[
            ("pending", "Pending"),
            ("approved", "Approved"),
            ("rejected", "Rejected"),
        ],
        string="Decision",
        default="pending",
        required=True,
        readonly=True,
        copy=False,
        tracking=True,
    )
    signature_meaning = fields.Char(
        string="Meaning of Signature",
        readonly=True,
        copy=False,
        help="Meaning associated with the recorded decision, stored with the "
             "decision itself so that the record remains self-explanatory.",
    )
    comment = fields.Text(help="Comment of the approver. It is mandatory for a rejection.",)
    date_requested = fields.Date(
        string="Requested On",
        readonly=True,
        copy=False,
        help="Date on which the approval was requested, used by the reminder "
             "scheduled action.",
    )
    date_decision = fields.Datetime(
        string="Decision Date",
        readonly=True,
        copy=False,
        help="Date and time of the decision, in UTC.",
    )
    decided_by_id = fields.Many2one(comodel_name="res.users", readonly=True,
                                    copy=False,
                                    help="User who actually recorded the decision.",)
    date_reminder = fields.Date(
        string="Last Reminder",
        readonly=True,
        copy=False,
    )

    _role_uniq_per_request = models.Constraint(
        "UNIQUE(request_id, approval_role)",
        "An approval role can only appear once per change request.",
    )

    @api.depends("approval_role", "user_id")
    def _compute_display_name(self):
        """Show the role and, when known, the approver."""
        labels = dict(APPROVAL_ROLES)
        for approval in self:
            role = labels.get(approval.approval_role, approval.approval_role)
            if approval.user_id:
                approval.display_name = "%s (%s)" % (role, approval.user_id.name)
            else:
                approval.display_name = role

    @api.model_create_multi
    def create(self, vals_list):
        """Stamp the request date used by the reminder scheduled action."""
        today = fields.Date.context_today(self)
        for vals in vals_list:
            vals.setdefault("date_requested", today)
        return super().create(vals_list)

    def write(self, vals):
        """Protect the decision fields and freeze decided approvals."""
        if not self.env.su:
            protected = {
                "state",
                "date_decision",
                "decided_by_id",
                "signature_meaning",
                "date_reminder",
                "date_requested",
            }
            forbidden = sorted(set(vals) & protected)
            if forbidden:
                raise AccessError(
                    _(
                        "The following fields are maintained by the approval "
                        "workflow and cannot be written directly: %(fields)s.",
                        fields=", ".join(forbidden),
                    )
                )
            decided = self.filtered(lambda a: a.state != "pending")
            if decided:
                raise UserError(
                    _(
                        "Approval %(name)s has been decided and can no "
                        "longer be modified.",
                        name=decided[0].display_name,
                    )
                )
        return super().write(vals)

    @api.ondelete(at_uninstall=False)
    def _ls_unlink_check_ls_change_control_approval(self):
        """Forbid the deletion of an approval that carries a decision."""
        decided = self.filtered(lambda a: a.state != "pending")
        if decided:
            raise UserError(
                _(
                    "Approval %(name)s carries a decision and cannot be "
                    "deleted.",
                    name=decided[0].display_name,
                )
            )

    # ------------------------------------------------------------------
    # Decision
    # ------------------------------------------------------------------
    def _check_can_decide(self):
        """Validate that the current user may decide on this approval."""
        for approval in self:
            if approval.state != "pending":
                raise UserError(
                    _("Approval %(name)s has already been decided.",
                      name=approval.display_name)
                )
            if approval.request_state != "impact_assessment":
                raise UserError(
                    _(
                        "Decisions can only be recorded while request "
                        "%(name)s is in the Impact Assessment state.",
                        name=approval.request_id.name,
                    )
                )
            if approval.user_id != self.env.user:
                raise AccessError(
                    _(
                        "Only %(user)s may record the decision for approval "
                        "%(name)s.",
                        user=approval.user_id.name or _("the assigned approver"),
                        name=approval.display_name,
                    )
                )

    def _apply_signature(self, meaning):
        """Record the decision metadata of an approval.

        This method is the extension point for the ``ls_electronic_signature``
        module: overriding it allows a stronger signing procedure to be
        applied before the decision is written.

        :param meaning: meaning of the signature, stored with the decision.
        :return: dictionary of values written on the approval.
        """
        self.ensure_one()
        return {
            "date_decision": fields.Datetime.now(),
            "decided_by_id": self.env.user.id,
            "signature_meaning": meaning,
        }

    def action_approve(self):
        """Record a favourable decision and try to approve the request."""
        self._check_can_decide()
        requests = self.request_id
        for approval in self:
            values = approval._apply_signature(_("Approved"))
            values["state"] = "approved"
            approval.sudo().write(values)
            approval.request_id.message_post(
                body=_(
                    "Approval granted by %(user)s for role %(role)s.",
                    user=self.env.user.name,
                    role=approval.display_name,
                ),
                subtype_xmlid="mail.mt_note",
            )
        requests._try_approve()
        return True

    def action_reject(self):
        """Record an unfavourable decision and reject the request."""
        self._check_can_decide()
        for approval in self:
            if not approval.comment or not approval.comment.strip():
                raise UserError(
                    _(
                        "A comment is required to reject approval %(name)s. "
                        "Save the comment before recording the decision.",
                        name=approval.display_name,
                    )
                )
        reasons_per_request = {}
        for approval in self:
            values = approval._apply_signature(_("Rejected"))
            values["state"] = "rejected"
            approval.sudo().write(values)
            reasons_per_request.setdefault(approval.request_id, []).append(
                _(
                    "Rejected by %(user)s for role %(role)s: %(comment)s",
                    user=self.env.user.name,
                    role=approval.display_name,
                    comment=approval.comment,
                )
            )
        for request, reasons in reasons_per_request.items():
            request.action_reject("\n".join(reasons))
        return True

    def _notify_approver(self, reminder=False):
        """Notify the approvers that a decision is expected.

        :param reminder: when True, the notification is a reminder and the
            reminder date is stamped on the approval.
        """
        today = fields.Date.context_today(self)
        template = self.env.ref(
            "ls_change_control.mail_template_approval_requested",
            raise_if_not_found=False,
        )
        for approval in self:
            if not approval.user_id:
                continue
            if template:
                template.sudo().send_mail(approval.id, force_send=False)
            approval.request_id.activity_schedule(
                "mail.mail_activity_data_todo",
                summary=_("Change control approval requested"),
                note=_(
                    "Your decision is expected on change request %(name)s "
                    "for the role %(role)s.",
                    name=approval.request_id.name,
                    role=approval.display_name,
                ),
                user_id=approval.user_id.id,
            )
            if reminder:
                approval.sudo().write({"date_reminder": today})
        return True
