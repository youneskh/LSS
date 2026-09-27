# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Assessment questionnaires and their scoring rules."""
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class LsSupplierAssessmentTemplate(models.Model):
    """A reusable questionnaire with its scoring scale and thresholds.

    Thresholds defined here are copied onto each assessment at creation time.
    A later change to the template therefore never alters the result of an
    assessment that has already been performed.
    """

    _name = "ls.supplier.assessment.template"
    _description = "Life Sciences Supplier Assessment Template"
    _order = "sequence, name"

    name = fields.Char(required=True, translate=True)
    code = fields.Char(required=True)
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)
    description = fields.Text(translate=True)
    category_ids = fields.Many2many(
        comodel_name="ls.supplier.category",
        relation="ls_supplier_template_category_rel",
        column1="template_id",
        column2="category_id",
        string="Supplier Categories",
        help="Categories this questionnaire is intended for. Informative "
             "only: any template can be selected on any assessment.",
    )
    line_ids = fields.One2many(
        comodel_name="ls.supplier.assessment.template.line",
        inverse_name="template_id",
        string="Criteria",
        copy=True,
    )
    max_score_per_criterion = fields.Integer(
        required=True,
        default=5,
        help="Upper bound of the scoring scale. Each criterion is scored "
             "from 0 to this value.",
    )
    mandatory_min_score = fields.Integer(
        required=True,
        default=3,
        help="Minimum score a mandatory criterion must reach for the "
             "assessment to be able to conclude 'Pass'.",
    )
    pass_threshold = fields.Float(
        required=True,
        default=80.0,
        digits=(5, 2),
        help="Weighted percentage at or above which the result is 'Pass'.",
    )
    conditional_threshold = fields.Float(
        required=True,
        default=60.0,
        digits=(5, 2),
        help="Weighted percentage at or above which the result is "
             "'Conditional'. Below this value the result is 'Fail'.",
    )
    company_id = fields.Many2one(
        comodel_name="res.company",
        required=True,
        default=lambda self: self.env.company,
        index=True,
    )
    line_count = fields.Integer(
        compute="_compute_line_count",
        string="Criteria Count",
    )

    _code_company_uniq = models.Constraint(
        "UNIQUE(code, company_id)",
        "The assessment template code must be unique per company.",
    )

    @api.depends("line_ids")
    def _compute_line_count(self):
        """Count criteria attached to the template."""
        for record in self:
            record.line_count = len(record.line_ids)

    @api.constrains(
        "max_score_per_criterion",
        "mandatory_min_score",
        "pass_threshold",
        "conditional_threshold",
    )
    def _check_scoring_rules(self):
        """Validate that the scoring scale and thresholds are coherent."""
        for record in self:
            if record.max_score_per_criterion <= 0:
                raise ValidationError(
                    _("Template '%s': the maximum score per criterion must be "
                      "strictly positive.", record.name)
                )
            if not 0 <= record.mandatory_min_score <= record.max_score_per_criterion:
                raise ValidationError(
                    _("Template '%s': the minimum score for mandatory "
                      "criteria must be between 0 and %s.",
                      record.name, record.max_score_per_criterion)
                )
            if not 0 <= record.conditional_threshold <= 100:
                raise ValidationError(
                    _("Template '%s': the conditional threshold must be "
                      "between 0 and 100.", record.name)
                )
            if not 0 <= record.pass_threshold <= 100:
                raise ValidationError(
                    _("Template '%s': the pass threshold must be between 0 "
                      "and 100.", record.name)
                )
            if record.conditional_threshold > record.pass_threshold:
                raise ValidationError(
                    _("Template '%s': the conditional threshold cannot be "
                      "greater than the pass threshold.", record.name)
                )

    def copy(self, default=None):
        """Suffix the name and code of a duplicated template."""
        self.ensure_one()
        default = dict(default or {})
        default.setdefault("name", _("%s (copy)", self.name))
        default.setdefault("code", "%s-COPY" % self.code)
        return super().copy(default)


class LsSupplierAssessmentTemplateLine(models.Model):
    """One criterion inside a questionnaire, with its template-level weight."""

    _name = "ls.supplier.assessment.template.line"
    _description = "Life Sciences Supplier Assessment Template Line"
    _check_company_auto = True
    _order = "sequence, id"

    template_id = fields.Many2one(
        comodel_name="ls.supplier.assessment.template",
        required=True,
        ondelete="cascade",
        index=True,
    )
    criterion_id = fields.Many2one(
        comodel_name="ls.supplier.criterion",
        required=True,
        ondelete="restrict",
        check_company=True,
    )
    sequence = fields.Integer(default=10)
    weight = fields.Float(required=True, default=1.0, digits=(6, 2))
    is_mandatory = fields.Boolean(string="Mandatory")
    company_id = fields.Many2one(
        related="template_id.company_id",
        store=True,
        index=True,
    )

    _criterion_template_uniq = models.Constraint(
        "UNIQUE(template_id, criterion_id)",
        "A criterion can only appear once in a given template.",
    )

    _weight_positive = models.Constraint(
        "CHECK(weight > 0)",
        "The weight must be strictly positive.",
    )

    @api.onchange("criterion_id")
    def _onchange_criterion_id(self):
        """Propose the criterion defaults when it is selected."""
        for record in self:
            if record.criterion_id:
                record.weight = record.criterion_id.default_weight
                record.is_mandatory = record.criterion_id.is_mandatory
