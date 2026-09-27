# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Moulding parameter specification.

A specification is the approved, versioned definition of the process window
for one component produced on one tool. Only one specification may be
approved at a time for a given component, tool and work centre combination.
Approving a new version automatically supersedes the previous one.

Segregation of duties is enforced at ORM level: the author of a specification
may neither review nor approve it, and the reviewer may not approve it.
"""

from dateutil.relativedelta import relativedelta

from odoo import api, fields, models
from odoo.exceptions import ValidationError

from ..constants import (
    DUE_SOON_DAYS,
    PARAMETER_SPEC_EFFECTIVE_STATE,
    PARAMETER_SPEC_STATES,
)


class LsMpMoldingParameter(models.Model):
    """Approved moulding process window for a component and tool."""

    _name = "ls.mp.molding_parameter"
    _description = "Medical Plastics Moulding Parameter Specification"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "component_id, tool_id, version desc, id desc"

    name = fields.Char(
        string="Reference",
        required=True,
        copy=False,
        readonly=True,
        index=True,
        default=lambda self: self.env._("New"),
    )
    component_id = fields.Many2one(comodel_name="ls.mp.component", required=True,
                                   ondelete="restrict",
                                   index=True,
                                   tracking=True,)
    tool_id = fields.Many2one(comodel_name="ls.mp.tool", required=True,
                              ondelete="restrict",
                              index=True,
                              tracking=True,)
    workcenter_id = fields.Many2one(
        comodel_name="mrp.workcenter",
        string="Work Centre",
        ondelete="restrict",
        tracking=True,
        help=(
            "Leave empty for a specification applicable to any work centre. "
            "Set it to constrain the specification to one moulding machine."
        ),
    )
    version = fields.Integer(default=1,
                             required=True,
                             readonly=True,
                             copy=False,
                             tracking=True,)
    state = fields.Selection(
        selection=PARAMETER_SPEC_STATES,
        string="Status",
        default="draft",
        required=True,
        tracking=True,
        copy=False,
    )

    line_ids = fields.One2many(
        comodel_name="ls.mp.molding_parameter.line",
        inverse_name="spec_id",
        string="Parameters",
        copy=True,
    )
    parameter_count = fields.Integer(compute="_compute_parameter_counts",
                                     store=True,)
    critical_parameter_count = fields.Integer(
        string="Critical Parameters",
        compute="_compute_parameter_counts",
        store=True,
    )

    # -- Lifecycle stamps ---------------------------------------------------
    author_id = fields.Many2one(comodel_name="res.users", default=lambda self: self.env.user,
                                required=True,
                                ondelete="restrict",
                                tracking=True,)
    reviewer_id = fields.Many2one(
        comodel_name="res.users",
        string="Reviewed By",
        readonly=True,
        copy=False,
        ondelete="restrict",
        tracking=True,
    )
    review_date = fields.Datetime(string="Reviewed On", readonly=True, copy=False)
    approver_id = fields.Many2one(
        comodel_name="res.users",
        string="Approved By",
        readonly=True,
        copy=False,
        ondelete="restrict",
        tracking=True,
    )
    approval_date = fields.Datetime(string="Approved On", readonly=True, copy=False)
    effective_date = fields.Date(
        string="Effective From",
        copy=False,
        tracking=True,
        help="Date from which the approved specification applies in production.",
    )

    change_reason = fields.Text(
        string="Reason for Change",
        copy=False,
        help="Mandatory from version 2 onwards.",
    )
    previous_version_id = fields.Many2one(comodel_name="ls.mp.molding_parameter", readonly=True,
                                          copy=False,
                                          ondelete="restrict",)

    review_interval_months = fields.Integer(
        string="Periodic Review Interval (months)",
        default=0,
        help="Zero disables periodic review scheduling for this specification.",
    )
    next_review_date = fields.Date(
        string="Next Review Due",
        compute="_compute_next_review_date",
        store=True,
    )
    review_overdue = fields.Boolean(compute="_compute_next_review_date",
                                    store=True,)

    run_ids = fields.One2many(
        comodel_name="ls.mp.injection_molding",
        inverse_name="parameter_spec_id",
        string="Moulding Runs",
    )
    run_count = fields.Integer(compute="_compute_run_count")

    company_id = fields.Many2one(comodel_name="res.company", required=True,
                                 index=True,
                                 default=lambda self: self.env.company,)
    active = fields.Boolean(default=True)
    note = fields.Text(string="Internal Notes")

    _version_positive = models.Constraint(
        "CHECK(version > 0)",
        "The specification version must be strictly positive.",
    )
    _review_interval_non_negative = models.Constraint(
        "CHECK(review_interval_months >= 0)",
        "The periodic review interval cannot be negative.",
    )

    @api.model_create_multi
    def create(self, vals_list):
        """Assign the specification reference from the sequence."""
        placeholder = self.env._("New")
        for vals in vals_list:
            if not vals.get("name") or vals.get("name") == placeholder:
                company_id = vals.get("company_id") or self.env.company.id
                vals["name"] = self.env["ir.sequence"].with_company(company_id).next_by_code(
                    "ls.mp.molding_parameter"
                ) or placeholder
        return super().create(vals_list)

    @api.depends("line_ids", "line_ids.is_critical")
    def _compute_parameter_counts(self):
        """Count total and critical parameters."""
        for spec in self:
            spec.parameter_count = len(spec.line_ids)
            spec.critical_parameter_count = len(
                spec.line_ids.filtered(lambda line: line.is_critical)
            )

    @api.depends("run_ids")
    def _compute_run_count(self):
        """Count the runs executed against this specification."""
        for spec in self:
            spec.run_count = len(spec.run_ids)

    @api.depends("effective_date", "review_interval_months", "state")
    def _compute_next_review_date(self):
        """Derive the periodic review due date for approved specifications."""
        today = fields.Date.context_today(self)
        for spec in self:
            if (
                spec.state == PARAMETER_SPEC_EFFECTIVE_STATE
                and spec.effective_date
                and spec.review_interval_months > 0
            ):
                due = spec.effective_date + relativedelta(months=spec.review_interval_months)
                spec.next_review_date = due
                spec.review_overdue = due <= today
            else:
                spec.next_review_date = False
                spec.review_overdue = False

    @api.depends("name", "component_id.code", "tool_id.code", "version")
    def _compute_display_name(self):
        """Render the specification as ``REF - COMPONENT/TOOL v N``."""
        for spec in self:
            component_code = spec.component_id.code or ""
            tool_code = spec.tool_id.code or ""
            spec.display_name = (
                f"{spec.name} - {component_code}/{tool_code} v{spec.version}"
            )

    # -- Constraints --------------------------------------------------------

    @api.constrains("state", "component_id", "tool_id", "workcenter_id", "company_id")
    def _check_single_approved_specification(self):
        """Only one approved specification may exist per production context.

        The rule is enforced in Python rather than by a unique index because
        the work centre is optional, and SQL unique indexes do not treat NULL
        values as equal.
        """
        for spec in self:
            if spec.state != PARAMETER_SPEC_EFFECTIVE_STATE:
                continue
            duplicate = self.search_count(
                [
                    ("id", "!=", spec.id),
                    ("state", "=", PARAMETER_SPEC_EFFECTIVE_STATE),
                    ("component_id", "=", spec.component_id.id),
                    ("tool_id", "=", spec.tool_id.id),
                    ("workcenter_id", "=", spec.workcenter_id.id or False),
                    ("company_id", "=", spec.company_id.id),
                ]
            )
            if duplicate:
                raise ValidationError(
                    self.env._(
                        "An approved specification already exists for component "
                        "%(component)s on tool %(tool)s. Supersede it before "
                        "approving %(name)s.",
                        component=spec.component_id.display_name,
                        tool=spec.tool_id.display_name,
                        name=spec.name,
                    )
                )

    @api.constrains("component_id", "tool_id")
    def _check_tool_produces_component(self):
        """The tool must be declared as producing the component."""
        for spec in self:
            if spec.component_id not in spec.tool_id.component_ids:
                raise ValidationError(
                    self.env._(
                        "Tool %(tool)s is not declared as producing component "
                        "%(component)s. Add the component to the tool first.",
                        tool=spec.tool_id.display_name,
                        component=spec.component_id.display_name,
                    )
                )

    @api.constrains("version", "change_reason")
    def _check_change_reason(self):
        """Any version after the first must justify the change."""
        for spec in self:
            if spec.version > 1 and not spec.change_reason:
                raise ValidationError(
                    self.env._(
                        "Specification %(name)s is version %(version)s and must "
                        "record a reason for change.",
                        name=spec.name,
                        version=spec.version,
                    )
                )

    @api.constrains("author_id", "reviewer_id", "approver_id")
    def _check_segregation_of_duties(self):
        """Enforce separation between authoring, reviewing and approving."""
        for spec in self:
            if spec.reviewer_id and spec.reviewer_id == spec.author_id:
                raise ValidationError(
                    self.env._(
                        "The author of specification %(name)s cannot also review it.",
                        name=spec.name,
                    )
                )
            if spec.approver_id and spec.approver_id == spec.author_id:
                raise ValidationError(
                    self.env._(
                        "The author of specification %(name)s cannot also approve it.",
                        name=spec.name,
                    )
                )
            if spec.approver_id and spec.reviewer_id and spec.approver_id == spec.reviewer_id:
                raise ValidationError(
                    self.env._(
                        "The reviewer of specification %(name)s cannot also approve it.",
                        name=spec.name,
                    )
                )

    @api.constrains("company_id", "component_id", "tool_id")
    def _check_company_consistency(self):
        """Component and tool must belong to the specification company."""
        for spec in self:
            if spec.component_id.company_id != spec.company_id:
                raise ValidationError(
                    self.env._(
                        "Component %(component)s belongs to another company.",
                        component=spec.component_id.display_name,
                    )
                )
            if spec.tool_id.company_id != spec.company_id:
                raise ValidationError(
                    self.env._(
                        "Tool %(tool)s belongs to another company.",
                        tool=spec.tool_id.display_name,
                    )
                )

    # -- Workflow -----------------------------------------------------------

    def action_submit_for_review(self):
        """Send a draft specification for review."""
        for spec in self:
            if spec.state != "draft":
                raise ValidationError(
                    self.env._(
                        "Specification %(name)s is not in draft.", name=spec.name
                    )
                )
            if not spec.line_ids:
                raise ValidationError(
                    self.env._(
                        "Specification %(name)s cannot be submitted without at "
                        "least one parameter.",
                        name=spec.name,
                    )
                )
        return self.write({"state": "review"})

    def action_review(self):
        """Record the review of the specification by the current user."""
        for spec in self:
            if spec.state != "review":
                raise ValidationError(
                    self.env._(
                        "Specification %(name)s is not under review.", name=spec.name
                    )
                )
            if self.env.user == spec.author_id:
                raise ValidationError(
                    self.env._(
                        "The author of specification %(name)s cannot review it.",
                        name=spec.name,
                    )
                )
            spec.write(
                {
                    "reviewer_id": self.env.user.id,
                    "review_date": fields.Datetime.now(),
                }
            )
        return True

    def action_approve(self):
        """Approve the specification and supersede the previous version."""
        for spec in self:
            if spec.state != "review":
                raise ValidationError(
                    self.env._(
                        "Specification %(name)s must be under review before it can "
                        "be approved.",
                        name=spec.name,
                    )
                )
            if not spec.reviewer_id:
                raise ValidationError(
                    self.env._(
                        "Specification %(name)s must be reviewed before approval.",
                        name=spec.name,
                    )
                )
            if self.env.user == spec.author_id:
                raise ValidationError(
                    self.env._(
                        "The author of specification %(name)s cannot approve it.",
                        name=spec.name,
                    )
                )
            if self.env.user == spec.reviewer_id:
                raise ValidationError(
                    self.env._(
                        "The reviewer of specification %(name)s cannot also approve "
                        "it.",
                        name=spec.name,
                    )
                )
            spec._supersede_previous_versions()
            spec.write(
                {
                    "state": PARAMETER_SPEC_EFFECTIVE_STATE,
                    "approver_id": self.env.user.id,
                    "approval_date": fields.Datetime.now(),
                    "effective_date": spec.effective_date
                    or fields.Date.context_today(spec),
                }
            )
        return True

    def _supersede_previous_versions(self):
        """Move any other approved specification for the same context aside."""
        self.ensure_one()
        others = self.search(
            [
                ("id", "!=", self.id),
                ("state", "=", PARAMETER_SPEC_EFFECTIVE_STATE),
                ("component_id", "=", self.component_id.id),
                ("tool_id", "=", self.tool_id.id),
                ("workcenter_id", "=", self.workcenter_id.id or False),
                ("company_id", "=", self.company_id.id),
            ]
        )
        if others:
            others.write({"state": "superseded"})
            for other in others:
                other.message_post(
                    body=self.env._(
                        "Superseded by specification %(name)s version %(version)s.",
                        name=self.name,
                        version=self.version,
                    )
                )
        return True

    def action_reject(self):
        """Return a specification under review to draft."""
        for spec in self:
            if spec.state != "review":
                raise ValidationError(
                    self.env._(
                        "Specification %(name)s is not under review.", name=spec.name
                    )
                )
        return self.write(
            {"state": "draft", "reviewer_id": False, "review_date": False}
        )

    def action_cancel(self):
        """Cancel a specification that has never been approved."""
        for spec in self:
            if spec.state not in ("draft", "review"):
                raise ValidationError(
                    self.env._(
                        "Specification %(name)s has been approved and cannot be "
                        "cancelled. Mark it obsolete instead.",
                        name=spec.name,
                    )
                )
        return self.write({"state": "cancelled"})

    def action_set_obsolete(self):
        """Withdraw an approved or superseded specification from use."""
        for spec in self:
            if spec.state not in (PARAMETER_SPEC_EFFECTIVE_STATE, "superseded"):
                raise ValidationError(
                    self.env._(
                        "Only approved or superseded specifications can be made "
                        "obsolete. Specification %(name)s is neither.",
                        name=spec.name,
                    )
                )
            if spec.state == PARAMETER_SPEC_EFFECTIVE_STATE and spec._has_open_runs():
                raise ValidationError(
                    self.env._(
                        "Specification %(name)s is still used by moulding runs in "
                        "progress and cannot be made obsolete.",
                        name=spec.name,
                    )
                )
        return self.write({"state": "obsolete"})

    def _has_open_runs(self):
        """Return whether runs referencing this specification are still open.

        :rtype: bool
        """
        self.ensure_one()
        return bool(
            self.env["ls.mp.injection_molding"].search_count(
                [
                    ("parameter_spec_id", "=", self.id),
                    ("state", "not in", ("closed", "cancelled")),
                ]
            )
        )

    def action_create_new_version(self):
        """Create the next draft version of this specification.

        :return: an action opening the newly created draft version.
        :rtype: dict
        """
        self.ensure_one()
        if self.state not in (PARAMETER_SPEC_EFFECTIVE_STATE, "superseded", "obsolete"):
            raise ValidationError(
                self.env._(
                    "A new version can only be created from an approved, "
                    "superseded or obsolete specification. Specification %(name)s "
                    "is in status %(state)s.",
                    name=self.name,
                    state=dict(PARAMETER_SPEC_STATES)[self.state],
                )
            )
        new_version = self.copy(
            {
                "version": self.version + 1,
                "state": "draft",
                "previous_version_id": self.id,
                "author_id": self.env.user.id,
                "reviewer_id": False,
                "review_date": False,
                "approver_id": False,
                "approval_date": False,
                "effective_date": False,
                "change_reason": self.env._(
                    "Revision of version %(version)s.", version=self.version
                ),
            }
        )
        return {
            "type": "ir.actions.act_window",
            "name": self.env._("Moulding Parameter Specification"),
            "res_model": self._name,
            "res_id": new_version.id,
            "view_mode": "form",
        }

    def action_view_runs(self):
        """Open the moulding runs executed against this specification."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": self.env._("Moulding Runs"),
            "res_model": "ls.mp.injection_molding",
            "view_mode": "list,form",
            "domain": [("parameter_spec_id", "=", self.id)],
        }

    @api.ondelete(at_uninstall=False)
    def _ls_unlink_check_ls_mp_molding_parameter(self):
        """Prevent deletion of specifications that have been approved or used."""
        for spec in self:
            if spec.state not in ("draft", "cancelled"):
                raise ValidationError(
                    self.env._(
                        "Specification %(name)s has left the draft stage and cannot "
                        "be deleted.",
                        name=spec.name,
                    )
                )
            if spec.run_ids:
                raise ValidationError(
                    self.env._(
                        "Specification %(name)s is referenced by moulding runs and "
                        "cannot be deleted.",
                        name=spec.name,
                    )
                )

    @api.model
    def _cron_check_specification_review(self):
        """Scheduled action flagging approved specifications due for review.

        :return: ``True`` once processing has completed.
        :rtype: bool
        """
        today = fields.Date.context_today(self)
        horizon = today + relativedelta(days=DUE_SOON_DAYS)
        specs = self.search(
            [
                ("state", "=", PARAMETER_SPEC_EFFECTIVE_STATE),
                ("next_review_date", "!=", False),
                ("next_review_date", "<=", horizon),
            ]
        )
        for spec in specs:
            spec.message_post(
                body=self.env._(
                    "Periodic review of this specification is due on %(date)s.",
                    date=spec.next_review_date,
                )
            )
        return True
