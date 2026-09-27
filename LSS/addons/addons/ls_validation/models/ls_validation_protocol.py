# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Validation protocol.

A protocol declares *what will be tested and against which acceptance
criteria*, before any test is executed. The module enforces the pre-approval
rule: test cases cannot be added, modified or removed once the protocol has
been approved, and execution records can only be created from an approved
protocol.
"""

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

from .ls_validation_constants import PROTOCOL_TYPES

PROTOCOL_STATES = [
    ("draft", "Draft"),
    ("review", "Under Review"),
    ("approved", "Approved"),
    ("execution", "In Execution"),
    ("executed", "Executed"),
    ("closed", "Closed"),
    ("cancelled", "Cancelled"),
]

#: States in which the content of a protocol may still be edited.
EDITABLE_STATES = ("draft", "review")


class LsValidationProtocol(models.Model):
    """Pre-approved test plan for a validation item."""

    _name = "ls.validation.protocol"
    _description = "Validation Protocol"
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
    previous_version_id = fields.Many2one(comodel_name="ls.validation.protocol", readonly=True,
                                          copy=False,
                                          ondelete="restrict",)
    protocol_type = fields.Selection(selection=PROTOCOL_TYPES, required=True,
                                     tracking=True,)
    state = fields.Selection(
        selection=PROTOCOL_STATES,
        string="Status",
        default="draft",
        required=True,
        tracking=True,
        copy=False,
    )
    item_id = fields.Many2one(
        comodel_name="ls.validation.item",
        string="Validation Item",
        required=True,
        ondelete="restrict",
        tracking=True,
        check_company=True,
    )
    master_plan_id = fields.Many2one(comodel_name="ls.validation.master.plan", ondelete="restrict",
                                     tracking=True,
                                     check_company=True,)
    objective = fields.Html(sanitize=True)
    scope = fields.Html(sanitize=True)
    prerequisites = fields.Html(sanitize=True,
                                help="Conditions to be met before execution, for example calibration "
                                "status of the instruments used or training of the executors.",)
    reference_documents = fields.Text(help="One reference per line: SOP numbers, drawings, user manuals, "
                                      "risk assessments.",)
    test_ids = fields.One2many(
        comodel_name="ls.validation.protocol.test",
        inverse_name="protocol_id",
        string="Test Cases",
        copy=True,
    )
    test_count = fields.Integer(compute="_compute_test_count")
    execution_ids = fields.One2many(
        comodel_name="ls.validation.execution",
        inverse_name="protocol_id",
        string="Execution Records",
    )
    execution_count = fields.Integer(compute="_compute_execution_count")
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
    planned_start_date = fields.Date(string="Planned Start", tracking=True)
    planned_end_date = fields.Date(string="Planned End", tracking=True)
    company_id = fields.Many2one(comodel_name="res.company", required=True,
                                 default=lambda self: self.env.company,)

    _unique_reference_version = models.Constraint(
        "UNIQUE(reference, version, company_id)",
        "A protocol with the same reference and version already exists.",
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
        """Display the protocol as ``REFERENCE v<version> - Title``."""
        for protocol in self:
            protocol.display_name = "%s v%s - %s" % (
                protocol.reference or "",
                protocol.version,
                protocol.name or "",
            )

    @api.depends("test_ids")
    def _compute_test_count(self):
        """Count the test cases of the protocol."""
        for protocol in self:
            protocol.test_count = len(protocol.test_ids)

    @api.depends("execution_ids")
    def _compute_execution_count(self):
        """Count the execution records generated from the protocol."""
        for protocol in self:
            protocol.execution_count = len(protocol.execution_ids)

    # ------------------------------------------------------------------
    # Constraints
    # ------------------------------------------------------------------
    @api.constrains("planned_start_date", "planned_end_date")
    def _check_planned_dates(self):
        """The planned end date cannot precede the planned start date."""
        for protocol in self:
            if (
                protocol.planned_start_date
                and protocol.planned_end_date
                and protocol.planned_end_date < protocol.planned_start_date
            ):
                raise ValidationError(
                    _("The planned end date cannot precede the planned start date.")
                )

    @api.constrains("item_id", "master_plan_id")
    def _check_item_in_master_plan(self):
        """Warn against a protocol referencing an item outside its plan scope."""
        for protocol in self:
            plan = protocol.master_plan_id
            if plan and plan.item_ids and protocol.item_id not in plan.item_ids:
                raise ValidationError(
                    _(
                        "Item %(item)s is not part of the scope of master plan "
                        "%(plan)s."
                    )
                    % {
                        "item": protocol.item_id.display_name,
                        "plan": plan.display_name,
                    }
                )

    # ------------------------------------------------------------------
    # ORM
    # ------------------------------------------------------------------
    @api.model_create_multi
    def create(self, vals_list):
        """Assign the protocol sequence on creation."""
        for vals in vals_list:
            if vals.get("reference", _("New")) == _("New"):
                company_id = vals.get("company_id", self.env.company.id)
                vals["reference"] = self.env["ir.sequence"].with_company(
                    company_id
                ).next_by_code("ls.validation.protocol") or _("New")
        return super().create(vals_list)

    def write(self, vals):
        """Freeze the pre-approved content after approval."""
        controlled_fields = {
            "name",
            "protocol_type",
            "item_id",
            "objective",
            "scope",
            "prerequisites",
            "reference_documents",
            "test_ids",
            "version",
        }
        if controlled_fields.intersection(vals):
            for protocol in self:
                if protocol.state not in EDITABLE_STATES:
                    raise UserError(
                        _(
                            "Protocol %s is approved or executed: create a new "
                            "version to change its content."
                        )
                        % protocol.display_name
                    )
        return super().write(vals)

    @api.ondelete(at_uninstall=False)
    def _ls_unlink_check_ls_validation_protocol(self):
        """Only draft or cancelled protocols may be deleted."""
        for protocol in self:
            if protocol.state not in ("draft", "cancelled"):
                raise UserError(
                    _(
                        "Protocol %s cannot be deleted because it is not draft "
                        "or cancelled."
                    )
                    % protocol.display_name
                )

    # ------------------------------------------------------------------
    # Workflow
    # ------------------------------------------------------------------
    def action_submit_review(self):
        """Submit a draft protocol for review."""
        for protocol in self:
            if protocol.state != "draft":
                raise UserError(
                    _("Only a draft protocol can be submitted for review.")
                )
            if not protocol.test_ids:
                raise UserError(
                    _("Protocol %s has no test case.") % protocol.display_name
                )
            protocol.state = "review"
            protocol.message_post(body=_("Submitted for review."))
        return True

    def action_back_to_draft(self):
        """Return a protocol under review to the draft state."""
        for protocol in self:
            if protocol.state != "review":
                raise UserError(
                    _("Only a protocol under review can return to draft.")
                )
            protocol.state = "draft"
            protocol.message_post(body=_("Returned to draft."))
        return True

    def action_approve(self):
        """Open the electronic signature wizard to approve the protocol."""
        self.ensure_one()
        if self.state != "review":
            raise UserError(_("Only a protocol under review can be approved."))
        if not self.test_ids:
            raise UserError(
                _("A protocol without test case cannot be approved.")
            )
        missing = self.test_ids.filtered(lambda test: not test.acceptance_criteria)
        if missing:
            raise UserError(
                _("Every test case must define an acceptance criterion.")
            )
        return self._ls_open_sign_wizard(
            meaning="approved",
            callback="_ls_do_approve",
            title=_("Approve Validation Protocol"),
        )

    def _ls_do_approve(self):
        """Apply the approval once the electronic signature is recorded."""
        self.ensure_one()
        self._ls_check_group(
            "ls_validation.group_ls_validation_approver",
            _("Only a Validation Approver may approve a protocol."),
        )
        if self.state != "review":
            raise UserError(_("Only a protocol under review can be approved."))
        self.write(
            {
                "state": "approved",
                "approver_id": self.env.user.id,
                "approval_date": fields.Datetime.now(),
            }
        )
        self.message_post(body=_("Approved and signed electronically."))
        return True

    def action_cancel(self):
        """Cancel a protocol that has never been executed."""
        for protocol in self:
            if protocol.execution_ids:
                raise UserError(
                    _(
                        "Protocol %s has execution records and cannot be "
                        "cancelled."
                    )
                    % protocol.display_name
                )
            protocol.state = "cancelled"
            protocol.message_post(body=_("Protocol cancelled."))
        return True

    def action_close(self):
        """Close an executed protocol."""
        for protocol in self:
            if protocol.state != "executed":
                raise UserError(
                    _("Only an executed protocol can be closed.")
                )
            protocol.state = "closed"
            protocol.message_post(body=_("Protocol closed."))
        return True

    def action_new_version(self):
        """Create the next version of an approved or executed protocol."""
        self.ensure_one()
        if self.state in ("draft", "review"):
            raise UserError(
                _(
                    "A new version is only required for a protocol that is "
                    "already approved."
                )
            )
        new_protocol = self.copy(
            {
                "reference": self.reference,
                "version": self.version + 1,
                "previous_version_id": self.id,
                "state": "draft",
            }
        )
        new_protocol.message_post(
            body=_("Created as version %(version)s of %(reference)s.")
            % {"version": new_protocol.version, "reference": self.reference}
        )
        return {
            "type": "ir.actions.act_window",
            "res_model": self._name,
            "res_id": new_protocol.id,
            "view_mode": "form",
        }

    def action_create_execution(self):
        """Create an execution record from an approved protocol."""
        self.ensure_one()
        if self.state not in ("approved", "execution"):
            raise UserError(
                _(
                    "Execution records can only be created from an approved "
                    "protocol."
                )
            )
        execution = self.env["ls.validation.execution"].create(
            {"protocol_id": self.id}
        )
        if self.state == "approved":
            self.state = "execution"
        return {
            "type": "ir.actions.act_window",
            "res_model": "ls.validation.execution",
            "res_id": execution.id,
            "view_mode": "form",
        }

    def action_view_executions(self):
        """Open the execution records of the protocol."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Execution Records"),
            "res_model": "ls.validation.execution",
            "view_mode": "list,form",
            "domain": [("protocol_id", "=", self.id)],
            "context": {"default_protocol_id": self.id},
        }

    def _mark_in_execution(self):
        """Set an approved protocol to "In Execution" when a run starts."""
        for protocol in self:
            if protocol.state == "approved":
                protocol.state = "execution"
        return True

    def _mark_executed(self):
        """Set the protocol to executed when an execution is approved.

        An execution may be created from the protocol button or directly
        (form, import, code), so an approved protocol is accepted as well as
        a protocol already in execution.
        """
        self.ensure_one()
        if self.state in ("approved", "execution"):
            self.state = "executed"
            self.message_post(
                body=_("All planned executions are approved.")
            )
        return True
