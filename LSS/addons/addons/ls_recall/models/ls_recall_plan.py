# Part of the Life Sciences Suite for Odoo 19 Community Edition.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Recall plan.

A recall plan is the standing, approved arrangement that describes how the
organisation will conduct a recall: who decides, who is informed, which
products are in scope, and how often the arrangement is rehearsed.

It is modelled as a controlled document with an explicit review and
approval cycle, because EudraLex Volume 4 Part I Chapter 8 expects written
procedures for recall activities to be established in advance so that a
recall can be initiated promptly at any time.
"""

from dateutil.relativedelta import relativedelta

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError

from .constants import EFFECTIVENESS_LEVEL_SELECTION, PLAN_STATE_SELECTION


class LsRecallPlan(models.Model):
    """Standing arrangement governing how recalls are conducted."""

    _name = "ls.recall.plan"
    _description = "Recall Plan"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "code desc, id desc"
    _check_company_auto = True

    # --- Identification ------------------------------------------------
    name = fields.Char(
        string="Title",
        required=True,
        tracking=True,
        help="Short title of the recall plan, for example "
             "'Recall plan - sterile injectables'.",
    )
    code = fields.Char(
        string="Reference",
        readonly=True,
        copy=False,
        index=True,
        default=lambda self: self.env._("New"),
        help="Unique reference allocated automatically on creation.",
    )
    version = fields.Integer(
        default=1,
        readonly=True,
        copy=False,
        tracking=True,
        help="Version number. A new version is created by the "
             "'New Revision' action; existing versions are never edited "
             "once approved.",
    )
    active = fields.Boolean(default=True)
    company_id = fields.Many2one(
        comodel_name="res.company",
        required=True,
        index=True,
        default=lambda self: self.env.company,
    )
    state = fields.Selection(
        selection=PLAN_STATE_SELECTION,
        default="draft",
        required=True,
        copy=False,
        tracking=True,
        index=True,
    )

    # --- Responsibilities ----------------------------------------------
    responsible_user_id = fields.Many2one(
        comodel_name="res.users",
        string="Recall Coordinator",
        required=True,
        tracking=True,
        default=lambda self: self.env.user,
        help="Person accountable for conducting a recall executed under "
             "this plan.",
    )
    deputy_user_id = fields.Many2one(
        comodel_name="res.users",
        string="Deputy",
        tracking=True,
        help="Person who assumes the coordinator role when the "
             "coordinator is unavailable, including outside office hours.",
    )
    decision_member_ids = fields.Many2many(
        comodel_name="res.users",
        relation="ls_recall_plan_decision_user_rel",
        column1="plan_id",
        column2="user_id",
        string="Decision Team",
        help="Members of the team that decides whether to initiate a "
             "recall under this plan.",
    )
    authority_partner_ids = fields.Many2many(
        comodel_name="res.partner",
        relation="ls_recall_plan_authority_partner_rel",
        column1="plan_id",
        column2="partner_id",
        string="Competent Authorities",
        help="Authorities to be notified when a recall is initiated "
             "under this plan.",
    )

    # --- Scope ----------------------------------------------------------
    scope_type = fields.Selection(
        selection=[
            ("all", "All Products"),
            ("product", "Selected Products"),
            ("category", "Selected Product Categories"),
        ],
        default="all",
        required=True,
        tracking=True,
    )
    product_ids = fields.Many2many(
        comodel_name="product.product",
        relation="ls_recall_plan_product_rel",
        column1="plan_id",
        column2="product_id",
        string="Products",
        check_company=True,
    )
    product_category_ids = fields.Many2many(
        comodel_name="product.category",
        relation="ls_recall_plan_categ_rel",
        column1="plan_id",
        column2="categ_id",
        string="Product Categories",
    )
    description = fields.Html(
        string="Procedure",
        sanitize=True,
        help="Description of the arrangement: decision route, "
             "communication route, disposition rules and out-of-hours "
             "arrangements.",
    )

    # --- Default strategy ------------------------------------------------
    default_effectiveness_level = fields.Selection(
        selection=EFFECTIVENESS_LEVEL_SELECTION,
        string="Default Effectiveness Check Level",
        default="a",
        required=True,
        help="Default level proposed on recalls created from this plan. "
             "The level structure follows 21 CFR 7.42(b)(3).",
    )
    target_reconciliation_rate = fields.Float(
        string="Target Reconciliation Rate (%)",
        default=100.0,
        help="Percentage of the distributed quantity that the "
             "organisation expects to account for before a recall "
             "executed under this plan may be closed.",
    )
    initiation_target_hours = fields.Integer(
        string="Initiation Target (hours)",
        default=24,
        help="Internal target, in hours, between the recall decision and "
             "the first recall communication being sent.",
    )

    # --- Mock recall -----------------------------------------------------
    mock_recall_interval_months = fields.Integer(
        string="Mock Recall Interval (months)",
        default=12,
        help="Interval at which the arrangements described by this plan "
             "are rehearsed. Set to 0 to disable the reminder.",
    )
    last_mock_recall_date = fields.Date(
        compute="_compute_mock_recall_dates",
        store=True,
        help="Closure date of the most recent closed mock recall "
             "executed under this plan.",
    )
    next_mock_recall_date = fields.Date(
        compute="_compute_mock_recall_dates",
        store=True,
        help="Date on which the next mock recall becomes due.",
    )

    # --- Approval --------------------------------------------------------
    approved_by_user_id = fields.Many2one(
        comodel_name="res.users",
        string="Approved By",
        readonly=True,
        copy=False,
        tracking=True,
    )
    approval_date = fields.Datetime(readonly=True, copy=False, tracking=True)

    # --- Executions ------------------------------------------------------
    execution_ids = fields.One2many(
        comodel_name="ls.recall.execution",
        inverse_name="plan_id",
        string="Recalls",
    )
    execution_count = fields.Integer(compute="_compute_execution_count")

    # A revision keeps the reference of the plan it supersedes with the next
    # version number, so the reference is unique per version.
    _code_company_uniq = models.Constraint(
        "UNIQUE(code, version, company_id)",
        "The recall plan reference and version must be unique per company.",
    )
    _reconciliation_rate_range = models.Constraint(
        "CHECK(target_reconciliation_rate >= 0"
        " AND target_reconciliation_rate <= 100)",
        "The target reconciliation rate must be between 0 and 100.",
    )
    _mock_interval_positive = models.Constraint(
        "CHECK(mock_recall_interval_months >= 0)",
        "The mock recall interval cannot be negative.",
    )
    _initiation_target_positive = models.Constraint(
        "CHECK(initiation_target_hours >= 0)",
        "The initiation target cannot be negative.",
    )

    # ------------------------------------------------------------------
    # Compute
    # ------------------------------------------------------------------
    @api.depends(
        "mock_recall_interval_months",
        "execution_ids.action_type",
        "execution_ids.state",
        "execution_ids.closure_date",
    )
    def _compute_mock_recall_dates(self):
        """Derive the last and next mock recall dates.

        Only closed mock recalls count as evidence that the arrangement
        has been rehearsed.
        """
        for plan in self:
            closed_mocks = plan.execution_ids.filtered(
                lambda e: e.action_type == "mock_recall"
                and e.state == "closed"
                and e.closure_date
            )
            last_date = False
            if closed_mocks:
                last_date = max(closed_mocks.mapped("closure_date")).date()
            plan.last_mock_recall_date = last_date
            if not plan.mock_recall_interval_months:
                plan.next_mock_recall_date = False
                continue
            base_date = last_date or (
                plan.approval_date.date() if plan.approval_date else False
            )
            if not base_date:
                plan.next_mock_recall_date = False
                continue
            plan.next_mock_recall_date = base_date + relativedelta(
                months=plan.mock_recall_interval_months
            )

    @api.depends("execution_ids")
    def _compute_execution_count(self):
        """Count the recalls executed under each plan."""
        data = self.env["ls.recall.execution"]._read_group(
            domain=[("plan_id", "in", self.ids)],
            groupby=["plan_id"],
            aggregates=["__count"],
        )
        mapping = {plan.id: count for plan, count in data}
        for plan in self:
            plan.execution_count = mapping.get(plan.id, 0)

    @api.depends("name", "code", "version")
    def _compute_display_name(self):
        """Show the reference, title and version together."""
        for plan in self:
            plan.display_name = f"[{plan.code}] {plan.name} (v{plan.version})"

    # ------------------------------------------------------------------
    # Constraints
    # ------------------------------------------------------------------
    @api.constrains("scope_type", "product_ids", "product_category_ids")
    def _check_scope(self):
        """A restricted scope must actually list something."""
        for plan in self:
            if plan.scope_type == "product" and not plan.product_ids:
                raise ValidationError(
                    self.env._(
                        "Plan %(code)s is limited to selected products but "
                        "no product is listed.",
                        code=plan.code,
                    )
                )
            if plan.scope_type == "category" and not plan.product_category_ids:
                raise ValidationError(
                    self.env._(
                        "Plan %(code)s is limited to selected categories "
                        "but no category is listed.",
                        code=plan.code,
                    )
                )

    @api.constrains("state", "description", "deputy_user_id")
    def _check_approval_completeness(self):
        """An approved plan must document the arrangement it approves."""
        for plan in self.filtered(lambda p: p.state == "approved"):
            if not plan.description:
                raise ValidationError(
                    self.env._(
                        "Plan %(code)s cannot be approved without a "
                        "documented procedure.",
                        code=plan.code,
                    )
                )
            if not plan.deputy_user_id:
                raise ValidationError(
                    self.env._(
                        "Plan %(code)s cannot be approved without a "
                        "deputy coordinator, so that a recall can be "
                        "initiated outside office hours.",
                        code=plan.code,
                    )
                )

    # ------------------------------------------------------------------
    # ORM
    # ------------------------------------------------------------------
    @api.model_create_multi
    def create(self, vals_list):
        """Allocate the plan reference from the dedicated sequence."""
        new_label = self.env._("New")
        for vals in vals_list:
            if not vals.get("code") or vals["code"] == new_label:
                company_id = vals.get("company_id") or self.env.company.id
                sequence = self.env["ir.sequence"].with_company(company_id)
                vals["code"] = (
                    sequence.next_by_code("ls.recall.plan") or new_label
                )
        return super().create(vals_list)

    def write(self, vals):
        """Prevent silent modification of approved or obsolete plans.

        Approved plans are controlled documents. Changing one requires a
        new revision, which keeps the superseded version available as
        evidence of what was approved at the time.
        """
        controlled = self.filtered(
            lambda p: p.state in ("approved", "obsolete")
        )
        if controlled:
            forbidden = set(vals) - self._allowed_writes_when_controlled()
            if forbidden:
                raise UserError(
                    self.env._(
                        "Plan %(code)s is approved. Create a new revision "
                        "to change the following: %(fields)s.",
                        code=controlled[0].code,
                        fields=", ".join(sorted(forbidden)),
                    )
                )
        return super().write(vals)

    @api.model
    def _allowed_writes_when_controlled(self):
        """Return field names that stay writable on a controlled plan.

        These are workflow and bookkeeping fields, not content fields.
        """
        return {
            "state",
            "active",
            "approved_by_user_id",
            "approval_date",
            "last_mock_recall_date",
            "next_mock_recall_date",
            "message_follower_ids",
            "message_ids",
            "message_main_attachment_id",
            "activity_ids",
        }

    @api.ondelete(at_uninstall=False)
    def _unlink_only_draft(self):
        """Block deletion of any plan that has ever been approved."""
        blocked = self.filtered(lambda p: p.state != "draft")
        if blocked:
            raise UserError(
                self.env._(
                    "Only draft plans can be deleted. Set plan %(code)s "
                    "to obsolete instead.",
                    code=blocked[0].code,
                )
            )

    # ------------------------------------------------------------------
    # Workflow
    # ------------------------------------------------------------------
    def action_submit_review(self):
        """Move a draft plan into review."""
        self._assert_state("draft", self.env._("submitted for review"))
        self.write({"state": "under_review"})
        return True

    def action_approve(self):
        """Approve a plan that is under review.

        The approver is recorded together with the server timestamp. This
        records *who approved what and when*; it is not, and is not
        presented as, an electronic signature within the meaning of
        21 CFR Part 11 Subpart C.
        """
        self._assert_state("under_review", self.env._("approved"))
        self.write(
            {
                "state": "approved",
                "approved_by_user_id": self.env.user.id,
                "approval_date": fields.Datetime.now(),
            }
        )
        for plan in self:
            plan.message_post(
                body=self.env._(
                    "Recall plan approved by %(user)s.",
                    user=self.env.user.display_name,
                )
            )
        return True

    def action_reject(self):
        """Send a plan under review back to draft."""
        self._assert_state("under_review", self.env._("rejected"))
        self.write({"state": "draft"})
        return True

    def action_set_obsolete(self):
        """Retire an approved plan."""
        self._assert_state("approved", self.env._("made obsolete"))
        self.write({"state": "obsolete", "active": False})
        return True

    def action_new_revision(self):
        """Create the next version of an approved plan.

        The current version is retired and a draft copy carrying the same
        reference with an incremented version number is returned.
        """
        self.ensure_one()
        if self.state != "approved":
            raise UserError(
                self.env._("Only an approved plan can be revised.")
            )
        new_plan = self.copy(
            {
                "code": self.code,
                "version": self.version + 1,
                "state": "draft",
                "approved_by_user_id": False,
                "approval_date": False,
                "active": True,
            }
        )
        self.action_set_obsolete()
        new_plan.message_post(
            body=self.env._(
                "Created as version %(version)s, superseding version "
                "%(previous)s.",
                version=new_plan.version,
                previous=self.version,
            )
        )
        return {
            "type": "ir.actions.act_window",
            "res_model": self._name,
            "res_id": new_plan.id,
            "view_mode": "form",
            "target": "current",
        }

    def action_view_executions(self):
        """Open the recalls executed under this plan."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": self.env._("Recalls"),
            "res_model": "ls.recall.execution",
            "view_mode": "list,form",
            "domain": [("plan_id", "=", self.id)],
            "context": {"default_plan_id": self.id},
        }

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _assert_state(self, expected_state, action_label):
        """Raise a readable error when a transition is not allowed.

        :param str expected_state: the state every record must be in.
        :param str action_label: the transition name used in the message.
        """
        wrong = self.filtered(lambda p: p.state != expected_state)
        if wrong:
            raise UserError(
                self.env._(
                    "Plan %(code)s is in state '%(state)s' and cannot be "
                    "%(action)s.",
                    code=wrong[0].code,
                    state=dict(
                        self._fields["state"].selection
                    ).get(wrong[0].state, wrong[0].state),
                    action=action_label,
                )
            )

    @api.model
    def _cron_check_mock_recall_due(self):
        """Raise an activity on plans whose mock recall is overdue.

        Scheduled action. Creates at most one open activity per plan.
        """
        today = fields.Date.context_today(self)
        due_plans = self.search(
            [
                ("state", "=", "approved"),
                ("next_mock_recall_date", "!=", False),
                ("next_mock_recall_date", "<=", today),
            ]
        )
        for plan in due_plans:
            if plan.activity_ids:
                # An activity is already open on this plan; do not stack
                # a second reminder on top of it.
                continue
            plan.activity_schedule(
                act_type_xmlid="mail.mail_activity_data_todo",
                summary=self.env._("Mock recall due"),
                note=self.env._(
                    "The rehearsal of this recall plan was due on "
                    "%(date)s.",
                    date=plan.next_mock_recall_date,
                ),
                user_id=plan.responsible_user_id.id,
            )
        return len(due_plans)
