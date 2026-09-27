# Copyright 2026 Life Sciences Suite
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Settings exposure of the deviation closure targets."""

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    """Expose the company closure targets in the Settings application."""

    _inherit = "res.config.settings"

    ls_deviation_target_days_minor = fields.Integer(
        related="company_id.ls_deviation_target_days_minor",
        readonly=False,
    )
    ls_deviation_target_days_major = fields.Integer(
        related="company_id.ls_deviation_target_days_major",
        readonly=False,
    )
    ls_deviation_target_days_critical = fields.Integer(
        related="company_id.ls_deviation_target_days_critical",
        readonly=False,
    )
