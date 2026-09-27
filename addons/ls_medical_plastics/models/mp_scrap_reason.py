# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Scrap and defect reason catalogue.

The catalogue lets a site classify rejected parts consistently. Start-up and
purge scrap is flagged separately so that it can be excluded from the quality
reject rate, which would otherwise be distorted by the material purged at
every tool change.
"""

from odoo import api, fields, models

from ..constants import CODE_MAX_LENGTH, SCRAP_CATEGORIES


class LsMpScrapReason(models.Model):
    """Configurable reason for rejecting moulded parts."""

    _name = "ls.mp.scrap.reason"
    _description = "Medical Plastics Scrap Reason"
    _order = "sequence, code"

    name = fields.Char(string="Reason", required=True, translate=True)
    code = fields.Char(required=True,
                       size=CODE_MAX_LENGTH,
                       index=True,)
    category = fields.Selection(selection=SCRAP_CATEGORIES, required=True,
                                default="process",)
    sequence = fields.Integer(default=10)
    is_startup = fields.Boolean(
        string="Start-up / Purge Scrap",
        help=(
            "Scrap generated while bringing the process to a stable condition. "
            "It is excluded from the quality reject rate of the run."
        ),
    )
    requires_investigation = fields.Boolean(help=(
            "Occurrences of this reason are expected to be investigated under "
            "the site deviation procedure."),
    )
    description = fields.Text(translate=True)
    company_id = fields.Many2one(comodel_name="res.company", index=True,
                                 default=lambda self: self.env.company,
                                 help="Leave empty to share the reason across all companies.",)
    active = fields.Boolean(default=True)

    _code_company_unique = models.Constraint(
        "UNIQUE(code, company_id)",
        "The scrap reason code must be unique per company.",
    )

    @api.depends("code", "name")
    def _compute_display_name(self):
        """Render the reason as ``[CODE] Name``."""
        for reason in self:
            reason.display_name = f"[{reason.code}] {reason.name}" if reason.code else reason.name
