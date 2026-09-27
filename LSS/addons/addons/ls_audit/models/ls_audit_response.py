# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Executed checklist question.

A response is the assessment of one question during one audit.  The question
text is copied from the checklist template rather than referenced, so that a
later change to the template never alters the record of what was actually
asked and answered during a past audit.
"""

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


class LsAuditResponse(models.Model):
    """Assessment of a single question during an audit."""

    _name = "ls.audit.response"
    _description = "Audit Checklist Response"
    _order = "audit_id, sequence, id"

    audit_id = fields.Many2one(comodel_name="ls.audit.schedule", required=True,
                               ondelete="cascade",
                               index=True,
                               help="Audit during which this question was assessed.",)
    checklist_line_id = fields.Many2one(
        comodel_name="ls.audit.checklist.line",
        string="Source Question",
        ondelete="set null",
        help="Checklist template question this response originates from. "
             "Kept for traceability only: the question text below is the "
             "text that was actually used during the audit.",
    )
    sequence = fields.Integer(default=10,
                              help="Order of the question inside the audit.",)
    name = fields.Text(
        string="Question",
        required=True,
        help="Question as it was asked during the audit.",
    )
    reference_clause = fields.Char(
        string="Reference",
        help="Reference of the requirement being verified.",
    )
    guidance = fields.Text(
        string="Auditor Guidance",
        help="Guidance copied from the checklist template.",
    )
    is_mandatory = fields.Boolean(
        string="Mandatory",
        default=True,
        help="Mandatory questions must be assessed before the audit can be "
             "completed.",
    )
    result = fields.Selection(
        selection=[
            ("pending", "Pending"),
            ("conform", "Conform"),
            ("nonconform", "Non-conform"),
            ("observation", "Observation"),
            ("not_applicable", "Not Applicable"),
        ],
        default="pending",
        required=True,
        index=True,
        help="Outcome of the assessment. Non-conform and observation results "
             "require objective evidence to be recorded.",
    )
    evidence = fields.Text(
        string="Objective Evidence",
        help="Records, statements of fact or other information examined, "
             "which is verifiable.",
    )
    auditor_id = fields.Many2one(
        comodel_name="res.users",
        string="Assessed By",
        readonly=True,
        help="Auditor who recorded the assessment.",
    )
    assessment_date = fields.Datetime(readonly=True,
                                      help="Date and time at which the assessment was recorded.",)
    finding_id = fields.Many2one(comodel_name="ls.audit.finding", readonly=True,
                                 ondelete="set null",
                                 copy=False,
                                 help="Finding raised from this question, when applicable.",)
    company_id = fields.Many2one(comodel_name="res.company", related="audit_id.company_id",
                                 store=True,
                                 readonly=True,
                                 help="Company owning this response, inherited from the audit.",)

    @api.constrains("result", "evidence")
    def _check_evidence_recorded(self):
        """Require objective evidence for adverse results.

        :raise ValidationError: when a non-conform or observation result is
            recorded without evidence.
        """
        for response in self:
            if response.result in ("nonconform", "observation") and not (
                response.evidence and response.evidence.strip()
            ):
                raise ValidationError(
                    _(
                        "Objective evidence is required for the "
                        "non-conform or observation result recorded on "
                        "question '%(question)s'.",
                        question=(response.name or "")[:80],
                    )
                )

    def write(self, vals):
        """Record the assessor and lock responses of a finished audit.

        :param vals: values to write.
        :return: ``True``.
        :rtype: bool
        :raise UserError: when the parent audit no longer accepts changes.
        """
        editable_states = ("scheduled", "in_progress")
        technical_fields = {"finding_id"}
        if not set(vals) <= technical_fields:
            locked = self.filtered(
                lambda response: response.audit_id.state
                not in editable_states
            )
            if locked:
                raise UserError(
                    _(
                        "Checklist responses can only be edited while the "
                        "audit is scheduled or in progress. Affected "
                        "audit(s): %(refs)s.",
                        refs=", ".join(
                            set(locked.mapped("audit_id.reference"))
                        ),
                    )
                )
        if "result" in vals and vals.get("result") != "pending":
            vals = dict(
                vals,
                auditor_id=self.env.user.id,
                assessment_date=fields.Datetime.now(),
            )
        return super().write(vals)

    @api.ondelete(at_uninstall=False)
    def _ls_unlink_check_ls_audit_response(self):
        """Forbid deletion once the audit fieldwork has started.

        :return: ``True``.
        :rtype: bool
        :raise UserError: when the parent audit is no longer scheduled.
        """
        locked = self.filtered(
            lambda response: response.audit_id.state != "scheduled"
        )
        if locked:
            raise UserError(
                _(
                    "Checklist responses can only be removed while the audit "
                    "is still scheduled."
                )
            )

    def action_create_finding(self):
        """Open a pre-filled finding form for this question.

        :return: an act window action opening a new finding.
        :rtype: dict
        :raise UserError: when the question is not adverse or already linked
            to a finding.
        """
        self.ensure_one()
        if self.finding_id:
            raise UserError(
                _("A finding has already been raised for this question.")
            )
        if self.result not in ("nonconform", "observation"):
            raise UserError(
                _(
                    "A finding can only be raised from a non-conform or "
                    "observation result."
                )
            )
        return {
            "type": "ir.actions.act_window",
            "name": _("New Finding"),
            "res_model": "ls.audit.finding",
            "view_mode": "form",
            "target": "current",
            "context": {
                "default_audit_id": self.audit_id.id,
                "default_response_id": self.id,
                "default_name": (self.name or "")[:120],
                "default_description": self.name,
                "default_evidence": self.evidence,
                "default_reference_clause": self.reference_clause,
                "default_company_id": self.company_id.id,
            },
        }
