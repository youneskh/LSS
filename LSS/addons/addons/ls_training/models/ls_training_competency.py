# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Competency definitions granted by training courses."""

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class LsTrainingCompetency(models.Model):
    """A demonstrable ability that a course confers and an assessment proves.

    A competency is a controlled master-data record. It is referenced by
    courses (which grant it) and by competency assessments (which evidence
    that a given employee holds it at a given level).
    """

    _name = "ls.training.competency"
    _description = "Training Competency"
    _order = "code, name"

    name = fields.Char(
        string="Competency",
        required=True,
        translate=True,
        index=True,
    )
    code = fields.Char(required=True,
                       copy=False,
                       help="Short unique identifier used in the training matrix and in "
                       "printed training records.",)
    active = fields.Boolean(default=True,
                            help="Archived competencies remain linked to historical assessments "
                            "but can no longer be selected on new records.",)
    company_id = fields.Many2one(comodel_name="res.company", required=True,
                                 index=True,
                                 default=lambda self: self.env.company,)
    description = fields.Text(translate=True,)
    minimum_level = fields.Selection(
        selection=[
            ("developing", "Developing"),
            ("proficient", "Proficient"),
            ("expert", "Expert"),
        ],
        string="Minimum Acceptable Level",
        required=True,
        default="proficient",
        help="Assessment level at or above which the employee is considered "
             "to hold this competency.",
    )
    reassessment_months = fields.Integer(
        string="Reassessment Interval (Months)",
        default=0,
        help="Number of months after which the competency must be "
             "reassessed. Zero means no periodic reassessment.",
    )
    course_ids = fields.Many2many(
        comodel_name="ls.training.course",
        relation="ls_training_course_competency_rel",
        column1="competency_id",
        column2="course_id",
        string="Granting Courses",
    )
    assessment_ids = fields.One2many(
        comodel_name="ls.training.competency.assessment",
        inverse_name="competency_id",
        string="Assessments",
    )
    assessment_count = fields.Integer(compute="_compute_assessment_count",)

    _code_company_uniq = models.Constraint(
        "UNIQUE(code, company_id)",
        "The competency code must be unique per company.",
    )

    @api.depends("assessment_ids")
    def _compute_assessment_count(self):
        """Count assessments per competency using a grouped read."""
        grouped = self.env["ls.training.competency.assessment"]._read_group(
            domain=[("competency_id", "in", self.ids)],
            groupby=["competency_id"],
            aggregates=["__count"],
        )
        mapped = {
            competency.id: count for competency, count in grouped
        }
        for record in self:
            record.assessment_count = mapped.get(record.id, 0)

    @api.constrains("reassessment_months")
    def _check_reassessment_months(self):
        """Forbid negative reassessment intervals."""
        for record in self:
            if record.reassessment_months < 0:
                raise ValidationError(
                    _("The reassessment interval of competency '%s' cannot "
                      "be negative.")
                    % record.display_name
                )

    @api.depends("code", "name")
    def _compute_display_name(self):
        """Show the competency code in front of its name."""
        for record in self:
            record.display_name = "[%s] %s" % (record.code, record.name)

    def action_view_assessments(self):
        """Open the assessments recorded for this competency."""
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id(
            "ls_training.ls_training_competency_assessment_action"
        )
        action["domain"] = [("competency_id", "=", self.id)]
        action["context"] = {"default_competency_id": self.id}
        return action
