# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0.html).
"""Product information file (Article 11 of Regulation (EC) No 1223/2009)."""

from dateutil.relativedelta import relativedelta

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError

from . import constants


class LsCosmeticPif(models.Model):
    """The product information file kept by the responsible person.

    Article 11(1) requires the responsible person to keep a product
    information file for a cosmetic product placed on the market, for a
    period of ten years following the date on which the last batch was placed
    on the market.

    Article 11(2) lists the five items the file must contain:

    (a) a description of the cosmetic product which enables the file to be
        clearly attributed to the product;
    (b) the cosmetic product safety report referred to in Article 10(1);
    (c) a description of the method of manufacturing and a statement on
        compliance with the good manufacturing practice referred to in
        Article 8;
    (d) where justified by the nature or the effect of the product, proof of
        the effect claimed;
    (e) data on any animal testing performed by the manufacturer, its agents
        or suppliers.

    Each of the five items is a separate field or relation, and the file
    cannot be activated while any applicable item is missing.

    **The date the last batch was placed on the market is entered manually.**
    Odoo has no native concept of a batch being "placed on the market": a
    stock move to a customer location is a commercial event, not necessarily
    the regulatory one, and inferring the date automatically would put an
    unverifiable value on the retention clock.  The date is therefore
    recorded by the regulatory user, and the retention end date is computed
    from it.
    """

    _name = "ls.cosmetic.pif"
    _description = "Cosmetic Product Information File"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "code desc, id desc"

    active = fields.Boolean(default=True)
    company_id = fields.Many2one(comodel_name="res.company", required=True,
                                 default=lambda self: self.env.company,
                                 index=True,)
    code = fields.Char(
        string="File Reference",
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: self.env._("New"),
        index=True,
        tracking=True,
    )
    name = fields.Char(string="File Name", required=True, tracking=True)
    state = fields.Selection(
        selection=constants.PIF_STATE,
        string="Status",
        default="draft",
        required=True,
        copy=False,
        tracking=True,
    )
    product_tmpl_id = fields.Many2one(
        comodel_name="product.template",
        string="Cosmetic Product",
        required=True,
        index=True,
        ondelete="restrict",
        tracking=True,
    )

    # -- Article 4 : responsible person --------------------------------
    responsible_person_id = fields.Many2one(comodel_name="res.partner", required=True,
                                            tracking=True,
                                            help="Article 4: a cosmetic product may not be placed on the market "
                                            "unless there is a responsible person in respect of it.",)
    responsible_person_basis = fields.Selection(
        selection=constants.RESPONSIBLE_PERSON_BASIS,
        string="Basis of Designation",
        required=True,
        tracking=True,
    )
    mandate_reference = fields.Char(
        string="Written Mandate Reference",
        help="Reference of the written mandate and of the written acceptance "
             "where the responsible person is a designated person - Article 4.",
    )
    file_address = fields.Char(
        string="Address Where the File Is Kept",
        required=True,
        help="Article 11(3): the responsible person makes the file readily "
             "accessible in electronic or other format at the address "
             "indicated on the label.",
    )
    file_language_ids = fields.Many2many(
        comodel_name="res.lang",
        relation="ls_cosmetic_pif_lang_rel",
        column1="pif_id",
        column2="lang_id",
        string="File Languages",
        help="Article 11(3): the information must be available in a language "
             "which can be easily understood by the competent authorities of "
             "the Member State in which the file is kept.",
    )

    # -- Article 11(2)(a) ----------------------------------------------
    product_description = fields.Text(
        string="(a) Description of the Cosmetic Product",
        help="Article 11(2)(a): a description that enables the product "
             "information file to be clearly attributed to the cosmetic "
             "product.",
    )

    # -- Article 11(2)(b) ----------------------------------------------
    safety_assessment_id = fields.Many2one(
        comodel_name="ls.cosmetic.safety_assessment",
        string="(b) Cosmetic Product Safety Report",
        tracking=True,
        ondelete="restrict",
    )
    formulation_id = fields.Many2one(related="safety_assessment_id.formulation_id", store=True,)
    label_id = fields.Many2one(
        comodel_name="ls.cosmetic.label",
        string="Approved Label",
        ondelete="restrict",
    )

    # -- Article 11(2)(c) ----------------------------------------------
    manufacturing_method = fields.Text(
        string="(c) Description of the Method of Manufacturing",
        help="Article 11(2)(c).",
    )
    gmp_statement = fields.Text(
        string="(c) Statement on GMP Compliance",
        help="Article 11(2)(c) requires a statement on compliance with the "
             "good manufacturing practice referred to in Article 8. "
             "Article 8(2) provides that compliance is presumed where the "
             "manufacture is in accordance with the relevant harmonised "
             "standards.",
    )
    gmp_standard = fields.Char(
        string="(c) GMP Standard Applied",
        default=constants.STD_ISO_22716,
        help="Standard the manufacturing site applies. ISO 22716:2007 is the "
             "cosmetics GMP standard; whether it is a harmonised standard for "
             "the purposes of Article 8(2) at a given date must be confirmed "
             "against the current list of harmonised standards.",
    )
    gmp_site_id = fields.Many2one(
        comodel_name="res.partner",
        string="(c) Manufacturing Site",
    )
    gmp_certificate_reference = fields.Char(
        string="(c) GMP Certificate or Audit Reference",
    )
    gmp_certificate_date = fields.Date(string="(c) GMP Evidence Date")

    # -- Article 11(2)(d) ----------------------------------------------
    claim_ids = fields.Many2many(
        comodel_name="ls.cosmetic.claim",
        relation="ls_cosmetic_pif_claim_rel",
        column1="pif_id",
        column2="claim_id",
        string="(d) Claims and Proof of Effect",
        help="Article 11(2)(d): where justified by the nature or the effect of "
             "the cosmetic product, proof of the effect claimed.",
    )
    claim_count = fields.Integer(
        string="Claims", compute="_compute_claim_count", store=True
    )
    unapproved_claim_count = fields.Integer(
        string="Unapproved Claims", compute="_compute_claim_count", store=True
    )
    no_claims_justification = fields.Text(
        string="(d) Justification for the Absence of Claims",
        help="Recorded where the nature or effect of the product does not "
             "justify proof of a claimed effect.",
    )

    # -- Article 11(2)(e) ----------------------------------------------
    animal_testing_data = fields.Text(
        string="(e) Data on Animal Testing",
        help="Article 11(2)(e): data on any animal testing performed by the "
             "manufacturer, its agents or suppliers relating to the "
             "development or safety assessment of the product or its "
             "ingredients, including any animal testing performed to meet the "
             "legislative or regulatory requirements of third countries.",
    )
    no_animal_testing = fields.Boolean(
        string="(e) No Animal Testing Performed",
        help="Tick where no animal testing has been performed. The statement "
             "still has to be recorded in the file.",
    )

    # -- Notification and retention ------------------------------------
    notification_reference = fields.Char(tracking=True,
                                         help="Reference issued when the information required by Article 13 "
                                         "was submitted to the competent authority before placing the "
                                         "product on the market.",)
    notification_date = fields.Date(tracking=True)
    dz_authorization_ids = fields.One2many(
        comodel_name="ls.cosmetic.dz_authorization",
        inverse_name="pif_id",
        string="Algerian Prior Authorisations",
    )
    first_placed_date = fields.Date(
        string="First Placed on the Market", tracking=True
    )
    last_batch_market_date = fields.Date(
        string="Last Batch Placed on the Market",
        tracking=True,
        help="Article 11(1): the retention period of ten years runs from this "
             "date. Entered manually because the moment a batch is placed on "
             "the market is a regulatory event that Odoo does not record.",
    )
    retention_end_date = fields.Date(compute="_compute_retention_end_date",
                                     store=True,
                                     help="Ten years after the date on which the last batch was placed on "
                                     "the market - Article 11(1).",
                                     )
    retention_elapsed = fields.Boolean(
        string="Retention Period Elapsed",
        compute="_compute_retention_elapsed",
        search="_search_retention_elapsed",
    )
    last_review_date = fields.Date(help="Article 11(2) requires the information and data in the file to "
                                   "be updated as necessary.",
                                   )
    attachment_ids = fields.Many2many(
        comodel_name="ir.attachment",
        relation="ls_cosmetic_pif_attachment_rel",
        column1="pif_id",
        column2="attachment_id",
        string="File Contents",
    )
    activated_by_id = fields.Many2one(comodel_name="res.users", readonly=True,
                                      copy=False,
                                      tracking=True,)
    activated_date = fields.Datetime(
        string="Activated On", readonly=True, copy=False
    )
    archived_by_id = fields.Many2one(comodel_name="res.users", readonly=True,
                                     copy=False,
                                     tracking=True,)
    archived_date = fields.Datetime(string="Archived On", readonly=True, copy=False)
    note = fields.Text(string="Internal Note")

    _code_unique = models.Constraint(
        "UNIQUE(code, company_id)",
        "A product information file with this reference already exists.",
    )

    #: Article 11(2) items that must be documented before activation.
    _ARTICLE_11_ITEMS = (
        ("product_description", "(a) description of the cosmetic product"),
        ("safety_assessment_id", "(b) cosmetic product safety report"),
        ("manufacturing_method", "(c) description of the method of manufacturing"),
        ("gmp_statement", "(c) statement on GMP compliance"),
    )

    # ------------------------------------------------------------------
    # Compute
    # ------------------------------------------------------------------
    @api.depends("last_batch_market_date")
    def _compute_retention_end_date(self):
        """Add the ten year retention period of Article 11(1)."""
        for pif in self:
            if pif.last_batch_market_date:
                pif.retention_end_date = pif.last_batch_market_date + relativedelta(
                    years=constants.PIF_RETENTION_YEARS
                )
            else:
                pif.retention_end_date = False

    def _compute_retention_elapsed(self):
        """Flag files whose ten year retention period has ended."""
        today = fields.Date.context_today(self)
        for pif in self:
            pif.retention_elapsed = bool(
                pif.retention_end_date and pif.retention_end_date < today
            )

    def _search_retention_elapsed(self, operator, value):
        """Search helper for the non-stored ``retention_elapsed`` field."""
        if operator not in ("=", "!="):
            raise UserError(
                self.env._("Only the = and != operators are supported here.")
            )
        today = fields.Date.context_today(self)
        looking_for_elapsed = (operator == "=") == bool(value)
        if looking_for_elapsed:
            return [
                ("retention_end_date", "!=", False),
                ("retention_end_date", "<", today),
            ]
        return [
            "|",
            ("retention_end_date", "=", False),
            ("retention_end_date", ">=", today),
        ]

    @api.depends("claim_ids", "claim_ids.state")
    def _compute_claim_count(self):
        """Count the claims attached to the file and those not yet approved."""
        for pif in self:
            pif.claim_count = len(pif.claim_ids)
            pif.unapproved_claim_count = len(
                pif.claim_ids.filtered(lambda claim: claim.state != "approved")
            )

    @api.depends("code", "name")
    def _compute_display_name(self):
        """Show the file reference together with its name."""
        for pif in self:
            pif_code = pif.code or ""
            pif.display_name = f"{pif_code} - {pif.name or ''}".strip(" -")

    # ------------------------------------------------------------------
    # Constraints
    # ------------------------------------------------------------------
    @api.constrains("state", "safety_assessment_id")
    def _check_safety_assessment_approved(self):
        """An active file must carry an approved safety report."""
        for pif in self:
            if pif.state not in ("active", "retention"):
                continue
            assessment = pif.safety_assessment_id
            if not assessment:
                raise ValidationError(
                    self.env._(
                        "File %(code)s carries no cosmetic product safety "
                        "report - Article 11(2)(b).",
                        code=pif.code,
                    )
                )
            if assessment.state != "approved":
                raise ValidationError(
                    self.env._(
                        "File %(code)s refers to safety report %(report)s, which "
                        "is not approved.",
                        code=pif.code,
                        report=assessment.display_name,
                    )
                )
            if assessment.conclusion == "not_safe":
                raise ValidationError(
                    self.env._(
                        "Safety report %(report)s concludes that the product is "
                        "not safe. File %(code)s cannot be activated.",
                        report=assessment.display_name,
                        code=pif.code,
                    )
                )

    @api.constrains("first_placed_date", "last_batch_market_date")
    def _check_market_dates(self):
        """The last batch cannot precede the first placing on the market."""
        for pif in self:
            if (
                pif.first_placed_date
                and pif.last_batch_market_date
                and pif.last_batch_market_date < pif.first_placed_date
            ):
                raise ValidationError(
                    self.env._(
                        "File %(code)s: the last batch cannot be placed on the "
                        "market before the product first was.",
                        code=pif.code,
                    )
                )

    @api.constrains("state", "animal_testing_data", "no_animal_testing")
    def _check_animal_testing_item(self):
        """Require the Article 11(2)(e) item to be documented either way."""
        for pif in self:
            if pif.state not in ("active", "retention"):
                continue
            if not pif.no_animal_testing and not (
                pif.animal_testing_data or ""
            ).strip():
                raise ValidationError(
                    self.env._(
                        "File %(code)s does not document animal testing data "
                        "and does not state that no animal testing was "
                        "performed - Article 11(2)(e).",
                        code=pif.code,
                    )
                )

    # ------------------------------------------------------------------
    # ORM overrides
    # ------------------------------------------------------------------
    @api.model_create_multi
    def create(self, vals_list):
        """Assign the file reference from the sequence."""
        new_label = self.env._("New")
        for vals in vals_list:
            if vals.get("code", new_label) == new_label:
                company_id = vals.get("company_id") or self.env.company.id
                sequence = self.env["ir.sequence"].with_company(company_id)
                vals["code"] = sequence.next_by_code("ls.cosmetic.pif") or new_label
        return super().create(vals_list)

    @api.ondelete(at_uninstall=False)
    def _ls_unlink_check_ls_cosmetic_pif(self):
        """Refuse deletion outside the draft state.

        Article 11(1) fixes a ten year retention period; deleting a file that
        has been active would destroy the record the competent authority is
        entitled to inspect.
        """
        blocked = self.filtered(lambda record: record.state != "draft")
        if blocked:
            raise UserError(
                self.env._(
                    "File %(code)s has left the draft state and cannot be "
                    "deleted. Article 11(1) requires it to be kept for ten "
                    "years after the last batch was placed on the market.",
                    code=blocked[0].code,
                )
            )

    def copy_data(self, default=None):
        """Reset reference, workflow and market dates on duplication."""
        default = dict(default or {})
        vals_list = super().copy_data(default=default)
        for vals in vals_list:
            vals.setdefault("code", self.env._("New"))
            vals.setdefault("state", "draft")
            vals.setdefault("first_placed_date", False)
            vals.setdefault("last_batch_market_date", False)
        return vals_list

    # ------------------------------------------------------------------
    # Workflow
    # ------------------------------------------------------------------
    def action_activate(self):
        """Activate the file when every applicable Article 11(2) item is present."""
        for pif in self:
            if pif.state != "draft":
                raise UserError(
                    self.env._(
                        "Only a draft file can be activated. %(code)s is "
                        "%(state)s.",
                        code=pif.code,
                        state=pif.state,
                    )
                )
            missing = pif._missing_article_11_items()
            if missing:
                raise UserError(
                    self.env._(
                        "File %(code)s cannot be activated. The following "
                        "Article 11(2) items are missing: %(items)s.",
                        code=pif.code,
                        items="; ".join(missing),
                    )
                )
        self.write(
            {
                "state": "active",
                "activated_by_id": self.env.user.id,
                "activated_date": fields.Datetime.now(),
            }
        )
        return True

    def action_enter_retention(self):
        """Move an active file into its retention period.

        The transition is made once the last batch has been placed on the
        market, which is the event that starts the ten year clock.
        """
        for pif in self:
            if pif.state != "active":
                raise UserError(
                    self.env._(
                        "Only an active file can enter the retention period. "
                        "%(code)s is %(state)s.",
                        code=pif.code,
                        state=pif.state,
                    )
                )
            if not pif.last_batch_market_date:
                raise UserError(
                    self.env._(
                        "File %(code)s cannot enter the retention period: the "
                        "date on which the last batch was placed on the market "
                        "is not recorded.",
                        code=pif.code,
                    )
                )
        self.write({"state": "retention"})
        return True

    def action_archive_file(self):
        """Archive a file once the ten year retention period has elapsed."""
        today = fields.Date.context_today(self)
        for pif in self:
            if pif.state != "retention":
                raise UserError(
                    self.env._(
                        "Only a file in its retention period can be archived. "
                        "%(code)s is %(state)s.",
                        code=pif.code,
                        state=pif.state,
                    )
                )
            if not pif.retention_end_date or pif.retention_end_date >= today:
                raise UserError(
                    self.env._(
                        "File %(code)s cannot be archived before %(date)s, the "
                        "end of the ten year retention period required by "
                        "Article 11(1).",
                        code=pif.code,
                        date=pif.retention_end_date or self.env._("an unknown date"),
                    )
                )
        self.write(
            {
                "state": "archived",
                "archived_by_id": self.env.user.id,
                "archived_date": fields.Datetime.now(),
            }
        )
        return True

    def action_reset_draft(self):
        """Return an active file to draft."""
        for pif in self:
            if pif.state != "active":
                raise UserError(
                    self.env._(
                        "Only an active file can be returned to draft. "
                        "%(code)s is %(state)s.",
                        code=pif.code,
                        state=pif.state,
                    )
                )
        self.write({"state": "draft", "activated_by_id": False, "activated_date": False})
        return True

    # ------------------------------------------------------------------
    # Business services
    # ------------------------------------------------------------------
    def _missing_article_11_items(self):
        """Return the Article 11(2) items that are not yet documented.

        :return: a list of human readable item labels.
        """
        self.ensure_one()
        missing = []
        for field_name, label in self._ARTICLE_11_ITEMS:
            value = self[field_name]
            if not value or (isinstance(value, str) and not value.strip()):
                missing.append(label)
        if not self.claim_ids and not (self.no_claims_justification or "").strip():
            missing.append(
                self.env._(
                    "(d) proof of the effect claimed, or a justification for "
                    "its absence"
                )
            )
        if self.unapproved_claim_count:
            missing.append(
                self.env._(
                    "(d) %(count)s claim(s) attached to the file are not approved",
                    count=self.unapproved_claim_count,
                )
            )
        if not self.no_animal_testing and not (self.animal_testing_data or "").strip():
            missing.append(self.env._("(e) data on animal testing"))
        return missing

    @api.model
    def _cron_monitor_retention(self):
        """Post a notice on files whose retention period has elapsed.

        The cron never archives a file by itself.  Ending the retention of a
        regulatory dossier is a decision, and the module records decisions
        made by people rather than making them.

        :return: the number of files a notice was posted on.
        """
        today = fields.Date.context_today(self)
        elapsed = self.search(
            [
                ("state", "=", "retention"),
                ("retention_end_date", "!=", False),
                ("retention_end_date", "<", today),
            ]
        )
        for pif in elapsed:
            pif.message_post(
                body=self.env._(
                    "The ten year retention period required by Article 11(1) "
                    "ended on %(date)s. This file may now be archived by a "
                    "regulatory manager.",
                    date=pif.retention_end_date,
                )
            )
        return len(elapsed)
