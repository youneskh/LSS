# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Storage conditions used by stability studies."""

from odoo import api, fields, models
from odoo.exceptions import ValidationError

from ..constants import STABILITY_CONDITION_TYPES


class LsPharmaStabilityCondition(models.Model):
    """A storage condition under which stability samples are held.

    The conditions published in ICH Q1A(R2) are shipped as data records
    rather than written into the source code, so that a manufacturer can add
    the conditions of other climatic zones or of a national guideline without
    modifying the module.

    The ICH Q1A(R2) general case conditions supplied with this module are the
    long-term conditions of 25 degrees Celsius with 60 per cent relative
    humidity and of 30 degrees Celsius with 65 per cent relative humidity, the
    intermediate condition of 30 degrees Celsius with 65 per cent relative
    humidity, and the accelerated condition of 40 degrees Celsius with 75 per
    cent relative humidity.

    Source: ICH Q1A(R2), reproduced by the United States Food and Drug
    Administration as Guidance for Industry Q1A(R2) Stability Testing of New
    Drug Substances and Products, https://www.fda.gov/media/71707/download
    """

    _name = "ls.pharma.stability.condition"
    _description = "Stability Storage Condition"
    _order = "condition_type, temperature_celsius, id"

    _code_uniq = models.Constraint(
        "UNIQUE(code)",
        "The code of a stability storage condition must be unique.",
    )

    name = fields.Char(string="Condition", required=True, translate=True)
    code = fields.Char(required=True)
    condition_type = fields.Selection(
        selection=STABILITY_CONDITION_TYPES,
        string="Type",
        required=True,
        default="long_term",
    )
    temperature_celsius = fields.Float(
        string="Temperature (Celsius)", digits=(16, 1), required=True
    )
    temperature_tolerance = fields.Float(
        string="Temperature Tolerance (Celsius)", digits=(16, 1)
    )
    relative_humidity = fields.Float(
        string="Relative Humidity (%)",
        digits=(16, 1),
        help=(
            "Relative humidity of the condition, expressed as a percentage "
            "between 0 and 100. A value of zero means that no relative "
            "humidity is specified for this condition."
        ),
    )
    humidity_tolerance = fields.Float(
        string="Relative Humidity Tolerance (%)", digits=(16, 1)
    )
    default_duration_months = fields.Integer(
        string="Default Duration (Months)",
        required=True,
        default=12,
        help="Duration used by the schedule wizard when it proposes time points.",
    )
    reference = fields.Char(
        string="Source Reference",
        help="Guideline from which this condition is taken.",
    )
    note = fields.Text(string="Notes")
    active = fields.Boolean(default=True)

    @api.depends("name", "temperature_celsius", "relative_humidity")
    def _compute_display_name(self):
        """Show the temperature and humidity alongside the condition name."""
        for condition in self:
            if condition.relative_humidity:
                condition.display_name = "%s (%.0f C / %.0f%% RH)" % (
                    condition.name,
                    condition.temperature_celsius,
                    condition.relative_humidity,
                )
            else:
                condition.display_name = "%s (%.0f C)" % (
                    condition.name,
                    condition.temperature_celsius,
                )

    @api.constrains("relative_humidity", "humidity_tolerance")
    def _check_humidity(self):
        """Reject a relative humidity outside the range 0 to 100."""
        for condition in self:
            if not 0.0 <= condition.relative_humidity <= 100.0:
                raise ValidationError(
                    self.env._(
                        "The relative humidity of %(name)s must lie between 0 "
                        "and 100 per cent.",
                        name=condition.name,
                    )
                )
            if condition.humidity_tolerance < 0.0:
                raise ValidationError(
                    self.env._("The humidity tolerance cannot be negative.")
                )

    @api.constrains("default_duration_months")
    def _check_duration(self):
        """Reject a non-positive default duration."""
        for condition in self:
            if condition.default_duration_months <= 0:
                raise ValidationError(
                    self.env._(
                        "The default duration of %(name)s must be strictly "
                        "positive.",
                        name=condition.name,
                    )
                )
