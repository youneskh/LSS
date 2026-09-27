# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0.html).
"""Labelling particulars required by Article 19 of Regulation (EC) No 1223/2009."""

from dateutil.relativedelta import relativedelta

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError

from . import constants


class LsCosmeticLabel(models.Model):
    """The set of particulars that must appear on container and packaging.

    Article 19(1) requires cosmetic products to be made available on the
    market only where the container and packaging bear, in indelible, easily
    legible and visible lettering, the particulars (a) to (g).  Each of those
    particulars has a dedicated field below, and approval is refused while
    any of them is missing.

    The list of ingredients is generated from the approved formulation rather
    than typed, so that the label and the regulatory composition cannot drift
    apart.
    """

    _name = "ls.cosmetic.label"
    _description = "Cosmetic Labelling Particulars"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "code desc, version desc, id desc"

    _LOCKED_FIELDS = (
        "code",
        "version",
        "formulation_id",
        "responsible_person_id",
        "responsible_person_address",
        "country_of_origin_id",
        "nominal_content",
        "durability_mode",
        "minimum_durability_date",
        "pao_months",
        "precautions",
        "batch_reference_rule",
        "product_function",
        "ingredient_list",
    )

    active = fields.Boolean(default=True)
    company_id = fields.Many2one(comodel_name="res.company", required=True,
                                 default=lambda self: self.env.company,
                                 index=True,)
    code = fields.Char(
        string="Label Reference",
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: self.env._("New"),
        index=True,
        tracking=True,
    )
    name = fields.Char(string="Label Name", required=True, tracking=True)
    version = fields.Integer(default=1, required=True, readonly=True, copy=False)
    state = fields.Selection(
        selection=constants.LABEL_STATE,
        string="Status",
        default="draft",
        required=True,
        copy=False,
        tracking=True,
    )
    formulation_id = fields.Many2one(comodel_name="ls.cosmetic.formulation", required=True,
                                     index=True,
                                     ondelete="restrict",
                                     tracking=True,)
    product_tmpl_id = fields.Many2one(
        related="formulation_id.product_tmpl_id",
        string="Finished Product",
        store=True,
    )

    # -- Article 19(1)(a) ----------------------------------------------
    responsible_person_id = fields.Many2one(comodel_name="res.partner", tracking=True,
                                            help="Article 19(1)(a): the name or registered name and the address "
                                            "of the responsible person.",
                                            )
    responsible_person_address = fields.Char(compute="_compute_responsible_person_address",
                                             store=True,
                                             readonly=False,
                                             help="Where several addresses are indicated, the one at which the "
                                             "responsible person makes the product information file readily "
                                             "available must be highlighted - Article 19(1)(a).",
                                             )
    is_imported = fields.Boolean(
        string="Imported Product",
        tracking=True,
        help="Article 19(1)(a): the country of origin must be specified for "
             "imported cosmetic products.",
    )
    country_of_origin_id = fields.Many2one(
        comodel_name="res.country",
        string="Country of Origin",
    )

    # -- Article 19(1)(b) ----------------------------------------------
    nominal_content = fields.Char(help="Article 19(1)(b): the nominal content at the time of packaging, "
                                  "given by weight or by volume.",
                                  )
    content_exempt = fields.Boolean(
        string="Content Indication Exempt",
        help="Article 19(1)(b) exempts packaging containing less than five "
             "grams or five millilitres, free samples and single-application "
             "packs.",
    )
    content_exempt_reason = fields.Char(string="Exemption Reason")

    # -- Article 19(1)(c) ----------------------------------------------
    durability_mode = fields.Selection(
        selection=constants.DURABILITY_MODE,
        string="Durability Indication",
        default="min_durability",
        required=True,
        tracking=True,
    )
    minimum_durability_date = fields.Date(
        string="Date of Minimum Durability",
        help="Article 19(1)(c): the date until which the product, stored "
             "under appropriate conditions, will continue to fulfil its "
             "initial function.",
    )
    durability_conditions = fields.Char(
        string="Storage Conditions",
        help="Indication of the conditions which must be satisfied to "
             "guarantee the stated durability - Article 19(1)(c).",
    )
    stated_durability_months = fields.Integer(
        string="Stated Minimum Durability (months)",
        help="Used only to check the 30 month threshold of Article 19(1)(c).",
    )
    pao_months = fields.Integer(
        string="Period After Opening (months)",
        help="Article 19(1)(c): for products with a minimum durability of "
             "more than 30 months, the period of time after opening for which "
             "the product is safe and can be used without any harm.",
    )

    # -- Article 19(1)(d) ----------------------------------------------
    precautions = fields.Text(
        string="Particular Precautions for Use",
        help="Article 19(1)(d): particular precautions to be observed in use, "
             "and at least those listed in Annexes III to VI, together with "
             "any special precautionary information for professional use.",
    )
    annex_wording = fields.Text(
        string="Wording Required by the Annexes",
        compute="_compute_annex_wording",
        help="Wording of conditions of use and warnings carried by the annex "
             "entries linked to the ingredients of the formulation.",
    )
    is_professional_use = fields.Boolean(string="For Professional Use")

    # -- Article 19(1)(e) ----------------------------------------------
    batch_reference_rule = fields.Char(
        string="Batch Number Rule",
        help="Article 19(1)(e): the batch number of manufacture or the "
             "reference for identifying the cosmetic product, and how it is "
             "applied.",
    )
    batch_on_packaging_only = fields.Boolean(
        string="Batch Number on Packaging Only",
        help="Article 19(1)(e) permits the information to appear only on the "
             "packaging where this is impossible for practical reasons "
             "because the products are too small.",
    )

    # -- Article 19(1)(f) ----------------------------------------------
    product_function = fields.Char(
        string="Function of the Product",
        help="Article 19(1)(f): the function of the cosmetic product, unless "
             "it is clear from its presentation.",
    )
    function_clear_from_presentation = fields.Boolean()

    # -- Article 19(1)(g) ----------------------------------------------
    ingredient_list = fields.Text(
        string="List of Ingredients",
        help="Article 19(1)(g). Generated from the formulation; the list is "
             "preceded by the term 'Ingredients'.",
    )
    ingredient_list_prefix = fields.Char(
        string="List Prefix",
        default=constants.INCI_LIST_PREFIX,
        required=True,
    )
    colorants_last = fields.Boolean(
        string="List Colorants Last",
        help="Article 19(1)(g) permits colorants other than those intended to "
             "colour the hair to be listed in any order after the other "
             "cosmetic ingredients.",
    )
    may_contain = fields.Boolean(
        string="Use 'may contain' Marker",
        help="Article 19(1)(g): for decorative cosmetic products marketed in "
             "several colour shades, all colorants other than hair colorants "
             "used in the range may be listed provided that the words 'may "
             "contain' or the symbol '+/-' are added.",
    )
    ingredient_list_generated_on = fields.Datetime(
        string="List Generated On", readonly=True, copy=False
    )

    # -- Article 19(2), (3) and (5) ------------------------------------
    information_on_leaflet = fields.Boolean(
        string="Particulars (d) and (g) on Enclosed Leaflet",
        help="Article 19(2): where it is impossible for practical reasons to "
             "label the information of points (d) and (g), it is mentioned on "
             "an enclosed or attached leaflet, label, tape, tag or card.",
    )
    notice_in_proximity = fields.Boolean(
        string="Ingredient List on Adjacent Notice",
        help="Article 19(3): in the case of soap, bath balls and other small "
             "products, the information of point (g) appears on a notice in "
             "immediate proximity to the container.",
    )
    language_ids = fields.Many2many(
        comodel_name="res.lang",
        relation="ls_cosmetic_label_lang_rel",
        column1="label_id",
        column2="lang_id",
        string="Label Languages",
        help="Article 19(5) makes the language of the information in points "
             "(b), (c), (d) and (f) subject to national law of the Member "
             "State in which the product is made available.",
    )
    artwork_attachment_ids = fields.Many2many(
        comodel_name="ir.attachment",
        relation="ls_cosmetic_label_artwork_rel",
        column1="label_id",
        column2="attachment_id",
        string="Artwork",
    )
    approved_by_id = fields.Many2one(comodel_name="res.users", readonly=True,
                                     copy=False,
                                     tracking=True,)
    approved_date = fields.Datetime(string="Approved On", readonly=True, copy=False)
    note = fields.Text(string="Internal Note")

    _code_version_unique = models.Constraint(
        "UNIQUE(code, version, company_id)",
        "A label with this reference and version already exists.",
    )
    _pao_months_positive = models.Constraint(
        "CHECK(pao_months >= 0)",
        "The period after opening cannot be negative.",
    )
    _durability_months_positive = models.Constraint(
        "CHECK(stated_durability_months >= 0)",
        "The stated minimum durability cannot be negative.",
    )

    # ------------------------------------------------------------------
    # Compute
    # ------------------------------------------------------------------
    @api.depends("responsible_person_id")
    def _compute_responsible_person_address(self):
        """Propose the responsible person address from the partner record."""
        for label in self:
            partner = label.responsible_person_id
            if not partner:
                label.responsible_person_address = False
                continue
            parts = [
                partner.street,
                partner.street2,
                partner.zip,
                partner.city,
                partner.country_id.name,
            ]
            label.responsible_person_address = ", ".join(
                part for part in parts if part
            )

    @api.depends("formulation_id", "formulation_id.line_ids")
    def _compute_annex_wording(self):
        """Collect the annex wording carried by the formulation ingredients."""
        for label in self:
            if not label.formulation_id:
                label.annex_wording = False
                continue
            wordings = label.formulation_id._get_annex_iii_other_warnings()
            label.annex_wording = "\n".join(wordings) if wordings else False

    @api.depends("code", "version", "name")
    def _compute_display_name(self):
        """Show the reference, version and name."""
        for label in self:
            label_code = label.code or ""
            label.display_name = (
                f"{label_code} v{label.version} - {label.name or ''}"
            ).strip(" -")

    # ------------------------------------------------------------------
    # Constraints
    # ------------------------------------------------------------------
    @api.constrains("durability_mode", "stated_durability_months", "pao_months",
                    "minimum_durability_date")
    def _check_durability(self):
        """Apply the 30 month rule of Article 19(1)(c)."""
        for label in self:
            mode = label.durability_mode
            if mode == "min_durability":
                if not label.minimum_durability_date:
                    continue
                if label.stated_durability_months > (
                    constants.MIN_DURABILITY_THRESHOLD_MONTHS
                ):
                    raise ValidationError(
                        self.env._(
                            "Label %(code)s states a minimum durability of "
                            "%(months)s months. Article 19(1)(c) makes the date "
                            "of minimum durability non-mandatory above "
                            "%(threshold)s months and requires a period after "
                            "opening instead.",
                            code=label.code,
                            months=label.stated_durability_months,
                            threshold=constants.MIN_DURABILITY_THRESHOLD_MONTHS,
                        )
                    )
            elif mode == "pao":
                if label.pao_months <= 0:
                    raise ValidationError(
                        self.env._(
                            "Label %(code)s indicates a period after opening "
                            "but no number of months is given.",
                            code=label.code,
                        )
                    )

    @api.constrains("state", "is_imported", "country_of_origin_id")
    def _check_country_of_origin(self):
        """Require the country of origin for imported products."""
        for label in self:
            if (
                label.state == "approved"
                and label.is_imported
                and not label.country_of_origin_id
            ):
                raise ValidationError(
                    self.env._(
                        "Label %(code)s is for an imported product. "
                        "Article 19(1)(a) requires the country of origin to be "
                        "specified.",
                        code=label.code,
                    )
                )

    @api.constrains("state", "nominal_content", "content_exempt",
                    "content_exempt_reason")
    def _check_nominal_content(self):
        """Require either a nominal content or a documented exemption."""
        for label in self:
            if label.state != "approved":
                continue
            if label.content_exempt:
                if not (label.content_exempt_reason or "").strip():
                    raise ValidationError(
                        self.env._(
                            "Label %(code)s claims the Article 19(1)(b) "
                            "exemption but gives no reason.",
                            code=label.code,
                        )
                    )
            elif not (label.nominal_content or "").strip():
                raise ValidationError(
                    self.env._(
                        "Label %(code)s has no nominal content and claims no "
                        "exemption - Article 19(1)(b).",
                        code=label.code,
                    )
                )

    @api.constrains("state", "product_function", "function_clear_from_presentation")
    def _check_product_function(self):
        """Require the function unless it is clear from the presentation."""
        for label in self:
            if label.state != "approved":
                continue
            if not label.function_clear_from_presentation and not (
                label.product_function or ""
            ).strip():
                raise ValidationError(
                    self.env._(
                        "Label %(code)s does not state the function of the "
                        "product and does not record that the function is "
                        "clear from its presentation - Article 19(1)(f).",
                        code=label.code,
                    )
                )

    # ------------------------------------------------------------------
    # ORM overrides
    # ------------------------------------------------------------------
    @api.model_create_multi
    def create(self, vals_list):
        """Assign the label reference from the sequence."""
        new_label = self.env._("New")
        for vals in vals_list:
            if vals.get("code", new_label) == new_label:
                company_id = vals.get("company_id") or self.env.company.id
                sequence = self.env["ir.sequence"].with_company(company_id)
                vals["code"] = sequence.next_by_code("ls.cosmetic.label") or new_label
        return super().create(vals_list)

    def write(self, vals):
        """Freeze the particulars once the label is approved or superseded."""
        protected = [field for field in vals if field in self._LOCKED_FIELDS]
        if protected:
            blocked = self.filtered(
                lambda record: record.state in ("approved", "superseded")
            )
            if blocked:
                raise UserError(
                    self.env._(
                        "Label %(code)s is %(state)s and its particulars can no "
                        "longer be modified. Create a new version instead.",
                        code=blocked[0].code,
                        state=blocked[0].state,
                    )
                )
        return super().write(vals)

    @api.ondelete(at_uninstall=False)
    def _ls_unlink_check_ls_cosmetic_label(self):
        """Allow deletion only while the label is still a draft."""
        blocked = self.filtered(lambda record: record.state != "draft")
        if blocked:
            raise UserError(
                self.env._(
                    "Label %(code)s is not a draft and cannot be deleted.",
                    code=blocked[0].code,
                )
            )

    def copy_data(self, default=None):
        """Reset reference and workflow data on duplication."""
        default = dict(default or {})
        vals_list = super().copy_data(default=default)
        for vals in vals_list:
            vals.setdefault("code", self.env._("New"))
            vals.setdefault("version", 1)
            vals.setdefault("state", "draft")
        return vals_list

    # ------------------------------------------------------------------
    # Workflow
    # ------------------------------------------------------------------
    def action_generate_ingredient_list(self):
        """Regenerate the Article 19(1)(g) list from the formulation."""
        for label in self:
            if label.state in ("approved", "superseded"):
                raise UserError(
                    self.env._(
                        "Label %(code)s is %(state)s and its ingredient list "
                        "can no longer be regenerated.",
                        code=label.code,
                        state=label.state,
                    )
                )
            if not label.formulation_id:
                raise UserError(
                    self.env._(
                        "Label %(code)s has no formulation to generate the "
                        "ingredient list from.",
                        code=label.code,
                    )
                )
            label.ingredient_list = label.formulation_id.build_ingredient_list(
                colorants_last=label.colorants_last,
                may_contain=label.may_contain,
            )
            label.ingredient_list_generated_on = fields.Datetime.now()
        return True

    def action_submit_review(self):
        """Move a draft label to review."""
        for label in self:
            if label.state != "draft":
                raise UserError(
                    self.env._(
                        "Only a draft label can be submitted for review. "
                        "%(code)s is %(state)s.",
                        code=label.code,
                        state=label.state,
                    )
                )
        self.write({"state": "review"})
        return True

    def action_approve(self):
        """Approve a label once every Article 19(1) particular is present."""
        for label in self:
            if label.state != "review":
                raise UserError(
                    self.env._(
                        "Only a label under review can be approved. %(code)s is "
                        "%(state)s.",
                        code=label.code,
                        state=label.state,
                    )
                )
            missing = label._missing_particulars()
            if missing:
                raise UserError(
                    self.env._(
                        "Label %(code)s cannot be approved. The following "
                        "Article 19(1) particulars are missing: %(items)s.",
                        code=label.code,
                        items="; ".join(missing),
                    )
                )
            if label.formulation_id.state != "approved":
                raise UserError(
                    self.env._(
                        "Label %(code)s refers to formulation %(formulation)s, "
                        "which is not approved.",
                        code=label.code,
                        formulation=label.formulation_id.display_name,
                    )
                )
        self.write(
            {
                "state": "approved",
                "approved_by_id": self.env.user.id,
                "approved_date": fields.Datetime.now(),
            }
        )
        return True

    def action_reset_draft(self):
        """Return a label under review to draft."""
        for label in self:
            if label.state != "review":
                raise UserError(
                    self.env._(
                        "Only a label under review can be returned to draft. "
                        "%(code)s is %(state)s.",
                        code=label.code,
                        state=label.state,
                    )
                )
        self.write({"state": "draft"})
        return True

    def action_open_generate_wizard(self):
        """Open the wizard that regenerates the ingredient list."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": self.env._("Generate Ingredient List"),
            "res_model": "ls.cosmetic.label.generate",
            "view_mode": "form",
            "target": "new",
            "context": {"default_label_id": self.id},
        }

    # ------------------------------------------------------------------
    # Business services
    # ------------------------------------------------------------------
    def _missing_particulars(self):
        """Return the Article 19(1) particulars that are not documented.

        :return: a list of human readable particular labels.
        """
        self.ensure_one()
        missing = []
        if not self.responsible_person_id or not (
            self.responsible_person_address or ""
        ).strip():
            missing.append(self.env._("(a) name and address of the responsible person"))
        if self.is_imported and not self.country_of_origin_id:
            missing.append(self.env._("(a) country of origin"))
        if not self.content_exempt and not (self.nominal_content or "").strip():
            missing.append(self.env._("(b) nominal content"))
        if self.durability_mode == "min_durability" and not self.minimum_durability_date:
            missing.append(self.env._("(c) date of minimum durability"))
        if self.durability_mode == "pao" and self.pao_months <= 0:
            missing.append(self.env._("(c) period after opening"))
        if not (self.precautions or "").strip() and (self.annex_wording or "").strip():
            missing.append(self.env._("(d) particular precautions required by the annexes"))
        if not (self.batch_reference_rule or "").strip():
            missing.append(self.env._("(e) batch number or identification reference"))
        if not self.function_clear_from_presentation and not (
            self.product_function or ""
        ).strip():
            missing.append(self.env._("(f) function of the product"))
        if not (self.ingredient_list or "").strip():
            missing.append(self.env._("(g) list of ingredients"))
        return missing

    def _suggested_pao_end_date(self, opening_date):
        """Return the date on which the period after opening elapses.

        The value is informative only; it is never printed on the label,
        because Article 19(1)(c) requires the period after opening to be
        expressed as a duration, not as a date.

        :param opening_date: :class:`datetime.date` the container was opened.
        :return: a :class:`datetime.date`, or ``False`` when no period applies.
        """
        self.ensure_one()
        if self.durability_mode != "pao" or self.pao_months <= 0:
            return False
        return opening_date + relativedelta(months=self.pao_months)
