# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0.html).
"""Integrity verification: the recorded outcome of a chain re-computation."""

from __future__ import annotations

import logging

from odoo import _, api, fields, models
from odoo.exceptions import AccessError

_logger = logging.getLogger(__name__)


class LsAuditTrailVerification(models.Model):
    """Recorded outcome of one integrity verification run.

    A verification record is evidence in its own right: it states who verified
    which range of which chain, when, and what the outcome was. It is therefore
    immutable once created, exactly like an audit entry.
    """

    _name = "ls.audit_trail.verification"
    _description = "Audit Trail Integrity Verification"
    _order = "executed_on desc, id desc"

    name = fields.Char(
        string="Reference",
        required=True,
        readonly=True,
        help="Human readable reference of the verification run.",
    )
    company_id = fields.Many2one(comodel_name="res.company", required=True,
                                 readonly=True,
                                 index=True,
                                 ondelete="restrict",
                                 help="Company whose audit chain was verified.",)
    date_from = fields.Datetime(
        string="Range Start",
        readonly=True,
        help="Lower bound applied to the event date of the verified entries.",
    )
    date_to = fields.Datetime(
        string="Range End",
        readonly=True,
        help="Upper bound applied to the event date of the verified entries.",
    )
    executed_on = fields.Datetime(required=True,
                                  readonly=True,
                                  index=True,
                                  help="Server date and time, in UTC, at which the verification ran.",)
    executed_by = fields.Many2one(comodel_name="res.users", required=True,
                                  readonly=True,
                                  ondelete="restrict",
                                  help="User under whose account the verification ran.",)
    source = fields.Selection(
        selection=[
            ("manual", "Manual"),
            ("cron", "Scheduled Action"),
        ],
        required=True,
        readonly=True,
        default="manual",
        index=True,
    )
    entries_checked = fields.Integer(
        string="Entries Verified",
        readonly=True,
        help="Number of audit entries whose digests were recomputed.",
    )
    result = fields.Selection(
        selection=[
            ("passed", "Passed"),
            ("failed", "Failed"),
        ],
        required=True,
        readonly=True,
        index=True,
    )
    first_failure_log_id = fields.Many2one(
        comodel_name="ls.audit_trail.log",
        string="First Divergent Entry",
        readonly=True,
        ondelete="set null",
        help="Earliest entry at which the recomputed digests stopped matching.",
    )
    first_failure_sequence = fields.Integer(
        string="First Divergent Position",
        readonly=True,
        help="Chain position of the earliest divergent entry.",
    )
    details = fields.Text(readonly=True,
                          help="Findings reported by the verification run.",)

    @api.depends("name", "result", "company_id")
    def _compute_display_name(self):
        """Build a display name stating the reference and the outcome."""
        labels = dict(self._fields["result"].selection)
        for verification in self:
            outcome = labels.get(verification.result, verification.result or "")
            verification.display_name = f"{verification.name} ({outcome})"

    def write(self, vals):
        """Reject every modification.

        :param vals: field values requested by the caller.
        :raise AccessError: always.
        """
        raise AccessError(
            _("Integrity verification records are immutable and cannot be modified.")
        )

    @api.ondelete(at_uninstall=False)
    def _ls_unlink_check_ls_audit_trail_verification(self):
        """Reject every deletion.

        :raise AccessError: always.
        """
        raise AccessError(
            _("Integrity verification records cannot be deleted.")
        )

    @api.model
    def _ls_run(self, company, date_from=None, date_to=None, source="manual"):
        """Verify a company chain and record the outcome.

        :param company: a ``res.company`` singleton recordset.
        :param date_from: optional lower bound on the event date.
        :param date_to: optional upper bound on the event date.
        :param source: ``manual`` or ``cron``.
        :return: the created ``ls.audit_trail.verification`` record.
        """
        log_model = self.env["ls.audit_trail.log"].sudo()
        outcome = log_model._ls_verify_chain(company, date_from, date_to)
        executed_on = fields.Datetime.now()
        reference = "VER/%s/%s" % (
            company.id,
            fields.Datetime.to_string(executed_on).replace("-", "").replace(":", ""),
        )
        verification = self.sudo().create(
            {
                "name": reference,
                "company_id": company.id,
                "date_from": date_from,
                "date_to": date_to,
                "executed_on": executed_on,
                "executed_by": self.env.uid,
                "source": source,
                "entries_checked": outcome["checked"],
                "result": "passed" if outcome["passed"] else "failed",
                "first_failure_log_id": outcome["first_failure_id"],
                "first_failure_sequence": outcome["first_failure_sequence"],
                "details": outcome["details"],
            }
        )
        if not outcome["passed"]:
            verification._ls_notify_failure()
        return verification

    def _ls_notify_failure(self):
        """Notify the audit administrators that a verification failed.

        The authoritative evidence of the failure is the verification record
        itself, which is already committed when this method runs. The
        notification is a best effort convenience: a mail server that is
        unavailable must not roll back the recording of the failure. Any
        problem encountered while notifying is therefore written to the server
        log instead of being raised.

        Group membership is evaluated with ``has_group`` rather than with a
        domain on the group field of ``res.users``, because ``has_group`` is
        stable across Odoo releases while the name of that field is not.
        """
        self.ensure_one()
        _logger.error(
            "ls_audit_trail: integrity verification %s of company %s failed at "
            "chain position %s: %s",
            self.name,
            self.company_id.id,
            self.first_failure_sequence,
            self.details,
        )
        administrators = (
            self.env["res.users"]
            .sudo()
            .search([("active", "=", True)])
            .filtered(
                lambda user: user.has_group(
                    "ls_audit_trail.group_ls_audit_trail_admin"
                )
            )
        )
        partners = administrators.mapped("partner_id")
        if not partners:
            return
        try:
            self.env["mail.thread"].sudo().message_notify(
                partner_ids=partners.ids,
                subject=_("Audit trail integrity verification failed"),
                body=_(
                    "The integrity verification %(reference)s of company "
                    "%(company)s reported a divergence at chain position "
                    "%(position)s.",
                    reference=self.name,
                    company=self.company_id.display_name,
                    position=self.first_failure_sequence,
                ),
                model=self._name,
                res_id=self.id,
            )
        except Exception:  # noqa: BLE001 - notification must not mask the finding
            _logger.exception(
                "ls_audit_trail: the failure notification for %s could not be sent",
                self.name,
            )
