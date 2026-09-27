# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Tool maintenance events.

Each maintenance intervention on a moulding tool is recorded as a discrete
event carrying the shot count at which it occurred, the findings and the
actions taken. Completing a preventive event resets the tool maintenance
baseline.
"""

from odoo import api, fields, models
from odoo.exceptions import ValidationError

from ..constants import MAINTENANCE_STATES, MAINTENANCE_TYPES


class LsMpToolMaintenance(models.Model):
    """Maintenance intervention performed on a moulding tool."""

    _name = "ls.mp.tool.maintenance"
    _description = "Medical Plastics Tool Maintenance"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "date_planned desc, id desc"

    name = fields.Char(
        string="Reference",
        required=True,
        copy=False,
        readonly=True,
        index=True,
        default=lambda self: self.env._("New"),
    )
    tool_id = fields.Many2one(comodel_name="ls.mp.tool", required=True,
                              ondelete="restrict",
                              index=True,
                              tracking=True,)
    maintenance_type = fields.Selection(selection=MAINTENANCE_TYPES, required=True,
                                        default="preventive",
                                        tracking=True,)
    state = fields.Selection(
        selection=MAINTENANCE_STATES,
        string="Status",
        default="draft",
        required=True,
        tracking=True,
        copy=False,
    )

    date_planned = fields.Date(
        string="Planned Date",
        required=True,
        default=fields.Date.context_today,
        tracking=True,
    )
    date_start = fields.Datetime(string="Started On", copy=False, tracking=True)
    date_end = fields.Datetime(string="Finished On", copy=False, tracking=True)
    shot_count_at_event = fields.Integer(
        string="Shot Count at Intervention",
        copy=False,
        help="Cumulative tool shot count recorded when the intervention started.",
    )

    performed_by_id = fields.Many2one(comodel_name="res.users", ondelete="restrict",
                                      tracking=True,)
    external_provider_id = fields.Many2one(comodel_name="res.partner", ondelete="restrict",
                                           help="Subcontractor that carried out the intervention, where applicable.",)

    findings = fields.Text()
    actions_taken = fields.Text()
    cavity_ids = fields.Many2many(
        comodel_name="ls.mp.tool.cavity",
        relation="ls_mp_maintenance_cavity_rel",
        column1="maintenance_id",
        column2="cavity_id",
        string="Cavities Affected",
        domain="[('tool_id', '=', tool_id)]",
    )
    requalification_required = fields.Boolean(tracking=True,
                                              help=(
                                                  "The intervention affected the tool such that the organisation "
                                                  "requires it to be requalified before returning to production."),
                                              )
    resets_maintenance_counter = fields.Boolean(
        string="Resets Maintenance Baseline",
        default=True,
        help=(
            "When set, completing this event resets the tool shots-since-"
            "maintenance baseline and the last maintenance date."
        ),
    )

    company_id = fields.Many2one(comodel_name="res.company", related="tool_id.company_id",
                                 store=True,
                                 index=True,
                                 readonly=True,)

    _dates_consistent = models.Constraint(
        "CHECK(date_end IS NULL OR date_start IS NULL OR date_end >= date_start)",
        "The maintenance end date cannot precede its start date.",
    )
    _shot_count_non_negative = models.Constraint(
        "CHECK(shot_count_at_event >= 0)",
        "The shot count at intervention cannot be negative.",
    )

    @api.model_create_multi
    def create(self, vals_list):
        """Assign the maintenance reference from the sequence."""
        placeholder = self.env._("New")
        for vals in vals_list:
            if not vals.get("name") or vals.get("name") == placeholder:
                vals["name"] = self.env["ir.sequence"].next_by_code(
                    "ls.mp.tool.maintenance"
                ) or placeholder
        return super().create(vals_list)

    @api.depends("name", "tool_id.code")
    def _compute_display_name(self):
        """Render the event as ``REFERENCE - TOOLCODE``."""
        for record in self:
            tool_code = record.tool_id.code
            record.display_name = f"{record.name} - {tool_code}" if tool_code else record.name

    @api.constrains("state", "actions_taken")
    def _check_actions_recorded(self):
        """A completed intervention must record what was done."""
        for record in self:
            if record.state == "done" and not record.actions_taken:
                raise ValidationError(
                    self.env._(
                        "Maintenance %(name)s cannot be completed without recording "
                        "the actions taken.",
                        name=record.name,
                    )
                )

    def action_start(self):
        """Start the intervention and snapshot the current tool shot count."""
        for record in self:
            if record.state != "draft":
                raise ValidationError(
                    self.env._(
                        "Maintenance %(name)s is not in draft and cannot be started.",
                        name=record.name,
                    )
                )
            record.write(
                {
                    "state": "in_progress",
                    "date_start": fields.Datetime.now(),
                    "shot_count_at_event": record.tool_id.total_shot_count,
                    "performed_by_id": record.performed_by_id.id or self.env.user.id,
                }
            )
        return True

    def action_done(self):
        """Complete the intervention and update the tool maintenance baseline."""
        for record in self:
            if record.state != "in_progress":
                raise ValidationError(
                    self.env._(
                        "Maintenance %(name)s is not in progress and cannot be "
                        "completed.",
                        name=record.name,
                    )
                )
            record.write({"state": "done", "date_end": fields.Datetime.now()})
            record._apply_to_tool()
        return True

    def _apply_to_tool(self):
        """Push the outcome of a completed intervention onto the tool record."""
        self.ensure_one()
        tool_values = {}
        if self.resets_maintenance_counter:
            tool_values.update(
                {
                    "shot_count_at_last_maintenance": self.tool_id.total_shot_count,
                    "last_maintenance_date": fields.Date.context_today(self),
                }
            )
        if tool_values:
            self.tool_id.write(tool_values)
        if self.requalification_required and self.tool_id.state != "quarantined":
            self.tool_id.write({"state": "quarantined"})
            self.tool_id.message_post(
                body=self.env._(
                    "Tool quarantined: maintenance %(name)s requires requalification "
                    "before return to production.",
                    name=self.name,
                )
            )
        return True

    def action_cancel(self):
        """Cancel a maintenance event that has not been completed."""
        for record in self:
            if record.state == "done":
                raise ValidationError(
                    self.env._(
                        "Maintenance %(name)s is completed and cannot be cancelled.",
                        name=record.name,
                    )
                )
        return self.write({"state": "cancelled"})

    def action_reset_to_draft(self):
        """Return a cancelled event to draft."""
        for record in self:
            if record.state != "cancelled":
                raise ValidationError(
                    self.env._(
                        "Only cancelled maintenance events can be reset to draft. "
                        "Maintenance %(name)s is not cancelled.",
                        name=record.name,
                    )
                )
        return self.write({"state": "draft"})

    @api.ondelete(at_uninstall=False)
    def _ls_unlink_check_ls_mp_tool_maintenance(self):
        """Prevent deletion of completed maintenance events."""
        for record in self:
            if record.state == "done":
                raise ValidationError(
                    self.env._(
                        "Completed maintenance event %(name)s cannot be deleted "
                        "because it forms part of the tool history.",
                        name=record.name,
                    )
                )
