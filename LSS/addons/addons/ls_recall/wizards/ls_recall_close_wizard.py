# Part of the Life Sciences Suite for Odoo 19 Community Edition.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Wizard closing or cancelling a recall.

Closure is the point at which the organisation states that the action is
complete. The wizard therefore evaluates a set of quality gates and shows
the result before anything is written. A gate that is not met can be
overridden, but only with a documented justification, so the record shows
both that the gate failed and why the organisation accepted it.
"""

from odoo import api, fields, models
from odoo.exceptions import UserError


class LsRecallCloseWizard(models.TransientModel):
    """Close or cancel a recall with a documented justification."""

    _name = "ls.recall.close.wizard"
    _description = "Close Recall"

    execution_id = fields.Many2one(
        comodel_name="ls.recall.execution",
        string="Recall",
        required=True,
        ondelete="cascade",
    )
    mode = fields.Selection(
        selection=[("close", "Close"), ("cancel", "Cancel")],
        default="close",
        required=True,
    )
    justification = fields.Text(
        required=True,
        help="Statement of the basis on which the action is being "
             "closed or cancelled.",
    )
    attestation = fields.Char(help="Free text recorded alongside the closure, for example the "
                              "reference of the signed paper closure record. This field "
                              "is not an electronic signature.",)
    gate_report = fields.Html(
        compute="_compute_gate_report",
        string="Closure Checks",
    )
    gates_passed = fields.Boolean(compute="_compute_gate_report")
    override_gates = fields.Boolean(
        string="Close despite failed checks",
        help="Only available to a recall manager. The justification is "
             "mandatory and is stored on the recall.",
    )

    @api.depends("execution_id", "mode")
    def _compute_gate_report(self):
        """Evaluate the closure gates and render them for the user."""
        for wizard in self:
            if wizard.mode == "cancel" or not wizard.execution_id:
                wizard.gate_report = False
                wizard.gates_passed = True
                continue
            results = wizard.execution_id._evaluate_closure_gates()
            wizard.gates_passed = all(passed for passed, _ in results)
            rows = []
            for passed, label in results:
                mark = "PASS" if passed else "FAIL"
                rows.append(f"<li><strong>{mark}</strong> - {label}</li>")
            wizard.gate_report = "<ul>" + "".join(rows) + "</ul>"

    def action_confirm(self):
        """Apply the closure or the cancellation.

        :return: an action closing the wizard window.
        :rtype: dict
        """
        self.ensure_one()
        execution = self.execution_id
        if self.mode == "cancel":
            execution.write(
                {
                    "state": "cancelled",
                    "cancellation_reason": self.justification,
                    "closed_by_user_id": self.env.user.id,
                    "closure_date": fields.Datetime.now(),
                }
            )
            execution.message_post(
                body=self.env._(
                    "Recall cancelled by %(user)s. Reason: %(reason)s",
                    user=self.env.user.display_name,
                    reason=self.justification,
                )
            )
            return {"type": "ir.actions.act_window_close"}

        if not self.gates_passed:
            if not self.override_gates:
                raise UserError(
                    self.env._(
                        "One or more closure checks have failed. Resolve "
                        "them, or tick the override and state why the "
                        "recall is nevertheless being closed."
                    )
                )
            if not self.env.user.has_group(
                "ls_recall.group_ls_recall_manager"
            ):
                raise UserError(
                    self.env._(
                        "Only a recall manager may close a recall whose "
                        "checks have failed."
                    )
                )
        execution._assert_transition("closed")
        execution.write(
            {
                "state": "closed",
                "closure_date": fields.Datetime.now(),
                "closure_justification": self.justification,
                "closure_attestation": self.attestation,
                "closed_by_user_id": self.env.user.id,
            }
        )
        body = self.env._(
            "Recall closed by %(user)s. Justification: %(reason)s",
            user=self.env.user.display_name,
            reason=self.justification,
        )
        if not self.gates_passed:
            body += "<br/>" + self.env._(
                "Closed with failed checks, overridden by a recall "
                "manager."
            )
        execution.message_post(body=body)
        return {"type": "ir.actions.act_window_close"}
