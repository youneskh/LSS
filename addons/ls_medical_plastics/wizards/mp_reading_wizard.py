# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Wizard used to capture a set of moulding parameter readings.

The wizard pre-loads the parameters of the specification frozen on the run and
lets the operator enter several values in one pass. It also supports
correcting an earlier reading, in which case a reason is mandatory and the
original reading is superseded rather than modified.
"""

from odoo import api, fields, models
from odoo.exceptions import ValidationError

from ..constants import MEASUREMENT_DIGITS, PARAMETER_VALUE_TYPES, READING_TYPES


class LsMpReadingWizard(models.TransientModel):
    """Capture several parameter readings for a moulding run at once."""

    _name = "ls.mp.reading.wizard"
    _description = "Record Moulding Parameter Readings"

    run_id = fields.Many2one(
        comodel_name="ls.mp.injection_molding",
        string="Moulding Run",
        required=True,
        ondelete="cascade",
    )
    reading_type = fields.Selection(selection=READING_TYPES, required=True,
                                    default="in_process",)
    line_ids = fields.One2many(
        comodel_name="ls.mp.reading.wizard.line",
        inverse_name="wizard_id",
        string="Parameters",
    )
    comment = fields.Char()

    @api.model
    def default_get(self, fields_list):
        """Pre-load the wizard with the parameters of the run specification."""
        defaults = super().default_get(fields_list)
        run_id = defaults.get("run_id") or self.env.context.get("default_run_id")
        if not run_id:
            return defaults
        run = self.env["ls.mp.injection_molding"].browse(run_id)
        lines = []
        for line in run.parameter_spec_id.line_ids:
            lines.append(
                (
                    0,
                    0,
                    {
                        "parameter_line_id": line.id,
                        "value_numeric": line.target_value,
                        "capture": line.record_required,
                    },
                )
            )
        defaults["line_ids"] = lines
        return defaults

    @api.onchange("run_id")
    def _onchange_run_id(self):
        """Default the reading type from the current state of the run."""
        if not self.run_id:
            return
        state_to_type = {
            "setup": "setup",
            "startup_check": "startup",
            "running": "in_process",
            "completed": "end_of_run",
        }
        self.reading_type = state_to_type.get(self.run_id.state, "in_process")

    def action_record(self):
        """Create the readings selected for capture.

        :return: an action closing the wizard window.
        :rtype: dict
        """
        self.ensure_one()
        selected = self.line_ids.filtered(lambda line: line.capture)
        if not selected:
            raise ValidationError(
                self.env._("Select at least one parameter to record.")
            )
        values = [line._prepare_reading_values() for line in selected]
        self.env["ls.mp.injection_molding.reading"].create(values)
        return {"type": "ir.actions.act_window_close"}


class LsMpReadingWizardLine(models.TransientModel):
    """One parameter row of the reading capture wizard."""

    _name = "ls.mp.reading.wizard.line"
    _description = "Moulding Parameter Reading Wizard Line"
    _order = "wizard_id, sequence, id"

    wizard_id = fields.Many2one(comodel_name="ls.mp.reading.wizard", required=True,
                                ondelete="cascade",)
    parameter_line_id = fields.Many2one(comodel_name="ls.mp.molding_parameter.line", required=True,
                                        ondelete="cascade",)
    sequence = fields.Integer(related="parameter_line_id.sequence", readonly=True)
    parameter_name = fields.Char(
        string="Parameter", related="parameter_line_id.name", readonly=True
    )
    parameter_uom = fields.Char(
        string="Unit", related="parameter_line_id.parameter_uom", readonly=True
    )
    value_type = fields.Selection(selection=PARAMETER_VALUE_TYPES, related="parameter_line_id.value_type",
                                  readonly=True,)
    target_value = fields.Float(
        string="Target",
        related="parameter_line_id.target_value",
        digits=MEASUREMENT_DIGITS,
        readonly=True,
    )
    min_value = fields.Float(
        string="Minimum",
        related="parameter_line_id.min_value",
        digits=MEASUREMENT_DIGITS,
        readonly=True,
    )
    max_value = fields.Float(
        string="Maximum",
        related="parameter_line_id.max_value",
        digits=MEASUREMENT_DIGITS,
        readonly=True,
    )
    is_critical = fields.Boolean(
        string="Critical", related="parameter_line_id.is_critical", readonly=True
    )
    capture = fields.Boolean(string="Record", default=True)
    value_numeric = fields.Float(string="Measured Value", digits=MEASUREMENT_DIGITS)
    value_text = fields.Char(string="Observed Value")
    supersedes_id = fields.Many2one(
        comodel_name="ls.mp.injection_molding.reading",
        string="Corrects Reading",
        ondelete="cascade",
        domain="[('parameter_line_id', '=', parameter_line_id)]",
        help="Select an earlier reading to correct it with this new value.",
    )
    correction_reason = fields.Char(string="Reason for Correction")

    @api.constrains("supersedes_id", "correction_reason", "capture")
    def _check_correction_reason(self):
        """A correction must always state its reason."""
        for line in self:
            if line.capture and line.supersedes_id and not line.correction_reason:
                raise ValidationError(
                    self.env._(
                        "A reason is required to correct the reading of parameter "
                        "%(name)s.",
                        name=line.parameter_name,
                    )
                )

    def _prepare_reading_values(self):
        """Build the values used to create the moulding parameter reading.

        :rtype: dict
        """
        self.ensure_one()
        return {
            "run_id": self.wizard_id.run_id.id,
            "parameter_line_id": self.parameter_line_id.id,
            "reading_type": self.wizard_id.reading_type,
            "value_numeric": self.value_numeric,
            "value_text": self.value_text,
            "supersedes_id": self.supersedes_id.id or False,
            "correction_reason": self.correction_reason or False,
            "comment": self.wizard_id.comment or False,
        }
