# Part of the Life Sciences Suite. See LICENSE file for full copyright and licensing details.
"""Storage condition master data.

No storage condition values are shipped with this module. The consolidated
ICH Q1 guideline reached Step 2b on 11 April 2025 and has not reached Step 4;
until it does, the legacy Q1A(R2)-Q1E and Q5C series remain applicable. Because
the governing reference is in transition, storage conditions are configuration
data owned by the implementing organisation and are never hardcoded here.
"""

from odoo import api, fields, models


class LsLabStorageCondition(models.Model):
    """A named storage condition used by samples and stability studies."""

    _name = "ls.lab.storage_condition"
    _description = "Laboratory Storage Condition"
    _order = "sequence, code"

    name = fields.Char(required=True,
                       translate=True,
                       help="Descriptive name of the storage condition, for example "
                       "'Long term - controlled room temperature'.",)
    code = fields.Char(required=True,
                       help="Short unique code used in listings and reports.",)
    sequence = fields.Integer(default=10)
    temperature_c = fields.Float(
        string="Temperature (deg C)",
        digits=(6, 2),
        help="Nominal storage temperature in degrees Celsius.",
    )
    temperature_tolerance_c = fields.Float(
        string="Temperature Tolerance (+/- deg C)",
        digits=(6, 2),
    )
    humidity_rh = fields.Float(
        string="Relative Humidity (%)",
        digits=(6, 2),
        help="Nominal relative humidity expressed on a 0-100 scale.",
    )
    humidity_tolerance_rh = fields.Float(
        string="Humidity Tolerance (+/- %)",
        digits=(6, 2),
    )
    light_condition = fields.Selection(
        selection=[
            ("not_specified", "Not Specified"),
            ("dark", "Protected From Light"),
            ("ambient", "Ambient Light"),
            ("controlled_exposure", "Controlled Light Exposure"),
        ],
        default="not_specified",
        required=True,
    )
    description = fields.Text(translate=True)
    reference = fields.Char(help="Free-text reference to the guideline or internal procedure that "
                            "defines this condition. No guideline content is stored by this "
                            "module.",)
    active = fields.Boolean(default=True)
    company_id = fields.Many2one(comodel_name="res.company", default=lambda self: self.env.company,
                                 index=True,)

    _code_uniq = models.Constraint(
        "UNIQUE (code)",
        "The storage condition code must be unique.",
    )

    @api.depends("code", "name")
    def _compute_display_name(self):
        """Show the code together with the descriptive name."""
        for condition in self:
            condition.display_name = f"[{condition.code}] {condition.name}"
