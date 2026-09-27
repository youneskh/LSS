# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Monitoring plan."""

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError

from .constants import (
    PLAN_APPROVED,
    PLAN_CANCELLED,
    PLAN_DRAFT,
    PLAN_STATES,
    PLAN_SUPERSEDED,
)


class LsEnvPlan(models.Model):
    """The approved schedule of routine environmental monitoring.

    A plan groups the monitoring requirements for a set of sampling points.
    Only an approved plan generates samples, and approving a replacement plan
    supersedes its predecessor rather than editing it, so that the schedule in
    force at any past date remains reconstructable.
    """

    _name = "ls.env.plan"
    _description = "Environmental Monitoring Plan"
    _inherit = ["mail.thread"]
    _order = "effective_date desc, name"

    name = fields.Char(string="Plan", required=True, tracking=True)
    code = fields.Char(required=True, tracking=True)
    version = fields.Integer(default=1, readonly=True, copy=False, tracking=True)
    state = fields.Selection(
        selection=PLAN_STATES,
        string="Status",
        default=PLAN_DRAFT,
        required=True,
        readonly=True,
        copy=False,
        tracking=True,
    )
    area_id = fields.Many2one(
        comodel_name="ls.env.area",
        string="Primary Area",
        tracking=True,
        ondelete="restrict",
        help="Area the plan principally covers. Individual lines may target "
        "sampling points in other areas.",
    )
    effective_date = fields.Date(
        string="Effective From", readonly=True, copy=False, tracking=True
    )
    review_date = fields.Date(
        string="Next Review Due",
        tracking=True,
        help="Date by which the plan is to be reviewed against current risk "
        "assessment and historical data.",
    )
    superseded_date = fields.Date(string="Superseded On", readonly=True, copy=False)
    approved_by_id = fields.Many2one(comodel_name="res.users", readonly=True,
                                     copy=False,
                                     tracking=True,)
    superseded_by_id = fields.Many2one(comodel_name="ls.env.plan", readonly=True,
                                       copy=False,
                                       ondelete="set null",)
    rationale = fields.Text(tracking=True,
                            help="Basis for the scope and frequency of this plan.",)
    line_ids = fields.One2many(
        comodel_name="ls.env.plan.line",
        inverse_name="plan_id",
        string="Plan Lines",
        copy=True,
    )
    line_count = fields.Integer(string="Lines", compute="_compute_line_count")
    company_id = fields.Many2one(comodel_name="res.company", required=True,
                                 default=lambda self: self.env.company,
                                 index=True,)

    _code_version_company_unique = models.Constraint(
        "UNIQUE(code, version, company_id)",
        "The plan code and version combination must be unique per company.",
    )
    _version_positive = models.Constraint(
        "CHECK(version > 0)",
        "The version number must be greater than zero.",
    )

    @api.depends("line_ids")
    def _compute_line_count(self):
        """Count the lines of each plan."""
        for record in self:
            record.line_count = len(record.line_ids)

    @api.constrains("area_id", "company_id")
    def _check_area_company(self):
        """Reject a primary area belonging to a different company."""
        for record in self:
            if record.area_id and record.area_id.company_id != record.company_id:
                raise ValidationError(
                    self.env._(
                        "The primary area must belong to the same company as the plan."
                    )
                )

    def action_approve(self):
        """Approve the plan and supersede the previous version.

        Approval is refused for an empty plan and for a plan approved by its
        own author.
        """
        for record in self:
            if record.state != PLAN_DRAFT:
                raise UserError(self.env._("Only a draft plan can be approved."))
            if not record.line_ids:
                raise UserError(
                    self.env._("A plan must contain at least one line to be approved.")
                )
            if record.create_uid == self.env.user:
                raise UserError(
                    self.env._(
                        "A plan must be approved by a user other than the one who "
                        "created it."
                    )
                )
            predecessor = self.search(
                [
                    ("id", "!=", record.id),
                    ("code", "=", record.code),
                    ("company_id", "=", record.company_id.id),
                    ("state", "=", PLAN_APPROVED),
                ],
                limit=1,
            )
            today = fields.Date.context_today(record)
            if predecessor:
                predecessor.write(
                    {
                        "state": PLAN_SUPERSEDED,
                        "superseded_date": today,
                        "superseded_by_id": record.id,
                    }
                )
            record.write(
                {
                    "state": PLAN_APPROVED,
                    "effective_date": today,
                    "approved_by_id": self.env.user.id,
                }
            )
            record.line_ids._reset_next_due_date()
        return True

    def action_cancel(self):
        """Cancel a plan that is not in force."""
        for record in self:
            if record.state == PLAN_APPROVED:
                raise UserError(
                    self.env._(
                        "An approved plan cannot be cancelled. Supersede it with a "
                        "revision instead."
                    )
                )
            if record.state == PLAN_CANCELLED:
                raise UserError(self.env._("The plan is already cancelled."))
            record.state = PLAN_CANCELLED
        return True

    def action_create_revision(self):
        """Create a draft copy of an approved plan."""
        self.ensure_one()
        if self.state != PLAN_APPROVED:
            raise UserError(self.env._("Only an approved plan can be revised."))
        revision = self.copy(
            {
                "state": PLAN_DRAFT,
                "version": self.version + 1,
                "effective_date": False,
                "superseded_date": False,
                "approved_by_id": False,
                "superseded_by_id": False,
            }
        )
        return {
            "type": "ir.actions.act_window",
            "name": self.env._("Plan Revision"),
            "res_model": "ls.env.plan",
            "res_id": revision.id,
            "view_mode": "form",
            "target": "current",
        }

    @api.depends("code", "name", "version")
    def _compute_display_name(self):
        """Show the code and version alongside the plan name."""
        for record in self:
            record.display_name = "[%s v%s] %s" % (
                record.code or "",
                record.version or 1,
                record.name or "",
            )

    @api.ondelete(at_uninstall=False)
    def _ls_unlink_check_ls_env_plan(self):
        """Prevent deletion of a plan that has been approved."""
        for record in self:
            if record.state in (PLAN_APPROVED, PLAN_SUPERSEDED):
                raise UserError(
                    self.env._(
                        "A plan that has been approved cannot be deleted."
                    )
                )
