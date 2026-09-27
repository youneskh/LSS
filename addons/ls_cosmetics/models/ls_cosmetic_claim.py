# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0.html).
"""Cosmetic product claims and their substantiation."""

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError

from . import constants


class LsCosmeticClaim(models.Model):
    """A claim made in labelling, marketing or advertising.

    Article 20(1) of Regulation (EC) No 1223/2009 forbids the use of text,
    names, trade marks, pictures and figurative or other signs to imply that
    a product has characteristics or functions which it does not have.
    Article 20(2) requires the responsible person to ensure that the wording
    of the claim complies with the common criteria set out in the annex to
    Commission Regulation (EU) No 655/2013.

    The six criteria are recorded individually: each carries a decision and a
    justification.  A claim cannot be approved while any criterion is
    unjustified, and the criteria are of equal importance, so none is
    optional.
    """

    _name = "ls.cosmetic.claim"
    _description = "Cosmetic Product Claim"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "code desc, id desc"

    active = fields.Boolean(default=True)
    company_id = fields.Many2one(comodel_name="res.company", required=True,
                                 default=lambda self: self.env.company,
                                 index=True,)
    code = fields.Char(
        string="Claim Reference",
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: self.env._("New"),
        index=True,
    )
    name = fields.Char(
        string="Claim Wording",
        required=True,
        tracking=True,
        help="The exact wording of the claim as it will appear.",
    )
    state = fields.Selection(
        selection=constants.CLAIM_STATE,
        string="Status",
        default="draft",
        required=True,
        copy=False,
        tracking=True,
    )
    product_tmpl_id = fields.Many2one(
        comodel_name="product.template",
        string="Product",
        tracking=True,
    )
    formulation_id = fields.Many2one(comodel_name="ls.cosmetic.formulation", tracking=True,
                                     help="Formulation the claim relates to. The evidence must have been "
                                     "generated on this composition.",)
    medium = fields.Char(help="Where the claim appears: packaging, leaflet, website, "
                         "advertising material.",)
    is_no_animal_testing_claim = fields.Boolean(
        string="No Animal Testing Claim",
        tracking=True,
        help="Article 20(3) allows a reference to the fact that no animal "
             "tests have been carried out only where the manufacturer and its "
             "suppliers have not carried out or commissioned any animal tests "
             "on the finished product, its prototype or any of its ingredients, "
             "and have not used ingredients tested on animals by others for "
             "the purpose of developing new cosmetic products.",
    )
    animal_testing_declaration = fields.Text(
        string="Article 20(3) Declaration",
        help="Record of the declarations obtained from the manufacturer and "
             "each supplier that support the claim.",
    )
    evidence_ids = fields.One2many(
        comodel_name="ls.cosmetic.claim.evidence",
        inverse_name="claim_id",
        string="Supporting Evidence",
    )
    evidence_count = fields.Integer(
        string="Evidence Items",
        compute="_compute_evidence_count",
        store=True,
    )

    # -- Common criteria of Regulation (EU) No 655/2013 -----------------
    criterion_legal = fields.Boolean(string="1. Legal Compliance Met", tracking=True)
    criterion_legal_note = fields.Text(string="Legal Compliance Justification")
    criterion_truth = fields.Boolean(string="2. Truthfulness Met", tracking=True)
    criterion_truth_note = fields.Text(string="Truthfulness Justification")
    criterion_evidence = fields.Boolean(string="3. Evidential Support Met", tracking=True)
    criterion_evidence_note = fields.Text(string="Evidential Support Justification")
    criterion_honesty = fields.Boolean(string="4. Honesty Met", tracking=True)
    criterion_honesty_note = fields.Text(string="Honesty Justification")
    criterion_fairness = fields.Boolean(string="5. Fairness Met", tracking=True)
    criterion_fairness_note = fields.Text(string="Fairness Justification")
    criterion_informed = fields.Boolean(
        string="6. Informed Decision-Making Met", tracking=True
    )
    criterion_informed_note = fields.Text(
        string="Informed Decision-Making Justification"
    )
    criteria_met_count = fields.Integer(
        string="Criteria Met",
        compute="_compute_criteria_met_count",
        store=True,
        help="Out of the six common criteria of Regulation (EU) No 655/2013.",
    )
    all_criteria_met = fields.Boolean(compute="_compute_criteria_met_count",
                                      store=True,)

    assessed_by_id = fields.Many2one(comodel_name="res.users", readonly=True,
                                     copy=False,
                                     tracking=True,)
    assessed_date = fields.Datetime(string="Assessed On", readonly=True, copy=False)
    approved_by_id = fields.Many2one(comodel_name="res.users", readonly=True,
                                     copy=False,
                                     tracking=True,)
    approved_date = fields.Datetime(string="Approved On", readonly=True, copy=False)
    decision_reason = fields.Text(readonly=True, copy=False)
    note = fields.Text(string="Internal Note")

    _code_unique = models.Constraint(
        "UNIQUE(code, company_id)",
        "A claim with this reference already exists for this company.",
    )

    #: Pairs of (boolean field, justification field) for the six criteria.
    _CRITERION_FIELDS = (
        ("criterion_legal", "criterion_legal_note"),
        ("criterion_truth", "criterion_truth_note"),
        ("criterion_evidence", "criterion_evidence_note"),
        ("criterion_honesty", "criterion_honesty_note"),
        ("criterion_fairness", "criterion_fairness_note"),
        ("criterion_informed", "criterion_informed_note"),
    )

    # ------------------------------------------------------------------
    # Compute
    # ------------------------------------------------------------------
    @api.depends("evidence_ids")
    def _compute_evidence_count(self):
        """Count the evidence items recorded against the claim."""
        for claim in self:
            claim.evidence_count = len(claim.evidence_ids)

    @api.depends(
        "criterion_legal",
        "criterion_truth",
        "criterion_evidence",
        "criterion_honesty",
        "criterion_fairness",
        "criterion_informed",
    )
    def _compute_criteria_met_count(self):
        """Count how many of the six common criteria are marked as met."""
        for claim in self:
            met = sum(
                1
                for field_name, _note_field in claim._CRITERION_FIELDS
                if claim[field_name]
            )
            claim.criteria_met_count = met
            claim.all_criteria_met = met == len(claim._CRITERION_FIELDS)

    @api.depends("code", "name")
    def _compute_display_name(self):
        """Show the reference together with the claim wording."""
        for claim in self:
            claim_code = claim.code or ""
            claim.display_name = f"{claim_code} - {claim.name or ''}".strip(" -")

    # ------------------------------------------------------------------
    # Constraints
    # ------------------------------------------------------------------
    @api.constrains(
        "state",
        "criterion_legal",
        "criterion_legal_note",
        "criterion_truth",
        "criterion_truth_note",
        "criterion_evidence",
        "criterion_evidence_note",
        "criterion_honesty",
        "criterion_honesty_note",
        "criterion_fairness",
        "criterion_fairness_note",
        "criterion_informed",
        "criterion_informed_note",
    )
    def _check_criteria_justified(self):
        """Require a written justification for every criterion once approved."""
        labels = dict(constants.CLAIM_COMMON_CRITERIA)
        suffix_by_field = {
            "criterion_legal": "legal",
            "criterion_truth": "truth",
            "criterion_evidence": "evidence",
            "criterion_honesty": "honesty",
            "criterion_fairness": "fairness",
            "criterion_informed": "informed",
        }
        for claim in self:
            if claim.state != "approved":
                continue
            for field_name, note_field in claim._CRITERION_FIELDS:
                if not claim[field_name] or not (claim[note_field] or "").strip():
                    criterion_label = labels.get(suffix_by_field[field_name], field_name)
                    raise ValidationError(
                        self.env._(
                            "Claim %(code)s cannot be approved: criterion "
                            "'%(criterion)s' is not marked as met with a written "
                            "justification.",
                            code=claim.code,
                            criterion=criterion_label,
                        )
                    )

    @api.constrains("state", "is_no_animal_testing_claim", "animal_testing_declaration")
    def _check_animal_testing_declaration(self):
        """Require the Article 20(3) declaration for a no-animal-testing claim."""
        for claim in self:
            if claim.state != "approved" or not claim.is_no_animal_testing_claim:
                continue
            if not (claim.animal_testing_declaration or "").strip():
                raise ValidationError(
                    self.env._(
                        "Claim %(code)s refers to the absence of animal testing "
                        "and cannot be approved without the declaration "
                        "required by Article 20(3).",
                        code=claim.code,
                    )
                )

    # ------------------------------------------------------------------
    # ORM overrides
    # ------------------------------------------------------------------
    @api.model_create_multi
    def create(self, vals_list):
        """Assign the claim reference from the sequence."""
        new_label = self.env._("New")
        for vals in vals_list:
            if vals.get("code", new_label) == new_label:
                company_id = vals.get("company_id") or self.env.company.id
                sequence = self.env["ir.sequence"].with_company(company_id)
                vals["code"] = sequence.next_by_code("ls.cosmetic.claim") or new_label
        return super().create(vals_list)

    @api.ondelete(at_uninstall=False)
    def _ls_unlink_check_ls_cosmetic_claim(self):
        """Allow deletion only while the claim is still a draft."""
        blocked = self.filtered(lambda record: record.state != "draft")
        if blocked:
            raise UserError(
                self.env._(
                    "Claim %(code)s is not a draft and cannot be deleted. "
                    "Withdraw it instead so that the substantiation record "
                    "remains available.",
                    code=blocked[0].code,
                )
            )

    def copy_data(self, default=None):
        """Reset reference and workflow data on duplication."""
        default = dict(default or {})
        vals_list = super().copy_data(default=default)
        for vals in vals_list:
            vals.setdefault("code", self.env._("New"))
            vals.setdefault("state", "draft")
        return vals_list

    # ------------------------------------------------------------------
    # Workflow
    # ------------------------------------------------------------------
    def action_start_substantiation(self):
        """Move a draft claim into substantiation."""
        for claim in self:
            if claim.state != "draft":
                raise UserError(
                    self.env._(
                        "Only a draft claim can be moved into substantiation. "
                        "%(code)s is %(state)s.",
                        code=claim.code,
                        state=claim.state,
                    )
                )
        self.write(
            {
                "state": "substantiation",
                "assessed_by_id": self.env.user.id,
                "assessed_date": fields.Datetime.now(),
            }
        )
        return True

    def action_approve(self):
        """Approve a substantiated claim.

        Evidential support is one of the six criteria, so a claim marked as
        evidentially supported must carry at least one evidence record.  The
        approver must differ from the user who performed the assessment.
        """
        for claim in self:
            if claim.state != "substantiation":
                raise UserError(
                    self.env._(
                        "Only a claim under substantiation can be approved. "
                        "%(code)s is %(state)s.",
                        code=claim.code,
                        state=claim.state,
                    )
                )
            if claim.assessed_by_id == self.env.user:
                raise UserError(
                    self.env._(
                        "Claim %(code)s was assessed by you and must be "
                        "approved by a different user.",
                        code=claim.code,
                    )
                )
            if claim.criterion_evidence and not claim.evidence_ids:
                raise UserError(
                    self.env._(
                        "Claim %(code)s is marked as evidentially supported but "
                        "carries no evidence record.",
                        code=claim.code,
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

    def action_reject(self):
        """Reject a claim under substantiation."""
        for claim in self:
            if claim.state != "substantiation":
                raise UserError(
                    self.env._(
                        "Only a claim under substantiation can be rejected. "
                        "%(code)s is %(state)s.",
                        code=claim.code,
                        state=claim.state,
                    )
                )
        self.write({"state": "rejected"})
        return True

    def action_withdraw(self):
        """Withdraw an approved claim."""
        for claim in self:
            if claim.state != "approved":
                raise UserError(
                    self.env._(
                        "Only an approved claim can be withdrawn. %(code)s is "
                        "%(state)s.",
                        code=claim.code,
                        state=claim.state,
                    )
                )
        self.write({"state": "withdrawn"})
        return True

    def action_reset_draft(self):
        """Return a rejected claim to draft for rework."""
        for claim in self:
            if claim.state != "rejected":
                raise UserError(
                    self.env._(
                        "Only a rejected claim can be returned to draft. "
                        "%(code)s is %(state)s.",
                        code=claim.code,
                        state=claim.state,
                    )
                )
        self.write(
            {"state": "draft", "assessed_by_id": False, "assessed_date": False}
        )
        return True
