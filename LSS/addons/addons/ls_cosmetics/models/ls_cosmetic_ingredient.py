# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0.html).
"""Register of substances used in cosmetic formulations."""

from odoo import api, fields, models
from odoo.exceptions import ValidationError

from . import constants


class LsCosmeticIngredient(models.Model):
    """A substance or mixture intentionally used in a cosmetic product.

    Article 19(1)(g) of Regulation (EC) No 1223/2009 defines an ingredient,
    for labelling purposes, as any substance or mixture intentionally used in
    the cosmetic product during the process of manufacturing, and excludes
    impurities in raw materials and subsidiary technical materials that are
    not present in the final product.  The two exclusions are represented by
    ``is_impurity`` and ``is_processing_aid``: such records may be held for
    Annex I Part A section 4 (impurities and traces) but are never emitted
    into a label ingredient list.
    """

    _name = "ls.cosmetic.ingredient"
    _description = "Cosmetic Ingredient"
    _inherit = ["mail.thread"]
    _order = "inci_name, id"
    _rec_name = "inci_name"

    active = fields.Boolean(default=True)
    company_id = fields.Many2one(comodel_name="res.company", default=lambda self: self.env.company,
                                 index=True,)
    inci_name = fields.Char(required=True,
                            index=True,
                            tracking=True,
                            help="Common ingredient name as required by Article 19(6). Where no "
                            "common ingredient name exists, a term from a generally accepted "
                            "nomenclature is used.",
                            )
    chemical_name = fields.Char(
        string="Chemical Name (IUPAC)",
        tracking=True,
        help="Annex I Part A section 1 requires the chemical identity of the "
             "substances, including the chemical name where possible.",
    )
    cas_number = fields.Char(tracking=True)
    ec_number = fields.Char(tracking=True,
                            help="EINECS or ELINCS number, per Annex I Part A section 1.",)
    technical_function = fields.Char(help="Intended function of the substance in the product, recorded as "
                                     "free text. Regulation (EC) No 1223/2009 defines only three "
                                     "functional categories subject to positive lists; those are "
                                     "recorded separately in 'Regulatory Category'.",
                                     )
    regulatory_category = fields.Selection(selection=constants.INGREDIENT_REGULATORY_CATEGORY, default="none",
                                           required=True,
                                           tracking=True,)
    is_nanomaterial = fields.Boolean(
        string="Nanomaterial",
        tracking=True,
        help="Article 2(1)(k). Ingredients present in the form of nanomaterials "
             "are followed by the word 'nano' in brackets in the list of "
             "ingredients - Article 19(1)(g).",
    )
    is_perfume_component = fields.Boolean(
        string="Perfume / Aromatic Composition",
        tracking=True,
        help="Perfume and aromatic compositions and their raw materials are "
             "referred to by the terms 'parfum' or 'aroma' in the list of "
             "ingredients - Article 19(1)(g).",
    )
    perfume_term = fields.Selection(
        selection=[
            (constants.INCI_PERFUME_TERM, "parfum"),
            (constants.INCI_AROMA_TERM, "aroma"),
        ],
        default=constants.INCI_PERFUME_TERM,
    )
    perfume_composition_code = fields.Char(
        string="Composition Code",
        help="Annex I Part A section 1 requires, for perfume and aromatic "
             "compositions, the name and code number of the composition and "
             "the identity of the supplier.",
    )
    perfume_supplier_id = fields.Many2one(
        comodel_name="res.partner",
        string="Composition Supplier",
    )
    requires_individual_listing = fields.Boolean(
        string="Must Be Listed Individually",
        help="Set for substances whose mention is required under the column "
             "'Other' in Annex III. Article 19(1)(g) requires their presence "
             "to be indicated in the list of ingredients in addition to the "
             "terms parfum or aroma.",
    )
    is_impurity = fields.Boolean(
        string="Impurity in Raw Material",
        help="Article 19(1)(g)(i): impurities in the raw materials used are "
             "not regarded as ingredients for labelling purposes.",
    )
    is_processing_aid = fields.Boolean(
        string="Subsidiary Technical Material",
        help="Article 19(1)(g)(ii): subsidiary technical materials used in "
             "the mixture but not present in the final product are not "
             "regarded as ingredients for labelling purposes.",
    )
    is_cmr = fields.Boolean(
        string="CMR Substance",
        tracking=True,
        help="Classified as carcinogenic, mutagenic or toxic for reproduction "
             "under Regulation (EC) No 1272/2008 - Article 15.",
    )
    cmr_category = fields.Selection(selection=constants.CMR_CATEGORY, tracking=True,)
    colour_index = fields.Char(help="CI nomenclature is used where applicable - Article 19(1)(g).",
                               )
    restriction_ids = fields.Many2many(
        comodel_name="ls.cosmetic.restriction",
        relation="ls_cosmetic_ingredient_restriction_rel",
        column1="ingredient_id",
        column2="restriction_id",
        string="Applicable Annex Entries",
    )
    prohibited = fields.Boolean(
        string="Prohibited (Annex II)",
        compute="_compute_prohibited",
        store=True,
        help="Computed from the linked annex entries. True as soon as an "
             "Annex II entry is linked.",
    )
    supplier_ids = fields.Many2many(
        comodel_name="res.partner",
        relation="ls_cosmetic_ingredient_supplier_rel",
        column1="ingredient_id",
        column2="partner_id",
        string="Suppliers",
    )
    product_id = fields.Many2one(
        comodel_name="product.product",
        string="Purchased Raw Material",
        help="Optional link to the raw material actually stocked and purchased.",
    )
    toxicological_profile = fields.Text(help="Annex I Part A section 8: toxicological profile of the substance "
                                        "for all relevant toxicological endpoints.",)
    toxicological_reference = fields.Char(
        string="Toxicological Data Source",
        help="Citation of the opinion, study or database entry the profile is "
             "taken from.",
    )
    note = fields.Text(string="Internal Note")

    _inci_name_unique = models.Constraint(
        "UNIQUE(inci_name, company_id)",
        "An ingredient with this INCI name already exists for this company.",
    )

    @api.depends("restriction_ids", "restriction_ids.annex")
    def _compute_prohibited(self):
        """Flag ingredients linked to an Annex II (prohibited) entry."""
        for record in self:
            record.prohibited = any(
                restriction.annex == "ii" for restriction in record.restriction_ids
            )

    @api.depends("inci_name", "is_nanomaterial")
    def _compute_display_name(self):
        """Show the nano marker in relations so it cannot be overlooked."""
        for record in self:
            name = record.inci_name or ""
            if record.is_nanomaterial and name:
                name = f"{name} {constants.INCI_NANO_SUFFIX}"
            record.display_name = name

    @api.constrains("is_cmr", "cmr_category")
    def _check_cmr_category(self):
        """A CMR flag without a category cannot be used for Article 15 checks."""
        for record in self:
            if record.is_cmr and not record.cmr_category:
                raise ValidationError(
                    self.env._(
                        "Ingredient %(name)s is flagged as a CMR substance but "
                        "no CMR category is set.",
                        name=record.inci_name,
                    )
                )
            if record.cmr_category and not record.is_cmr:
                raise ValidationError(
                    self.env._(
                        "Ingredient %(name)s carries a CMR category but is not "
                        "flagged as a CMR substance.",
                        name=record.inci_name,
                    )
                )

    @api.constrains("is_impurity", "is_processing_aid")
    def _check_exclusion_flags(self):
        """The two Article 19(1)(g) exclusions are mutually exclusive."""
        for record in self:
            if record.is_impurity and record.is_processing_aid:
                raise ValidationError(
                    self.env._(
                        "Ingredient %(name)s cannot be both an impurity in a raw "
                        "material and a subsidiary technical material.",
                        name=record.inci_name,
                    )
                )

    @api.constrains("is_perfume_component", "perfume_term")
    def _check_perfume_term(self):
        """A perfume component must state which of the two terms it uses."""
        for record in self:
            if record.is_perfume_component and not record.perfume_term:
                raise ValidationError(
                    self.env._(
                        "Ingredient %(name)s is a perfume or aromatic "
                        "composition and must be labelled either 'parfum' or "
                        "'aroma'.",
                        name=record.inci_name,
                    )
                )

    @api.onchange("regulatory_category")
    def _onchange_regulatory_category(self):
        """Clear the colour index when the substance is not a colorant."""
        for record in self:
            if record.regulatory_category != "colorant":
                record.colour_index = False

    def _label_token(self):
        """Return the token used for this ingredient in a label list.

        Article 19(1)(g) requires perfume and aromatic compositions to be
        referred to as 'parfum' or 'aroma', and ingredients present in the
        form of nanomaterials to be followed by the word 'nano' in brackets.

        :return: the label token as a string.
        """
        self.ensure_one()
        if self.is_perfume_component and not self.requires_individual_listing:
            return self.perfume_term or constants.INCI_PERFUME_TERM
        token = self.inci_name or ""
        if self.is_nanomaterial:
            token = f"{token} {constants.INCI_NANO_SUFFIX}"
        return token
