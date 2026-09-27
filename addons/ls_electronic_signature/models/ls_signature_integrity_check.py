# Part of the Life Sciences Suite. See LICENSE file for full copyright details.
"""Periodic verification of the signature hash chain."""

import logging

from odoo import _, api, fields, models

_logger = logging.getLogger(__name__)


class LsSignatureIntegrityCheck(models.Model):
    """The outcome of one verification pass over a company's chain."""

    _name = "ls.signature.integrity.check"
    _description = "Electronic Signature Integrity Check"
    _order = "checked_at desc, id desc"
    _rec_name = "display_name"

    company_id = fields.Many2one(
        comodel_name="res.company",
        required=True,
        readonly=True,
        index=True,
        ondelete="restrict",
    )
    checked_at = fields.Datetime(required=True, readonly=True, index=True)
    checked_by_id = fields.Many2one(
        comodel_name="res.users",
        readonly=True,
        ondelete="restrict",
    )
    trigger = fields.Selection(
        selection=[("manual", "Manual"), ("scheduled", "Scheduled")],
        required=True,
        readonly=True,
    )
    state = fields.Selection(
        selection=[("passed", "Passed"), ("failed", "Failed")],
        required=True,
        readonly=True,
        index=True,
    )
    entries_checked = fields.Integer(readonly=True)
    first_divergence_log_id = fields.Many2one(
        comodel_name="ls.signature.log",
        readonly=True,
        ondelete="restrict",
    )
    details = fields.Text(readonly=True)

    @api.depends("company_id", "checked_at", "state")
    def _compute_display_name(self):
        """Build a self describing label for list and reference display."""
        for check in self:
            check.display_name = "%s / %s / %s" % (
                check.company_id.name or "",
                fields.Datetime.to_string(check.checked_at) or "",
                dict(self._fields["state"].selection).get(check.state, ""),
            )

    @api.model
    def run(self, company, trigger="manual"):
        """Verify one company's chain and store the outcome.

        :param company: A single ``res.company`` recordset.
        :param str trigger: ``manual`` or ``scheduled``.
        :returns: The created ``ls.signature.integrity.check`` recordset.
        """
        outcome = self.env["ls.signature.log"].verify_chain(company)
        check = self.sudo().create(
            {
                "company_id": company.id,
                "checked_at": fields.Datetime.now(),
                "checked_by_id": self.env.uid,
                "trigger": trigger,
                "state": "passed" if outcome["passed"] else "failed",
                "entries_checked": outcome["entries_checked"],
                "first_divergence_log_id": outcome["first_divergence_id"],
                "details": "\n".join(outcome["messages"])
                or _("No divergence detected."),
            }
        )
        if not outcome["passed"]:
            _logger.error(
                "Electronic signature chain verification FAILED for company "
                "%s: %s",
                company.display_name,
                "; ".join(outcome["messages"]),
            )
            check._notify_failure()
        return check

    def _notify_failure(self):
        """Notify the security unit that a chain verification failed."""
        template = self.env.ref(
            "ls_electronic_signature.mail_template_integrity_failure",
            raise_if_not_found=False,
        )
        recipients = self.env["ls.signature.attempt"]._security_unit_recipients()
        if not template or not recipients:
            return False
        for check in self:
            template.sudo().with_context(
                security_recipients=recipients
            ).send_mail(check.id, force_send=True)
        return True

    @api.model
    def _cron_verify_all_companies(self):
        """Verify the chain of every company. Used by the scheduled action."""
        companies = self.env["res.company"].sudo().search([])
        for company in companies:
            self.run(company, trigger="scheduled")
        return len(companies)

    @api.model
    def action_run_now(self):
        """Verify the chain of the active company from the user interface."""
        check = self.run(self.env.company, trigger="manual")
        return {
            "type": "ir.actions.act_window",
            "res_model": self._name,
            "res_id": check.id,
            "view_mode": "form",
            "target": "current",
        }
