# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Execution record of a validation protocol.

The execution record is the raw evidence container: it copies the pre-approved
test cases into result lines, records the observed results, and is reviewed and
approved with electronic signatures. A failed result must be linked to a
discrepancy, and an execution carrying an open discrepancy cannot be approved.
"""

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

EXECUTION_STATES = [
    ("draft", "Draft"),
    ("in_progress", "In Progress"),
    ("completed", "Completed"),
    ("reviewed", "Reviewed"),
    ("approved", "Approved"),
    ("rejected", "Rejected"),
    ("cancelled", "Cancelled"),
]

OVERALL_RESULTS = [
    ("pending", "Pending"),
    ("pass", "Pass"),
    ("fail", "Fail"),
]


class LsValidationExecution(models.Model):
    """Execution of a protocol, holding the observed results."""

    _name = "ls.validation.execution"
    _description = "Validation Execution Record"
    _inherit = [
        "mail.thread",
        "mail.activity.mixin",
        "ls.validation.signature.mixin",
    ]
    _order = "reference desc"
    _check_company_auto = True

    _ls_signable_callbacks = ("_ls_do_review", "_ls_do_approve")

    reference = fields.Char(required=True,
                            readonly=True,
                            copy=False,
                            default=lambda self: _("New"),
                            index=True,
                            )
    protocol_id = fields.Many2one(comodel_name="ls.validation.protocol", required=True,
                                  ondelete="restrict",
                                  tracking=True,
                                  check_company=True,)
    protocol_type = fields.Selection(related="protocol_id.protocol_type", store=True,
                                     readonly=True,)
    item_id = fields.Many2one(
        comodel_name="ls.validation.item",
        string="Validation Item",
        related="protocol_id.item_id",
        store=True,
        readonly=True,
    )
    execution_round = fields.Integer(required=True,
                                     default=1,
                                     tracking=True,
                                     help="Sequential number of the execution attempt for this protocol.",)
    state = fields.Selection(
        selection=EXECUTION_STATES,
        string="Status",
        default="draft",
        required=True,
        tracking=True,
        copy=False,
    )
    date_start = fields.Datetime(string="Start", readonly=True, copy=False)
    date_end = fields.Datetime(string="End", readonly=True, copy=False)
    executed_by_id = fields.Many2one(
        comodel_name="res.users",
        string="Executed by",
        default=lambda self: self.env.user,
        tracking=True,
    )
    reviewed_by_id = fields.Many2one(
        comodel_name="res.users",
        string="Reviewed by",
        readonly=True,
        copy=False,
        tracking=True,
    )
    review_date = fields.Datetime(readonly=True, copy=False)
    approved_by_id = fields.Many2one(
        comodel_name="res.users",
        string="Approved by",
        readonly=True,
        copy=False,
        tracking=True,
    )
    approval_date = fields.Datetime(readonly=True, copy=False, tracking=True)
    rejection_reason = fields.Text(copy=False)
    result_ids = fields.One2many(
        comodel_name="ls.validation.execution.result",
        inverse_name="execution_id",
        string="Results",
    )
    discrepancy_ids = fields.One2many(
        comodel_name="ls.validation.discrepancy",
        inverse_name="execution_id",
        string="Discrepancies",
    )
    discrepancy_count = fields.Integer(compute="_compute_discrepancy_count")
    open_discrepancy_count = fields.Integer(
        string="Open Discrepancies", compute="_compute_discrepancy_count", search="_search_open_discrepancy_count"
    )
    test_count = fields.Integer(string="Tests", compute="_compute_result_summary")
    passed_count = fields.Integer(string="Passed", compute="_compute_result_summary")
    failed_count = fields.Integer(string="Failed", compute="_compute_result_summary", search="_search_failed_count")
    pending_count = fields.Integer(string="Pending", compute="_compute_result_summary")
    na_count = fields.Integer(string="Not Applicable", compute="_compute_result_summary")
    overall_result = fields.Selection(selection=OVERALL_RESULTS, compute="_compute_result_summary",
                                      store=True,)
    remarks = fields.Html(sanitize=True)
    company_id = fields.Many2one(comodel_name="res.company", required=True,
                                 default=lambda self: self.env.company,)

    _unique_round_per_protocol = models.Constraint(
        "UNIQUE(protocol_id, execution_round)",
        "An execution round with the same number already exists for this "
        "protocol.",
    )
    _positive_round = models.Constraint(
        "CHECK(execution_round > 0)",
        "The execution round must be strictly positive.",
    )

    # ------------------------------------------------------------------
    # Compute
    # ------------------------------------------------------------------
    @api.depends("reference", "protocol_id")
    def _compute_display_name(self):
        """Display the execution as ``REFERENCE - Protocol title``."""
        for execution in self:
            execution.display_name = "%s - %s" % (
                execution.reference or "",
                execution.protocol_id.name or "",
            )

    @api.depends("result_ids.verdict")
    def _compute_result_summary(self):
        """Aggregate the verdicts of the result lines."""
        for execution in self:
            results = execution.result_ids
            execution.test_count = len(results)
            execution.passed_count = len(
                results.filtered(lambda line: line.verdict == "pass")
            )
            execution.failed_count = len(
                results.filtered(lambda line: line.verdict == "fail")
            )
            execution.pending_count = len(
                results.filtered(lambda line: line.verdict == "pending")
            )
            execution.na_count = len(
                results.filtered(lambda line: line.verdict == "na")
            )
            if not results or execution.pending_count:
                execution.overall_result = "pending"
            elif execution.failed_count:
                execution.overall_result = "fail"
            else:
                execution.overall_result = "pass"

    @api.depends("discrepancy_ids.state")
    def _compute_discrepancy_count(self):
        """Count all and still open discrepancies."""
        for execution in self:
            execution.discrepancy_count = len(execution.discrepancy_ids)
            execution.open_discrepancy_count = len(
                execution.discrepancy_ids.filtered(
                    lambda discrepancy: discrepancy.state
                    not in ("closed", "cancelled")
                )
            )

    # ------------------------------------------------------------------
    # Constraints
    # ------------------------------------------------------------------
    @api.constrains("protocol_id", "state")
    def _check_protocol_approved(self):
        """An execution can only exist for an approved protocol."""
        for execution in self:
            if execution.protocol_id.state in ("draft", "review", "cancelled"):
                raise ValidationError(
                    _(
                        "Protocol %s must be approved before its execution can "
                        "be recorded."
                    )
                    % execution.protocol_id.display_name
                )

    @api.constrains("date_start", "date_end")
    def _check_dates(self):
        """The end date cannot precede the start date."""
        for execution in self:
            if (
                execution.date_start
                and execution.date_end
                and execution.date_end < execution.date_start
            ):
                raise ValidationError(
                    _("The end date cannot precede the start date.")
                )

    # ------------------------------------------------------------------
    # ORM
    # ------------------------------------------------------------------
    @api.model_create_multi
    def create(self, vals_list):
        """Assign the sequence and the next execution round."""
        for vals in vals_list:
            if vals.get("reference", _("New")) == _("New"):
                company_id = vals.get("company_id", self.env.company.id)
                vals["reference"] = self.env["ir.sequence"].with_company(
                    company_id
                ).next_by_code("ls.validation.execution") or _("New")
            if not vals.get("execution_round") and vals.get("protocol_id"):
                previous = self.search(
                    [("protocol_id", "=", vals["protocol_id"])],
                    order="execution_round desc",
                    limit=1,
                )
                vals["execution_round"] = (previous.execution_round or 0) + 1
        executions = super().create(vals_list)
        executions._generate_results()
        return executions

    def write(self, vals):
        """Prevent changing the protocol once results have been recorded."""
        if "protocol_id" in vals:
            for execution in self:
                if execution.state != "draft":
                    raise UserError(
                        _(
                            "The protocol of execution %s can no longer be "
                            "changed."
                        )
                        % execution.display_name
                    )
        return super().write(vals)

    @api.ondelete(at_uninstall=False)
    def _ls_unlink_check_ls_validation_execution(self):
        """Only draft or cancelled executions may be deleted."""
        for execution in self:
            if execution.state not in ("draft", "cancelled"):
                raise UserError(
                    _(
                        "Execution %s cannot be deleted because results have "
                        "been recorded."
                    )
                    % execution.display_name
                )

    # ------------------------------------------------------------------
    # Search methods for computed fields
    # ------------------------------------------------------------------
    def _search_failed_count(self, operator, value):
        """Allow filtering on the non-stored failed_count field.

        :param str operator: one of =, !=, in, not in, <, >, <=, >=
        :param int value: count to compare
        :return: domain for matching records
        :rtype: list
        """
        matching_ids = [
            record.id for record in self.search([])
            if self._evaluate_operator(record.failed_count, operator, value)
        ]
        return [("id", "in", matching_ids)]

    def _search_open_discrepancy_count(self, operator, value):
        """Allow filtering on the non-stored open_discrepancy_count field.

        :param str operator: one of =, !=, in, not in, <, >, <=, >=
        :param int value: count to compare
        :return: domain for matching records
        :rtype: list
        """
        matching_ids = [
            record.id for record in self.search([])
            if self._evaluate_operator(record.open_discrepancy_count, operator, value)
        ]
        return [("id", "in", matching_ids)]

    @staticmethod
    def _evaluate_operator(actual, operator, expected):
        """Evaluate a comparison operator between two values."""
        ops = {
            "=": lambda a, b: a == b,
            "!=": lambda a, b: a != b,
            "<": lambda a, b: a < b,
            ">": lambda a, b: a > b,
            "<=": lambda a, b: a <= b,
            ">=": lambda a, b: a >= b,
            # Odoo 19 normalises "=" and "!=" to "in" and "not in" before it
            # calls a field search method.
            "in": lambda a, b: a in b,
            "not in": lambda a, b: a not in b,
        }
        return ops.get(operator, lambda a, b: False)(actual, expected)

    # ------------------------------------------------------------------
    # Business methods
    # ------------------------------------------------------------------
    def _generate_results(self):
        """Copy the pre-approved test cases into result lines."""
        result_model = self.env["ls.validation.execution.result"]
        for execution in self:
            existing = execution.result_ids.mapped("protocol_test_id")
            missing = execution.protocol_id.test_ids - existing
            for test in missing:
                result_model.create(
                    {
                        "execution_id": execution.id,
                        "protocol_test_id": test.id,
                        "sequence": test.sequence,
                    }
                )
        return True

    def action_regenerate_results(self):
        """Add result lines for test cases that are not yet listed."""
        for execution in self:
            if execution.state not in ("draft", "in_progress"):
                raise UserError(
                    _(
                        "Result lines can only be generated while the execution "
                        "is draft or in progress."
                    )
                )
        return self._generate_results()

    # ------------------------------------------------------------------
    # Workflow
    # ------------------------------------------------------------------
    def action_start(self):
        """Start the execution and stamp the start date."""
        for execution in self:
            if execution.state != "draft":
                raise UserError(
                    _("Only a draft execution can be started.")
                )
            if not execution.result_ids:
                raise UserError(
                    _("The execution has no result line to complete.")
                )
            execution.write(
                {
                    "state": "in_progress",
                    "date_start": fields.Datetime.now(),
                    "executed_by_id": self.env.user.id,
                }
            )
            execution.message_post(body=_("Execution started."))
            execution.protocol_id._mark_in_execution()
        return True

    def action_complete(self):
        """Close the data entry once every result carries a verdict."""
        for execution in self:
            if execution.state != "in_progress":
                raise UserError(
                    _("Only an execution in progress can be completed.")
                )
            pending = execution.result_ids.filtered(
                lambda line: line.verdict == "pending"
            )
            if pending:
                raise UserError(
                    _("%d result line(s) still have no verdict.") % len(pending)
                )
            missing_actual = execution.result_ids.filtered(
                lambda line: line.verdict in ("pass", "fail")
                and not line.actual_result
            )
            if missing_actual:
                raise UserError(
                    _(
                        "%d result line(s) have a verdict but no observed "
                        "result."
                    )
                    % len(missing_actual)
                )
            unlinked_failures = execution.result_ids.filtered(
                lambda line: line.verdict == "fail" and not line.discrepancy_id
            )
            if unlinked_failures:
                raise UserError(
                    _(
                        "Every failed test case must be linked to a "
                        "discrepancy. %d failure(s) are not linked."
                    )
                    % len(unlinked_failures)
                )
            execution.write(
                {"state": "completed", "date_end": fields.Datetime.now()}
            )
            execution.message_post(body=_("Execution completed."))
        return True

    def action_review(self):
        """Open the electronic signature wizard for the review."""
        self.ensure_one()
        if self.state != "completed":
            raise UserError(
                _("Only a completed execution can be reviewed.")
            )
        return self._ls_open_sign_wizard(
            meaning="reviewed",
            callback="_ls_do_review",
            title=_("Review Execution Record"),
        )

    def _ls_do_review(self):
        """Apply the review once the electronic signature is recorded."""
        self.ensure_one()
        if self.state != "completed":
            raise UserError(_("Only a completed execution can be reviewed."))
        if self.executed_by_id == self.env.user:
            raise UserError(
                _(
                    "The reviewer must be different from the person who "
                    "executed the tests."
                )
            )
        self.write(
            {
                "state": "reviewed",
                "reviewed_by_id": self.env.user.id,
                "review_date": fields.Datetime.now(),
            }
        )
        self.message_post(body=_("Execution reviewed and signed electronically."))
        return True

    def action_approve(self):
        """Open the electronic signature wizard for the approval."""
        self.ensure_one()
        if self.state != "reviewed":
            raise UserError(
                _("Only a reviewed execution can be approved.")
            )
        if self.open_discrepancy_count:
            raise UserError(
                _(
                    "%d discrepancy(ies) are still open. Close them before "
                    "approving the execution."
                )
                % self.open_discrepancy_count
            )
        return self._ls_open_sign_wizard(
            meaning="approved",
            callback="_ls_do_approve",
            title=_("Approve Execution Record"),
        )

    def _ls_do_approve(self):
        """Apply the approval once the electronic signature is recorded."""
        self.ensure_one()
        self._ls_check_group(
            "ls_validation.group_ls_validation_approver",
            _("Only a Validation Approver may approve an execution record."),
        )
        if self.state != "reviewed":
            raise UserError(_("Only a reviewed execution can be approved."))
        if self.open_discrepancy_count:
            raise UserError(
                _("Open discrepancies prevent the approval of the execution.")
            )
        self.write(
            {
                "state": "approved",
                "approved_by_id": self.env.user.id,
                "approval_date": fields.Datetime.now(),
            }
        )
        self.message_post(body=_("Execution approved and signed electronically."))
        protocol = self.protocol_id
        if all(
            execution.state in ("approved", "cancelled")
            for execution in protocol.execution_ids
        ):
            protocol._mark_executed()
        return True

    def action_reject(self):
        """Reject a completed or reviewed execution."""
        for execution in self:
            if execution.state not in ("completed", "reviewed"):
                raise UserError(
                    _(
                        "Only a completed or reviewed execution can be "
                        "rejected."
                    )
                )
            if not execution.rejection_reason:
                raise UserError(
                    _("A rejection reason is required.")
                )
            execution.state = "rejected"
            execution.message_post(
                body=_("Execution rejected: %s") % execution.rejection_reason
            )
        return True

    def action_cancel(self):
        """Cancel an execution that was never approved."""
        for execution in self:
            if execution.state == "approved":
                raise UserError(
                    _("An approved execution cannot be cancelled.")
                )
            execution.state = "cancelled"
            execution.message_post(body=_("Execution cancelled."))
        return True

    def action_view_discrepancies(self):
        """Open the discrepancies raised during the execution."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Discrepancies"),
            "res_model": "ls.validation.discrepancy",
            "view_mode": "list,form",
            "domain": [("execution_id", "=", self.id)],
            "context": {"default_execution_id": self.id},
        }
