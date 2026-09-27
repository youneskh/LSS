# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0.html).
"""Quantitative composition line of a cosmetic formulation."""

from odoo import api, fields, models
from odoo.exceptions import ValidationError

from . import constants

#: Result codes produced by :meth:`LsCosmeticFormulationLine._evaluate_restrictions`.
RESTRICTION_STATUS = [
    ("no_reference_data", "No annex data loaded"),
    ("prohibited", "Prohibited substance (Annex II)"),
    ("over_limit", "Above the recorded numeric limit"),
    ("within_limit", "Within the recorded numeric limit"),
    ("manual_review", "Manual review required"),
]


class LsCosmeticFormulationLine(models.Model):
    """One substance and its concentration within a formulation.

    Concentrations are expressed as a percentage by weight of the finished
    product (% w/w).  The field is a plain float rather than a ratio, so the
    ``percentage`` widget is deliberately **not** used on it: that widget
    formats a 0-1 ratio and would display 5 % w/w as 500 %.
    """

    _name = "ls.cosmetic.formulation.line"
    _description = "Cosmetic Formulation Line"
    _order = "formulation_id, sequence, id"
    _rec_name = "ingredient_id"

    formulation_id = fields.Many2one(comodel_name="ls.cosmetic.formulation", required=True,
                                     ondelete="cascade",
                                     index=True,)
    company_id = fields.Many2one(
        related="formulation_id.company_id",
        store=True,
        index=True,
    )
    sequence = fields.Integer(default=10)
    ingredient_id = fields.Many2one(comodel_name="ls.cosmetic.ingredient", required=True,
                                    index=True,
                                    ondelete="restrict",)
    concentration = fields.Float(
        string="Concentration (% w/w)",
        digits=(16, 6),
        required=True,
        help="Percentage by weight of the ingredient in the finished product.",
    )
    function_in_product = fields.Char(
        string="Function in this Product",
        help="Intended function of the ingredient in this specific "
             "formulation - Annex I Part A section 1.",
    )
    is_nanomaterial = fields.Boolean(
        related="ingredient_id.is_nanomaterial",
        string="Nanomaterial",
        store=True,
    )
    is_perfume_component = fields.Boolean(
        related="ingredient_id.is_perfume_component",
        string="Perfume Component",
        store=True,
    )
    regulatory_category = fields.Selection(related="ingredient_id.regulatory_category", store=True,)
    exclude_from_label = fields.Boolean(
        string="Excluded from Label List",
        compute="_compute_exclude_from_label",
        store=True,
        help="True for impurities in raw materials and subsidiary technical "
             "materials, which Article 19(1)(g) does not regard as "
             "ingredients for labelling purposes.",
    )
    restriction_status = fields.Selection(
        selection=RESTRICTION_STATUS,
        string="Annex Status",
        compute="_compute_restriction_status",
        store=True,
    )
    restriction_message = fields.Char(
        string="Annex Finding",
        compute="_compute_restriction_status",
        store=True,
    )
    note = fields.Text()

    _concentration_positive = models.Constraint(
        "CHECK(concentration > 0)",
        "A formulation line must carry a concentration greater than zero.",
    )
    _concentration_max = models.Constraint(
        "CHECK(concentration <= 100)",
        "A concentration cannot exceed 100 % w/w.",
    )
    _ingredient_unique = models.Constraint(
        "UNIQUE(formulation_id, ingredient_id)",
        "This ingredient is already present in the formulation.",
    )

    @api.depends("ingredient_id.is_impurity", "ingredient_id.is_processing_aid")
    def _compute_exclude_from_label(self):
        """Apply the two labelling exclusions of Article 19(1)(g)."""
        for line in self:
            ingredient = line.ingredient_id
            line.exclude_from_label = bool(
                ingredient.is_impurity or ingredient.is_processing_aid
            )

    @api.depends(
        "concentration",
        "ingredient_id",
        "ingredient_id.restriction_ids",
        "ingredient_id.restriction_ids.annex",
        "ingredient_id.restriction_ids.has_numeric_limit",
        "ingredient_id.restriction_ids.max_concentration",
    )
    def _compute_restriction_status(self):
        """Evaluate the line against the annex entries linked to its ingredient."""
        for line in self:
            status, message = line._evaluate_restrictions()
            line.restriction_status = status
            line.restriction_message = message

    def _evaluate_restrictions(self):
        """Compare the line concentration with the linked annex entries.

        The method only compares against entries that were explicitly loaded
        by the organisation and flagged as carrying a single numeric limit.
        When no entry is linked the result is ``no_reference_data``: absence
        of a finding is never reported as compliance.

        :return: a tuple ``(status, message)``.
        """
        self.ensure_one()
        restrictions = self.ingredient_id.restriction_ids
        if not restrictions:
            return (
                "no_reference_data",
                self.env._(
                    "No annex entry is linked to this ingredient. Compliance "
                    "with Annexes II to VI has not been evaluated."
                ),
            )
        prohibited = restrictions.filtered(lambda entry: entry.annex == "ii")
        if prohibited:
            return (
                "prohibited",
                self.env._(
                    "Annex II entry %(reference)s prohibits this substance.",
                    reference=prohibited[0].reference_number,
                ),
            )
        numeric = restrictions.filtered("has_numeric_limit")
        if not numeric:
            return (
                "manual_review",
                self.env._(
                    "The linked annex entries do not express a single numeric "
                    "limit. The conditions of use must be reviewed manually."
                ),
            )
        exceeded = numeric.filtered(
            lambda entry: self.concentration > entry.max_concentration
        )
        if exceeded:
            entry = exceeded[0]
            return (
                "over_limit",
                self.env._(
                    "Concentration %(value)s %% exceeds the limit of "
                    "%(limit)s %% recorded for annex entry %(reference)s.",
                    value=self.concentration,
                    limit=entry.max_concentration,
                    reference=entry.reference_number,
                ),
            )
        lowest = min(numeric.mapped("max_concentration"))
        return (
            "within_limit",
            self.env._(
                "Within the lowest recorded limit of %(limit)s %%.",
                limit=lowest,
            ),
        )

    @api.constrains("ingredient_id", "formulation_id")
    def _check_prohibited_ingredient(self):
        """Refuse an Annex II substance on an approved formulation.

        Draft work is allowed to contain a prohibited substance so that a
        formulator can record and then remove it; approval is where the
        Regulation bites, so the check is enforced from the review state on.
        """
        for line in self:
            if line.formulation_id.state in ("review", "approved") and (
                line.ingredient_id.prohibited
            ):
                raise ValidationError(
                    self.env._(
                        "Ingredient %(name)s is linked to an Annex II entry and "
                        "cannot be present in a formulation under review or "
                        "approved - Article 14(1)(a).",
                        name=line.ingredient_id.inci_name,
                    )
                )

    @api.constrains("concentration")
    def _check_concentration_precision(self):
        """Reject concentrations that round to zero at the stored precision."""
        for line in self:
            if round(line.concentration, 6) == 0.0:
                raise ValidationError(
                    self.env._(
                        "The concentration of %(name)s rounds to zero at the "
                        "stored precision of six decimals.",
                        name=line.ingredient_id.inci_name,
                    )
                )

    def _label_sort_key(self):
        """Return the sort key used to build an Article 19(1)(g) list.

        Ingredients are listed in descending order of weight.  Ingredients in
        concentrations of less than 1 % may be listed in any order after those
        in concentrations of more than 1 %; the module keeps them in
        descending order as well, which satisfies the requirement.

        :return: a tuple suitable for :func:`sorted`.
        """
        self.ensure_one()
        below_threshold = (
            self.concentration < constants.INCI_ORDERING_THRESHOLD_PERCENT
        )
        return (1 if below_threshold else 0, -self.concentration, self.id)
