# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Implementation actions carrying out an approved change."""

from odoo import _, api, fields, models
from odoo.exceptions import AccessError, UserError


class LsChangeControlImplementation(models.Model):
    """One task to be executed in order to implement an approved change."""

    _name = "ls.change_control.implementation"
    _description = "Change Control Implementation Action"
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
    name = fields.Char(
        string="Action",
        required=True,
        help="Short description of the action to perform.",
    )
    action_type = fields.Selection(
        selection=[
            ("document_update", "Document Creation or Revision"),
            ("training", "Training"),
            ("qualification", "Equipment Qualification"),
            ("validation", "Process or Method Validation"),
            ("equipment_modification", "Equipment Modification"),
            ("facility_modification", "Facility Modification"),
            ("process_modification", "Process Modification"),
            ("material_change", "Material or Supplier Change"),
            ("system_configuration", "Computerised System Configuration"),
            ("regulatory_submission", "Regulatory Submission"),
            ("customer_notification", "Customer Notification"),
            ("stock_disposition", "Disposition of Existing Stock"),
        ],
        required=True,
        help="Nature of the action, used for reporting and for planning the "
             "evidence to be retained.",
    )
    description = fields.Text()
    responsible_id = fields.Many2one(comodel_name="res.users", required=True,
                                     tracking=True,
                                     domain="[('share', '=', False)]",
                                     )
    date_planned = fields.Date(
        string="Planned Date",
        required=True,
        tracking=True,
    )
    date_done = fields.Date(
        string="Completion Date",
        readonly=True,
        copy=False,
        tracking=True,
    )
    evidence_reference = fields.Char(help="Reference of the document, record or system entry that "
                                     "evidences the completion of the action.",)
    state = fields.Selection(
        selection=[
            ("pending", "Pending"),
            ("in_progress", "In Progress"),
            ("done", "Done"),
            ("cancelled", "Cancelled"),
        ],
        string="Status",
        default="pending",
        required=True,
        readonly=True,
        copy=False,
        tracking=True,
    )
    cancellation_reason = fields.Text(help="Justification recorded when the action is cancelled. It must "
                                      "be filled in before the action can be cancelled.",)
    done_by_id = fields.Many2one(
        comodel_name="res.users",
        string="Completed By",
        readonly=True,
        copy=False,
    )

    @api.depends("name", "request_id")
    def _compute_display_name(self):
        """Show the request reference and the action name."""
        for action in self:
            action.display_name = "%s / %s" % (
                action.request_id.name or "",
                action.name or "",
            )

    def write(self, vals):
        """Protect the workflow fields and freeze closed actions."""
        if not self.env.su:
            protected = {
                "state",
                "date_done",
                "done_by_id",
            }
            forbidden = sorted(set(vals) & protected)
            if forbidden:
                raise AccessError(
                    _(
                        "The following fields are maintained by the "
                        "implementation workflow and cannot be written "
                        "directly: %(fields)s.",
                        fields=", ".join(forbidden),
                    )
                )
            closed = self.filtered(lambda a: a.state in ("done", "cancelled"))
            if closed:
                raise UserError(
                    _(
                        "Implementation action %(name)s is closed and can no "
                        "longer be modified.",
                        name=closed[0].display_name,
                    )
                )
        return super().write(vals)

    @api.ondelete(at_uninstall=False)
    def _ls_unlink_check_ls_change_control_implementation(self):
        """Forbid the deletion of an action that has been started."""
        started = self.filtered(lambda a: a.state != "pending")
        if started:
            raise UserError(
                _(
                    "Implementation action %(name)s has been started and "
                    "cannot be deleted.",
                    name=started[0].display_name,
                )
            )

    def _check_request_state(self):
        """Ensure the parent request allows implementation activity."""
        for action in self:
            if action.request_state not in ("approved", "implementation"):
                raise UserError(
                    _(
                        "Implementation actions of request %(name)s can only "
                        "be executed once the change is approved.",
                        name=action.request_id.name,
                    )
                )

    def _check_responsible(self):
        """Ensure the current user may act on the implementation action."""
        is_manager = self.env.user.has_group(
            "ls_change_control.group_ls_change_control_manager"
        )
        for action in self:
            if action.responsible_id != self.env.user and not is_manager:
                raise AccessError(
                    _(
                        "Only %(user)s or a Change Control Manager may update "
                        "action %(name)s.",
                        user=action.responsible_id.name,
                        name=action.display_name,
                    )
                )

    def action_start(self):
        """Move a Pending action to In Progress."""
        self._check_request_state()
        self._check_responsible()
        wrong = self.filtered(lambda a: a.state != "pending")
        if wrong:
            raise UserError(
                _("Action %(name)s is not Pending.",
                  name=wrong[0].display_name)
            )
        self.sudo().write({"state": "in_progress"})
        return True

    def action_done(self):
        """Close an action as Done.

        An evidence reference is mandatory: a completed action of a regulated
        change must be traceable to a record.
        """
        self._check_request_state()
        self._check_responsible()
        for action in self:
            if action.state not in ("pending", "in_progress"):
                raise UserError(
                    _("Action %(name)s is already closed.",
                      name=action.display_name)
                )
            if not action.evidence_reference or not action.evidence_reference.strip():
                raise UserError(
                    _(
                        "An evidence reference is required before closing "
                        "action %(name)s.",
                        name=action.display_name,
                    )
                )
        self.sudo().write(
            {
                "state": "done",
                "date_done": fields.Date.context_today(self),
                "done_by_id": self.env.user.id,
            }
        )
        for action in self:
            action.request_id.message_post(
                body=_(
                    "Implementation action '%(name)s' completed by %(user)s. "
                    "Evidence: %(evidence)s.",
                    name=action.name,
                    user=self.env.user.name,
                    evidence=action.evidence_reference,
                ),
                subtype_xmlid="mail.mt_note",
            )
        return True

    def action_cancel(self):
        """Cancel an action that is no longer required.

        The cancellation reason must have been recorded on the action before
        the cancellation, and only a change control manager may cancel a
        planned implementation action.
        """
        self._check_request_state()
        if not self.env.user.has_group(
            "ls_change_control.group_ls_change_control_manager"
        ):
            raise AccessError(
                _("Only a Change Control Manager may cancel an "
                  "implementation action.")
            )
        for action in self:
            if action.state in ("done", "cancelled"):
                raise UserError(
                    _("Action %(name)s is already closed.",
                      name=action.display_name)
                )
            if not action.cancellation_reason or not action.cancellation_reason.strip():
                raise UserError(
                    _(
                        "A cancellation reason must be recorded on action "
                        "%(name)s before it can be cancelled.",
                        name=action.display_name,
                    )
                )
        self.sudo().write(
            {
                "state": "cancelled",
                "done_by_id": self.env.user.id,
                "date_done": False,
            }
        )
        for action in self:
            action.request_id.message_post(
                body=_(
                    "Implementation action '%(name)s' cancelled by %(user)s: "
                    "%(reason)s",
                    name=action.name,
                    user=self.env.user.name,
                    reason=action.cancellation_reason,
                ),
                subtype_xmlid="mail.mt_note",
            )
        return True
