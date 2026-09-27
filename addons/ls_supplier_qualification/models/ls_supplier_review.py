# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Periodic review of a qualified supplier and its decision."""
from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

REVIEW_TYPE_SELECTION = [
    ("periodic", "Periodic Review"),
    ("event_driven", "Event-Driven Review"),
]

REVIEW_STATE_SELECTION = [
    ("draft", "Draft"),
    ("done", "Completed"),
    ("cancelled", "Cancelled"),
]

REVIEW_DECISION_SELECTION = [
    ("maintain", "Maintain Approval"),
    ("maintain_conditional", "Maintain with Conditions"),
    ("requalify", "Requalification Required"),
    ("suspend", "Suspend"),
    ("disqualify", "Disqualify"),
]


class LsSupplierReview(models.Model):
    """A periodic review that consolidates the evidence and takes a decision.

    Completing a review applies its decision to the dossier: it can extend the
    validity, add conditions, send the dossier back to requalification,
    suspend it or disqualify it.
    """

    _name = "ls.supplier.review"
    _description = "Life Sciences Supplier Periodic Review"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "review_date desc, id desc"
    _check_company_auto = True

    name = fields.Char(
        required=True,
        readonly=True,
        copy=False,
        default="/",
        index=True,
    )
    qualification_id = fields.Many2one(
        comodel_name="ls.supplier.qualification",
        required=True,
        ondelete="cascade",
        index=True,
        tracking=True,
    )
    partner_id = fields.Many2one(
        related="qualification_id.partner_id",
        store=True,
        index=True,
    )
    company_id = fields.Many2one(
        related="qualification_id.company_id",
        store=True,
        index=True,
    )
    review_type = fields.Selection(
        selection=REVIEW_TYPE_SELECTION,
        required=True,
        default="periodic",
        tracking=True,
    )
    review_date = fields.Date(
        required=True,
        default=fields.Date.context_today,
        tracking=True,
        index=True,
    )
    reviewer_id = fields.Many2one(
        comodel_name="res.users",
        required=True,
        default=lambda self: self.env.user,
        tracking=True,
        domain=[("share", "=", False)],
    )
    period_start = fields.Date(required=True)
    period_end = fields.Date(required=True)
    assessment_ids = fields.Many2many(
        comodel_name="ls.supplier.assessment",
        relation="ls_supplier_review_assessment_rel",
        column1="review_id",
        column2="assessment_id",
        string="Assessments Reviewed",
        check_company=True,
    )
    audit_ids = fields.Many2many(
        comodel_name="ls.supplier.audit",
        relation="ls_supplier_review_audit_rel",
        column1="review_id",
        column2="audit_id",
        string="Audits Reviewed",
        check_company=True,
    )
    performance_ids = fields.Many2many(
        comodel_name="ls.supplier.performance",
        relation="ls_supplier_review_performance_rel",
        column1="review_id",
        column2="performance_id",
        string="Performance Evaluations Reviewed",
        check_company=True,
    )
    summary = fields.Text(required=True)
    decision = fields.Selection(
        selection=REVIEW_DECISION_SELECTION,
        required=True,
        default="maintain",
        tracking=True,
    )
    decision_justification = fields.Text()
    new_expiry_date = fields.Date(
        string="New Validity End",
        help="Applied to the dossier when the decision maintains the "
             "approval. Left empty, the interval of the dossier is used.",
    )
    new_conditions = fields.Text(
        help="Conditions written on the dossier when the decision maintains "
             "the approval with conditions.",
    )
    state = fields.Selection(
        selection=REVIEW_STATE_SELECTION,
        required=True,
        default="draft",
        tracking=True,
        index=True,
        copy=False,
    )

    _name_company_uniq = models.Constraint(
        "UNIQUE(name, company_id)",
        "The review reference must be unique per company.",
    )

    @api.constrains("period_start", "period_end")
    def _check_period(self):
        """The reviewed period must be a strictly positive interval."""
        for record in self:
            if record.period_end <= record.period_start:
                raise ValidationError(
                    _("Review %s: the period end must be after the period "
                      "start.", record.name)
                )

    @api.constrains("decision", "new_conditions", "decision_justification", "state")
    def _check_decision_documentation(self):
        """Adverse or conditional decisions must be justified in writing.

        ``state`` is a trigger: the rule applies when the review is
        completed, which is a change of state only.
        """
        for record in self:
            if record.state != "done":
                continue
            if record.decision == "maintain_conditional" and not (
                record.new_conditions or ""
            ).strip():
                raise ValidationError(
                    _("Review %s maintains the approval with conditions: the "
                      "conditions must be documented.", record.name)
                )
            if record.decision in (
                "requalify", "suspend", "disqualify"
            ) and not (record.decision_justification or "").strip():
                raise ValidationError(
                    _("Review %s: an adverse decision must be justified.",
                      record.name)
                )

    @api.model_create_multi
    def create(self, vals_list):
        """Assign the review reference from the company sequence."""
        for vals in vals_list:
            if vals.get("name", "/") == "/":
                qualification = self.env["ls.supplier.qualification"].browse(
                    vals.get("qualification_id")
                )
                company_id = qualification.company_id.id or self.env.company.id
                vals["name"] = self.env["ir.sequence"].with_company(
                    company_id
                ).next_by_code("ls.supplier.review") or "/"
        return super().create(vals_list)

    @api.ondelete(at_uninstall=False)
    def _ls_unlink_check_ls_supplier_review(self):
        """Only draft or cancelled reviews may be deleted."""
        for record in self:
            if record.state == "done":
                raise UserError(
                    _("Completed review %s cannot be deleted.", record.name)
                )

    def action_collect_evidence(self):
        """Attach the dossier records that fall inside the reviewed period."""
        for record in self:
            if record.state != "draft":
                raise UserError(
                    _("Evidence can only be collected on a draft review "
                      "(review %s).", record.name)
                )
            qualification = record.qualification_id
            record.assessment_ids = [fields.Command.set(
                qualification.assessment_ids.filtered(
                    lambda assessment: assessment.state in ("done", "reviewed")
                    and record.period_start <= assessment.date <= record.period_end
                ).ids
            )]
            record.audit_ids = [fields.Command.set(
                qualification.audit_ids.filtered(
                    lambda audit: audit.state == "closed"
                    and audit.date_stop
                    and record.period_start <= audit.date_stop <= record.period_end
                ).ids
            )]
            record.performance_ids = [fields.Command.set(
                qualification.performance_ids.filtered(
                    lambda evaluation: evaluation.state == "confirmed"
                    and evaluation.period_end >= record.period_start
                    and evaluation.period_start <= record.period_end
                ).ids
            )]
            record.message_post(body=_(
                "Evidence collected: %s assessment(s), %s audit(s), "
                "%s performance evaluation(s).",
                len(record.assessment_ids),
                len(record.audit_ids),
                len(record.performance_ids),
            ))
        return True

    def action_done(self):
        """Complete the review and apply its decision to the dossier."""
        for record in self:
            if record.state != "draft":
                raise UserError(
                    _("Only a draft review can be completed (review %s).",
                      record.name)
                )
            record.state = "done"
            record._apply_decision()
            record.message_post(body=_(
                "Review completed. Decision: %s.",
                dict(REVIEW_DECISION_SELECTION).get(record.decision, ""),
            ))
            self.env["ls.supplier.signature"].sign(
                record=record,
                meaning="reviewed",
                reason=record.decision_justification or record.summary,
                payload={
                    "decision": record.decision,
                    "new_expiry_date": record.new_expiry_date,
                    "assessment_ids": record.assessment_ids.ids,
                    "audit_ids": record.audit_ids.ids,
                    "performance_ids": record.performance_ids.ids,
                },
            )
        return True

    def _apply_decision(self):
        """Write the review decision onto the qualification dossier."""
        self.ensure_one()
        qualification = self.qualification_id
        if self.decision in ("maintain", "maintain_conditional"):
            expiry = self.new_expiry_date or (
                self.review_date
                + relativedelta(
                    months=qualification.requalification_interval_months
                )
            )
            values = {
                "expiry_date": expiry,
                "state": (
                    "approved" if self.decision == "maintain"
                    else "conditional"
                ),
            }
            if self.decision == "maintain_conditional":
                values["approval_conditions"] = self.new_conditions
            else:
                values["approval_conditions"] = False
            qualification.write(values)
        elif self.decision == "requalify":
            qualification.write({
                "state": "assessment",
                "approval_date": False,
                "approved_by_id": False,
                "expiry_date": False,
                "approval_conditions": False,
            })
        elif self.decision == "suspend":
            qualification.write({
                "state": "suspended",
                "suspension_reason": self.decision_justification,
            })
        elif self.decision == "disqualify":
            qualification.write({
                "state": "disqualified",
                "disqualification_reason": self.decision_justification,
            })
        qualification.message_post(body=_(
            "Decision of periodic review %s applied: %s.",
            self.name,
            dict(REVIEW_DECISION_SELECTION).get(self.decision, ""),
        ))

    def action_cancel(self):
        """Cancel a draft review."""
        for record in self:
            if record.state == "done":
                raise UserError(
                    _("A completed review cannot be cancelled (review %s).",
                      record.name)
                )
            record.state = "cancelled"
            record.message_post(body=_("Review cancelled."))
        return True
