# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0.html).
"""Algerian prior authorisation for cosmetic and body hygiene products."""

from datetime import timedelta

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError

from . import constants


class LsCosmeticDzAuthorization(models.Model):
    """Prior authorisation dossier under the Algerian cosmetics decree.

    Cosmetic and body hygiene products placed on the Algerian national market
    are governed by decret executif n° 97-37 of 14 January 1997, defining the
    conditions and procedures for manufacture, packaging, importation and
    marketing, as modified and completed by decret executif n° 10-114 of
    18 April 2010, which introduced a prior authorisation requirement.

    The procedure published by the Ministere du Commerce is reproduced here:

    * the application is filed with the territorially competent Direction de
      Wilaya du Commerce, by post with recorded delivery or in person against
      a deposit receipt, which is not itself an authorisation;
    * the dossier comprises the sixteen items listed in
      :data:`constants.DZ_DOSSIER_ITEMS`;
    * the authorisation is issued by the Minister of Commerce after the
      opinion of the Scientific and Technical Commission of the Centre
      Algerien du Controle de la Qualite et de l'Emballage;
    * the decision is notified within forty-five days from the date the
      deposit receipt was issued;
    * where an element on which the authorisation was granted subsequently
      fails, the operator is formally notified and has one month to comply,
      failing which the authorisation is withdrawn.

    Two points are stated plainly.  First, cosmetics in Algeria fall under
    the Ministere du Commerce, not under the ANPP, which is the
    pharmaceutical authority; no ANPP requirement is asserted by this model.
    Second, the composition of the Algerian annexes of permitted and
    prohibited substances could not be reliably established from the
    ministry's published index, so no annex numbering is encoded here.
    """

    _name = "ls.cosmetic.dz_authorization"
    _description = "Algerian Prior Authorisation (Cosmetics)"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "code desc, id desc"

    active = fields.Boolean(default=True)
    company_id = fields.Many2one(comodel_name="res.company", required=True,
                                 default=lambda self: self.env.company,
                                 index=True,)
    code = fields.Char(
        string="Dossier Reference",
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: self.env._("New"),
        index=True,
        tracking=True,
    )
    name = fields.Char(
        string="Product Denomination",
        required=True,
        tracking=True,
        help="Denomination and designation of the product, item 7 of the "
             "dossier.",
    )
    state = fields.Selection(
        selection=constants.DZ_AUTHORIZATION_STATE,
        string="Status",
        default="draft",
        required=True,
        copy=False,
        tracking=True,
    )
    authorization_type = fields.Selection(
        selection=constants.DZ_AUTHORIZATION_TYPE,
        string="Authorisation Type",
        required=True,
        tracking=True,
    )
    product_tmpl_id = fields.Many2one(
        comodel_name="product.template",
        string="Product",
        index=True,
    )
    pif_id = fields.Many2one(
        comodel_name="ls.cosmetic.pif",
        string="Product Information File",
        index=True,
        ondelete="set null",
    )
    formulation_id = fields.Many2one(comodel_name="ls.cosmetic.formulation", help="Supports item 9 of the dossier, the qualitative composition and "
                                     "the analytical quality of the raw materials.",)
    operator_partner_id = fields.Many2one(
        comodel_name="res.partner",
        string="Operator",
        required=True,
        tracking=True,
        help="Manufacturer, packager or importer applying for the "
             "authorisation.",
    )
    wilaya_direction = fields.Char(
        string="Direction de Wilaya du Commerce",
        help="Territorially competent directorate the application is filed "
             "with.",
    )
    submission_mode = fields.Selection(
        selection=[
            ("post", "Recorded delivery with acknowledgement of receipt"),
            ("hand", "Filed in person"),
        ],
    )
    submission_date = fields.Date(tracking=True)
    receipt_reference = fields.Char(
        string="Deposit Receipt Reference",
        tracking=True,
        help="A deposit receipt is issued when the application is filed in "
             "person. It cannot in any case be treated as an authorisation.",
    )
    receipt_date = fields.Date(
        string="Deposit Receipt Date",
        tracking=True,
        help="The forty-five day notification period runs from this date.",
    )
    decision_due_date = fields.Date(compute="_compute_decision_due_date",
                                    store=True,
                                    help="Forty-five days after the deposit receipt was issued.",)
    decision_overdue = fields.Boolean(compute="_compute_decision_overdue",
                                      search="_search_decision_overdue",)
    decision_date = fields.Date(tracking=True)
    authorization_reference = fields.Char(
        string="Authorisation Reference", tracking=True
    )
    refusal_reason = fields.Text(
        string="Reasoned Refusal",
        help="The decision refusing a prior authorisation is a reasoned "
             "decision.",
    )
    notice_date = fields.Date(
        string="Formal Notice Date",
        tracking=True,
        help="Date the written formal notice (mise en demeure) was notified "
             "to the operator.",
    )
    notice_deadline = fields.Date(
        string="Compliance Deadline",
        compute="_compute_notice_deadline",
        store=True,
        help="One month from the notification of the formal notice.",
    )
    notice_subject = fields.Text(string="Formal Notice Subject")
    withdrawal_date = fields.Date(tracking=True)
    scientific_commission_opinion = fields.Text(
        string="Scientific and Technical Commission Opinion",
        help="Opinion of the Scientific and Technical Commission of the "
             "Centre Algerien du Controle de la Qualite et de l'Emballage, on "
             "which the Minister's decision is based.",
    )

    # -- The sixteen dossier items -------------------------------------
    doc_rc = fields.Boolean(string="1. Commercial Register Extract")
    doc_fiscal = fields.Boolean(string="2. Tax Identification Number")
    doc_statutes = fields.Boolean(string="3. Company Statutes")
    doc_accounts = fields.Boolean(string="4. CNRC Social Accounts Filing Certificate")
    doc_tax_roll = fields.Boolean(string="5. Cleared Tax Roll Extract")
    doc_social = fields.Boolean(string="6. CNAS / CASNOS Certificate")
    doc_denomination = fields.Boolean(string="7. Denomination and Designation")
    doc_usage = fields.Boolean(string="8. Use and Directions for Use")
    doc_composition = fields.Boolean(string="9. Qualitative Composition")
    doc_analyses = fields.Boolean(string="10. Raw Material and Finished Product Analyses")
    doc_toxicity = fields.Boolean(string="11. Toxicity Testing Results and Methods")
    doc_batch_id = fields.Boolean(string="12. Batch Identification Method")
    doc_precautions = fields.Boolean(string="13. Particular Precautions for Use")
    doc_label_model = fields.Boolean(string="14. Label Model or Artwork")
    doc_responsible = fields.Boolean(string="15. Responsible Persons and Qualifications")
    doc_trademark = fields.Boolean(string="16. Trademark Registration or Authorisation")
    dossier_complete = fields.Boolean(compute="_compute_dossier_completeness",
                                      store=True,)
    dossier_item_count = fields.Integer(
        string="Items Provided",
        compute="_compute_dossier_completeness",
        store=True,
    )
    attachment_ids = fields.Many2many(
        comodel_name="ir.attachment",
        relation="ls_cosmetic_dz_authorization_attachment_rel",
        column1="authorization_id",
        column2="attachment_id",
        string="Dossier Attachments",
    )
    note = fields.Text(string="Internal Note")

    _code_unique = models.Constraint(
        "UNIQUE(code, company_id)",
        "An authorisation dossier with this reference already exists.",
    )

    #: Field names of the sixteen dossier items, derived from the constants so
    #: that the model and the documentation cannot drift apart.
    _DOSSIER_FIELDS = tuple(
        f"doc_{suffix}" for suffix, _label in constants.DZ_DOSSIER_ITEMS
    )

    # ------------------------------------------------------------------
    # Compute
    # ------------------------------------------------------------------
    @api.depends("receipt_date")
    def _compute_decision_due_date(self):
        """Add the forty-five day notification period to the receipt date."""
        for dossier in self:
            if dossier.receipt_date:
                dossier.decision_due_date = dossier.receipt_date + timedelta(
                    days=constants.DZ_DECISION_DELAY_DAYS
                )
            else:
                dossier.decision_due_date = False

    @api.depends("notice_date")
    def _compute_notice_deadline(self):
        """Add the one month compliance period to the formal notice date."""
        for dossier in self:
            if dossier.notice_date:
                dossier.notice_deadline = dossier.notice_date + timedelta(
                    days=constants.DZ_COMPLIANCE_DELAY_DAYS
                )
            else:
                dossier.notice_deadline = False

    def _compute_decision_overdue(self):
        """Flag dossiers awaiting a decision past the forty-five day period."""
        today = fields.Date.context_today(self)
        for dossier in self:
            dossier.decision_overdue = bool(
                dossier.state == "receipt"
                and dossier.decision_due_date
                and dossier.decision_due_date < today
            )

    def _search_decision_overdue(self, operator, value):
        """Search helper for the non-stored ``decision_overdue`` field."""
        if operator not in ("=", "!="):
            raise UserError(
                self.env._("Only the = and != operators are supported here.")
            )
        today = fields.Date.context_today(self)
        overdue_domain = [
            ("state", "=", "receipt"),
            ("decision_due_date", "!=", False),
            ("decision_due_date", "<", today),
        ]
        looking_for_overdue = (operator == "=") == bool(value)
        if looking_for_overdue:
            return overdue_domain
        matching = self.search(overdue_domain)
        return [("id", "not in", matching.ids)]

    @api.depends(*_DOSSIER_FIELDS)
    def _compute_dossier_completeness(self):
        """Count the dossier items provided and flag a complete dossier."""
        total = len(self._DOSSIER_FIELDS)
        for dossier in self:
            provided = sum(1 for name in self._DOSSIER_FIELDS if dossier[name])
            dossier.dossier_item_count = provided
            dossier.dossier_complete = provided == total

    @api.depends("code", "name")
    def _compute_display_name(self):
        """Show the dossier reference with the product denomination."""
        for dossier in self:
            dossier_code = dossier.code or ""
            dossier.display_name = f"{dossier_code} - {dossier.name or ''}".strip(" -")

    # ------------------------------------------------------------------
    # Constraints
    # ------------------------------------------------------------------
    @api.constrains("submission_date", "receipt_date", "decision_date")
    def _check_chronology(self):
        """Keep the procedural dates in order."""
        for dossier in self:
            if (
                dossier.submission_date
                and dossier.receipt_date
                and dossier.receipt_date < dossier.submission_date
            ):
                raise ValidationError(
                    self.env._(
                        "Dossier %(code)s: the deposit receipt cannot predate "
                        "the submission.",
                        code=dossier.code,
                    )
                )
            if (
                dossier.receipt_date
                and dossier.decision_date
                and dossier.decision_date < dossier.receipt_date
            ):
                raise ValidationError(
                    self.env._(
                        "Dossier %(code)s: the decision cannot predate the "
                        "deposit receipt.",
                        code=dossier.code,
                    )
                )

    @api.constrains("state", "refusal_reason")
    def _check_refusal_reason(self):
        """A refusal must be reasoned."""
        for dossier in self:
            if dossier.state == "refused" and not (
                dossier.refusal_reason or ""
            ).strip():
                raise ValidationError(
                    self.env._(
                        "Dossier %(code)s is refused. The decision refusing a "
                        "prior authorisation is a reasoned decision and the "
                        "reason must be recorded.",
                        code=dossier.code,
                    )
                )

    # ------------------------------------------------------------------
    # ORM overrides
    # ------------------------------------------------------------------
    @api.model_create_multi
    def create(self, vals_list):
        """Assign the dossier reference from the sequence."""
        new_label = self.env._("New")
        for vals in vals_list:
            if vals.get("code", new_label) == new_label:
                company_id = vals.get("company_id") or self.env.company.id
                sequence = self.env["ir.sequence"].with_company(company_id)
                vals["code"] = (
                    sequence.next_by_code("ls.cosmetic.dz_authorization") or new_label
                )
        return super().create(vals_list)

    @api.ondelete(at_uninstall=False)
    def _ls_unlink_check_ls_cosmetic_dz_authorization(self):
        """Allow deletion only while the dossier is still a draft."""
        blocked = self.filtered(lambda record: record.state != "draft")
        if blocked:
            raise UserError(
                self.env._(
                    "Dossier %(code)s has been submitted and cannot be "
                    "deleted.",
                    code=blocked[0].code,
                )
            )

    def copy_data(self, default=None):
        """Reset the reference, workflow and procedural dates on duplication."""
        default = dict(default or {})
        vals_list = super().copy_data(default=default)
        for vals in vals_list:
            vals.setdefault("code", self.env._("New"))
            vals.setdefault("state", "draft")
            vals.setdefault("submission_date", False)
            vals.setdefault("receipt_date", False)
            vals.setdefault("decision_date", False)
        return vals_list

    # ------------------------------------------------------------------
    # Workflow
    # ------------------------------------------------------------------
    def action_submit(self):
        """Record the submission of a complete dossier."""
        for dossier in self:
            if dossier.state != "draft":
                raise UserError(
                    self.env._(
                        "Only a draft dossier can be submitted. %(code)s is "
                        "%(state)s.",
                        code=dossier.code,
                        state=dossier.state,
                    )
                )
            if not dossier.dossier_complete:
                missing = dossier._missing_dossier_items()
                raise UserError(
                    self.env._(
                        "Dossier %(code)s is incomplete. Missing items: "
                        "%(items)s.",
                        code=dossier.code,
                        items="; ".join(missing),
                    )
                )
        self.write(
            {
                "state": "submitted",
                "submission_date": fields.Date.context_today(self),
            }
        )
        return True

    def action_register_receipt(self):
        """Record the deposit receipt, which starts the forty-five day period."""
        for dossier in self:
            if dossier.state != "submitted":
                raise UserError(
                    self.env._(
                        "Only a submitted dossier can register a deposit "
                        "receipt. %(code)s is %(state)s.",
                        code=dossier.code,
                        state=dossier.state,
                    )
                )
            if not dossier.receipt_date:
                raise UserError(
                    self.env._(
                        "Dossier %(code)s has no deposit receipt date. The "
                        "forty-five day notification period runs from that "
                        "date.",
                        code=dossier.code,
                    )
                )
        self.write({"state": "receipt"})
        return True

    def action_grant(self):
        """Record the authorisation decision."""
        for dossier in self:
            if dossier.state != "receipt":
                raise UserError(
                    self.env._(
                        "Only a dossier with a registered deposit receipt can "
                        "be granted. %(code)s is %(state)s.",
                        code=dossier.code,
                        state=dossier.state,
                    )
                )
            if not dossier.authorization_reference:
                raise UserError(
                    self.env._(
                        "Dossier %(code)s has no authorisation reference.",
                        code=dossier.code,
                    )
                )
        self.write(
            {
                "state": "granted",
                "decision_date": fields.Date.context_today(self),
            }
        )
        return True

    def action_refuse(self):
        """Record a reasoned refusal."""
        for dossier in self:
            if dossier.state != "receipt":
                raise UserError(
                    self.env._(
                        "Only a dossier with a registered deposit receipt can "
                        "be refused. %(code)s is %(state)s.",
                        code=dossier.code,
                        state=dossier.state,
                    )
                )
            if not (dossier.refusal_reason or "").strip():
                raise UserError(
                    self.env._(
                        "Dossier %(code)s cannot be refused without recording "
                        "the reason for the decision.",
                        code=dossier.code,
                    )
                )
        self.write(
            {
                "state": "refused",
                "decision_date": fields.Date.context_today(self),
            }
        )
        return True

    def action_register_notice(self):
        """Record a formal notice served on a granted authorisation."""
        for dossier in self:
            if dossier.state != "granted":
                raise UserError(
                    self.env._(
                        "Only a granted authorisation can receive a formal "
                        "notice. %(code)s is %(state)s.",
                        code=dossier.code,
                        state=dossier.state,
                    )
                )
            if not dossier.notice_date:
                raise UserError(
                    self.env._(
                        "Dossier %(code)s has no formal notice date. The one "
                        "month compliance period runs from that date.",
                        code=dossier.code,
                    )
                )
            if not (dossier.notice_subject or "").strip():
                raise UserError(
                    self.env._(
                        "Dossier %(code)s: record what the formal notice "
                        "requires the operator to bring into conformity.",
                        code=dossier.code,
                    )
                )
        self.write({"state": "notice"})
        return True

    def action_resolve_notice(self):
        """Return an authorisation to the granted state after compliance."""
        for dossier in self:
            if dossier.state != "notice":
                raise UserError(
                    self.env._(
                        "Only a dossier under formal notice can be resolved. "
                        "%(code)s is %(state)s.",
                        code=dossier.code,
                        state=dossier.state,
                    )
                )
        self.write({"state": "granted"})
        return True

    def action_withdraw(self):
        """Record the withdrawal of an authorisation."""
        for dossier in self:
            if dossier.state not in ("granted", "notice"):
                raise UserError(
                    self.env._(
                        "Only a granted authorisation, or one under formal "
                        "notice, can be withdrawn. %(code)s is %(state)s.",
                        code=dossier.code,
                        state=dossier.state,
                    )
                )
        self.write(
            {
                "state": "withdrawn",
                "withdrawal_date": fields.Date.context_today(self),
            }
        )
        return True

    def action_reset_draft(self):
        """Return a submitted dossier to draft before a receipt is registered."""
        for dossier in self:
            if dossier.state != "submitted":
                raise UserError(
                    self.env._(
                        "Only a submitted dossier can be returned to draft. "
                        "%(code)s is %(state)s.",
                        code=dossier.code,
                        state=dossier.state,
                    )
                )
        self.write({"state": "draft", "submission_date": False})
        return True

    # ------------------------------------------------------------------
    # Business services
    # ------------------------------------------------------------------
    def _missing_dossier_items(self):
        """Return the labels of the dossier items that are not provided.

        :return: a list of item labels.
        """
        self.ensure_one()
        missing = []
        for suffix, label in constants.DZ_DOSSIER_ITEMS:
            if not self[f"doc_{suffix}"]:
                missing.append(label)
        return missing

    @api.model
    def _cron_monitor_deadlines(self):
        """Post a notice on dossiers past a procedural deadline.

        Two deadlines are monitored: the forty-five day notification period
        following the deposit receipt, and the one month compliance period
        following a formal notice.

        :return: the number of dossiers a notice was posted on.
        """
        today = fields.Date.context_today(self)
        overdue_decisions = self.search(
            [
                ("state", "=", "receipt"),
                ("decision_due_date", "!=", False),
                ("decision_due_date", "<", today),
            ]
        )
        for dossier in overdue_decisions:
            dossier.message_post(
                body=self.env._(
                    "The forty-five day period following the deposit receipt "
                    "ended on %(date)s and no decision has been recorded.",
                    date=dossier.decision_due_date,
                )
            )
        overdue_notices = self.search(
            [
                ("state", "=", "notice"),
                ("notice_deadline", "!=", False),
                ("notice_deadline", "<", today),
            ]
        )
        for dossier in overdue_notices:
            dossier.message_post(
                body=self.env._(
                    "The compliance period following the formal notice ended "
                    "on %(date)s. Failing compliance, the authorisation is "
                    "withdrawn.",
                    date=dossier.notice_deadline,
                )
            )
        return len(overdue_decisions) + len(overdue_notices)
