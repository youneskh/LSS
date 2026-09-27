# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Excipient master data."""

from odoo import api, fields, models
from odoo.exceptions import ValidationError

from ..constants import EXCIPIENT_FUNCTIONS


class LsPharmaExcipient(models.Model):
    """Master record of an excipient.

    An excipient shares its structure with an active pharmaceutical
    ingredient but is distinguished by its function in the formulation and by
    the concentration limits that apply to it.
    """

    _name = "ls.pharma.excipient"
    _description = "Excipient"
    _inherit = ["ls.pharma.material.mixin"]

    _code_company_uniq = models.Constraint(
        "UNIQUE(code, company_id)",
        "The internal code of an excipient must be unique per company.",
    )

    excipient_function = fields.Selection(
        selection=EXCIPIENT_FUNCTIONS,
        string="Function",
        required=True,
        tracking=True,
        help="Role played by the excipient in the formulation.",
    )
    is_novel = fields.Boolean(
        string="Novel Excipient",
        tracking=True,
        help=(
            "Indicates an excipient that has no established use in an "
            "authorised medicinal product by the intended route of "
            "administration and therefore requires additional justification."
        ),
    )
    maximum_daily_intake_mg = fields.Float(
        string="Maximum Daily Intake (mg)",
        digits=(16, 4),
        help=(
            "Maximum daily intake established for this excipient. A value of "
            "zero means that no limit has been established in this system."
        ),
    )
    requires_declaration = fields.Boolean(
        string="Requires Label Declaration",
        help=(
            "Indicates that the excipient must be declared on the product "
            "labelling because of a known effect."
        ),
    )

    @api.constrains("maximum_daily_intake_mg")
    def _check_maximum_daily_intake(self):
        """Reject a negative maximum daily intake."""
        for excipient in self:
            if excipient.maximum_daily_intake_mg < 0.0:
                raise ValidationError(
                    self.env._(
                        "The maximum daily intake of %(name)s cannot be "
                        "negative.",
                        name=excipient.display_name,
                    )
                )
