# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Configurable impact areas used to structure a change impact assessment."""

from odoo import fields, models


class LsChangeControlImpactArea(models.Model):
    """An area of the quality system that a change may impact.

    One impact assessment record is produced per impact area retained on a
    change request, which gives a deterministic and auditable assessment
    coverage instead of a free text evaluation.
    """

    _name = "ls.change_control.impact_area"
    _description = "Change Control Impact Area"
    _order = "sequence, name"

    name = fields.Char(
        string="Impact Area",
        required=True,
        translate=True,
    )
    code = fields.Char(required=True,
                       help="Short unique code used in reports and exports.",)
    sequence = fields.Integer(default=10,
                              help="Display order of the impact area in lists and reports.",)
    description = fields.Text(translate=True,
                              help="Scope of the impact area, used as guidance for the assessor.",)
    requires_assessment = fields.Boolean(
        string="Assessment Mandatory",
        default=True,
        help="When enabled, an assessment on this area must be completed "
             "before the change request can leave the Impact Assessment "
             "state.",
    )
    active = fields.Boolean(default=True,
                            help="Archived impact areas remain on existing change requests but "
                            "can no longer be selected on new ones.",)

    _code_unique = models.Constraint(
        "UNIQUE(code)",
        "The impact area code must be unique.",
    )
