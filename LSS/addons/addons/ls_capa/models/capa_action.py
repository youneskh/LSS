# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0.html).
"""CAPA action model."""

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


class LsCapaAction(models.Model):
    """A single corrective or preventive action within a CAPA.

    Actions can optionally be mirrored as ``project.task`` records so that
    execution is tracked in the tool the performing department already uses,
    while the CAPA remains the controlled quality record.
    """

    _name = "ls.capa.action"
    _description = "CAPA Action"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "issue_id, sequence, date_planned, id"

    name = fields.Char(
        string="Reference",
        required=True,
        readonly=True,
        copy=False,
        index=True,
        default=lambda self: _("New"),
    )
    issue_id = fields.Many2one(
        comodel_name="ls.capa.issue",
        string="CAPA",
        required=True,
        ondelete="cascade",
        index=True,
    )
    root_cause_id = fields.Many2one(
        comodel_name="ls.capa.root_cause",
        string="Root Cause Addressed",
        ondelete="set null",
        help="Root cause analysis this action is intended to eliminate.",
    )
    sequence = fields.Integer(default=10)
    action_type = fields.Selection(
        selection=[
            ("corrective", "Corrective"),
            ("preventive", "Preventive"),
        ],
        required=True,
        default="corrective",
        tracking=True,
    )
    description = fields.Text(
        string="Action Description",
        required=True,
        help="Description of what will be done, phrased so that completion "
             "can be objectively verified.",
    )
    responsible_id = fields.Many2one(comodel_name="res.users", required=True,
                                     default=lambda self: self.env.user,
                                     tracking=True,)
    date_planned = fields.Date(
        string="Planned Completion Date",
        required=True,
        tracking=True,
    )
    date_done = fields.Date(
        string="Actual Completion Date",
        readonly=True,
        copy=False,
        tracking=True,
    )
    completion_evidence = fields.Text(copy=False,
                                      help="Reference to the objective evidence demonstrating that the "
                                      "action was performed, for example a document or record number.",)
    state = fields.Selection(
        selection=[
            ("draft", "Draft"),
            ("in_progress", "In Progress"),
            ("done", "Done"),
            ("cancelled", "Cancelled"),
        ],
        string="Status",
        default="draft",
        required=True,
        tracking=True,
        copy=False,
        index=True,
    )
    cancellation_reason = fields.Text(copy=False,)
    task_id = fields.Many2one(
        comodel_name="project.task",
        string="Linked Task",
        readonly=True,
        copy=False,
        ondelete="set null",
        help="Project task created to execute this action.",
    )
    company_id = fields.Many2one(comodel_name="res.company", related="issue_id.company_id",
                                 store=True,
                                 index=True,)
    is_late = fields.Boolean(
        string="Late",
        compute="_compute_is_late",
        search="_search_is_late",
        help="True when the planned date has passed and the action is "
             "neither done nor cancelled.",
    )

    _name_uniq = models.Constraint(
        "UNIQUE(name)",
        "The CAPA action reference must be unique.",
    )

    @api.depends("date_planned", "state")
    def _compute_is_late(self):
        """Flag actions that passed their planned date while still open."""
        today = fields.Date.context_today(self)
        for record in self:
            record.is_late = bool(
                record.date_planned
                and record.date_planned < today
                and record.state not in ("done", "cancelled")
            )

    def _search_is_late(self, operator, value):
        """Allow searching on the non-stored late flag.

        :param str operator: comparison operator supplied by the search view.
        :param bool value: value the operator is applied against.
        :return: a search domain selecting late or non-late actions.
        :rtype: list
        """
        if operator not in ("=", "!="):
            raise UserError(
                _("The Late filter only supports the = and != operators.")
            )
        today = fields.Date.context_today(self)
        positive = (operator == "=") == bool(value)
        if positive:
            return [
                ("date_planned", "<", today),
                ("state", "not in", ["done", "cancelled"]),
            ]
        return [
            "|",
            ("date_planned", ">=", today),
            ("state", "in", ["done", "cancelled"]),
        ]

    @api.constrains("root_cause_id", "issue_id")
    def _check_root_cause_issue(self):
        """Ensure a linked root cause belongs to the same CAPA."""
        for record in self:
            if (
                record.root_cause_id
                and record.root_cause_id.issue_id != record.issue_id
            ):
                raise ValidationError(
                    _(
                        "Action %(reference)s references a root cause that "
                        "belongs to a different CAPA.",
                        reference=record.name,
                    )
                )

    @api.constrains("state", "cancellation_reason")
    def _check_cancellation_reason(self):
        """Require a justification when an action is cancelled."""
        for record in self:
            if record.state == "cancelled" and not (
                record.cancellation_reason or ""
            ).strip():
                raise ValidationError(
                    _(
                        "Action %(reference)s cannot be cancelled without a "
                        "cancellation reason.",
                        reference=record.name,
                    )
                )

    @api.model_create_multi
    def create(self, vals_list):
        """Allocate the action reference from the sequence.

        :param list vals_list: list of value dictionaries.
        :return: the created recordset.
        :rtype: ls.capa.action
        """
        for vals in vals_list:
            if vals.get("name", _("New")) == _("New"):
                vals["name"] = self.env["ir.sequence"].next_by_code(
                    "ls.capa.action"
                ) or _("New")
        return super().create(vals_list)

    def action_start(self):
        """Move a draft action to In Progress.

        :return: True when every record was started.
        :rtype: bool
        """
        invalid = self.filtered(lambda r: r.state != "draft")
        if invalid:
            raise UserError(
                _(
                    "Only draft actions can be started: %(refs)s.",
                    refs=", ".join(invalid.mapped("name")),
                )
            )
        self.write({"state": "in_progress"})
        return True

    def action_done(self):
        """Mark an action as completed and stamp the completion date.

        Completion evidence is mandatory so that the record supports later
        effectiveness verification.

        :return: True when every record was completed.
        :rtype: bool
        """
        invalid = self.filtered(
            lambda r: r.state not in ("draft", "in_progress")
        )
        if invalid:
            raise UserError(
                _(
                    "Only draft or in progress actions can be completed: "
                    "%(refs)s.",
                    refs=", ".join(invalid.mapped("name")),
                )
            )
        missing = self.filtered(
            lambda r: not (r.completion_evidence or "").strip()
        )
        if missing:
            raise UserError(
                _(
                    "Completion evidence must be recorded before completing "
                    "actions %(refs)s.",
                    refs=", ".join(missing.mapped("name")),
                )
            )
        self.write(
            {"state": "done", "date_done": fields.Date.context_today(self)}
        )
        return True

    def action_cancel(self):
        """Cancel an action that is no longer applicable.

        :return: True when every record was cancelled.
        :rtype: bool
        """
        invalid = self.filtered(lambda r: r.state == "done")
        if invalid:
            raise UserError(
                _(
                    "Completed actions cannot be cancelled: %(refs)s.",
                    refs=", ".join(invalid.mapped("name")),
                )
            )
        self.write({"state": "cancelled"})
        return True

    def action_reset_to_draft(self):
        """Return a cancelled action to draft.

        :return: True when every record was reset.
        :rtype: bool
        """
        invalid = self.filtered(lambda r: r.state != "cancelled")
        if invalid:
            raise UserError(
                _(
                    "Only cancelled actions can be reset to draft: %(refs)s.",
                    refs=", ".join(invalid.mapped("name")),
                )
            )
        self.write({"state": "draft", "cancellation_reason": False})
        return True

    def action_create_task(self):
        """Create a ``project.task`` mirroring this action.

        The task is created in the project referenced by the
        ``ls_capa.default_project_id`` configuration parameter when set, and
        otherwise without a project so the user can file it manually.

        :return: an ``ir.actions.act_window`` dictionary opening the task.
        """
        self.ensure_one()
        if self.task_id:
            raise UserError(
                _(
                    "Action %(reference)s is already linked to a task.",
                    reference=self.name,
                )
            )
        project_id = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("ls_capa.default_project_id")
        )
        task_vals = {
            "name": _("%(reference)s - %(capa)s", reference=self.name,
                      capa=self.issue_id.title),
            "description": self.description,
            "user_ids": [fields.Command.set(self.responsible_id.ids)],
            "date_deadline": self.date_planned,
            "company_id": self.company_id.id,
        }
        if project_id and project_id.isdigit():
            task_vals["project_id"] = int(project_id)
        task = self.env["project.task"].create(task_vals)
        self.task_id = task
        return {
            "type": "ir.actions.act_window",
            "name": _("CAPA Task"),
            "res_model": "project.task",
            "res_id": task.id,
            "view_mode": "form",
        }
