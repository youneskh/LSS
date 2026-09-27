# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Sampling and test method."""

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class LsEnvMethod(models.Model):
    """The documented method used to take and read a sample.

    Recording the method against every result makes the result attributable to
    a defined procedure and allows a change of method to be identified when
    historical data are reviewed.
    """

    _name = "ls.env.method"
    _description = "Environmental Monitoring Method"
    _order = "name"

    name = fields.Char(string="Method", required=True, translate=True)
    code = fields.Char(required=True)
    parameter_id = fields.Many2one(comodel_name="ls.env.parameter", required=True,
                                   ondelete="restrict",
                                   help="Parameter this method measures.",)
    media_type = fields.Char(
        string="Growth Medium",
        help="Culture medium used, for microbiological methods.",
    )
    incubation_conditions = fields.Text(help="Temperature and duration of each incubation stage, as defined "
                                        "in the controlling procedure.",)
    exposure_duration_minutes = fields.Integer(
        string="Exposure Duration (minutes)",
        help="Duration for which the sampling device is exposed. Zero when "
        "the method does not define an exposure period.",
    )
    sample_volume = fields.Float(digits=(16, 4),
                                 help="Volume of air or other medium sampled. Zero when the method "
                                 "does not define a volume.",
                                 )
    sample_volume_uom_label = fields.Char(string="Volume Unit")
    reference_document = fields.Char(
        string="Controlling Procedure",
        help="Identifier of the procedure that defines this method.",
    )
    description = fields.Text(translate=True)
    active = fields.Boolean(default=True)
    company_id = fields.Many2one(comodel_name="res.company", required=True,
                                 default=lambda self: self.env.company,
                                 index=True,)

    _code_company_unique = models.Constraint(
        "UNIQUE(code, company_id)",
        "The method code must be unique per company.",
    )
    _exposure_duration_positive = models.Constraint(
        "CHECK(exposure_duration_minutes >= 0)",
        "Exposure duration must not be negative.",
    )
    _sample_volume_positive = models.Constraint(
        "CHECK(sample_volume >= 0)",
        "Sample volume must not be negative.",
    )

    @api.constrains("parameter_id", "company_id")
    def _check_parameter_company(self):
        """Reject a parameter belonging to a different company."""
        for record in self:
            if record.parameter_id.company_id != record.company_id:
                raise ValidationError(
                    self.env._(
                        "Method '%(method)s' must reference a parameter of the same "
                        "company.",
                        method=record.name,
                    )
                )

    @api.depends("code", "name")
    def _compute_display_name(self):
        """Show the code alongside the method name."""
        for record in self:
            record.display_name = "[%s] %s" % (record.code or "", record.name or "")
