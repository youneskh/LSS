# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Finding response wizard.

Collects the auditee response to a finding in a single controlled step so
that the root cause, the correction and the corrective action are recorded
together with the identity of the responder and the date of the response.
"""

from odoo import _, fields, models
from odoo.exceptions import UserError


class LsAuditFindingResponse(models.TransientModel):
    """Wizard collecting the auditee response to a finding."""

    _name = "ls.audit.finding.response"
    _description = "Audit Finding Response"

    finding_id = fields.Many2one(comodel_name="ls.audit.finding", required=True,
                                 ondelete="cascade",
                                 help="Finding being responded to.",)
    requires_root_cause = fields.Boolean(
        string="Root Cause Required",
        related="finding_id.requires_root_cause",
        readonly=True,
        help="Whether a documented root cause is mandatory.",
    )
    requires_capa = fields.Boolean(
        string="CAPA Required",
        related="finding_id.requires_capa",
        readonly=True,
        help="Whether a CAPA reference is mandatory.",
    )
    root_cause = fields.Text(help="Result of the root cause investigation.",)
    correction = fields.Text(
        string="Immediate Correction",
        help="Action taken to eliminate the detected non-conformity itself.",
    )
    corrective_action = fields.Text(help="Action taken to eliminate the cause so that the "
                                    "non-conformity does not recur.",)
    capa_reference = fields.Char(help="Reference of the corrective and preventive action record.",)
    action_due_date = fields.Date(required=True,
                                  help="Date by which the corrective action will be completed.",)

    def action_submit(self):
        """Write the response onto the finding and advance its status.

        :return: an action closing the wizard window.
        :rtype: dict
        :raise UserError: when the finding is not awaiting a response or when
            a mandatory element of the response is missing.
        """
        self.ensure_one()
        finding = self.finding_id
        if finding.state != "open":
            raise UserError(
                _(
                    "Finding %(ref)s is not awaiting a response.",
                    ref=finding.reference,
                )
            )
        if not (self.corrective_action and self.corrective_action.strip()):
            raise UserError(
                _("A corrective action must be described in the response.")
            )
        if self.requires_root_cause and not (
            self.root_cause and self.root_cause.strip()
        ):
            raise UserError(
                _(
                    "Finding %(ref)s requires a documented root cause.",
                    ref=finding.reference,
                )
            )
        if self.requires_capa and not (
            self.capa_reference and self.capa_reference.strip()
        ):
            raise UserError(
                _(
                    "Finding %(ref)s requires a CAPA reference.",
                    ref=finding.reference,
                )
            )
        finding.write(
            {
                "root_cause": self.root_cause,
                "correction": self.correction,
                "corrective_action": self.corrective_action,
                "capa_reference": self.capa_reference,
                "action_due_date": self.action_due_date,
                "responded_by_id": self.env.user.id,
                "response_date": fields.Date.context_today(self),
                "state": "responded",
            }
        )
        finding.message_post(
            body=_(
                "Response submitted by %(user)s.", user=self.env.user.name
            )
        )
        return {"type": "ir.actions.act_window_close"}
