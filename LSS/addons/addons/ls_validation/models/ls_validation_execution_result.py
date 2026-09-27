# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Result line of an execution record.

Each line pairs one pre-approved test case with the result observed during
execution. Once the execution leaves the data entry states the lines become
read only, so that recorded raw data cannot be silently altered.
"""

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

from .ls_validation_constants import RESULT_VERDICT

#: Execution states in which result lines may still be edited.
DATA_ENTRY_STATES = ("draft", "in_progress")


class LsValidationExecutionResult(models.Model):
    """Observed result of a single test case."""

    _name = "ls.validation.execution.result"
    _description = "Validation Execution Result"
    _order = "execution_id, sequence, id"
    _check_company_auto = True

    execution_id = fields.Many2one(comodel_name="ls.validation.execution", required=True,
                                   ondelete="cascade",
                                   index=True,)
    company_id = fields.Many2one(comodel_name="res.company", related="execution_id.company_id",
                                 store=True,
                                 readonly=True,)
    execution_state = fields.Selection(
        related="execution_id.state",
        string="Execution Status",
        readonly=True,
    )
    protocol_test_id = fields.Many2one(
        comodel_name="ls.validation.protocol.test",
        string="Test Case",
        required=True,
        ondelete="restrict",
    )
    sequence = fields.Integer(default=10)
    code = fields.Char(
        string="Test Case",
        related="protocol_test_id.code",
        store=True,
        readonly=True,
    )
    name = fields.Char(
        string="Title",
        related="protocol_test_id.name",
        store=True,
        readonly=True,
    )
    acceptance_criteria = fields.Text(related="protocol_test_id.acceptance_criteria",
                                      readonly=True,)
    is_critical = fields.Boolean(
        string="Critical Test",
        related="protocol_test_id.is_critical",
        store=True,
        readonly=True,
    )
    actual_result = fields.Text(string="Observed Result")
    verdict = fields.Selection(selection=RESULT_VERDICT, default="pending",
                               required=True,)
    performed_by_id = fields.Many2one(
        comodel_name="res.users",
        string="Performed by",
    )
    performed_on = fields.Datetime()
    comment = fields.Text()
    discrepancy_id = fields.Many2one(comodel_name="ls.validation.discrepancy", ondelete="set null",
                                     check_company=True,
                                     help="Discrepancy documenting the failure of this test case.",)

    _unique_test_per_execution = models.Constraint(
        "UNIQUE(execution_id, protocol_test_id)",
        "A test case can only appear once in an execution record.",
    )

    # ------------------------------------------------------------------
    # Compute and onchange
    # ------------------------------------------------------------------
    @api.depends("code", "name")
    def _compute_display_name(self):
        """Display the result line as ``CODE - Title``."""
        for line in self:
            line.display_name = "%s - %s" % (line.code or "", line.name or "")

    @api.onchange("verdict")
    def _onchange_verdict(self):
        """Stamp the executor and the timestamp when a verdict is entered."""
        for line in self:
            if line.verdict in ("pass", "fail", "na"):
                if not line.performed_by_id:
                    line.performed_by_id = self.env.user
                if not line.performed_on:
                    line.performed_on = fields.Datetime.now()

    # ------------------------------------------------------------------
    # Constraints
    # ------------------------------------------------------------------
    @api.constrains("protocol_test_id", "execution_id")
    def _check_test_belongs_to_protocol(self):
        """The test case must belong to the protocol being executed."""
        for line in self:
            if line.protocol_test_id.protocol_id != line.execution_id.protocol_id:
                raise ValidationError(
                    _(
                        "Test case %(test)s does not belong to protocol "
                        "%(protocol)s."
                    )
                    % {
                        "test": line.protocol_test_id.display_name,
                        "protocol": line.execution_id.protocol_id.display_name,
                    }
                )

    @api.constrains("verdict", "discrepancy_id")
    def _check_discrepancy_on_failure(self):
        """A discrepancy can only be linked to a failed test case."""
        for line in self:
            if line.discrepancy_id and line.verdict not in ("fail", "pending"):
                raise ValidationError(
                    _(
                        "A discrepancy can only be linked to a failed test "
                        "case."
                    )
                )

    # ------------------------------------------------------------------
    # ORM
    # ------------------------------------------------------------------
    def _check_execution_editable(self):
        """Raise when the parent execution no longer accepts data entry."""
        for line in self:
            if line.execution_id.state not in DATA_ENTRY_STATES:
                raise UserError(
                    _(
                        "Results of execution %s can no longer be modified. "
                        "Record a new execution round instead."
                    )
                    % line.execution_id.display_name
                )

    def write(self, vals):
        """Freeze the result lines outside the data entry states.

        When a verdict is recorded, the executor and the timestamp are stamped
        on each line that does not carry them yet, which keeps the attribution
        of every raw result explicit.
        """
        self._check_execution_editable()
        if vals.get("verdict") not in ("pass", "fail", "na"):
            return super().write(vals)
        now = fields.Datetime.now()
        user = self.env.user
        for line in self:
            line_values = dict(vals)
            if "performed_by_id" not in vals and not line.performed_by_id:
                line_values["performed_by_id"] = user.id
            if "performed_on" not in vals and not line.performed_on:
                line_values["performed_on"] = now
            super(LsValidationExecutionResult, line).write(line_values)
        return True

    @api.ondelete(at_uninstall=False)
    def _ls_unlink_check_ls_validation_execution_result(self):
        """Freeze the result lines outside the data entry states."""
        self._check_execution_editable()

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------
    def action_create_discrepancy(self):
        """Create and open a discrepancy prefilled from the failed line."""
        self.ensure_one()
        if self.verdict != "fail":
            raise UserError(
                _("A discrepancy is only required for a failed test case.")
            )
        discrepancy = self.env["ls.validation.discrepancy"].create(
            {
                "name": _("Failure of test case %s") % (self.code or ""),
                "execution_id": self.execution_id.id,
                "description": self.actual_result or "",
                "classification": "major" if self.is_critical else "minor",
            }
        )
        self.discrepancy_id = discrepancy
        return {
            "type": "ir.actions.act_window",
            "res_model": "ls.validation.discrepancy",
            "res_id": discrepancy.id,
            "view_mode": "form",
            "target": "current",
        }
