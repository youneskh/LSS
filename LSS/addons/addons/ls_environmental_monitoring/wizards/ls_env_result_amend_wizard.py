# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Wizard that records an amendment to an approved result."""

from odoo import api, fields, models

from ..models.constants import QUALITATIVE_VALUES, RESULT_TYPE_QUANTITATIVE


class LsEnvResultAmendWizard(models.TransientModel):
    """Capture the corrected value and the reason for the correction.

    The original value is retained on the result. The amendment is recorded
    alongside it rather than replacing the history of what was reported.
    """

    _name = "ls.env.result.amend.wizard"
    _description = "Amend Environmental Monitoring Result"

    result_id = fields.Many2one(comodel_name="ls.env.result", required=True,
                                ondelete="cascade",)
    result_type = fields.Selection(related="result_id.result_type")
    current_value_numeric = fields.Float(
        related="result_id.value_numeric", string="Current Value"
    )
    current_value_qualitative = fields.Selection(
        related="result_id.value_qualitative", string="Current Outcome"
    )
    new_value_numeric = fields.Float(string="Corrected Value", digits=(16, 4))
    new_value_qualitative = fields.Selection(
        selection=QUALITATIVE_VALUES, string="Corrected Outcome"
    )
    reason = fields.Text(
        string="Reason for Amendment",
        required=True,
        help="Explanation of why the originally reported value is being "
        "corrected. Retained on the result record.",
    )

    @api.onchange("result_id")
    def _onchange_result_id(self):
        """Pre-fill the corrected value with the value currently recorded."""
        for wizard in self:
            wizard.new_value_numeric = wizard.result_id.value_numeric
            wizard.new_value_qualitative = wizard.result_id.value_qualitative

    def action_amend(self):
        """Apply the amendment to the result."""
        self.ensure_one()
        if self.result_id.result_type == RESULT_TYPE_QUANTITATIVE:
            self.result_id.amend_value(
                self.reason, value_numeric=self.new_value_numeric
            )
        else:
            self.result_id.amend_value(
                self.reason, value_qualitative=self.new_value_qualitative
            )
        return {"type": "ir.actions.act_window_close"}
