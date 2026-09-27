# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Individual parameter of a moulding parameter specification.

Each line declares one process parameter with its target, its acceptable
range, whether it is critical and how often it must be verified during
production.
"""

from odoo import api, fields, models
from odoo.exceptions import ValidationError

from ..constants import (
    CODE_MAX_LENGTH,
    MEASUREMENT_DIGITS,
    MONITORING_FREQUENCIES,
    PARAMETER_VALUE_TYPES,
)


class LsMpMoldingParameterLine(models.Model):
    """One process parameter within a moulding parameter specification."""

    _name = "ls.mp.molding_parameter.line"
    _description = "Medical Plastics Moulding Parameter"
    _order = "spec_id, sequence, id"

    spec_id = fields.Many2one(
        comodel_name="ls.mp.molding_parameter",
        string="Specification",
        required=True,
        ondelete="cascade",
        index=True,
    )
    sequence = fields.Integer(default=10)
    name = fields.Char(string="Parameter", required=True)
    code = fields.Char(
        string="Parameter Code",
        required=True,
        size=CODE_MAX_LENGTH,
    )
    parameter_uom = fields.Char(
        string="Unit",
        required=True,
        help=(
            "Unit label recorded as free text, for example bar, degC, s or "
            "mm/s. Moulding parameter units are not represented as Odoo units "
            "of measure because they are not stock units."
        ),
    )
    value_type = fields.Selection(selection=PARAMETER_VALUE_TYPES, required=True,
                                  default="numeric",)
    target_value = fields.Float(string="Target", digits=MEASUREMENT_DIGITS)
    min_value = fields.Float(string="Minimum", digits=MEASUREMENT_DIGITS)
    max_value = fields.Float(string="Maximum", digits=MEASUREMENT_DIGITS)
    expected_text = fields.Char(
        string="Expected Value",
        help="Expected result for qualitative parameters.",
    )
    is_critical = fields.Boolean(
        string="Critical Parameter",
        help=(
            "The parameter has been classified by the organisation as critical "
            "to the quality of the moulded component."
        ),
    )
    monitoring_frequency = fields.Selection(selection=MONITORING_FREQUENCIES, required=True,
                                            default="per_startup",)
    record_required = fields.Boolean(
        string="Recording Required",
        default=True,
        help="A value must be recorded on the moulding run for this parameter.",
    )
    note = fields.Text(string="Notes")

    state = fields.Selection(
        related="spec_id.state",
        string="Specification Status",
        store=True,
        readonly=True,
    )
    company_id = fields.Many2one(comodel_name="res.company", related="spec_id.company_id",
                                 store=True,
                                 index=True,
                                 readonly=True,)

    _code_spec_unique = models.Constraint(
        "UNIQUE(spec_id, code)",
        "A parameter code must be unique within a specification.",
    )

    @api.depends("name", "parameter_uom")
    def _compute_display_name(self):
        """Render the parameter as ``Name (unit)``."""
        for line in self:
            line.display_name = (
                f"{line.name} ({line.parameter_uom})" if line.parameter_uom else line.name
            )

    @api.constrains("value_type", "min_value", "max_value", "target_value")
    def _check_numeric_range(self):
        """Validate that the numeric range is coherent and contains the target."""
        for line in self:
            if line.value_type != "numeric":
                continue
            if line.min_value > line.max_value:
                raise ValidationError(
                    self.env._(
                        "Parameter %(name)s has a minimum greater than its maximum.",
                        name=line.name,
                    )
                )
            if not line.min_value <= line.target_value <= line.max_value:
                raise ValidationError(
                    self.env._(
                        "The target of parameter %(name)s lies outside its "
                        "minimum and maximum values.",
                        name=line.name,
                    )
                )

    @api.constrains("value_type", "expected_text")
    def _check_qualitative_expected(self):
        """A qualitative parameter must declare its expected value."""
        for line in self:
            if line.value_type == "qualitative" and not line.expected_text:
                raise ValidationError(
                    self.env._(
                        "Qualitative parameter %(name)s must declare an expected "
                        "value.",
                        name=line.name,
                    )
                )

    @api.constrains("is_critical", "record_required")
    def _check_critical_is_recorded(self):
        """A critical parameter must always be recorded."""
        for line in self:
            if line.is_critical and not line.record_required:
                raise ValidationError(
                    self.env._(
                        "Critical parameter %(name)s must have recording enabled.",
                        name=line.name,
                    )
                )

    def _evaluate_value(self, value_numeric, value_text):
        """Return whether a captured value satisfies this parameter.

        :param float value_numeric: measured numeric value.
        :param str value_text: measured qualitative value.
        :return: ``True`` when the value is within specification.
        :rtype: bool
        """
        self.ensure_one()
        if self.value_type == "numeric":
            return self.min_value <= value_numeric <= self.max_value
        expected = (self.expected_text or "").strip().lower()
        observed = (value_text or "").strip().lower()
        return bool(observed) and observed == expected

    def _snapshot_values(self):
        """Return the specification values to freeze onto a reading.

        Readings copy the acceptance criteria in force at the moment of
        capture, so that a later revision of the specification cannot change
        the meaning of a historical record.

        :rtype: dict
        """
        self.ensure_one()
        return {
            "parameter_name": self.name,
            "parameter_code": self.code,
            "parameter_uom": self.parameter_uom,
            "value_type": self.value_type,
            "target_value": self.target_value,
            "min_value": self.min_value,
            "max_value": self.max_value,
            "expected_text": self.expected_text,
            "is_critical": self.is_critical,
        }
