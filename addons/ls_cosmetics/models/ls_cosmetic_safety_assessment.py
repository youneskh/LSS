# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0.html).
"""Cosmetic product safety report (Annex I of Regulation (EC) No 1223/2009)."""

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError

from . import constants


class LsCosmeticSafetyAssessment(models.Model):
    """The cosmetic product safety report required by Article 10.

    Article 10(1) requires the responsible person, prior to placing a
    cosmetic product on the market, to ensure that the product has undergone
    a safety assessment on the basis of the relevant information and that a
    cosmetic product safety report is set up in accordance with Annex I.

    The field layout below reproduces the structure of Annex I exactly:

    * Part A - Cosmetic product safety information, sections 1 to 10.
    * Part B - Cosmetic product safety assessment, sections 1 to 4.

    Article 10(2) requires the Part B assessment to be carried out by a
    person in possession of a diploma or other evidence of formal
    qualifications awarded on completion of a university course of
    theoretical and practical study in pharmacy, toxicology, medicine or a
    similar discipline, or a course recognised as equivalent.  The module
    records the assessor's identity, address and qualification evidence; it
    cannot verify a diploma, and does not pretend to.
    """

    _name = "ls.cosmetic.safety_assessment"
    _description = "Cosmetic Product Safety Report"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "code desc, version desc, id desc"

    #: Part B fields, locked once the assessment is approved.
    _LOCKED_FIELDS = (
        "code",
        "version",
        "formulation_id",
        "conclusion",
        "conclusion_statement",
        "labelled_warnings",
        "reasoning",
        "assessor_partner_id",
        "assessor_qualification",
        "assessor_address",
    )

    active = fields.Boolean(default=True)
    company_id = fields.Many2one(comodel_name="res.company", required=True,
                                 default=lambda self: self.env.company,
                                 index=True,)
    code = fields.Char(
        string="Report Reference",
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: self.env._("New"),
        index=True,
        tracking=True,
    )
    name = fields.Char(string="Report Title", required=True, tracking=True)
    version = fields.Integer(default=1, required=True, readonly=True, copy=False)
    state = fields.Selection(
        selection=constants.SAFETY_ASSESSMENT_STATE,
        string="Status",
        default="draft",
        required=True,
        copy=False,
        tracking=True,
    )
    formulation_id = fields.Many2one(comodel_name="ls.cosmetic.formulation", required=True,
                                     index=True,
                                     tracking=True,
                                     ondelete="restrict",)
    product_tmpl_id = fields.Many2one(
        related="formulation_id.product_tmpl_id",
        string="Finished Product",
        store=True,
    )
    predecessor_id = fields.Many2one(
        comodel_name="ls.cosmetic.safety_assessment",
        string="Supersedes",
        readonly=True,
        copy=False,
    )

    # ------------------------------------------------------------------
    # Annex I - Part A : Cosmetic product safety information
    # ------------------------------------------------------------------
    part_a_1_composition = fields.Text(
        string="A1. Quantitative and Qualitative Composition",
        help="Annex I Part A section 1. The composition itself is held on the "
             "linked formulation; this field records the narrative, including "
             "the name and code number of any perfume or aromatic composition "
             "and the identity of its supplier.",
    )
    part_a_2_physchem = fields.Text(
        string="A2. Physical/Chemical Characteristics and Stability",
        help="Annex I Part A section 2: the physical and chemical "
             "characteristics of the substances or mixtures and of the "
             "cosmetic product, and the stability of the product under "
             "reasonably foreseeable storage conditions.",
    )
    part_a_3_microbiology = fields.Text(
        string="A3. Microbiological Quality",
        help="Annex I Part A section 3: microbiological specifications of the "
             "substance or mixture and of the cosmetic product, and the "
             "results of the preservation challenge test.",
    )
    part_a_4_impurities = fields.Text(
        string="A4. Impurities, Traces, Packaging Material",
        help="Annex I Part A section 4: purity of the substances and mixtures, "
             "evidence of technical unavoidability for traces of prohibited "
             "substances, and the relevant characteristics of the packaging "
             "material.",
    )
    part_a_5_use = fields.Text(
        string="A5. Normal and Reasonably Foreseeable Use",
        help="Annex I Part A section 5.",
    )
    part_a_6_product_exposure = fields.Text(
        string="A6. Exposure to the Cosmetic Product",
        help="Annex I Part A section 6: sites and surface areas of "
             "application, amount applied, duration and frequency of use, "
             "exposure routes and targeted populations.",
    )
    part_a_7_substance_exposure = fields.Text(
        string="A7. Exposure to the Substances",
        help="Annex I Part A section 7.",
    )
    part_a_8_toxicological = fields.Text(
        string="A8. Toxicological Profile of the Substances",
        help="Annex I Part A section 8, including local toxicity, skin "
             "sensitisation, photo-induced toxicity where UV absorption "
             "applies, and the margin of safety.",
    )
    part_a_9_undesirable_effects = fields.Text(
        string="A9. Undesirable and Serious Undesirable Effects",
        help="Annex I Part A section 9.",
    )
    part_a_10_other_information = fields.Text(
        string="A10. Other Information on the Cosmetic Product",
        help="Annex I Part A section 10.",
    )
    margin_of_safety = fields.Float(
        string="Lowest Margin of Safety",
        digits=(16, 2),
        help="Lowest margin of safety calculated across the substances "
             "assessed. Recorded as reported by the assessor; the module "
             "performs no toxicological calculation.",
    )
    margin_of_safety_basis = fields.Char(help="Substance and endpoint the lowest margin of safety relates to.",)

    # ------------------------------------------------------------------
    # Annex I - Part B : Cosmetic product safety assessment
    # ------------------------------------------------------------------
    conclusion = fields.Selection(
        selection=constants.SAFETY_CONCLUSION,
        string="B1. Assessment Conclusion",
        tracking=True,
        help="Annex I Part B section 1: statement on the safety of the "
             "cosmetic product in relation to Article 3.",
    )
    conclusion_statement = fields.Text(
        string="B1. Conclusion Statement",
        help="The full wording of the conclusion as signed by the assessor.",
    )
    labelled_warnings = fields.Text(
        string="B2. Labelled Warnings and Instructions of Use",
        help="Annex I Part B section 2: statement on the need to label any "
             "particular warnings and instructions of use in accordance with "
             "Article 19(1)(d).",
    )
    reasoning = fields.Text(
        string="B3. Reasoning",
        help="Annex I Part B section 3: explanation of the scientific "
             "reasoning leading to the conclusion of section 1 and the "
             "statement of section 2, based on the descriptions in Part A.",
    )
    reasoning_children = fields.Text(
        string="B3. Specific Assessment - Children Under Three",
        help="Annex I Part B section 3 requires a specific assessment for "
             "cosmetic products intended for use on children under the age of "
             "three.",
    )
    reasoning_intimate_hygiene = fields.Text(
        string="B3. Specific Assessment - External Intimate Hygiene",
        help="Annex I Part B section 3 requires a specific assessment for "
             "cosmetic products intended exclusively for use in external "
             "intimate hygiene.",
    )
    reasoning_interactions = fields.Text(
        string="B3. Interactions Between Substances",
        help="Annex I Part B section 3 requires possible interactions of the "
             "substances contained in the cosmetic product to be assessed.",
    )
    reasoning_stability_impact = fields.Text(
        string="B3. Impact of Stability on Safety",
        help="Annex I Part B section 3 requires the impacts of stability on "
             "the safety of the cosmetic product to be duly considered.",
    )
    reasoning_toxicological_scope = fields.Text(
        string="B3. Justification of Toxicological Profiles Considered",
        help="Annex I Part B section 3 requires the consideration and "
             "non-consideration of the different toxicological profiles to be "
             "duly justified.",
    )
    assessor_partner_id = fields.Many2one(
        comodel_name="res.partner",
        string="B4. Safety Assessor",
        tracking=True,
        help="Annex I Part B section 4: name and address of the safety "
             "assessor.",
    )
    assessor_address = fields.Char(
        string="B4. Assessor Address",
        compute="_compute_assessor_address",
        store=True,
        readonly=False,
    )
    assessor_qualification = fields.Char(
        string="B4. Assessor Qualification",
        help="Diploma or other evidence of formal qualifications relied upon "
             "under Article 10(2): a university course of theoretical and "
             "practical study in pharmacy, toxicology, medicine or a similar "
             "discipline, or a course recognised as equivalent.",
    )
    assessor_qualification_attachment_ids = fields.Many2many(
        comodel_name="ir.attachment",
        relation="ls_cosmetic_assessment_qualification_rel",
        column1="assessment_id",
        column2="attachment_id",
        string="B4. Qualification Evidence",
    )
    assessor_user_id = fields.Many2one(
        comodel_name="res.users",
        string="Assessor User Account",
        help="Internal user account through which the assessor approves the "
             "report. Required so that the approval is attributable.",
    )
    approval_date = fields.Date(
        string="B4. Date of Approval", readonly=True, copy=False, tracking=True
    )
    approved_by_id = fields.Many2one(comodel_name="res.users", readonly=True,
                                     copy=False,
                                     tracking=True,)
    review_date = fields.Date(
        string="Next Review Date",
        tracking=True,
        help="Article 10(1)(c) requires the safety report to be kept up to "
             "date in view of additional relevant information generated after "
             "the product is placed on the market. This date drives the "
             "review reminder.",
    )
    review_overdue = fields.Boolean(compute="_compute_review_overdue",
                                    search="_search_review_overdue",)
    non_clinical_glp_statement = fields.Text(
        string="Non-Clinical Studies Compliance",
        help="Article 10(3): non-clinical safety studies carried out after "
             "30 June 1988 for the purpose of assessing the safety of a "
             "cosmetic product must comply with good laboratory practice or "
             "with international standards recognised as equivalent.",
    )
    note = fields.Text(string="Internal Note")

    _code_version_unique = models.Constraint(
        "UNIQUE(code, version, company_id)",
        "A safety report with this reference and version already exists.",
    )
    _version_positive = models.Constraint(
        "CHECK(version > 0)",
        "The version number must be greater than zero.",
    )
    _margin_of_safety_positive = models.Constraint(
        "CHECK(margin_of_safety >= 0)",
        "The margin of safety cannot be negative.",
    )

    #: Part A sections that must all be completed before Part B may start.
    _PART_A_FIELDS = (
        ("part_a_1_composition", "A1. Quantitative and qualitative composition"),
        ("part_a_2_physchem", "A2. Physical/chemical characteristics and stability"),
        ("part_a_3_microbiology", "A3. Microbiological quality"),
        ("part_a_4_impurities", "A4. Impurities, traces, packaging material"),
        ("part_a_5_use", "A5. Normal and reasonably foreseeable use"),
        ("part_a_6_product_exposure", "A6. Exposure to the cosmetic product"),
        ("part_a_7_substance_exposure", "A7. Exposure to the substances"),
        ("part_a_8_toxicological", "A8. Toxicological profile of the substances"),
        ("part_a_9_undesirable_effects", "A9. Undesirable and serious undesirable effects"),
        ("part_a_10_other_information", "A10. Other information on the cosmetic product"),
    )

    # ------------------------------------------------------------------
    # Compute
    # ------------------------------------------------------------------
    @api.depends("assessor_partner_id")
    def _compute_assessor_address(self):
        """Propose the assessor address from the partner record."""
        for assessment in self:
            partner = assessment.assessor_partner_id
            if not partner:
                assessment.assessor_address = False
                continue
            parts = [
                partner.street,
                partner.street2,
                partner.zip,
                partner.city,
                partner.country_id.name,
            ]
            assessment.assessor_address = ", ".join(part for part in parts if part)

    def _compute_review_overdue(self):
        """Flag reports whose review date has passed."""
        today = fields.Date.context_today(self)
        for assessment in self:
            assessment.review_overdue = bool(
                assessment.state == "approved"
                and assessment.review_date
                and assessment.review_date < today
            )

    def _search_review_overdue(self, operator, value):
        """Search helper for the non-stored ``review_overdue`` field."""
        today = fields.Date.context_today(self)
        overdue_domain = [
            ("state", "=", "approved"),
            ("review_date", "!=", False),
            ("review_date", "<", today),
        ]
        if operator not in ("=", "!="):
            raise UserError(
                self.env._("Only the = and != operators are supported here.")
            )
        looking_for_overdue = (operator == "=") == bool(value)
        if looking_for_overdue:
            return overdue_domain
        matching = self.search(overdue_domain)
        return [("id", "not in", matching.ids)]

    @api.depends("code", "version", "name")
    def _compute_display_name(self):
        """Show the reference, version and title."""
        for assessment in self:
            assessment_code = assessment.code or ""
            assessment.display_name = (
                f"{assessment_code} v{assessment.version} - {assessment.name or ''}"
            ).strip(" -")

    # ------------------------------------------------------------------
    # Constraints
    # ------------------------------------------------------------------
    @api.constrains("state", "formulation_id")
    def _check_formulation_approved(self):
        """Part B may only assess an approved composition.

        Assessing a composition that can still change would make the report
        unattributable to the product actually placed on the market.
        """
        for assessment in self:
            if assessment.state in ("part_b", "approved") and (
                assessment.formulation_id.state != "approved"
            ):
                raise ValidationError(
                    self.env._(
                        "Safety report %(code)s assesses formulation %(formulation)s, "
                        "which is not approved. Part B requires an approved "
                        "composition.",
                        code=assessment.code,
                        formulation=assessment.formulation_id.display_name,
                    )
                )

    @api.constrains(
        "state",
        "conclusion",
        "conclusion_statement",
        "labelled_warnings",
        "reasoning",
        "assessor_partner_id",
        "assessor_address",
        "assessor_qualification",
    )
    def _check_part_b_complete(self):
        """Require every Annex I Part B section before approval."""
        required = (
            ("conclusion", "B1. Assessment conclusion"),
            ("conclusion_statement", "B1. Conclusion statement"),
            ("labelled_warnings", "B2. Labelled warnings and instructions of use"),
            ("reasoning", "B3. Reasoning"),
            ("assessor_partner_id", "B4. Safety assessor"),
            ("assessor_address", "B4. Assessor address"),
            ("assessor_qualification", "B4. Assessor qualification"),
        )
        for assessment in self:
            if assessment.state != "approved":
                continue
            for field_name, label in required:
                value = assessment[field_name]
                if not value or (isinstance(value, str) and not value.strip()):
                    raise ValidationError(
                        self.env._(
                            "Safety report %(code)s cannot be approved: section "
                            "'%(section)s' is empty.",
                            code=assessment.code,
                            section=label,
                        )
                    )

    @api.constrains("state", "reasoning_children", "reasoning_intimate_hygiene")
    def _check_specific_assessments(self):
        """Enforce the two specific assessments named in Annex I Part B."""
        for assessment in self:
            if assessment.state != "approved":
                continue
            formulation = assessment.formulation_id
            if formulation.for_children_under_three and not (
                assessment.reasoning_children or ""
            ).strip():
                raise ValidationError(
                    self.env._(
                        "Formulation %(formulation)s is intended for children "
                        "under three. Annex I Part B section 3 requires a "
                        "specific assessment, which is missing from report "
                        "%(code)s.",
                        formulation=formulation.display_name,
                        code=assessment.code,
                    )
                )
            if formulation.for_intimate_hygiene and not (
                assessment.reasoning_intimate_hygiene or ""
            ).strip():
                raise ValidationError(
                    self.env._(
                        "Formulation %(formulation)s is intended exclusively for "
                        "external intimate hygiene. Annex I Part B section 3 "
                        "requires a specific assessment, which is missing from "
                        "report %(code)s.",
                        formulation=formulation.display_name,
                        code=assessment.code,
                    )
                )

    # ------------------------------------------------------------------
    # ORM overrides
    # ------------------------------------------------------------------
    @api.model_create_multi
    def create(self, vals_list):
        """Assign the report reference from the sequence."""
        new_label = self.env._("New")
        for vals in vals_list:
            if vals.get("code", new_label) == new_label:
                company_id = vals.get("company_id") or self.env.company.id
                sequence = self.env["ir.sequence"].with_company(company_id)
                vals["code"] = (
                    sequence.next_by_code("ls.cosmetic.safety_assessment") or new_label
                )
        return super().create(vals_list)

    def write(self, vals):
        """Freeze Part B once the report has been approved."""
        protected = [field for field in vals if field in self._LOCKED_FIELDS]
        if protected:
            blocked = self.filtered(
                lambda record: record.state in ("approved", "superseded")
            )
            if blocked:
                raise UserError(
                    self.env._(
                        "Safety report %(code)s is %(state)s. Its assessment can "
                        "no longer be modified; issue a new version instead.",
                        code=blocked[0].code,
                        state=blocked[0].state,
                    )
                )
        return super().write(vals)

    @api.ondelete(at_uninstall=False)
    def _ls_unlink_check_ls_cosmetic_safety_assessment(self):
        """Allow deletion only while the report is still a draft."""
        blocked = self.filtered(lambda record: record.state != "draft")
        if blocked:
            raise UserError(
                self.env._(
                    "Safety report %(code)s is not a draft and cannot be "
                    "deleted. Cancel it instead.",
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
    def action_start_part_a(self):
        """Open Part A for completion."""
        for assessment in self:
            if assessment.state != "draft":
                raise UserError(
                    self.env._(
                        "Only a draft report can start Part A. %(code)s is "
                        "%(state)s.",
                        code=assessment.code,
                        state=assessment.state,
                    )
                )
        self.write({"state": "part_a"})
        return True

    def action_start_part_b(self):
        """Close Part A and open Part B.

        Every Annex I Part A section must be documented before the assessor
        can reason on it: Part B section 3 explicitly requires the
        explanation to be based on the descriptions set out under Part A.
        """
        for assessment in self:
            if assessment.state != "part_a":
                raise UserError(
                    self.env._(
                        "Only a report with Part A in preparation can move to "
                        "Part B. %(code)s is %(state)s.",
                        code=assessment.code,
                        state=assessment.state,
                    )
                )
            missing = assessment._missing_part_a_sections()
            if missing:
                raise UserError(
                    self.env._(
                        "Report %(code)s cannot move to Part B. The following "
                        "Part A sections are empty: %(sections)s.",
                        code=assessment.code,
                        sections="; ".join(missing),
                    )
                )
        self.write({"state": "part_b"})
        return True

    def action_approve(self):
        """Approve the report on behalf of the safety assessor.

        The approval must be performed by the user account designated as the
        assessor, so that the record of who signed Part B is accurate.
        """
        for assessment in self:
            if assessment.state != "part_b":
                raise UserError(
                    self.env._(
                        "Only a report with Part B in assessment can be "
                        "approved. %(code)s is %(state)s.",
                        code=assessment.code,
                        state=assessment.state,
                    )
                )
            if not assessment.assessor_user_id:
                raise UserError(
                    self.env._(
                        "Report %(code)s has no assessor user account. Part B "
                        "must be attributable to the qualified person named in "
                        "section B4.",
                        code=assessment.code,
                    )
                )
            if assessment.assessor_user_id != self.env.user:
                raise UserError(
                    self.env._(
                        "Report %(code)s must be approved by %(assessor)s, the "
                        "assessor named in section B4.",
                        code=assessment.code,
                        assessor=assessment.assessor_user_id.name,
                    )
                )
        self.write(
            {
                "state": "approved",
                "approval_date": fields.Date.context_today(self),
                "approved_by_id": self.env.user.id,
            }
        )
        return True

    def action_reset_draft(self):
        """Return a report in preparation to draft."""
        for assessment in self:
            if assessment.state not in ("part_a", "part_b"):
                raise UserError(
                    self.env._(
                        "Only a report in preparation can be returned to draft. "
                        "%(code)s is %(state)s.",
                        code=assessment.code,
                        state=assessment.state,
                    )
                )
        self.write({"state": "draft"})
        return True

    def action_cancel(self):
        """Cancel a report that has not been approved."""
        for assessment in self:
            if assessment.state in ("approved", "superseded"):
                raise UserError(
                    self.env._(
                        "Report %(code)s is %(state)s and cannot be cancelled.",
                        code=assessment.code,
                        state=assessment.state,
                    )
                )
        self.write({"state": "cancelled"})
        return True

    # ------------------------------------------------------------------
    # Business services
    # ------------------------------------------------------------------
    def _missing_part_a_sections(self):
        """Return the labels of the Part A sections that are still empty.

        :return: a list of section labels.
        """
        self.ensure_one()
        missing = []
        for field_name, label in self._PART_A_FIELDS:
            if not (self[field_name] or "").strip():
                missing.append(label)
        return missing

    @api.model
    def _cron_notify_review_due(self):
        """Post a reminder on approved reports whose review date has passed.

        Article 10(1)(c) requires the safety report to be kept up to date.
        The reminder is posted on the record chatter; no external mail
        template is used so that the module does not depend on a mail server
        being configured.

        :return: the number of reports the reminder was posted on.
        """
        today = fields.Date.context_today(self)
        due = self.search(
            [
                ("state", "=", "approved"),
                ("review_date", "!=", False),
                ("review_date", "<=", today),
            ]
        )
        for assessment in due:
            assessment.message_post(
                body=self.env._(
                    "The review date of this cosmetic product safety report "
                    "(%(date)s) has been reached. Article 10(1)(c) requires the "
                    "report to be kept up to date in view of additional "
                    "relevant information.",
                    date=assessment.review_date,
                )
            )
        return len(due)
