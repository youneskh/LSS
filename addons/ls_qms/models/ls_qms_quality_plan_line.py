# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0.html).
"""Individual controls declared inside a quality plan."""

from odoo import fields, models


class LsQmsQualityPlanLine(models.Model):
    """One control of a quality plan."""

    _name = "ls.qms.quality_plan.line"
    _description = "Quality Plan Control Line"
    _check_company_auto = True
    _order = "quality_plan_id, sequence, id"

    sequence = fields.Integer(default=10)
    quality_plan_id = fields.Many2one(comodel_name="ls.qms.quality_plan", required=True,
                                      ondelete="cascade",
                                      index=True,)
    company_id = fields.Many2one(
        related="quality_plan_id.company_id",
        store=True,
        index=True,
    )
    stage = fields.Char(
        string="Process Stage",
        required=True,
        help="Manufacturing or service stage at which the control applies.",
    )
    characteristic = fields.Char(required=True,
                                 help="Property being controlled.",)
    specification = fields.Char(help="Acceptance criteria applied to the characteristic.",)
    control_method = fields.Char(help="Method, instrument or test used to perform the control.",)
    frequency = fields.Char(help="How often the control is performed.",)
    sample_size = fields.Char()
    responsible_id = fields.Many2one(comodel_name="res.users")
    sop_id = fields.Many2one(
        comodel_name="ls.qms.sop",
        string="Reference Procedure",
        check_company=True,
    )
    record_reference = fields.Char(
        string="Recording Form",
        help="Form or record in which the result of the control is written.",
    )
