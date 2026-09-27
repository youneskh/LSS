# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Resolution actions taken to answer a complaint."""

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

RESOLUTION_TYPE_SELECTION = [
    ("replacement", "Product Replacement"),
    ("credit_note", "Credit Note"),
    ("refund", "Refund"),
    ("repair", "Repair"),
    ("product_return", "Product Return"),
    ("customer_information", "Customer Information"),
    ("no_action", "No Action Justified"),
    ("field_safety_notice", "Field Safety Notice"),
    ("recall_initiated", "Recall Initiated"),
]


class LsComplaintResolution(models.Model):
    """Individual resolution action attached to a complaint."""

    _name = "ls.complaint.resolution"
    _description = "Complaint Resolution"
    _inherit = ["mail.thread"]
    _order = "complaint_id, due_date, id"
    _check_company_auto = True

    complaint_id = fields.Many2one(comodel_name="ls.complaint", required=True,
                                   ondelete="cascade",
                                   index=True,
                                   check_company=True,)
    company_id = fields.Many2one(comodel_name="res.company", related="complaint_id.company_id",
                                 store=True,
                                 index=True,
                                 readonly=True,)
    resolution_type = fields.Selection(
        selection=RESOLUTION_TYPE_SELECTION,
        required=True,
        tracking=True,
    )
    description = fields.Text(required=True)
    owner_id = fields.Many2one(
        comodel_name="res.users",
        string="Responsible",
        required=True,
        default=lambda self: self.env.user,
        tracking=True,
    )
    due_date = fields.Date(tracking=True)
    completion_date = fields.Date(readonly=True, copy=False)
    state = fields.Selection(
        selection=[
            ("draft", "Draft"),
            ("in_progress", "In Progress"),
            ("done", "Done"),
            ("cancelled", "Cancelled"),
        ],
        default="draft",
        required=True,
        copy=False,
        index=True,
        tracking=True,
    )
    completion_evidence = fields.Text(
        help="Objective evidence that the resolution action was performed.",
    )
    cancellation_reason = fields.Text(
        copy=False,
        help="Justification of the cancellation. Must be filled in before "
        "the Cancel action is used.",
    )

    @api.depends("resolution_type", "complaint_id.name")
    def _compute_display_name(self):
        """Show the complaint reference and the resolution type label."""
        labels = dict(self._fields["resolution_type"].selection)
        for record in self:
            type_label = labels.get(record.resolution_type, _("Resolution"))
            record.display_name = f"{record.complaint_id.name} / {type_label}"

    @api.constrains("due_date", "completion_date")
    def _check_dates(self):
        """Completion cannot precede the creation date of the record."""
        for record in self:
            if (
                record.completion_date
                and record.create_date
                and record.completion_date < record.create_date.date()
            ):
                raise ValidationError(
                    _(
                        "Resolution %(name)s: the completion date cannot precede "
                        "the creation date.",
                        name=record.display_name,
                    )
                )

    def write(self, vals):
        """Freeze resolutions that reached a final state."""
        tracked = {"state", "message_follower_ids", "message_ids"}
        if set(vals) - tracked:
            frozen = self.filtered(
                lambda record: record.state in ("done", "cancelled")
            )
            if frozen:
                raise UserError(
                    _(
                        "Resolutions %(names)s are finalised and can no longer be "
                        "modified.",
                        names=", ".join(frozen.mapped("display_name")),
                    )
                )
        return super().write(vals)

    @api.ondelete(at_uninstall=False)
    def _unlink_except_started(self):
        """Forbid deletion once a resolution left the draft state."""
        started = self.filtered(lambda record: record.state != "draft")
        if started:
            raise UserError(
                _(
                    "Resolutions %(names)s cannot be deleted because they are no "
                    "longer in draft.",
                    names=", ".join(started.mapped("display_name")),
                )
            )

    def _ensure_state(self, allowed_states, action_label):
        """Raise when a record is not in one of ``allowed_states``.

        :param tuple allowed_states: technical state values allowed
        :param str action_label: human readable action used in the message
        :raises UserError: when at least one record is in a wrong state
        """
        wrong = self.filtered(lambda record: record.state not in allowed_states)
        if wrong:
            raise UserError(
                _(
                    "Action '%(action)s' is not allowed for resolutions %(names)s "
                    "in their current status.",
                    action=action_label,
                    names=", ".join(wrong.mapped("display_name")),
                )
            )

    def action_start(self):
        """Move the resolution from Draft to In Progress."""
        self._ensure_state(("draft",), _("Start"))
        self.write({"state": "in_progress"})
        return True

    def action_done(self):
        """Complete the resolution once evidence is recorded."""
        self._ensure_state(("draft", "in_progress"), _("Mark as Done"))
        for record in self:
            if not record.completion_evidence:
                raise UserError(
                    _(
                        "Resolution %(name)s: completion evidence is mandatory.",
                        name=record.display_name,
                    )
                )
        self.write(
            {"state": "done", "completion_date": fields.Date.context_today(self)}
        )
        return True

    def action_cancel(self, reason=None):
        """Cancel the resolution with a documented reason.

        :param str reason: cancellation justification, taken from the context
            key ``cancellation_reason`` when not supplied
        :return: ``True``
        """
        self._ensure_state(("draft", "in_progress"), _("Cancel"))
        for record in self:
            record_reason = (
                reason
                or self.env.context.get("cancellation_reason")
                or record.cancellation_reason
            )
            if not record_reason:
                raise UserError(
                    _(
                        "Resolution %(name)s: a cancellation reason is mandatory.",
                        name=record.display_name,
                    )
                )
            super(LsComplaintResolution, record).write(
                {"state": "cancelled", "cancellation_reason": record_reason}
            )
        return True
