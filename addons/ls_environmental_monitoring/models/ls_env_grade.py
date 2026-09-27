# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Cleanroom classification grade."""

from odoo import api, fields, models


class LsEnvGrade(models.Model):
    """User-defined cleanroom classification grade.

    Grades are configuration data owned by the implementing organisation. The
    module ships no grade records and no numeric limits attached to a grade,
    because the applicable classification scheme and its acceptance criteria
    depend on the regulatory framework the organisation operates under and on
    its own contamination control strategy. Acceptance criteria are held on
    ``ls.env.limit`` records against individual sampling points.
    """

    _name = "ls.env.grade"
    _description = "Environmental Monitoring Cleanroom Grade"
    _order = "sequence, code"

    name = fields.Char(
        string="Grade",
        required=True,
        translate=True,
        help="Label of the classification grade, for example a cleanliness "
        "grade or ISO class designation used by the organisation.",
    )
    code = fields.Char(required=True,
                       help="Short unique code used in reports and sampling point codes.",)
    sequence = fields.Integer(default=10,
                              help="Ordering of grades from the most to the least stringent.",)
    description = fields.Text(translate=True,
                              help="Scope of the grade and the reference document that defines it.",)
    reference_document = fields.Char(help="Internal document that defines this grade, for example the "
                                     "contamination control strategy or a classification procedure.",)
    active = fields.Boolean(default=True)
    company_id = fields.Many2one(comodel_name="res.company", required=True,
                                 default=lambda self: self.env.company,
                                 index=True,)
    area_ids = fields.One2many(
        comodel_name="ls.env.area",
        inverse_name="grade_id",
        string="Monitored Areas",
    )
    area_count = fields.Integer(compute="_compute_area_count",)

    _code_company_unique = models.Constraint(
        "UNIQUE(code, company_id)",
        "The grade code must be unique per company.",
    )

    @api.depends("area_ids")
    def _compute_area_count(self):
        """Count the monitored areas classified at this grade."""
        grouped = self.env["ls.env.area"]._read_group(
            [("grade_id", "in", self.ids)],
            groupby=["grade_id"],
            aggregates=["__count"],
        )
        counts = {grade.id: count for grade, count in grouped}
        for record in self:
            record.area_count = counts.get(record.id, 0)

    @api.depends("code", "name")
    def _compute_display_name(self):
        """Show the code alongside the grade label."""
        for record in self:
            record.display_name = "[%s] %s" % (record.code or "", record.name or "")
