# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Validation Master Plan (VMP).

The VMP is the governing document of a validation programme: it declares the
scope, the strategy, the responsibilities and the list of items covered. It
follows a controlled lifecycle with review, approval and versioning, and every
state transition that requires accountability is bound to an electronic
signature.
"""

from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

MASTER_PLAN_STATES = [
    ("draft", "Draft"),
    ("review", "Under Review"),
    ("approved", "Approved"),
    ("active", "Active"),
    ("superseded", "Superseded"),
    ("cancelled", "Cancelled"),
]


class LsValidationMasterPlan(models.Model):
    """Controlled Validation Master Plan document."""

    _name = "ls.validation.master.plan"
    _description = "Validation Master Plan"
    _inherit = [
        "mail.thread",
        "mail.activity.mixin",
        "ls.validation.signature.mixin",
    ]
    _order = "reference desc, version desc"
    _check_company_auto = True

    _ls_signable_callbacks = ("_ls_do_approve",)

    reference = fields.Char(required=True,
                            readonly=True,
                            copy=False,
                            default=lambda self: _("New"),
                            index=True,
                            )
    name = fields.Char(string="Title", required=True, tracking=True)
    version = fields.Integer(required=True, default=1, tracking=True)
    previous_version_id = fields.Many2one(comodel_name="ls.validation.master.plan", readonly=True,
                                          copy=False,
                                          ondelete="restrict",)
    state = fields.Selection(
        selection=MASTER_PLAN_STATES,
        string="Status",
        default="draft",
        required=True,
        tracking=True,
        copy=False,
    )
    scope = fields.Html(sanitize=True,
                        help="Sites, systems, processes and periods covered by the plan.",)
    strategy = fields.Html(
        string="Validation Strategy",
        sanitize=True,
        help="Risk based approach, deliverables and acceptance philosophy.",
    )
    responsibilities = fields.Html(sanitize=True)
    author_id = fields.Many2one(comodel_name="res.users", required=True,
                                default=lambda self: self.env.user,
                                tracking=True,)
    reviewer_id = fields.Many2one(comodel_name="res.users", tracking=True)
    approver_id = fields.Many2one(
        comodel_name="res.users",
        string="Approved by",
        readonly=True,
        copy=False,
        tracking=True,
    )
    approval_date = fields.Datetime(readonly=True, copy=False, tracking=True)
    effective_date = fields.Date(tracking=True, copy=False)
    review_interval_months = fields.Integer(
        string="Review Interval (months)",
        default=24,
        help="Interval used to compute the next periodic review of the plan.",
    )
    next_review_date = fields.Date(compute="_compute_next_review_date",
                                   store=True,)
    item_ids = fields.Many2many(
        comodel_name="ls.validation.item",
        relation="ls_validation_master_plan_item_rel",
        column1="master_plan_id",
        column2="item_id",
        string="Items in Scope",
        check_company=True,
    )
    protocol_ids = fields.One2many(
        comodel_name="ls.validation.protocol",
        inverse_name="master_plan_id",
        string="Protocols",
    )
    protocol_count = fields.Integer(compute="_compute_protocol_count")
    company_id = fields.Many2one(comodel_name="res.company", required=True,
                                 default=lambda self: self.env.company,)

    _unique_reference_version = models.Constraint(
        "UNIQUE(reference, version, company_id)",
        "A master plan with the same reference and version already exists.",
    )
    _positive_version = models.Constraint(
        "CHECK(version > 0)",
        "The version number must be strictly positive.",
    )

    # ------------------------------------------------------------------
    # Compute
    # ------------------------------------------------------------------
    @api.depends("reference", "name", "version")
    def _compute_display_name(self):
        """Display the plan as ``REFERENCE v<version> - Title``."""
        for plan in self:
            plan.display_name = "%s v%s - %s" % (
                plan.reference or "",
                plan.version,
                plan.name or "",
            )

    @api.depends("effective_date", "review_interval_months")
    def _compute_next_review_date(self):
        """Compute the next periodic review date of the plan."""
        for plan in self:
            if plan.effective_date and plan.review_interval_months > 0:
                plan.next_review_date = plan.effective_date + relativedelta(
                    months=plan.review_interval_months
                )
            else:
                plan.next_review_date = False

    @api.depends("protocol_ids")
    def _compute_protocol_count(self):
        """Count the protocols governed by the plan."""
        data = self.env["ls.validation.protocol"]._read_group(
            [("master_plan_id", "in", self.ids)],
            groupby=["master_plan_id"],
            aggregates=["__count"],
        )
        mapped = {plan.id: count for plan, count in data}
        for plan in self:
            plan.protocol_count = mapped.get(plan.id, 0)

    # ------------------------------------------------------------------
    # Constraints
    # ------------------------------------------------------------------
    @api.constrains("review_interval_months")
    def _check_review_interval(self):
        """Reject a negative review interval."""
        for plan in self:
            if plan.review_interval_months < 0:
                raise ValidationError(
                    _("The review interval cannot be negative.")
                )

    # ------------------------------------------------------------------
    # ORM
    # ------------------------------------------------------------------
    @api.model_create_multi
    def create(self, vals_list):
        """Assign the master plan sequence on creation."""
        for vals in vals_list:
            if vals.get("reference", _("New")) == _("New"):
                company_id = vals.get("company_id", self.env.company.id)
                vals["reference"] = self.env["ir.sequence"].with_company(
                    company_id
                ).next_by_code("ls.validation.master.plan") or _("New")
        return super().create(vals_list)

    def write(self, vals):
        """Protect approved content against uncontrolled modification."""
        controlled_fields = {
            "name",
            "scope",
            "strategy",
            "responsibilities",
            "item_ids",
            "version",
        }
        if controlled_fields.intersection(vals):
            for plan in self:
                if plan.state not in ("draft", "review"):
                    raise UserError(
                        _(
                            "Master plan %s is %s: create a new version to "
                            "change its content."
                        )
                        % (plan.display_name, plan.state)
                    )
        return super().write(vals)

    @api.ondelete(at_uninstall=False)
    def _ls_unlink_check_ls_validation_master_plan(self):
        """Only draft or cancelled plans may be deleted."""
        for plan in self:
            if plan.state not in ("draft", "cancelled"):
                raise UserError(
                    _(
                        "Master plan %s cannot be deleted because it is not "
                        "draft or cancelled."
                    )
                    % plan.display_name
                )

    # ------------------------------------------------------------------
    # Workflow
    # ------------------------------------------------------------------
    def action_submit_review(self):
        """Move a draft plan to the review state."""
        for plan in self:
            if plan.state != "draft":
                raise UserError(
                    _("Only a draft master plan can be submitted for review.")
                )
            if not plan.scope:
                raise UserError(
                    _("The scope must be documented before review.")
                )
            plan.state = "review"
            plan.message_post(body=_("Submitted for review."))
        return True

    def action_back_to_draft(self):
        """Return a plan under review to the draft state."""
        for plan in self:
            if plan.state != "review":
                raise UserError(
                    _("Only a master plan under review can return to draft.")
                )
            plan.state = "draft"
            plan.message_post(body=_("Returned to draft."))
        return True

    def action_approve(self):
        """Open the electronic signature wizard to approve the plan."""
        self.ensure_one()
        if self.state != "review":
            raise UserError(
                _("Only a master plan under review can be approved.")
            )
        return self._ls_open_sign_wizard(
            meaning="approved",
            callback="_ls_do_approve",
            title=_("Approve Validation Master Plan"),
        )

    def _ls_do_approve(self):
        """Apply the approval once the electronic signature is recorded."""
        self.ensure_one()
        self._ls_check_group(
            "ls_validation.group_ls_validation_approver",
            _("Only a Validation Approver may approve a master plan."),
        )
        if self.state != "review":
            raise UserError(
                _("Only a master plan under review can be approved.")
            )
        self.write(
            {
                "state": "approved",
                "approver_id": self.env.user.id,
                "approval_date": fields.Datetime.now(),
            }
        )
        self.message_post(body=_("Approved and signed electronically."))
        return True

    def action_activate(self):
        """Put an approved plan in force."""
        for plan in self:
            if plan.state != "approved":
                raise UserError(
                    _("Only an approved master plan can be activated.")
                )
            values = {"state": "active"}
            if not plan.effective_date:
                values["effective_date"] = fields.Date.context_today(plan)
            plan.write(values)
            if plan.previous_version_id.state == "active":
                plan.previous_version_id.write({"state": "superseded"})
            plan.message_post(body=_("Master plan is now active."))
        return True

    def action_cancel(self):
        """Cancel a plan that is not in force."""
        for plan in self:
            if plan.state in ("active", "superseded"):
                raise UserError(
                    _("An active or superseded master plan cannot be cancelled.")
                )
            plan.state = "cancelled"
            plan.message_post(body=_("Master plan cancelled."))
        return True

    def action_new_version(self):
        """Create the next version of an active or approved plan."""
        self.ensure_one()
        if self.state not in ("approved", "active"):
            raise UserError(
                _(
                    "A new version can only be created from an approved or "
                    "active master plan."
                )
            )
        new_plan = self.copy(
            {
                "reference": self.reference,
                "version": self.version + 1,
                "previous_version_id": self.id,
                "state": "draft",
            }
        )
        new_plan.message_post(
            body=_("Created as version %(version)s of %(reference)s.")
            % {"version": new_plan.version, "reference": self.reference}
        )
        return {
            "type": "ir.actions.act_window",
            "res_model": self._name,
            "res_id": new_plan.id,
            "view_mode": "form",
        }

    def action_view_protocols(self):
        """Open the protocols governed by the plan."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Protocols"),
            "res_model": "ls.validation.protocol",
            "view_mode": "list,form",
            "domain": [("master_plan_id", "=", self.id)],
            "context": {"default_master_plan_id": self.id},
        }
