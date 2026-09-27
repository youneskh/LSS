# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Change control request: the controlling record of the change lifecycle."""

import logging
from datetime import timedelta

from odoo import _, api, fields, models
from odoo.exceptions import AccessError, UserError, ValidationError

_logger = logging.getLogger(__name__)

#: Ordered states of the change control lifecycle.
#: The sequence is imposed by the functional specification of the
#: Life Sciences Suite, section 7.6.
STATES = [
    ("draft", "Draft"),
    ("under_review", "Under Review"),
    ("impact_assessment", "Impact Assessment"),
    ("approved", "Approved"),
    ("implementation", "Implementation"),
    ("verified", "Verified"),
    ("closed", "Closed"),
    ("rejected", "Rejected"),
    ("cancelled", "Cancelled"),
]

#: States from which no further workflow transition is possible.
FINAL_STATES = ("closed", "rejected", "cancelled")


class LsChangeControlRequest(models.Model):
    """A controlled change to a facility, equipment, process, product,
    material, computerised system or document.

    The record is the single point of control for the whole change: it holds
    the description of the change, the impact assessments, the approvals, the
    implementation actions and the effectiveness verifications.

    Data integrity design
    ---------------------
    Two independent mechanisms protect the record:

    * ``_CONTENT_FIELDS`` are frozen as soon as the request leaves the Draft
      state. They can never be modified again, by any user, including a
      change control manager. A change to an approved request requires a new
      change request.
    * ``_SYSTEM_FIELDS`` are workflow results (state, decision dates, decision
      reasons). They are only writable in superuser mode, which the module
      enters exclusively from its own transition methods through ``sudo()``.
      ``sudo()`` keeps the real user on the environment, so message tracking
      remains attributed to the person who performed the transition.
    """

    _name = "ls.change_control.request"
    _description = "Change Control Request"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "date_request desc, id desc"

    #: Fields frozen once the request has been submitted.
    _CONTENT_FIELDS = (
        "title",
        "category_id",
        "change_type",
        "temporary_end_date",
        "current_situation",
        "proposed_change",
        "justification",
    )
    #: Prefixes of the messaging and activity fields, excluded from the
    #: business modification check performed by ``_check_writer``.
    _TECHNICAL_FIELD_PREFIXES = (
        "message_",
        "activity_",
        "website_message_",
    )
    #: Fields that only the workflow methods may write.
    _SYSTEM_FIELDS = (
        "state",
        "name",
        "date_approved",
        "date_closed",
        "date_rejected",
        "date_cancelled",
        "rejection_reason",
        "cancellation_reason",
        "closure_statement",
    )

    # ------------------------------------------------------------------
    # Identification
    # ------------------------------------------------------------------
    name = fields.Char(
        string="Reference",
        required=True,
        readonly=True,
        copy=False,
        index=True,
        default=lambda self: _("New"),
        help="Unique reference allocated from the sequence when the request "
             "is created. It is never reused and never modified.",
    )
    title = fields.Char(required=True,
                        tracking=True,
                        help="Short description of the change, used in lists and reports.",)
    company_id = fields.Many2one(comodel_name="res.company", required=True,
                                 index=True,
                                 default=lambda self: self.env.company,
                                 help="Manufacturing site owning the change request.",)
    active = fields.Boolean(default=True,
                            help="Only Draft requests may be archived. Submitted requests are "
                            "retained for the full record retention period.",)

    # ------------------------------------------------------------------
    # Classification
    # ------------------------------------------------------------------
    category_id = fields.Many2one(
        comodel_name="ls.change_control.category",
        string="Change Category",
        required=True,
        tracking=True,
        help="Category driving the impact areas to assess, the approval "
             "matrix and the applicable deadlines.",
    )
    change_type = fields.Selection(
        selection=[
            ("permanent", "Permanent"),
            ("temporary", "Temporary"),
        ],
        required=True,
        default="permanent",
        tracking=True,
        help="A temporary change is reverted at the end of a defined period.",
    )
    temporary_end_date = fields.Date(
        string="Temporary Change End Date",
        help="Date on which a temporary change is reverted. Mandatory for "
             "temporary changes.",
    )
    classification = fields.Selection(
        selection=[
            ("minor", "Minor"),
            ("major", "Major"),
            ("critical", "Critical"),
        ],
        required=True,
        default="minor",
        tracking=True,
        help="Criticality of the change, assigned during the review.",
    )
    priority = fields.Selection(
        selection=[
            ("0", "Normal"),
            ("1", "Urgent"),
        ],
        default="0",
        help="Urgent requests are highlighted in the kanban and list views.",
    )

    # ------------------------------------------------------------------
    # Actors
    # ------------------------------------------------------------------
    requester_id = fields.Many2one(comodel_name="res.users", required=True,
                                   default=lambda self: self.env.user,
                                   tracking=True,
                                   domain="[('share', '=', False)]",
                                   help="Person who initiated the change request.",
                                   )
    department_id = fields.Many2one(
        comodel_name="hr.department",
        string="Requesting Department",
        help="Department that initiated the change request.",
    )
    manager_id = fields.Many2one(
        comodel_name="res.users",
        string="Change Control Manager",
        tracking=True,
        domain="[('share', '=', False)]",
        help="Person accountable for driving the request through its "
             "lifecycle. Assigned during the review.",
    )

    # ------------------------------------------------------------------
    # Content
    # ------------------------------------------------------------------
    current_situation = fields.Text(required=True,
                                    help="Description of the situation before the change.",)
    proposed_change = fields.Text(required=True,
                                  help="Description of the situation after the change.",)
    justification = fields.Text(required=True,
                                help="Reason why the change is required.",)

    # ------------------------------------------------------------------
    # Impact declaration
    # ------------------------------------------------------------------
    impact_area_ids = fields.Many2many(
        comodel_name="ls.change_control.impact_area",
        relation="ls_cc_request_impact_area_rel",
        column1="request_id",
        column2="impact_area_id",
        string="Impact Areas",
        help="Areas of the quality system to be assessed for this change.",
    )
    gmp_impact = fields.Boolean(tracking=True,
                                help="The change affects an activity carried out under good "
                                "manufacturing practices.",)
    product_quality_impact = fields.Selection(
        selection=[
            ("none", "None"),
            ("low", "Low"),
            ("medium", "Medium"),
            ("high", "High"),
        ],
        default="none",
        tracking=True,
        help="Assessed impact of the change on the quality of the product.",
    )
    regulatory_impact = fields.Selection(
        selection=[
            ("none", "No Regulatory Action"),
            ("notification", "Notification to the Authority"),
            ("variation", "Variation of the Marketing Authorisation"),
            ("prior_approval", "Prior Approval Required"),
        ],
        default="none",
        tracking=True,
        help="Regulatory action triggered by the change. The applicable "
             "action must be determined by Regulatory Affairs against the "
             "regulations of each market concerned.",
    )
    validation_impact = fields.Boolean(
        string="Requires Revalidation",
        help="The change requires a qualification or validation activity.",
    )
    training_impact = fields.Boolean(
        string="Requires Training",
        help="The change requires personnel to be trained before it becomes "
             "effective.",
    )
    documentation_impact = fields.Boolean(
        string="Requires Document Update",
        help="The change requires the creation or revision of a controlled "
             "document.",
    )
    customer_notification_required = fields.Boolean(
        string="Requires Customer Notification",
        help="The change must be notified to customers, for example under a "
             "quality agreement.",
    )
    risk_assessment_reference = fields.Char(help="Reference of the risk assessment supporting the change. The "
                                            "risk assessment itself is managed outside this module.",)

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------
    state = fields.Selection(
        selection=STATES,
        string="Status",
        required=True,
        readonly=True,
        copy=False,
        default="draft",
        tracking=True,
        index=True,
        help="Current position of the request in the change control "
             "lifecycle.",
    )
    date_request = fields.Datetime(
        string="Request Date",
        required=True,
        readonly=True,
        copy=False,
        default=fields.Datetime.now,
        help="Creation date and time of the request, in UTC.",
    )
    date_required = fields.Date(
        string="Requested Target Date",
        help="Date on which the requester would like the change to be "
             "effective. It is not binding.",
    )
    date_planned_implementation = fields.Date(
        string="Planned Implementation Date",
        tracking=True,
        help="Date on which the change is planned to be implemented. "
             "Proposed from the category deadline when the request is "
             "approved.",
    )
    date_actual_implementation = fields.Date(
        string="Actual Implementation Date",
        compute="_compute_date_actual_implementation",
        store=True,
        help="Latest completion date of the implementation actions. It is "
             "only set once every action is Done or Cancelled.",
    )
    date_verification_planned = fields.Date(
        string="Planned Verification Date",
        compute="_compute_date_verification_planned",
        store=True,
        help="Actual implementation date increased by the verification delay "
             "of the category, or of the company when the category does not "
             "define one.",
    )
    date_approved = fields.Datetime(
        string="Approval Date",
        readonly=True,
        copy=False,
        help="Date and time at which the last mandatory approval was granted.",
    )
    date_rejected = fields.Datetime(
        string="Rejection Date",
        readonly=True,
        copy=False,
    )
    date_cancelled = fields.Datetime(
        string="Cancellation Date",
        readonly=True,
        copy=False,
    )
    date_closed = fields.Datetime(
        string="Closure Date",
        readonly=True,
        copy=False,
    )
    rejection_reason = fields.Text(readonly=True,
                                   copy=False,)
    cancellation_reason = fields.Text(readonly=True,
                                      copy=False,)
    closure_statement = fields.Text(readonly=True,
                                    copy=False,
                                    help="Conclusion recorded by the change control manager at closure.",)

    # ------------------------------------------------------------------
    # Related records
    # ------------------------------------------------------------------
    assessment_ids = fields.One2many(
        comodel_name="ls.change_control.assessment",
        inverse_name="request_id",
        string="Impact Assessments",
    )
    approval_ids = fields.One2many(
        comodel_name="ls.change_control.approval",
        inverse_name="request_id",
        string="Approvals",
    )
    implementation_ids = fields.One2many(
        comodel_name="ls.change_control.implementation",
        inverse_name="request_id",
        string="Implementation Actions",
    )
    verification_ids = fields.One2many(
        comodel_name="ls.change_control.verification",
        inverse_name="request_id",
        string="Effectiveness Verifications",
    )

    # ------------------------------------------------------------------
    # Indicators
    # ------------------------------------------------------------------
    assessment_count = fields.Integer(
        string="Assessments",
        compute="_compute_assessment_count",
    )
    assessment_done_count = fields.Integer(
        string="Completed Assessments",
        compute="_compute_assessment_count",
    )
    approval_count = fields.Integer(
        string="Approvals",
        compute="_compute_approval_count",
    )
    approval_done_count = fields.Integer(
        string="Granted Approvals",
        compute="_compute_approval_count",
    )
    implementation_count = fields.Integer(
        string="Actions",
        compute="_compute_implementation_count",
    )
    implementation_done_count = fields.Integer(
        string="Closed Actions",
        compute="_compute_implementation_count",
    )
    verification_count = fields.Integer(
        string="Verifications",
        compute="_compute_verification_count",
    )
    blocking_reasons = fields.Text(
        string="Outstanding Items",
        compute="_compute_blocking_reasons",
        help="List of the items preventing the next transition. It is "
             "recomputed on every display and is never stored.",
    )

    # ------------------------------------------------------------------
    # SQL constraints
    # ------------------------------------------------------------------
    _name_unique = models.Constraint(
        "UNIQUE(name)",
        "The change request reference must be unique.",
    )

    # ------------------------------------------------------------------
    # Compute methods
    # ------------------------------------------------------------------
    @api.depends("name", "title")
    def _compute_display_name(self):
        """Show the reference followed by the title."""
        for request in self:
            if request.title:
                request.display_name = "%s - %s" % (request.name, request.title)
            else:
                request.display_name = request.name

    @api.depends("assessment_ids.state")
    def _compute_assessment_count(self):
        """Count the assessments and the completed ones."""
        for request in self:
            assessments = request.assessment_ids
            request.assessment_count = len(assessments)
            request.assessment_done_count = len(
                assessments.filtered(lambda a: a.state == "completed")
            )

    @api.depends("approval_ids.state")
    def _compute_approval_count(self):
        """Count the approvals and the granted ones."""
        for request in self:
            approvals = request.approval_ids
            request.approval_count = len(approvals)
            request.approval_done_count = len(
                approvals.filtered(lambda a: a.state == "approved")
            )

    @api.depends("implementation_ids.state")
    def _compute_implementation_count(self):
        """Count the implementation actions and the closed ones."""
        for request in self:
            actions = request.implementation_ids
            request.implementation_count = len(actions)
            request.implementation_done_count = len(
                actions.filtered(lambda a: a.state in ("done", "cancelled"))
            )

    @api.depends("verification_ids")
    def _compute_verification_count(self):
        """Count the effectiveness verification records."""
        for request in self:
            request.verification_count = len(request.verification_ids)

    @api.depends("implementation_ids.state", "implementation_ids.date_done")
    def _compute_date_actual_implementation(self):
        """Set the actual implementation date once all actions are closed.

        The date is the latest completion date of the Done actions. When at
        least one action is still Pending or In Progress, or when no action
        was actually done, the field is emptied.
        """
        for request in self:
            actions = request.implementation_ids
            open_actions = actions.filtered(
                lambda a: a.state in ("pending", "in_progress")
            )
            done_dates = actions.filtered(
                lambda a: a.state == "done" and a.date_done
            ).mapped("date_done")
            if actions and not open_actions and done_dates:
                request.date_actual_implementation = max(done_dates)
            else:
                request.date_actual_implementation = False

    @api.depends(
        "date_actual_implementation",
        "category_id",
        "category_id.verification_delay",
        "company_id",
        "company_id.ls_cc_default_verification_delay",
    )
    def _compute_date_verification_planned(self):
        """Derive the planned verification date from the implementation date."""
        for request in self:
            if not request.date_actual_implementation or not request.category_id:
                request.date_verification_planned = False
                continue
            delay = request.category_id.get_verification_delay(
                request.company_id
            )
            request.date_verification_planned = (
                request.date_actual_implementation + timedelta(days=delay)
            )

    @api.depends(
        "state",
        "assessment_ids.state",
        "assessment_ids.impact_area_id",
        "approval_ids.state",
        "approval_ids.user_id",
        "approval_ids.mandatory",
        "implementation_ids.state",
        "verification_ids.state",
        "verification_ids.result",
    )
    def _compute_blocking_reasons(self):
        """Expose the outstanding items of the current state to the user."""
        for request in self:
            reasons = request._get_blocking_reasons()
            request.blocking_reasons = "\n".join(reasons) if reasons else False

    # ------------------------------------------------------------------
    # Constraints
    # ------------------------------------------------------------------
    @api.constrains("change_type", "temporary_end_date")
    def _check_temporary_end_date(self):
        """A temporary change must declare when it ends."""
        for request in self:
            if request.change_type == "temporary" and not request.temporary_end_date:
                raise ValidationError(
                    _(
                        "Request %(name)s is a temporary change and must "
                        "declare a temporary change end date.",
                        name=request.name,
                    )
                )
            if request.change_type == "permanent" and request.temporary_end_date:
                raise ValidationError(
                    _(
                        "Request %(name)s is a permanent change and must not "
                        "declare a temporary change end date.",
                        name=request.name,
                    )
                )

    @api.constrains("date_required", "date_planned_implementation")
    def _check_dates_after_request(self):
        """Planning dates cannot precede the request date."""
        for request in self:
            request_date = fields.Datetime.context_timestamp(
                request, request.date_request
            ).date()
            for field_name, label in (
                ("date_required", _("Requested Target Date")),
                ("date_planned_implementation", _("Planned Implementation Date")),
            ):
                value = request[field_name]
                if value and value < request_date:
                    raise ValidationError(
                        _(
                            "On request %(name)s, the %(label)s cannot be "
                            "earlier than the request date.",
                            name=request.name,
                            label=label,
                        )
                    )

    @api.constrains("requester_id", "manager_id")
    def _check_users_are_internal(self):
        """Portal and public users cannot act on a change request."""
        for request in self:
            users = request.requester_id | request.manager_id
            if any(user.share for user in users):
                raise ValidationError(
                    _("The requester and the change control manager must be "
                      "internal users.")
                )

    @api.constrains("active", "state")
    def _check_archive_only_draft(self):
        """Only Draft requests may be archived."""
        for request in self:
            if not request.active and request.state != "draft":
                raise ValidationError(
                    _(
                        "Request %(name)s cannot be archived because it is "
                        "not in the Draft state. Submitted change requests "
                        "are retained.",
                        name=request.name,
                    )
                )

    # ------------------------------------------------------------------
    # Onchange methods
    # ------------------------------------------------------------------
    @api.onchange("category_id")
    def _onchange_category_id(self):
        """Propose the default impact areas of the selected category."""
        for request in self:
            if request.category_id:
                request.impact_area_ids = request.category_id.impact_area_ids

    @api.onchange("change_type")
    def _onchange_change_type(self):
        """Clear the end date when the change becomes permanent."""
        for request in self:
            if request.change_type == "permanent":
                request.temporary_end_date = False

    @api.onchange("requester_id")
    def _onchange_requester_id(self):
        """Propose the department of the requester."""
        for request in self:
            employee = self.env["hr.employee"].search(
                [("user_id", "=", request.requester_id.id)], limit=1
            )
            if employee.department_id:
                request.department_id = employee.department_id

    # ------------------------------------------------------------------
    # ORM overrides
    # ------------------------------------------------------------------
    @api.model_create_multi
    def create(self, vals_list):
        """Allocate the request reference from the company sequence."""
        for vals in vals_list:
            if vals.get("name", _("New")) == _("New"):
                company_id = vals.get("company_id") or self.env.company.id
                company = self.env["res.company"].browse(company_id)
                sequence = self.env["ir.sequence"].with_company(company)
                vals["name"] = sequence.next_by_code(
                    "ls.change_control.request"
                ) or _("New")
        requests = super().create(vals_list)
        for request in requests:
            request.message_subscribe(
                partner_ids=request.requester_id.partner_id.ids
            )
        return requests

    def write(self, vals):
        """Enforce the field level integrity rules before writing.

        :raises AccessError: when a workflow field is written outside of a
            transition method.
        :raises UserError: when a frozen content field is written on a
            submitted request.
        """
        self._check_system_fields(vals)
        self._check_content_fields(vals)
        self._check_writer(vals)
        return super().write(vals)

    @api.ondelete(at_uninstall=False)
    def _ls_unlink_check_ls_change_control_request(self):
        """Forbid the deletion of a submitted request.

        Deleting a submitted change request would destroy quality records.
        Only Draft requests, which carry no decision, may be deleted.
        """
        submitted = self.filtered(lambda r: r.state != "draft")
        if submitted:
            raise UserError(
                _(
                    "The following change requests cannot be deleted because "
                    "they have been submitted: %(names)s.",
                    names=", ".join(submitted.mapped("name")),
                )
            )

    def copy_data(self, default=None):
        """Reset the lifecycle data when a request is duplicated."""
        default = dict(default or {})
        default.setdefault("name", _("New"))
        default.setdefault("state", "draft")
        default.setdefault("date_request", fields.Datetime.now())
        vals_list = super().copy_data(default=default)
        for vals in vals_list:
            vals.pop("assessment_ids", None)
            vals.pop("approval_ids", None)
            vals.pop("implementation_ids", None)
            vals.pop("verification_ids", None)
        return vals_list

    # ------------------------------------------------------------------
    # Integrity helpers
    # ------------------------------------------------------------------
    def _check_system_fields(self, vals):
        """Reject a direct write on a workflow field."""
        if self.env.su:
            return
        forbidden = sorted(set(vals) & set(self._SYSTEM_FIELDS))
        if forbidden:
            raise AccessError(
                _(
                    "The following fields are maintained by the change "
                    "control workflow and cannot be written directly: "
                    "%(fields)s.",
                    fields=", ".join(forbidden),
                )
            )

    def _check_content_fields(self, vals):
        """Reject a write on a frozen field of a submitted request."""
        touched = sorted(set(vals) & set(self._CONTENT_FIELDS))
        if not touched:
            return
        submitted = self.filtered(lambda r: r.state != "draft")
        if submitted:
            raise UserError(
                _(
                    "Request %(name)s has been submitted. The fields "
                    "%(fields)s are frozen. A modification of the change "
                    "itself requires a new change request.",
                    name=submitted[0].name,
                    fields=", ".join(touched),
                )
            )

    def _check_writer(self, vals):
        """Reserve business modifications of a submitted request to managers.

        Once a request has been submitted, only a change control manager may
        modify it. Messaging and activity fields are excluded from the check
        because they carry the discussion and the tasks of the record, not
        the change itself.
        """
        if self.env.su:
            return
        business_fields = [
            name
            for name in vals
            if not name.startswith(self._TECHNICAL_FIELD_PREFIXES)
        ]
        if not business_fields:
            return
        submitted = self.filtered(lambda r: r.state != "draft")
        if not submitted:
            return
        if not self.env.user.has_group(
            "ls_change_control.group_ls_change_control_manager"
        ):
            raise AccessError(
                _(
                    "Request %(name)s has been submitted. Only a Change "
                    "Control Manager may modify it.",
                    name=submitted[0].name,
                )
            )

    def _check_manager(self):
        """Ensure the current user is a change control manager."""
        if not self.env.user.has_group(
            "ls_change_control.group_ls_change_control_manager"
        ):
            raise AccessError(
                _("Only a Change Control Manager may perform this operation.")
            )

    def _check_state(self, expected):
        """Ensure every record of the set is in one of the expected states.

        :param expected: tuple of accepted state technical values.
        :raises UserError: when at least one record is in another state.
        """
        wrong = self.filtered(lambda r: r.state not in expected)
        if wrong:
            labels = dict(STATES)
            raise UserError(
                _(
                    "Request %(name)s is in state '%(state)s'. This "
                    "operation is only allowed in: %(expected)s.",
                    name=wrong[0].name,
                    state=labels.get(wrong[0].state, wrong[0].state),
                    expected=", ".join(labels.get(s, s) for s in expected),
                )
            )

    def _get_blocking_reasons(self):
        """Return the human readable items blocking the next transition.

        :return: list of strings, empty when the next transition is allowed.
        """
        self.ensure_one()
        reasons = []
        if self.state == "under_review":
            if not self.manager_id:
                reasons.append(_("No change control manager is assigned."))
            if not self.impact_area_ids:
                reasons.append(_("No impact area is selected."))
            if not self.approval_ids:
                reasons.append(_("No approval is defined."))
            unassigned = self.approval_ids.filtered(lambda a: not a.user_id)
            if unassigned:
                reasons.append(
                    _("%(count)s approval(s) have no approver assigned.",
                      count=len(unassigned))
                )
        elif self.state == "impact_assessment":
            pending_assessments = self.assessment_ids.filtered(
                lambda a: a.state != "completed"
                and a.impact_area_id.requires_assessment
            )
            for assessment in pending_assessments:
                reasons.append(
                    _("Assessment of area '%(area)s' is not completed.",
                      area=assessment.impact_area_id.name)
                )
            pending_approvals = self.approval_ids.filtered(
                lambda a: a.mandatory and a.state == "pending"
            )
            for approval in pending_approvals:
                reasons.append(
                    _("Approval '%(role)s' is still pending.",
                      role=approval.display_name)
                )
        elif self.state == "implementation":
            open_actions = self.implementation_ids.filtered(
                lambda a: a.state in ("pending", "in_progress")
            )
            if open_actions and self.company_id.ls_cc_block_close_on_open_actions:
                for action in open_actions:
                    reasons.append(
                        _("Implementation action '%(name)s' is not closed.",
                          name=action.name)
                    )
            if self._is_verification_required():
                completed = self.verification_ids.filtered(
                    lambda v: v.state == "completed"
                )
                if not completed:
                    reasons.append(
                        _("No effectiveness verification has been completed.")
                    )
                ineffective = completed.filtered(
                    lambda v: v.result == "not_effective"
                )
                for verification in ineffective:
                    reasons.append(
                        _("Verification '%(name)s' concluded that the change "
                          "is not effective.", name=verification.name)
                    )
        return reasons

    def _is_verification_required(self):
        """Tell whether an effectiveness verification must be completed."""
        self.ensure_one()
        return bool(
            self.company_id.ls_cc_require_verification
            and self.category_id.requires_verification
        )

    # ------------------------------------------------------------------
    # Workflow generation
    # ------------------------------------------------------------------
    def _generate_assessments(self):
        """Create one assessment per impact area that has none yet."""
        assessment_model = self.env["ls.change_control.assessment"]
        vals_list = []
        for request in self:
            existing = request.assessment_ids.mapped("impact_area_id")
            for area in request.impact_area_ids - existing:
                vals_list.append(
                    {
                        "request_id": request.id,
                        "impact_area_id": area.id,
                        "assessor_id": request.manager_id.id or False,
                    }
                )
        if vals_list:
            assessment_model.sudo().create(vals_list)

    def _generate_approvals(self):
        """Create the approvals defined by the category approval template."""
        approval_model = self.env["ls.change_control.approval"]
        vals_list = []
        for request in self:
            existing = set(request.approval_ids.mapped("approval_role"))
            for template in request.category_id.approval_template_ids:
                if template.approval_role in existing:
                    continue
                vals_list.append(
                    {
                        "request_id": request.id,
                        "sequence": template.sequence,
                        "approval_role": template.approval_role,
                        "user_id": template.user_id.id or False,
                        "mandatory": template.mandatory,
                    }
                )
        if vals_list:
            approval_model.sudo().create(vals_list)

    # ------------------------------------------------------------------
    # Workflow transitions
    # ------------------------------------------------------------------
    def action_submit_review(self):
        """Move a Draft request to Under Review.

        The requester or a change control manager may submit. Submitting
        freezes the content fields of the request.
        """
        self._check_state(("draft",))
        for request in self:
            if (
                request.requester_id != self.env.user
                and not self.env.user.has_group(
                    "ls_change_control.group_ls_change_control_manager"
                )
            ):
                raise AccessError(
                    _("Only the requester or a Change Control Manager may "
                      "submit request %(name)s.", name=request.name)
                )
        self.sudo().write({"state": "under_review"})
        self._notify_managers_of_submission()
        return True

    def action_start_assessment(self):
        """Move an Under Review request to Impact Assessment.

        Generates the assessments and the approvals defined by the category
        when they do not exist yet.
        """
        self._check_manager()
        self._check_state(("under_review",))
        self._generate_assessments()
        self._generate_approvals()
        for request in self:
            reasons = request._get_blocking_reasons()
            if reasons:
                raise UserError(
                    _(
                        "Request %(name)s cannot start the impact "
                        "assessment:\n%(reasons)s",
                        name=request.name,
                        reasons="\n".join("- %s" % r for r in reasons),
                    )
                )
        self.sudo().write({"state": "impact_assessment"})
        self.approval_ids.filtered(
            lambda a: a.state == "pending"
        )._notify_approver()
        return True

    def action_reset_draft(self):
        """Send an Under Review request back to Draft.

        Only a change control manager may do so, and only before the impact
        assessment has started. Rejected, cancelled and closed requests are
        final and are never reopened.
        """
        self._check_manager()
        self._check_state(("under_review",))
        self.sudo().write({"state": "draft"})
        for request in self:
            request.message_post(
                body=_("Request returned to Draft for completion."),
                subtype_xmlid="mail.mt_note",
            )
        return True

    def _try_approve(self):
        """Move to Approved when every blocking item has been cleared.

        Called by the approval lines. Records that still have outstanding
        items are left untouched.
        """
        for request in self:
            if request.state != "impact_assessment":
                continue
            if request._get_blocking_reasons():
                continue
            values = {
                "state": "approved",
                "date_approved": fields.Datetime.now(),
            }
            if (
                not request.date_planned_implementation
                and request.category_id.implementation_delay
            ):
                values["date_planned_implementation"] = (
                    fields.Date.context_today(request)
                    + timedelta(days=request.category_id.implementation_delay)
                )
            request.sudo().write(values)
            request._send_mail_template(
                "ls_change_control.mail_template_change_approved"
            )
        return True

    def action_start_implementation(self):
        """Move an Approved request to Implementation."""
        self._check_manager()
        self._check_state(("approved",))
        for request in self:
            if not request.implementation_ids:
                raise UserError(
                    _(
                        "Request %(name)s has no implementation action. "
                        "At least one action must be planned before the "
                        "implementation starts.",
                        name=request.name,
                    )
                )
        self.sudo().write({"state": "implementation"})
        return True

    def action_verify(self):
        """Move an Implementation request to Verified."""
        self._check_manager()
        self._check_state(("implementation",))
        for request in self:
            reasons = request._get_blocking_reasons()
            if reasons:
                raise UserError(
                    _(
                        "Request %(name)s cannot be verified:\n%(reasons)s",
                        name=request.name,
                        reasons="\n".join("- %s" % r for r in reasons),
                    )
                )
        self.sudo().write({"state": "verified"})
        return True

    def action_open_close_wizard(self):
        """Open the closure wizard on the selected requests."""
        return self._open_decision_wizard("close")

    def action_open_reject_wizard(self):
        """Open the rejection wizard on the selected requests."""
        return self._open_decision_wizard("reject")

    def action_open_cancel_wizard(self):
        """Open the cancellation wizard on the selected requests."""
        return self._open_decision_wizard("cancel")

    def _open_decision_wizard(self, mode):
        """Return the window action opening the decision wizard.

        :param mode: one of ``close``, ``reject`` or ``cancel``.
        """
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": dict(
                close=_("Close Change Request"),
                reject=_("Reject Change Request"),
                cancel=_("Cancel Change Request"),
            )[mode],
            "res_model": "ls.change_control.decision_wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_request_id": self.id,
                "default_mode": mode,
            },
        }

    def action_close(self, closure_statement):
        """Close a Verified request.

        :param closure_statement: mandatory conclusion recorded at closure.
        """
        self._check_manager()
        self._check_state(("verified",))
        if not closure_statement or not closure_statement.strip():
            raise UserError(_("A closure statement is required."))
        self.sudo().write(
            {
                "state": "closed",
                "date_closed": fields.Datetime.now(),
                "closure_statement": closure_statement,
            }
        )
        for request in self:
            # Approvers may not hold write access on the request, which Odoo
            # requires to remove its activities.
            request.sudo().activity_unlink(["mail.mail_activity_data_todo"])
        return True

    def action_reject(self, reason):
        """Reject a request under review or under assessment.

        :param reason: mandatory rejection reason.
        """
        self._check_state(("under_review", "impact_assessment"))
        if not reason or not reason.strip():
            raise UserError(_("A rejection reason is required."))
        for request in self:
            is_manager = self.env.user.has_group(
                "ls_change_control.group_ls_change_control_manager"
            )
            is_approver = self.env.user in request.approval_ids.mapped("user_id")
            if not is_manager and not is_approver:
                raise AccessError(
                    _("Only a Change Control Manager or an assigned approver "
                      "may reject request %(name)s.", name=request.name)
                )
        self.sudo().write(
            {
                "state": "rejected",
                "date_rejected": fields.Datetime.now(),
                "rejection_reason": reason,
            }
        )
        for request in self:
            # Approvers may not hold write access on the request, which Odoo
            # requires to remove its activities.
            request.sudo().activity_unlink(["mail.mail_activity_data_todo"])
            request._send_mail_template(
                "ls_change_control.mail_template_change_rejected"
            )
        return True

    def action_cancel(self, reason):
        """Cancel a request that has not been implemented.

        :param reason: mandatory cancellation reason.
        """
        self._check_manager()
        self._check_state(
            ("draft", "under_review", "impact_assessment", "approved")
        )
        if not reason or not reason.strip():
            raise UserError(_("A cancellation reason is required."))
        self.sudo().write(
            {
                "state": "cancelled",
                "date_cancelled": fields.Datetime.now(),
                "cancellation_reason": reason,
            }
        )
        for request in self:
            # Approvers may not hold write access on the request, which Odoo
            # requires to remove its activities.
            request.sudo().activity_unlink(["mail.mail_activity_data_todo"])
        return True

    # ------------------------------------------------------------------
    # Notifications
    # ------------------------------------------------------------------
    def _notify_managers_of_submission(self):
        """Post a note and add the change control managers as followers."""
        group = self.env.ref(
            "ls_change_control.group_ls_change_control_manager",
            raise_if_not_found=False,
        )
        if not group:
            return
        for request in self:
            managers = group.sudo().all_user_ids.filtered(
                lambda u: request.company_id in u.company_ids
            )
            if managers:
                request.message_subscribe(
                    partner_ids=managers.mapped("partner_id").ids
                )
            request.message_post(
                body=_("Change request submitted for review."),
                subtype_xmlid="mail.mt_note",
            )

    def _send_mail_template(self, template_xmlid):
        """Send a mail template on the current record when it exists.

        :param template_xmlid: external identifier of the ``mail.template``.
        """
        self.ensure_one()
        template = self.env.ref(template_xmlid, raise_if_not_found=False)
        if not template:
            _logger.warning(
                "Mail template %s is missing, no notification sent for %s.",
                template_xmlid,
                self.name,
            )
            return
        template.sudo().send_mail(self.id, force_send=False)

    # ------------------------------------------------------------------
    # Smart buttons
    # ------------------------------------------------------------------
    def action_view_assessments(self):
        """Open the impact assessments of the request."""
        return self._action_view_related(
            "ls_change_control.action_ls_change_control_assessment"
        )

    def action_view_approvals(self):
        """Open the approvals of the request."""
        return self._action_view_related(
            "ls_change_control.action_ls_change_control_approval"
        )

    def action_view_implementations(self):
        """Open the implementation actions of the request."""
        return self._action_view_related(
            "ls_change_control.action_ls_change_control_implementation"
        )

    def action_view_verifications(self):
        """Open the effectiveness verifications of the request."""
        return self._action_view_related(
            "ls_change_control.action_ls_change_control_verification"
        )

    def _action_view_related(self, action_xmlid):
        """Return a window action filtered on the current request.

        :param action_xmlid: external identifier of the target action.
        """
        self.ensure_one()
        action = self.env["ir.actions.act_window"]._for_xml_id(action_xmlid)
        action["domain"] = [("request_id", "=", self.id)]
        action["context"] = {"default_request_id": self.id}
        return action

    # ------------------------------------------------------------------
    # Scheduled actions
    # ------------------------------------------------------------------
    @api.model
    def _cron_remind_pending_approvals(self):
        """Remind approvers of the approvals pending for too long.

        A reminder is sent once per day and per approval, for every company
        whose reminder delay is strictly positive.
        """
        approval_model = self.env["ls.change_control.approval"]
        today = fields.Date.context_today(self)
        for company in self.env["res.company"].search([]):
            delay = company.ls_cc_approval_reminder_days
            if delay <= 0:
                continue
            limit_date = today - timedelta(days=delay)
            approvals = approval_model.search(
                [
                    ("company_id", "=", company.id),
                    ("state", "=", "pending"),
                    ("request_state", "=", "impact_assessment"),
                    ("user_id", "!=", False),
                    "|",
                    ("date_reminder", "=", False),
                    ("date_reminder", "<", today),
                    ("date_requested", "<=", limit_date),
                ]
            )
            if approvals:
                approvals._notify_approver(reminder=True)
        return True

    @api.model
    def _cron_remind_overdue_implementations(self):
        """Schedule an activity on the requests whose implementation is late."""
        today = fields.Date.context_today(self)
        requests = self.search(
            [
                ("state", "in", ("approved", "implementation")),
                ("date_planned_implementation", "<", today),
                ("date_actual_implementation", "=", False),
            ]
        )
        for request in requests:
            responsible = request.manager_id or request.requester_id
            request._schedule_todo(
                user=responsible,
                summary=_("Change control implementation overdue"),
                note=_(
                    "The planned implementation date of change request "
                    "%(name)s has passed.",
                    name=request.name,
                ),
            )
        return True

    @api.model
    def _cron_remind_due_verifications(self):
        """Schedule an activity on the requests whose verification is due."""
        today = fields.Date.context_today(self)
        requests = self.search(
            [
                ("state", "=", "implementation"),
                ("date_verification_planned", "!=", False),
                ("date_verification_planned", "<=", today),
            ]
        )
        for request in requests:
            if not request._is_verification_required():
                continue
            if request.verification_ids.filtered(
                lambda v: v.state == "completed"
            ):
                continue
            responsible = request.manager_id or request.requester_id
            request._schedule_todo(
                user=responsible,
                summary=_("Change control effectiveness verification due"),
                note=_(
                    "The effectiveness verification of change request "
                    "%(name)s is due.",
                    name=request.name,
                ),
            )
        return True

    def _schedule_todo(self, user, summary, note):
        """Schedule a to-do activity, avoiding duplicates.

        :param user: ``res.users`` record the activity is assigned to.
        :param summary: activity summary.
        :param note: activity note.
        """
        self.ensure_one()
        if not user:
            return
        existing = self.activity_ids.filtered(
            lambda a: a.user_id == user and a.summary == summary
        )
        if existing:
            return
        self.activity_schedule(
            "mail.mail_activity_data_todo",
            summary=summary,
            note=note,
            user_id=user.id,
        )
