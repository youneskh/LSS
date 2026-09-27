# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Supplier qualification dossier: the central record of the module."""
from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

from .ls_supplier_category import CRITICALITY_SELECTION

STATE_SELECTION = [
    ("draft", "Registered"),
    ("assessment", "Under Assessment"),
    ("audit", "Under Audit"),
    ("approval", "Pending Approval"),
    ("approved", "Approved"),
    ("conditional", "Conditionally Approved"),
    ("suspended", "Suspended"),
    ("expired", "Expired"),
    ("disqualified", "Disqualified"),
]

APPROVED_STATES = ("approved", "conditional")
EDITABLE_HEADER_STATES = ("draft", "assessment", "audit", "approval")


class LsSupplierQualification(models.Model):
    """Qualification dossier of one supplier for one company.

    The dossier aggregates the evidence produced by the qualification process
    (assessments, audits, qualified materials, performance evaluations,
    periodic reviews) and carries the approval status that other modules and
    the purchase flow can rely on.
    """

    _name = "ls.supplier.qualification"
    _description = "Life Sciences Supplier Qualification Dossier"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "expiry_date, name"
    _check_company_auto = True

    # ------------------------------------------------------------------
    # Identification
    # ------------------------------------------------------------------
    name = fields.Char(
        required=True,
        readonly=True,
        copy=False,
        default="/",
        index=True,
    )
    partner_id = fields.Many2one(
        comodel_name="res.partner",
        string="Supplier",
        required=True,
        index=True,
        tracking=True,
        ondelete="restrict",
        check_company=True,
        help="Contact record of the supplier. One active dossier is allowed "
             "per supplier and per company.",
    )
    category_id = fields.Many2one(
        comodel_name="ls.supplier.category",
        string="Supplier Category",
        required=True,
        tracking=True,
        ondelete="restrict",
        check_company=True,
    )
    criticality = fields.Selection(
        selection=CRITICALITY_SELECTION,
        required=True,
        tracking=True,
        compute="_compute_criticality",
        store=True,
        precompute=True,
        readonly=False,
        help="Defaults to the category criticality and can be raised or "
             "lowered on the dossier with a justification in the log.",
    )
    responsible_id = fields.Many2one(comodel_name="res.users", required=True,
                                     tracking=True,
                                     default=lambda self: self.env.user,
                                     domain=[("share", "=", False)],
                                     )
    company_id = fields.Many2one(
        comodel_name="res.company",
        required=True,
        index=True,
        default=lambda self: self.env.company,
    )
    active = fields.Boolean(default=True)
    color = fields.Integer()
    notes = fields.Html(sanitize=True)

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------
    state = fields.Selection(
        selection=STATE_SELECTION,
        required=True,
        default="draft",
        tracking=True,
        index=True,
        copy=False,
    )
    registration_date = fields.Date(
        required=True,
        default=fields.Date.context_today,
        tracking=True,
    )
    approval_date = fields.Date(readonly=True, copy=False, tracking=True)
    approved_by_id = fields.Many2one(comodel_name="res.users", readonly=True,
                                     copy=False,
                                     tracking=True,)
    # No static default: it would take precedence over the computation on
    # creation and ignore the interval of the category (the computation
    # falls back to 36 months without a category).
    requalification_interval_months = fields.Integer(
        required=True,
        compute="_compute_requalification_interval_months",
        store=True,
        precompute=True,
        readonly=False,
        tracking=True,
    )
    expiry_date = fields.Date(
        string="Approval Valid Until",
        readonly=True,
        copy=False,
        tracking=True,
        index=True,
    )
    approval_conditions = fields.Text(
        copy=False,
        help="Conditions attached to a conditional approval.",
    )
    suspension_reason = fields.Text(readonly=True, copy=False)
    disqualification_reason = fields.Text(readonly=True, copy=False)

    # ------------------------------------------------------------------
    # Evidence
    # ------------------------------------------------------------------
    assessment_ids = fields.One2many(
        comodel_name="ls.supplier.assessment",
        inverse_name="qualification_id",
        string="Assessments",
    )
    audit_ids = fields.One2many(
        comodel_name="ls.supplier.audit",
        inverse_name="qualification_id",
        string="Audits",
    )
    material_ids = fields.One2many(
        comodel_name="ls.supplier.material",
        inverse_name="qualification_id",
        string="Qualified Scope",
    )
    performance_ids = fields.One2many(
        comodel_name="ls.supplier.performance",
        inverse_name="qualification_id",
        string="Performance Evaluations",
    )
    review_ids = fields.One2many(
        comodel_name="ls.supplier.review",
        inverse_name="qualification_id",
        string="Periodic Reviews",
    )
    signature_ids = fields.One2many(
        comodel_name="ls.supplier.signature",
        inverse_name="qualification_id",
        string="Signature Log",
    )

    assessment_count = fields.Integer(compute="_compute_counts")
    audit_count = fields.Integer(compute="_compute_counts")
    material_count = fields.Integer(compute="_compute_counts")
    performance_count = fields.Integer(compute="_compute_counts")
    review_count = fields.Integer(compute="_compute_counts")
    signature_count = fields.Integer(compute="_compute_counts")

    # ------------------------------------------------------------------
    # Derived indicators
    # ------------------------------------------------------------------
    latest_assessment_id = fields.Many2one(
        comodel_name="ls.supplier.assessment",
        compute="_compute_latest_assessment",
        store=True,
    )
    latest_assessment_score = fields.Float(
        compute="_compute_latest_assessment",
        store=True,
        digits=(5, 2),
        string="Latest Assessment Score (%)",
    )
    latest_assessment_result = fields.Selection(
        selection=[
            ("pass", "Pass"),
            ("conditional", "Conditional"),
            ("fail", "Fail"),
        ],
        compute="_compute_latest_assessment",
        store=True,
    )
    latest_performance_rating = fields.Selection(
        selection=[
            ("a", "A"),
            ("b", "B"),
            ("c", "C"),
            ("d", "D"),
        ],
        compute="_compute_latest_performance",
        store=True,
    )
    latest_performance_score = fields.Float(
        compute="_compute_latest_performance",
        store=True,
        digits=(5, 2),
    )
    open_critical_finding_count = fields.Integer(
        compute="_compute_finding_counts",
        store=True,
    )
    open_major_finding_count = fields.Integer(
        compute="_compute_finding_counts",
        store=True,
    )
    risk_level = fields.Selection(
        selection=[
            ("low", "Low"),
            ("medium", "Medium"),
            ("high", "High"),
        ],
        compute="_compute_risk_level",
        store=True,
        help="Derived from the dossier criticality, the latest assessment "
             "result, the latest performance rating and the open critical or "
             "major audit findings. The computation rule is documented in "
             "doc/03_functional_specification.md.",
    )
    next_audit_date = fields.Date(
        compute="_compute_next_dates",
        store=True,
        index=True,
    )
    next_review_date = fields.Date(
        compute="_compute_next_dates",
        store=True,
        index=True,
    )
    days_to_expiry = fields.Integer(compute="_compute_days_to_expiry")
    expiry_status = fields.Selection(
        selection=[
            ("not_applicable", "Not Applicable"),
            ("valid", "Valid"),
            ("expiring", "Expiring Soon"),
            ("expired", "Expired"),
        ],
        compute="_compute_days_to_expiry",
        search="_search_expiry_status",
    )
    blocking_reasons = fields.Text(
        compute="_compute_blocking_reasons",
        help="Prerequisites that are not met yet for submitting the dossier "
             "to approval.",
    )
    is_ready_for_approval = fields.Boolean(
        compute="_compute_blocking_reasons",
    )

    _name_company_uniq = models.Constraint(
        "UNIQUE(name, company_id)",
        "The dossier reference must be unique per company.",
    )

    _requalification_interval_positive = models.Constraint(
        "CHECK(requalification_interval_months > 0)",
        "The requalification interval must be strictly positive.",
    )

    # ------------------------------------------------------------------
    # Compute methods
    # ------------------------------------------------------------------
    @api.depends("category_id")
    def _compute_criticality(self):
        """Inherit the category criticality while keeping manual overrides."""
        for record in self:
            if record.category_id:
                record.criticality = record.category_id.criticality
            elif not record.criticality:
                record.criticality = "major"

    @api.depends("category_id")
    def _compute_requalification_interval_months(self):
        """Inherit the category interval while keeping manual overrides."""
        for record in self:
            if record.category_id:
                record.requalification_interval_months = (
                    record.category_id.requalification_interval_months
                )
            elif not record.requalification_interval_months:
                record.requalification_interval_months = 36

    @api.depends(
        "assessment_ids",
        "audit_ids",
        "material_ids",
        "performance_ids",
        "review_ids",
        "signature_ids",
    )
    def _compute_counts(self):
        """Fill the smart-button counters."""
        for record in self:
            record.assessment_count = len(record.assessment_ids)
            record.audit_count = len(record.audit_ids)
            record.material_count = len(record.material_ids)
            record.performance_count = len(record.performance_ids)
            record.review_count = len(record.review_ids)
            record.signature_count = len(record.signature_ids)

    @api.depends(
        "assessment_ids.state",
        "assessment_ids.date",
        "assessment_ids.score_percent",
        "assessment_ids.result",
    )
    def _compute_latest_assessment(self):
        """Expose the most recent concluded assessment on the dossier."""
        for record in self:
            concluded = record.assessment_ids.filtered(
                lambda assessment: assessment.state in ("done", "reviewed")
            ).sorted(key=lambda assessment: (assessment.date, assessment.id))
            latest = concluded[-1] if concluded else False
            record.latest_assessment_id = latest.id if latest else False
            record.latest_assessment_score = latest.score_percent if latest else 0.0
            record.latest_assessment_result = latest.result if latest else False

    @api.depends(
        "performance_ids.state",
        "performance_ids.period_end",
        "performance_ids.overall_score",
        "performance_ids.rating",
    )
    def _compute_latest_performance(self):
        """Expose the most recent confirmed performance evaluation."""
        for record in self:
            confirmed = record.performance_ids.filtered(
                lambda evaluation: evaluation.state == "confirmed"
            ).sorted(key=lambda evaluation: (evaluation.period_end, evaluation.id))
            latest = confirmed[-1] if confirmed else False
            record.latest_performance_rating = latest.rating if latest else False
            record.latest_performance_score = latest.overall_score if latest else 0.0

    @api.depends("audit_ids.finding_ids.severity", "audit_ids.finding_ids.state")
    def _compute_finding_counts(self):
        """Count the audit findings that are not closed or cancelled."""
        for record in self:
            open_findings = record.audit_ids.finding_ids.filtered(
                lambda finding: finding.state not in ("closed", "cancelled")
            )
            record.open_critical_finding_count = len(
                open_findings.filtered(lambda f: f.severity == "critical")
            )
            record.open_major_finding_count = len(
                open_findings.filtered(lambda f: f.severity == "major")
            )

    @api.depends(
        "criticality",
        "latest_assessment_result",
        "latest_performance_rating",
        "open_critical_finding_count",
        "open_major_finding_count",
    )
    def _compute_risk_level(self):
        """Derive a three-level risk indicator from the dossier evidence.

        The rule is deterministic and fully described in the functional
        specification. It is an internal prioritisation aid defined by this
        module; it is not derived from any regulatory text.
        """
        for record in self:
            score = 0
            if record.criticality == "critical":
                score += 2
            elif record.criticality == "major":
                score += 1
            if record.latest_assessment_result == "fail":
                score += 3
            elif record.latest_assessment_result == "conditional":
                score += 1
            if record.latest_performance_rating == "d":
                score += 3
            elif record.latest_performance_rating == "c":
                score += 1
            score += 3 * record.open_critical_finding_count
            score += record.open_major_finding_count
            if score >= 4:
                record.risk_level = "high"
            elif score >= 2:
                record.risk_level = "medium"
            else:
                record.risk_level = "low"

    @api.depends(
        "approval_date",
        "state",
        "category_id.requires_periodic_audit",
        "category_id.audit_interval_months",
        "category_id.review_interval_months",
        "audit_ids.state",
        "audit_ids.date_stop",
        "review_ids.state",
        "review_ids.review_date",
    )
    def _compute_next_dates(self):
        """Compute the next planned audit and the next periodic review."""
        for record in self:
            record.next_audit_date = False
            record.next_review_date = False
            if record.state not in APPROVED_STATES:
                continue
            category = record.category_id
            if category.requires_periodic_audit and category.audit_interval_months:
                closed_audits = record.audit_ids.filtered(
                    lambda audit: audit.state == "closed" and audit.date_stop
                ).sorted(key=lambda audit: audit.date_stop)
                anchor = (
                    closed_audits[-1].date_stop
                    if closed_audits
                    else record.approval_date
                )
                if anchor:
                    record.next_audit_date = anchor + relativedelta(
                        months=category.audit_interval_months
                    )
            if category.review_interval_months:
                done_reviews = record.review_ids.filtered(
                    lambda review: review.state == "done" and review.review_date
                ).sorted(key=lambda review: review.review_date)
                anchor = (
                    done_reviews[-1].review_date
                    if done_reviews
                    else record.approval_date
                )
                if anchor:
                    record.next_review_date = anchor + relativedelta(
                        months=category.review_interval_months
                    )

    @api.depends("expiry_date", "state")
    def _compute_days_to_expiry(self):
        """Compute the remaining validity in days and a status label."""
        today = fields.Date.context_today(self)
        for record in self:
            if record.state not in APPROVED_STATES or not record.expiry_date:
                record.days_to_expiry = 0
                record.expiry_status = "not_applicable"
                continue
            delta = (record.expiry_date - today).days
            record.days_to_expiry = delta
            reminder = record.company_id.ls_expiry_reminder_days
            if delta < 0:
                record.expiry_status = "expired"
            elif delta <= reminder:
                record.expiry_status = "expiring"
            else:
                record.expiry_status = "valid"

    def _search_expiry_status(self, operator, value):
        """Allow filtering on the non-stored ``expiry_status`` field.

        The status depends on the current date and on a per-company
        reminder window, so it cannot be expressed as a stored column or a
        plain SQL domain. It is instead resolved by evaluating the compute
        in Python over the candidate records.

        :param str operator: one of ``=``, ``!=``, ``in``, ``not in``.
        :param value: a single status or a list/tuple of statuses.
        :return: a domain equivalent to the requested filter.
        :rtype: list
        """
        if operator in ("=", "in"):
            wanted = {value} if isinstance(value, str) else set(value)
            negate = False
        elif operator in ("!=", "not in"):
            wanted = {value} if isinstance(value, str) else set(value)
            negate = True
        else:
            raise UserError(
                _("Unsupported operator for a search on expiry status.")
            )
        matching_ids = [
            record.id
            for record in self.search([])
            if (record.expiry_status in wanted) != negate
        ]
        return [("id", "in", matching_ids)]

    @api.depends(
        "state",
        "category_id.requires_assessment",
        "category_id.requires_initial_audit",
        "assessment_ids.state",
        "assessment_ids.result",
        "audit_ids.state",
        "audit_ids.outcome",
        "open_critical_finding_count",
        "material_ids.state",
    )
    def _compute_blocking_reasons(self):
        """List the unmet prerequisites for submitting to approval."""
        for record in self:
            reasons = record._get_blocking_reasons()
            record.blocking_reasons = "\n".join(reasons)
            record.is_ready_for_approval = not reasons

    def _get_blocking_reasons(self):
        """Return the list of unmet prerequisites as translated strings.

        :return: list of human-readable reasons; empty when the dossier can
            be submitted for approval.
        :rtype: list
        """
        self.ensure_one()
        reasons = []
        category = self.category_id
        if category.requires_assessment:
            valid_assessments = self.assessment_ids.filtered(
                lambda assessment: assessment.state in ("done", "reviewed")
                and assessment.result in ("pass", "conditional")
            )
            if not valid_assessments:
                reasons.append(_(
                    "No completed assessment with a Pass or Conditional "
                    "result is attached to the dossier."
                ))
        if category.requires_initial_audit:
            closed_audits = self.audit_ids.filtered(
                lambda audit: audit.state == "closed"
                and audit.outcome in ("acceptable", "acceptable_with_actions")
            )
            if not closed_audits:
                reasons.append(_(
                    "No closed audit with an acceptable outcome is attached "
                    "to the dossier."
                ))
        if self.open_critical_finding_count:
            reasons.append(_(
                "%s critical audit finding(s) are still open.",
                self.open_critical_finding_count,
            ))
        if not self.material_ids.filtered(
            lambda material: material.state == "qualified"
        ):
            reasons.append(_(
                "No qualified material or service defines the approval scope."
            ))
        return reasons

    # ------------------------------------------------------------------
    # Constraints
    # ------------------------------------------------------------------
    @api.constrains("partner_id", "company_id", "state", "active")
    def _check_unique_active_dossier(self):
        """Allow at most one live dossier per supplier and per company."""
        for record in self:
            if not record.active or record.state == "disqualified":
                continue
            duplicate = self.search_count([
                ("id", "!=", record.id),
                ("partner_id", "=", record.partner_id.id),
                ("company_id", "=", record.company_id.id),
                ("state", "!=", "disqualified"),
                ("active", "=", True),
            ])
            if duplicate:
                raise ValidationError(
                    _("Supplier '%s' already has an active qualification "
                      "dossier in company '%s'. Requalify the existing "
                      "dossier instead of creating a second one.",
                      record.partner_id.display_name,
                      record.company_id.display_name)
                )

    @api.constrains("approval_date", "expiry_date")
    def _check_validity_dates(self):
        """The expiry date must be strictly after the approval date."""
        for record in self:
            if (
                record.approval_date
                and record.expiry_date
                and record.expiry_date <= record.approval_date
            ):
                raise ValidationError(
                    _("Dossier %s: the approval expiry date must be after the "
                      "approval date.", record.name)
                )

    @api.constrains("state", "approval_date", "approved_by_id", "expiry_date")
    def _check_approval_completeness(self):
        """An approved dossier must carry a full approval record."""
        for record in self:
            if record.state not in APPROVED_STATES:
                continue
            missing = []
            if not record.approval_date:
                missing.append(_("approval date"))
            if not record.approved_by_id:
                missing.append(_("approver"))
            if not record.expiry_date:
                missing.append(_("validity end date"))
            if missing:
                raise ValidationError(
                    _("Dossier %s is approved but the following information "
                      "is missing: %s.", record.name, ", ".join(missing))
                )

    @api.constrains("state", "approval_conditions")
    def _check_conditional_approval(self):
        """A conditional approval must state its conditions."""
        for record in self:
            if record.state == "conditional" and not (
                record.approval_conditions or ""
            ).strip():
                raise ValidationError(
                    _("Dossier %s is conditionally approved: the conditions "
                      "must be documented.", record.name)
                )

    # ------------------------------------------------------------------
    # ORM overrides
    # ------------------------------------------------------------------
    @api.model_create_multi
    def create(self, vals_list):
        """Assign the dossier reference from the company sequence."""
        for vals in vals_list:
            if vals.get("name", "/") == "/":
                company_id = vals.get("company_id") or self.env.company.id
                vals["name"] = self.env["ir.sequence"].with_company(
                    company_id
                ).next_by_code("ls.supplier.qualification") or "/"
        return super().create(vals_list)

    def write(self, vals):
        """Protect identification fields once the dossier has left draft."""
        protected = {"partner_id", "category_id"}
        if protected & set(vals):
            for record in self:
                if record.state not in ("draft", "assessment"):
                    raise UserError(
                        _("The supplier and the category of dossier %s can no "
                          "longer be changed once the dossier has reached the "
                          "'%s' status. Create a new dossier or reset the "
                          "current one to draft.",
                          record.name,
                          dict(STATE_SELECTION).get(record.state))
                    )
        return super().write(vals)

    def copy(self, default=None):
        """Duplicate a dossier as a fresh draft without approval history."""
        self.ensure_one()
        default = dict(default or {})
        default.update({
            "name": "/",
            "state": "draft",
            "approval_date": False,
            "approved_by_id": False,
            "expiry_date": False,
            "approval_conditions": False,
            "suspension_reason": False,
            "disqualification_reason": False,
        })
        return super().copy(default)

    @api.ondelete(at_uninstall=False)
    def _ls_unlink_check_ls_supplier_qualification(self):
        """Only draft dossiers may be deleted, to preserve the audit trail."""
        for record in self:
            if record.state != "draft":
                raise UserError(
                    _("Dossier %s cannot be deleted because it has reached "
                      "the '%s' status. Archive it instead.",
                      record.name,
                      dict(STATE_SELECTION).get(record.state))
                )

    # ------------------------------------------------------------------
    # Workflow
    # ------------------------------------------------------------------
    def action_start_assessment(self):
        """Move a registered dossier to the assessment stage."""
        for record in self:
            if record.state != "draft":
                raise UserError(
                    _("Only a registered dossier can be moved to assessment "
                      "(dossier %s).", record.name)
                )
            record.state = "assessment"
            record.message_post(body=_("Assessment stage started."))
        return True

    def action_start_audit(self):
        """Move a dossier under assessment to the audit stage."""
        for record in self:
            if record.state not in ("assessment", "approval"):
                raise UserError(
                    _("Only a dossier under assessment or pending approval "
                      "can be moved to audit (dossier %s).", record.name)
                )
            record.state = "audit"
            record.message_post(body=_("Audit stage started."))
        return True

    def action_submit_for_approval(self):
        """Submit the dossier to the approval stage after prerequisite check."""
        for record in self:
            if record.state not in ("assessment", "audit"):
                raise UserError(
                    _("Only a dossier under assessment or under audit can be "
                      "submitted for approval (dossier %s).", record.name)
                )
            reasons = record._get_blocking_reasons()
            if reasons:
                raise UserError(
                    _("Dossier %s cannot be submitted for approval:\n- %s",
                      record.name, "\n- ".join(reasons))
                )
            record.state = "approval"
            record.message_post(body=_("Dossier submitted for approval."))
            record.activity_schedule(
                "mail.mail_activity_data_todo",
                summary=_("Approve supplier qualification %s", record.name),
                user_id=record.responsible_id.id,
            )
        return True

    def action_open_approve_wizard(self):
        """Open the approval wizard for the selected dossiers."""
        self.ensure_one()
        if self.state != "approval":
            raise UserError(
                _("Only a dossier pending approval can be approved "
                  "(dossier %s).", self.name)
            )
        return {
            "type": "ir.actions.act_window",
            "name": _("Approve Supplier Qualification"),
            "res_model": "ls.supplier.approve.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {"default_qualification_id": self.id},
        }

    def action_open_status_wizard(self):
        """Open the status-change wizard (suspend, reinstate, disqualify)."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Change Qualification Status"),
            "res_model": "ls.supplier.status.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {"default_qualification_id": self.id},
        }

    def action_requalify(self):
        """Reopen an expired or suspended dossier for requalification."""
        for record in self:
            if record.state not in ("expired", "suspended"):
                raise UserError(
                    _("Only an expired or suspended dossier can be sent to "
                      "requalification (dossier %s).", record.name)
                )
            record.write({
                "state": "assessment",
                "approval_date": False,
                "approved_by_id": False,
                "expiry_date": False,
                "approval_conditions": False,
            })
            record.message_post(body=_("Requalification started."))
        return True

    def action_reset_to_draft(self):
        """Return a non-approved dossier to the registered status."""
        for record in self:
            if record.state in APPROVED_STATES + ("disqualified",):
                raise UserError(
                    _("An approved or disqualified dossier cannot be reset to "
                      "draft (dossier %s).", record.name)
                )
            record.state = "draft"
            record.message_post(body=_("Dossier reset to registered status."))
        return True

    def _apply_approval(self, decision, conditions, expiry_date, reason, login):
        """Write the approval decision and append the signature entry.

        :param str decision: ``approved`` or ``conditional``.
        :param str conditions: conditions text for a conditional approval.
        :param expiry_date: end of validity of the approval.
        :param str reason: justification recorded with the signature.
        :param str login: login typed by the approver.
        """
        self.ensure_one()
        self._check_segregation_of_duties(self.env.user)
        self.write({
            "state": decision,
            "approval_date": fields.Date.context_today(self),
            "approved_by_id": self.env.user.id,
            "expiry_date": expiry_date,
            "approval_conditions": conditions or False,
        })
        self.env["ls.supplier.signature"].sign(
            record=self,
            meaning=(
                "approved" if decision == "approved"
                else "conditionally_approved"
            ),
            reason=reason,
            login=login,
            payload={
                "state": decision,
                "approval_date": self.approval_date,
                "expiry_date": self.expiry_date,
                "criticality": self.criticality,
                "latest_assessment_score": self.latest_assessment_score,
                "qualified_material_ids": self.material_ids.filtered(
                    lambda material: material.state == "qualified"
                ).ids,
            },
        )
        self.message_post(body=_(
            "Qualification %(decision)s until %(date)s.",
            decision=dict(STATE_SELECTION).get(decision),
            date=expiry_date,
        ))
        template = self.env.ref(
            "ls_supplier_qualification.mail_template_qualification_approved",
            raise_if_not_found=False,
        )
        if template:
            template.send_mail(self.id, force_send=False)

    def _check_segregation_of_duties(self, user):
        """Refuse an approval signed by an assessor or lead auditor.

        The check is active when the company flag
        ``ls_enforce_sod`` is set. It compares the approver with the assessors
        of the concluded assessments and the lead auditors of the closed
        audits of the dossier.

        :param user: user performing the approval.
        :raise UserError: when the same user would both produce and approve
            the evidence.
        """
        self.ensure_one()
        if not self.company_id.ls_enforce_sod:
            return
        assessors = self.assessment_ids.filtered(
            lambda assessment: assessment.state in ("done", "reviewed")
        ).mapped("assessor_id")
        lead_auditors = self.audit_ids.filtered(
            lambda audit: audit.state == "closed"
        ).mapped("lead_auditor_id")
        if user in assessors or user in lead_auditors:
            raise UserError(
                _("Segregation of duties: %s produced assessment or audit "
                  "evidence for dossier %s and therefore cannot approve it. "
                  "The rule can be disabled per company in the Supplier "
                  "Qualification settings.",
                  user.display_name, self.name)
            )

    # ------------------------------------------------------------------
    # Smart buttons
    # ------------------------------------------------------------------
    def _action_open_related(self, xml_id):
        """Return an act_window on a related one2many of the dossier."""
        self.ensure_one()
        action = self.env["ir.actions.act_window"]._for_xml_id(xml_id)
        action["domain"] = [("qualification_id", "=", self.id)]
        action["context"] = {"default_qualification_id": self.id}
        return action

    def action_view_assessments(self):
        """Open the assessments of the dossier."""
        return self._action_open_related(
            "ls_supplier_qualification.action_ls_supplier_assessment"
        )

    def action_view_audits(self):
        """Open the audits of the dossier."""
        return self._action_open_related(
            "ls_supplier_qualification.action_ls_supplier_audit"
        )

    def action_view_materials(self):
        """Open the qualified scope of the dossier."""
        return self._action_open_related(
            "ls_supplier_qualification.action_ls_supplier_material"
        )

    def action_view_performances(self):
        """Open the performance evaluations of the dossier."""
        return self._action_open_related(
            "ls_supplier_qualification.action_ls_supplier_performance"
        )

    def action_view_reviews(self):
        """Open the periodic reviews of the dossier."""
        return self._action_open_related(
            "ls_supplier_qualification.action_ls_supplier_review"
        )

    def action_view_signatures(self):
        """Open the signature log entries of the dossier."""
        return self._action_open_related(
            "ls_supplier_qualification.action_ls_supplier_signature"
        )

    # ------------------------------------------------------------------
    # Scheduled actions
    # ------------------------------------------------------------------
    @api.model
    def _cron_check_expiry(self):
        """Expire elapsed approvals and warn about approaching expiries.

        :return: number of dossiers moved to the expired status.
        :rtype: int
        """
        today = fields.Date.context_today(self)
        expired = self.search([
            ("state", "in", list(APPROVED_STATES)),
            ("expiry_date", "<", today),
        ])
        for record in expired:
            record.state = "expired"
            record.message_post(body=_(
                "Approval validity elapsed on %s: the dossier is now "
                "expired.", record.expiry_date
            ))
            record.activity_schedule(
                "mail.mail_activity_data_todo",
                summary=_("Requalify supplier %s", record.partner_id.display_name),
                user_id=record.responsible_id.id,
            )
        template = self.env.ref(
            "ls_supplier_qualification.mail_template_qualification_expiring",
            raise_if_not_found=False,
        )
        for company in self.env["res.company"].search([]):
            horizon = today + relativedelta(
                days=company.ls_expiry_reminder_days
            )
            expiring = self.search([
                ("company_id", "=", company.id),
                ("state", "in", list(APPROVED_STATES)),
                ("expiry_date", ">=", today),
                ("expiry_date", "<=", horizon),
            ])
            for record in expiring:
                if record.activity_ids.filtered(
                    lambda activity: activity.summary == _(
                        "Plan requalification of supplier %s",
                        record.partner_id.display_name,
                    )
                ):
                    continue
                record.activity_schedule(
                    "mail.mail_activity_data_todo",
                    date_deadline=record.expiry_date,
                    summary=_(
                        "Plan requalification of supplier %s",
                        record.partner_id.display_name,
                    ),
                    user_id=record.responsible_id.id,
                )
                if template:
                    template.send_mail(record.id, force_send=False)
        return len(expired)

    @api.model
    def _cron_check_due_dates(self):
        """Create activities for audits and reviews that fall due.

        :return: number of activities created.
        :rtype: int
        """
        today = fields.Date.context_today(self)
        created = 0
        for company in self.env["res.company"].search([]):
            horizon = today + relativedelta(
                days=company.ls_expiry_reminder_days
            )
            audits_due = self.search([
                ("company_id", "=", company.id),
                ("state", "in", list(APPROVED_STATES)),
                ("next_audit_date", "!=", False),
                ("next_audit_date", "<=", horizon),
            ])
            for record in audits_due:
                summary = _(
                    "Plan periodic audit of supplier %s",
                    record.partner_id.display_name,
                )
                if record._has_pending_activity(summary):
                    continue
                record.activity_schedule(
                    "mail.mail_activity_data_todo",
                    date_deadline=record.next_audit_date,
                    summary=summary,
                    user_id=record.responsible_id.id,
                )
                created += 1
            reviews_due = self.search([
                ("company_id", "=", company.id),
                ("state", "in", list(APPROVED_STATES)),
                ("next_review_date", "!=", False),
                ("next_review_date", "<=", horizon),
            ])
            for record in reviews_due:
                summary = _(
                    "Perform periodic review of supplier %s",
                    record.partner_id.display_name,
                )
                if record._has_pending_activity(summary):
                    continue
                record.activity_schedule(
                    "mail.mail_activity_data_todo",
                    date_deadline=record.next_review_date,
                    summary=summary,
                    user_id=record.responsible_id.id,
                )
                created += 1
        return created

    def _has_pending_activity(self, summary):
        """Return True when an open activity already carries this summary."""
        self.ensure_one()
        return bool(self.activity_ids.filtered(
            lambda activity: activity.summary == summary
        ))

    # ------------------------------------------------------------------
    # Reporting helpers
    # ------------------------------------------------------------------
    def _get_report_base_filename(self):
        """Return the file name proposed when printing the dossier."""
        self.ensure_one()
        return "%s - %s" % (self.name, self.partner_id.display_name)
