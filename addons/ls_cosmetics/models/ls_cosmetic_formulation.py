# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0.html).
"""Cosmetic product formulations."""

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError

from . import constants


class LsCosmeticFormulation(models.Model):
    """The qualitative and quantitative composition of a cosmetic product.

    Annex I Part A section 1 of Regulation (EC) No 1223/2009 requires the
    qualitative and quantitative composition of the cosmetic product,
    including the chemical identity of the substances and their intended
    function.  This model holds that composition and is the source from which
    the label ingredient list of Article 19(1)(g) is generated.

    Approved formulations are immutable.  A change is made by creating a new
    version, which supersedes the previous one; the superseded record is kept
    because the product information file must remain reconstructable for the
    ten year retention period of Article 11(1).
    """

    _name = "ls.cosmetic.formulation"
    _description = "Cosmetic Formulation"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "code desc, version desc, id desc"

    #: Fields that cannot be modified once the formulation is approved.
    _LOCKED_FIELDS = (
        "code",
        "name",
        "version",
        "product_tmpl_id",
        "bom_id",
        "line_ids",
        "intended_use",
        "target_population",
        "for_children_under_three",
        "for_intimate_hygiene",
    )

    active = fields.Boolean(default=True)
    company_id = fields.Many2one(comodel_name="res.company", required=True,
                                 default=lambda self: self.env.company,
                                 index=True,)
    code = fields.Char(
        string="Formulation Code",
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: self.env._("New"),
        index=True,
        tracking=True,
    )
    name = fields.Char(string="Formulation Name", required=True, tracking=True)
    version = fields.Integer(default=1,
                             required=True,
                             readonly=True,
                             copy=False,
                             tracking=True,)
    state = fields.Selection(
        selection=constants.FORMULATION_STATE,
        string="Status",
        default="draft",
        required=True,
        copy=False,
        tracking=True,
    )
    product_tmpl_id = fields.Many2one(
        comodel_name="product.template",
        string="Finished Product",
        tracking=True,
        help="Product this formulation produces. Optional while the "
             "formulation is still under development.",
    )
    bom_id = fields.Many2one(
        comodel_name="mrp.bom",
        string="Bill of Materials",
        help="Manufacturing bill of materials realising this formulation. "
             "The formulation remains the regulatory record; the bill of "
             "materials remains the production record.",
    )
    predecessor_id = fields.Many2one(
        comodel_name="ls.cosmetic.formulation",
        string="Supersedes",
        readonly=True,
        copy=False,
    )
    successor_id = fields.Many2one(
        comodel_name="ls.cosmetic.formulation",
        string="Superseded By",
        readonly=True,
        copy=False,
    )
    line_ids = fields.One2many(
        comodel_name="ls.cosmetic.formulation.line",
        inverse_name="formulation_id",
        string="Composition",
        copy=True,
    )
    total_percentage = fields.Float(
        string="Total (% w/w)",
        digits=(16, 6),
        compute="_compute_total_percentage",
        store=True,
    )
    line_count = fields.Integer(
        string="Ingredients",
        compute="_compute_total_percentage",
        store=True,
    )
    intended_use = fields.Text(
        string="Normal and Reasonably Foreseeable Use",
        help="Annex I Part A section 5.",
    )
    target_population = fields.Text(
        string="Targeted Population",
        help="Annex I Part A section 6, item 6: the targeted or exposed "
             "populations.",
    )
    for_children_under_three = fields.Boolean(
        string="Intended for Children Under Three",
        tracking=True,
        help="Annex I Part B section 3 requires a specific assessment for "
             "cosmetic products intended for use on children under the age of "
             "three.",
    )
    for_intimate_hygiene = fields.Boolean(
        string="Exclusively for External Intimate Hygiene",
        tracking=True,
        help="Annex I Part B section 3 requires a specific assessment for "
             "cosmetic products intended exclusively for use in external "
             "intimate hygiene.",
    )
    contains_nanomaterial = fields.Boolean(
        string="Contains Nanomaterials",
        compute="_compute_regulatory_flags",
        store=True,
    )
    contains_cmr = fields.Boolean(
        string="Contains CMR Substances",
        compute="_compute_regulatory_flags",
        store=True,
    )
    blocking_finding_count = fields.Integer(
        string="Blocking Annex Findings",
        compute="_compute_regulatory_flags",
        store=True,
    )
    unevaluated_line_count = fields.Integer(
        string="Lines Without Annex Data",
        compute="_compute_regulatory_flags",
        store=True,
    )
    safety_assessment_ids = fields.One2many(
        comodel_name="ls.cosmetic.safety_assessment",
        inverse_name="formulation_id",
        string="Safety Assessments",
    )
    safety_assessment_count = fields.Integer(compute="_compute_safety_assessment_count",)
    submitted_by_id = fields.Many2one(comodel_name="res.users", readonly=True,
                                      copy=False,
                                      tracking=True,)
    submitted_date = fields.Datetime(
        string="Submitted On", readonly=True, copy=False
    )
    approved_by_id = fields.Many2one(comodel_name="res.users", readonly=True,
                                     copy=False,
                                     tracking=True,)
    approved_date = fields.Datetime(
        string="Approved On", readonly=True, copy=False
    )
    cancel_reason = fields.Text(string="Cancellation Reason", readonly=True, copy=False)
    note = fields.Text(string="Internal Note")

    _code_version_unique = models.Constraint(
        "UNIQUE(code, version, company_id)",
        "A formulation with this code and version already exists.",
    )
    _version_positive = models.Constraint(
        "CHECK(version > 0)",
        "The version number must be greater than zero.",
    )

    # ------------------------------------------------------------------
    # Compute
    # ------------------------------------------------------------------
    @api.depends("line_ids.concentration")
    def _compute_total_percentage(self):
        """Sum the composition and count its lines."""
        for formulation in self:
            formulation.total_percentage = sum(formulation.line_ids.mapped("concentration"))
            formulation.line_count = len(formulation.line_ids)

    @api.depends(
        "line_ids.is_nanomaterial",
        "line_ids.restriction_status",
        "line_ids.ingredient_id.is_cmr",
    )
    def _compute_regulatory_flags(self):
        """Summarise the regulatory findings carried by the composition."""
        for formulation in self:
            lines = formulation.line_ids
            formulation.contains_nanomaterial = any(lines.mapped("is_nanomaterial"))
            formulation.contains_cmr = any(
                line.ingredient_id.is_cmr for line in lines
            )
            formulation.blocking_finding_count = len(
                lines.filtered(
                    lambda line: line.restriction_status in ("prohibited", "over_limit")
                )
            )
            formulation.unevaluated_line_count = len(
                lines.filtered(lambda line: line.restriction_status == "no_reference_data")
            )

    def _compute_safety_assessment_count(self):
        """Count the safety assessments attached to each formulation."""
        grouped = self.env["ls.cosmetic.safety_assessment"]._read_group(
            domain=[("formulation_id", "in", self.ids)],
            groupby=["formulation_id"],
            aggregates=["__count"],
        )
        counts = {formulation.id: count for formulation, count in grouped}
        for formulation in self:
            formulation.safety_assessment_count = counts.get(formulation.id, 0)

    @api.depends("code", "name", "version")
    def _compute_display_name(self):
        """Show code, version and name so versions are distinguishable."""
        for formulation in self:
            record_code = formulation.code or ""
            record_name = formulation.name or ""
            formulation.display_name = (
                f"{record_code} v{formulation.version} - {record_name}".strip(" -")
            )

    # ------------------------------------------------------------------
    # Constraints
    # ------------------------------------------------------------------
    @api.constrains("state", "total_percentage")
    def _check_total_percentage(self):
        """Require the composition to total 100 % w/w from review onwards."""
        lower = constants.FORMULATION_TOTAL_PERCENT - constants.FORMULATION_TOTAL_TOLERANCE
        upper = constants.FORMULATION_TOTAL_PERCENT + constants.FORMULATION_TOTAL_TOLERANCE
        for formulation in self:
            if formulation.state not in ("review", "approved"):
                continue
            if not lower <= formulation.total_percentage <= upper:
                raise ValidationError(
                    self.env._(
                        "Formulation %(name)s totals %(total).6f %% w/w. A "
                        "formulation submitted for review must total "
                        "%(target).2f %% w/w within a tolerance of "
                        "%(tolerance).2f %%.",
                        name=formulation.display_name,
                        total=formulation.total_percentage,
                        target=constants.FORMULATION_TOTAL_PERCENT,
                        tolerance=constants.FORMULATION_TOTAL_TOLERANCE,
                    )
                )

    @api.constrains("state", "line_ids")
    def _check_lines_present(self):
        """A formulation without composition cannot leave the draft state."""
        for formulation in self:
            if formulation.state != "draft" and not formulation.line_ids:
                raise ValidationError(
                    self.env._(
                        "Formulation %(name)s has no composition and cannot "
                        "leave the draft state.",
                        name=formulation.display_name,
                    )
                )

    @api.constrains("predecessor_id")
    def _check_predecessor_not_self(self):
        """A formulation cannot supersede itself."""
        for formulation in self:
            if formulation.predecessor_id == formulation:
                raise ValidationError(
                    self.env._("A formulation cannot supersede itself.")
                )

    # ------------------------------------------------------------------
    # ORM overrides
    # ------------------------------------------------------------------
    @api.model_create_multi
    def create(self, vals_list):
        """Assign the formulation code from the sequence."""
        new_label = self.env._("New")
        for vals in vals_list:
            if vals.get("code", new_label) == new_label:
                company_id = vals.get("company_id") or self.env.company.id
                sequence = self.env["ir.sequence"].with_company(company_id)
                vals["code"] = sequence.next_by_code("ls.cosmetic.formulation") or new_label
        return super().create(vals_list)

    def write(self, vals):
        """Protect approved and superseded formulations from modification."""
        locked_states = ("approved", "superseded")
        protected = [field for field in vals if field in self._LOCKED_FIELDS]
        if protected:
            blocked = self.filtered(lambda record: record.state in locked_states)
            if blocked:
                raise UserError(
                    self.env._(
                        "Formulation %(name)s is %(state)s and its composition "
                        "and identification can no longer be modified. Create a "
                        "new version instead.",
                        name=blocked[0].display_name,
                        state=blocked[0].state,
                    )
                )
        return super().write(vals)

    @api.ondelete(at_uninstall=False)
    def _ls_unlink_check_ls_cosmetic_formulation(self):
        """Allow deletion only while the formulation is still a draft."""
        blocked = self.filtered(lambda record: record.state != "draft")
        if blocked:
            raise UserError(
                self.env._(
                    "Formulation %(name)s is not a draft and cannot be deleted. "
                    "Cancel it instead so that the record remains available for "
                    "the retention period of Article 11(1).",
                    name=blocked[0].display_name,
                )
            )

    def copy_data(self, default=None):
        """Reset identification and workflow data on duplication."""
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
    def action_submit_review(self):
        """Move a draft formulation to review and record the submitter."""
        for formulation in self:
            if formulation.state != "draft":
                raise UserError(
                    self.env._(
                        "Only a draft formulation can be submitted for review. "
                        "%(name)s is %(state)s.",
                        name=formulation.display_name,
                        state=formulation.state,
                    )
                )
        self.write(
            {
                "state": "review",
                "submitted_by_id": self.env.user.id,
                "submitted_date": fields.Datetime.now(),
            }
        )
        return True

    def action_approve(self):
        """Approve a formulation under review.

        Segregation of duties: the approver must not be the user who
        submitted the formulation for review.  Blocking annex findings must
        be cleared first.
        """
        for formulation in self:
            if formulation.state != "review":
                raise UserError(
                    self.env._(
                        "Only a formulation under review can be approved. "
                        "%(name)s is %(state)s.",
                        name=formulation.display_name,
                        state=formulation.state,
                    )
                )
            if formulation.submitted_by_id == self.env.user:
                raise UserError(
                    self.env._(
                        "Formulation %(name)s was submitted for review by you "
                        "and must be approved by a different user.",
                        name=formulation.display_name,
                    )
                )
            if formulation.blocking_finding_count:
                raise UserError(
                    self.env._(
                        "Formulation %(name)s carries %(count)s blocking annex "
                        "finding(s) and cannot be approved.",
                        name=formulation.display_name,
                        count=formulation.blocking_finding_count,
                    )
                )
        self.write(
            {
                "state": "approved",
                "approved_by_id": self.env.user.id,
                "approved_date": fields.Datetime.now(),
            }
        )
        for formulation in self:
            predecessor = formulation.predecessor_id
            if predecessor and predecessor.state == "approved":
                predecessor.write({"state": "superseded"})
                predecessor.message_post(
                    body=self.env._(
                        "Superseded by version %(version)s.",
                        version=formulation.version,
                    )
                )
        return True

    def action_reset_draft(self):
        """Return a formulation under review to draft."""
        for formulation in self:
            if formulation.state != "review":
                raise UserError(
                    self.env._(
                        "Only a formulation under review can be returned to "
                        "draft. %(name)s is %(state)s.",
                        name=formulation.display_name,
                        state=formulation.state,
                    )
                )
        self.write({"state": "draft", "submitted_by_id": False, "submitted_date": False})
        return True

    def action_cancel(self):
        """Cancel a draft or reviewed formulation without deleting it."""
        for formulation in self:
            if formulation.state not in ("draft", "review"):
                raise UserError(
                    self.env._(
                        "Only a draft or reviewed formulation can be cancelled. "
                        "%(name)s is %(state)s.",
                        name=formulation.display_name,
                        state=formulation.state,
                    )
                )
        self.write({"state": "cancelled"})
        return True

    def action_open_revise_wizard(self):
        """Open the wizard that creates the next version of a formulation."""
        self.ensure_one()
        if self.state != "approved":
            raise UserError(
                self.env._(
                    "Only an approved formulation can be revised. %(name)s is "
                    "%(state)s.",
                    name=self.display_name,
                    state=self.state,
                )
            )
        return {
            "type": "ir.actions.act_window",
            "name": self.env._("Revise Formulation"),
            "res_model": "ls.cosmetic.formulation.revise",
            "view_mode": "form",
            "target": "new",
            "context": {"default_formulation_id": self.id},
        }

    def action_view_safety_assessments(self):
        """Open the safety assessments linked to this formulation."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": self.env._("Safety Assessments"),
            "res_model": "ls.cosmetic.safety_assessment",
            "view_mode": "list,form",
            "domain": [("formulation_id", "=", self.id)],
            "context": {"default_formulation_id": self.id},
        }

    # ------------------------------------------------------------------
    # Business services
    # ------------------------------------------------------------------
    def _label_lines(self):
        """Return the composition lines that appear on a label, in order.

        Impurities and subsidiary technical materials are removed per
        Article 19(1)(g)(i) and (ii).  The remaining lines are ordered in
        descending order of weight.

        :return: a list of ``ls.cosmetic.formulation.line`` records.
        """
        self.ensure_one()
        lines = self.line_ids.filtered(lambda line: not line.exclude_from_label)
        return sorted(lines, key=lambda line: line._label_sort_key())

    def build_ingredient_list(self, colorants_last=False, may_contain=False):
        """Build the Article 19(1)(g) list of ingredients.

        The list is established in descending order of weight of the
        ingredients at the time they are added to the cosmetic product.
        Ingredients in concentrations of less than 1 % may be listed in any
        order after those in concentrations of more than 1 %.  Ingredients
        present in the form of nanomaterials are followed by the word 'nano'
        in brackets.  Perfume and aromatic compositions and their raw
        materials are referred to by the terms 'parfum' or 'aroma'; a
        substance whose mention is required under the column 'Other' in
        Annex III is listed individually in addition to those terms.

        :param colorants_last: when True, colorants are moved after the other
            ingredients. Article 19(1)(g) permits colorants other than hair
            colorants to be listed in any order after the other cosmetic
            ingredients.
        :param may_contain: when True, the colorant block is prefixed with the
            marker permitted for decorative products marketed in several
            colour shades.
        :return: the ingredient list as a single string.
        """
        self.ensure_one()
        ordered = self._label_lines()
        main_tokens = []
        colorant_tokens = []
        perfume_terms = []
        for line in ordered:
            ingredient = line.ingredient_id
            if ingredient.is_perfume_component and not ingredient.requires_individual_listing:
                term = ingredient.perfume_term or constants.INCI_PERFUME_TERM
                if term not in perfume_terms:
                    perfume_terms.append(term)
                continue
            token = ingredient._label_token()
            if colorants_last and ingredient.regulatory_category == "colorant":
                if token not in colorant_tokens:
                    colorant_tokens.append(token)
            elif token not in main_tokens:
                main_tokens.append(token)
        tokens = main_tokens + perfume_terms
        if colorant_tokens:
            if may_contain:
                tokens.append(constants.INCI_MAY_CONTAIN_MARKER)
            tokens.extend(colorant_tokens)
        return ", ".join(tokens)

    def _get_annex_iii_other_warnings(self):
        """Return the label wording required by linked Annex III entries.

        Annex III carries a column 'Wording of conditions of use and
        warnings'.  Article 19(1)(d) requires particular precautions to be
        observed in use, and at least those listed in Annexes III to VI, to
        appear on the label.

        :return: a list of distinct wording strings.
        """
        self.ensure_one()
        wordings = []
        for line in self.line_ids:
            for restriction in line.ingredient_id.restriction_ids:
                text = (restriction.label_wording or "").strip()
                if text and text not in wordings:
                    wordings.append(text)
        return wordings
