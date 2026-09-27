# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Validation Summary Report (VSR).

The report concludes a validation exercise: it consolidates the approved
execution records, states the conclusion and defines the period during which
the item is considered validated. Approving a report is the only way to grant
the ``validated`` status to an item, which keeps the status traceable to a
signed document.
"""

from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

from .ls_validation_constants import REPORT_CONCLUSION

REPORT_STATES = [
    ("draft", "Draft"),
    ("review", "Under Review"),
    ("approved", "Approved"),
    ("cancelled", "Cancelled"),
]


class LsValidationReport(models.Model):
    """Signed conclusion of a validation exercise."""

    _name = "ls.validation.report"
    _description = "Validation Summary Report"
    _inherit = [
        "mail.thread",
        "mail.activity.mixin",
        "ls.validation.signature.mixin",
    ]
    _order = "reference desc"
    _check_company_auto = True

    _ls_signable_callbacks = ("_ls_do_approve",)

    reference = fields.Char(required=True,
                            readonly=True,
                            copy=False,
                            default=lambda self: _("New"),
                            index=True,
                            )
    name = fields.Char(string="Title", required=True, tracking=True)
    item_id = fields.Many2one(
        comodel_name="ls.validation.item",
        string="Validation Item",
        required=True,
        ondelete="restrict",
        tracking=True,
        check_company=True,
    )
    master_plan_id = fields.Many2one(comodel_name="ls.validation.master.plan", ondelete="restrict",
                                     check_company=True,)
    execution_ids = fields.Many2many(
        comodel_name="ls.validation.execution",
        relation="ls_validation_report_execution_rel",
        column1="report_id",
        column2="execution_id",
        string="Execution Records",
        check_company=True,
    )
    protocol_ids = fields.Many2many(
        comodel_name="ls.validation.protocol",
        string="Protocols Covered",
        compute="_compute_protocol_ids",
    )
    state = fields.Selection(
        selection=REPORT_STATES,
        string="Status",
        default="draft",
        required=True,
        tracking=True,
        copy=False,
    )
    conclusion = fields.Selection(selection=REPORT_CONCLUSION, required=True,
                                  default="validated",
                                  tracking=True,)
    restrictions = fields.Text(help="Conditions of use imposed by the conclusion, mandatory when the "
                               "conclusion is 'Validated with Restrictions'.",)
    summary = fields.Html(sanitize=True,
                          help="Summary of the executions performed, deviations encountered and "
                          "conclusions drawn.",)
    open_discrepancy_count = fields.Integer(
        string="Open Discrepancies",
        compute="_compute_discrepancy_summary",
    )
    failed_test_count = fields.Integer(
        string="Failed Tests",
        compute="_compute_discrepancy_summary",
    )
    report_date = fields.Date(required=True,
                              default=fields.Date.context_today,
                              tracking=True,)
    valid_from = fields.Date(tracking=True, copy=False)
    validity_months = fields.Integer(
        string="Validity (months)",
        default=36,
        tracking=True,
        help="Period of validity granted by this report. Set to 0 for a "
             "validation without expiry.",
    )
    valid_until = fields.Date(compute="_compute_valid_until",
                              store=True,
                              tracking=True,)
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
    company_id = fields.Many2one(comodel_name="res.company", required=True,
                                 default=lambda self: self.env.company,)

    _positive_validity = models.Constraint(
        "CHECK(validity_months >= 0)",
        "The validity period cannot be negative.",
    )

    # ------------------------------------------------------------------
    # Compute
    # ------------------------------------------------------------------
    @api.depends("reference", "name")
    def _compute_display_name(self):
        """Display the report as ``REFERENCE - Title``."""
        for report in self:
            report.display_name = "%s - %s" % (
                report.reference or "",
                report.name or "",
            )

    @api.depends("execution_ids.protocol_id")
    def _compute_protocol_ids(self):
        """List the protocols covered by the selected executions."""
        for report in self:
            report.protocol_ids = report.execution_ids.mapped("protocol_id")

    @api.depends("valid_from", "validity_months")
    def _compute_valid_until(self):
        """Compute the expiry date of the validated status."""
        for report in self:
            if report.valid_from and report.validity_months > 0:
                report.valid_until = report.valid_from + relativedelta(
                    months=report.validity_months
                )
            else:
                report.valid_until = False

    @api.depends(
        "execution_ids.open_discrepancy_count", "execution_ids.failed_count"
    )
    def _compute_discrepancy_summary(self):
        """Aggregate the open discrepancies and failures of the executions."""
        for report in self:
            report.open_discrepancy_count = sum(
                report.execution_ids.mapped("open_discrepancy_count")
            )
            report.failed_test_count = sum(
                report.execution_ids.mapped("failed_count")
            )

    # ------------------------------------------------------------------
    # Constraints
    # ------------------------------------------------------------------
    @api.constrains("conclusion", "restrictions")
    def _check_restrictions(self):
        """Restrictions are mandatory for a restricted conclusion."""
        for report in self:
            if report.conclusion == "validated_restricted" and not report.restrictions:
                raise ValidationError(
                    _(
                        "The restrictions must be documented when the "
                        "conclusion is 'Validated with Restrictions'."
                    )
                )

    @api.constrains("execution_ids", "item_id")
    def _check_executions_item(self):
        """Every execution of the report must concern the reported item."""
        for report in self:
            wrong = report.execution_ids.filtered(
                lambda execution: execution.item_id != report.item_id
            )
            if wrong:
                raise ValidationError(
                    _(
                        "Execution record(s) %s do not concern the item of "
                        "this report."
                    )
                    % ", ".join(wrong.mapped("reference"))
                )

    @api.constrains("valid_from", "report_date")
    def _check_valid_from(self):
        """The validity cannot start before the report date."""
        for report in self:
            if (
                report.valid_from
                and report.report_date
                and report.valid_from < report.report_date
            ):
                raise ValidationError(
                    _("The validity cannot start before the report date.")
                )

    # ------------------------------------------------------------------
    # ORM
    # ------------------------------------------------------------------
    @api.model_create_multi
    def create(self, vals_list):
        """Assign the report sequence on creation."""
        for vals in vals_list:
            if vals.get("reference", _("New")) == _("New"):
                company_id = vals.get("company_id", self.env.company.id)
                vals["reference"] = self.env["ir.sequence"].with_company(
                    company_id
                ).next_by_code("ls.validation.report") or _("New")
        return super().create(vals_list)

    def write(self, vals):
        """Freeze the content of an approved report."""
        controlled_fields = {
            "name",
            "item_id",
            "execution_ids",
            "conclusion",
            "restrictions",
            "summary",
            "valid_from",
            "validity_months",
            "report_date",
        }
        if controlled_fields.intersection(vals):
            for report in self:
                if report.state == "approved":
                    raise UserError(
                        _(
                            "Approved report %s can no longer be modified. "
                            "Issue a new report instead."
                        )
                        % report.display_name
                    )
        return super().write(vals)

    @api.ondelete(at_uninstall=False)
    def _ls_unlink_check_ls_validation_report(self):
        """Only draft or cancelled reports may be deleted."""
        for report in self:
            if report.state not in ("draft", "cancelled"):
                raise UserError(
                    _(
                        "Report %s cannot be deleted because it is under "
                        "review or approved."
                    )
                    % report.display_name
                )

    # ------------------------------------------------------------------
    # Workflow
    # ------------------------------------------------------------------
    def _check_ready_for_review(self):
        """Verify the completeness rules before review."""
        self.ensure_one()
        if not self.execution_ids:
            raise UserError(
                _("The report must reference at least one execution record.")
            )
        not_approved = self.execution_ids.filtered(
            lambda execution: execution.state != "approved"
        )
        if not_approved:
            raise UserError(
                _("Execution record(s) %s are not approved.")
                % ", ".join(not_approved.mapped("reference"))
            )
        if not self.summary:
            raise UserError(_("The summary must be documented."))
        return True

    def action_submit_review(self):
        """Submit a draft report for review."""
        for report in self:
            if report.state != "draft":
                raise UserError(
                    _("Only a draft report can be submitted for review.")
                )
            report._check_ready_for_review()
            report.state = "review"
            report.message_post(body=_("Submitted for review."))
        return True

    def action_back_to_draft(self):
        """Return a report under review to the draft state."""
        for report in self:
            if report.state != "review":
                raise UserError(
                    _("Only a report under review can return to draft.")
                )
            report.state = "draft"
            report.message_post(body=_("Returned to draft."))
        return True

    def action_approve(self):
        """Open the electronic signature wizard to approve the report."""
        self.ensure_one()
        if self.state != "review":
            raise UserError(_("Only a report under review can be approved."))
        if self.open_discrepancy_count:
            raise UserError(
                _(
                    "%d discrepancy(ies) linked to the executions are still "
                    "open."
                )
                % self.open_discrepancy_count
            )
        if self.conclusion == "validated":
            critical_failures = self.execution_ids.mapped("result_ids").filtered(
                lambda line: line.verdict == "fail" and line.is_critical
            )
            if critical_failures:
                raise UserError(
                    _(
                        "%d critical test case(s) failed: the conclusion "
                        "cannot be 'Validated'."
                    )
                    % len(critical_failures)
                )
        return self._ls_open_sign_wizard(
            meaning="approved",
            callback="_ls_do_approve",
            title=_("Approve Validation Summary Report"),
        )

    def _ls_do_approve(self):
        """Apply the approval once the electronic signature is recorded."""
        self.ensure_one()
        self._ls_check_group(
            "ls_validation.group_ls_validation_approver",
            _("Only a Validation Approver may approve a summary report."),
        )
        if self.state != "review":
            raise UserError(_("Only a report under review can be approved."))
        values = {
            "state": "approved",
            "approver_id": self.env.user.id,
            "approval_date": fields.Datetime.now(),
        }
        if not self.valid_from:
            values["valid_from"] = fields.Date.context_today(self)
        self.write(values)
        self.message_post(body=_("Report approved and signed electronically."))
        self.item_id._ls_recompute_stored("_compute_validation_status")
        return True

    def action_cancel(self):
        """Cancel a report that has not been approved."""
        for report in self:
            if report.state == "approved":
                raise UserError(
                    _("An approved report cannot be cancelled.")
                )
            report.state = "cancelled"
            report.message_post(body=_("Report cancelled."))
        return True

    def action_view_executions(self):
        """Open the execution records consolidated by the report."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Execution Records"),
            "res_model": "ls.validation.execution",
            "view_mode": "list,form",
            "domain": [("id", "in", self.execution_ids.ids)],
        }
