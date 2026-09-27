# Copyright 2026 Life Sciences Suite
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Wizard collecting the closure evidence of a deviation."""

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class LsDeviationCloseWizard(models.TransientModel):
    """Collect and commit the closure record of a deviation.

    21 CFR 211.192 requires a written record of the investigation including
    the conclusions and follow-up. This wizard makes both mandatory at the
    point of closure so that a deviation cannot be closed without them.
    """

    _name = "ls.deviation.close.wizard"
    _description = "Close Deviation Wizard"

    deviation_id = fields.Many2one(
        comodel_name="ls.deviation",
        required=True,
        ondelete="cascade",
    )
    conclusion = fields.Text(required=True)
    followup = fields.Text(
        string="Follow-up",
        required=True,
        help="Follow-up recorded with the conclusions. Where no follow-up is "
        "required, record that determination and its rationale.",
    )
    capa_required = fields.Boolean()
    capa_reference = fields.Char()
    capa_decision_rationale = fields.Text(required=True)
    qa_reviewer_id = fields.Many2one(
        comodel_name="res.users",
        string="QA Reviewer",
        required=True,
        default=lambda self: self.env.user,
    )

    @api.model
    def default_get(self, fields_list):
        """Pre-fill the wizard from the deviation being closed."""
        defaults = super().default_get(fields_list)
        deviation_id = defaults.get("deviation_id") or self.env.context.get(
            "default_deviation_id"
        )
        if not deviation_id:
            return defaults
        deviation = self.env["ls.deviation"].browse(deviation_id)
        defaults.setdefault("conclusion", deviation.conclusion or "")
        defaults.setdefault("followup", deviation.followup or "")
        defaults.setdefault("capa_required", deviation.capa_required)
        defaults.setdefault("capa_reference", deviation.capa_reference or "")
        defaults.setdefault(
            "capa_decision_rationale", deviation.capa_decision_rationale or ""
        )
        if deviation.qa_reviewer_id:
            defaults.setdefault("qa_reviewer_id", deviation.qa_reviewer_id.id)
        return defaults

    def action_confirm(self):
        """Write the closure evidence and move the deviation to ``closed``."""
        self.ensure_one()
        deviation = self.deviation_id
        if self.capa_required and not (self.capa_reference or "").strip():
            raise UserError(
                _(
                    "A CAPA reference is required because the closure records "
                    "that a CAPA is required."
                )
            )
        open_actions = deviation.immediate_action_ids.filtered(
            lambda action: action.state == "todo"
        )
        if open_actions:
            raise UserError(
                _(
                    "Deviation %(ref)s still has %(count)s open immediate "
                    "action(s) and cannot be closed.",
                    ref=deviation.name,
                    count=len(open_actions),
                )
            )
        draft_dispositions = deviation.disposition_ids.filtered(
            lambda disposition: disposition.state == "draft"
        )
        if draft_dispositions:
            raise UserError(
                _(
                    "Deviation %(ref)s still has %(count)s unapproved product "
                    "disposition(s) and cannot be closed.",
                    ref=deviation.name,
                    count=len(draft_dispositions),
                )
            )
        deviation.write(
            {
                "conclusion": self.conclusion,
                "followup": self.followup,
                "capa_required": self.capa_required,
                "capa_reference": self.capa_reference,
                "capa_decision_rationale": self.capa_decision_rationale,
                "qa_reviewer_id": self.qa_reviewer_id.id,
                "closed_by_id": self.env.user.id,
                "closure_date": fields.Datetime.now(),
            }
        )
        deviation._apply_transition("closed", _("Deviation closed by QA"))
        return {"type": "ir.actions.act_window_close"}
