# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0.html).
"""Wizard executing an approved retention run on an audit chain.

Removing audit trail entries is a regulated act. This wizard is the only path
through which an entry can leave the database, and it is deliberately hard to
use by accident:

* the company must have retention runs explicitly allowed;
* a retention period in days and a procedure reference must be recorded on the
  company;
* only entries older than that period can be selected;
* the operator must type a justification and confirm the exact number of
  entries that will be removed;
* the removed range is replaced by a **retention anchor** entry that carries the
  aggregate digest of the removed entries and links the surviving chain, so the
  chain remains verifiable end to end and the removal itself becomes evidence.

The rows are deleted with a parameterised SQL statement rather than through the
ORM, because ``ls.audit_trail.log.unlink`` refuses every deletion for every
user, including the superuser. Keeping the ORM path unconditionally closed means
no future code path can delete entries silently.
"""

from __future__ import annotations

import logging

from odoo import _, api, fields, models
from odoo.exceptions import UserError

from ..tools import constants, serialization

_logger = logging.getLogger(__name__)


class LsAuditTrailPurgeWizard(models.TransientModel):
    """Collect, validate and execute an approved retention run."""

    _name = "ls.audit_trail.purge.wizard"
    _description = "Audit Trail Retention Run"

    company_id = fields.Many2one(comodel_name="res.company", required=True,
                                 default=lambda self: self.env.company,)
    retention_days = fields.Integer(
        string="Retention Period (days)",
        related="company_id.ls_audit_retention_days",
        readonly=True,
    )
    purge_allowed = fields.Boolean(
        string="Retention Runs Allowed",
        related="company_id.ls_audit_allow_purge",
        readonly=True,
    )
    procedure_reference = fields.Char(related="company_id.ls_audit_retention_procedure",
                                      readonly=True,)
    cutoff_datetime = fields.Datetime(
        string="Cut-off",
        compute="_compute_scope",
        help=(
            "Entries whose event date is strictly earlier than this moment are "
            "in scope. It is derived from the retention period of the company."
        ),
    )
    entry_count = fields.Integer(
        string="Entries In Scope",
        compute="_compute_scope",
    )
    first_sequence = fields.Integer(
        string="First Chain Position",
        compute="_compute_scope",
    )
    last_sequence = fields.Integer(
        string="Last Chain Position",
        compute="_compute_scope",
    )
    confirm_entry_count = fields.Integer(help=(
            "Type the number of entries shown above. The run refuses to "
            "proceed on any other value."),
    )
    justification = fields.Text(required=True,
                                help=(
                                    "Documented reason for the run. It is stored verbatim on the "
                                    "retention anchor entry and can never be modified afterwards."),
                                )

    @api.depends("company_id", "company_id.ls_audit_retention_days")
    def _compute_scope(self):
        """Derive the cut-off and describe the entries in scope."""
        log_model = self.env["ls.audit_trail.log"].sudo()
        for wizard in self:
            days = wizard.company_id.ls_audit_retention_days
            if not days:
                wizard.cutoff_datetime = False
                wizard.entry_count = 0
                wizard.first_sequence = 0
                wizard.last_sequence = 0
                continue
            cutoff = fields.Datetime.subtract(fields.Datetime.now(), days=days)
            entries = log_model.search(
                wizard._ls_scope_domain(cutoff), order="sequence_number asc"
            )
            wizard.cutoff_datetime = cutoff
            wizard.entry_count = len(entries)
            wizard.first_sequence = entries[0].sequence_number if entries else 0
            wizard.last_sequence = entries[-1].sequence_number if entries else 0

    def _ls_scope_domain(self, cutoff):
        """Return the domain selecting the entries in scope of the run.

        Retention anchors are excluded: an anchor is the evidence that a
        previous range was removed and must itself be kept.

        :param cutoff: the cut-off datetime.
        :return: an Odoo search domain.
        """
        self.ensure_one()
        return [
            ("company_id", "=", self.company_id.id),
            ("event_datetime", "<", cutoff),
            ("entry_type", "=", constants.ENTRY_TYPE_DATA),
        ]

    def _ls_check_preconditions(self):
        """Verify every precondition of a retention run.

        :raise UserError: when any precondition is not satisfied.
        """
        self.ensure_one()
        company = self.company_id
        if not company.ls_audit_allow_purge:
            raise UserError(
                _(
                    "Retention runs are not allowed for company %(company)s. "
                    "Enable them on the company only once an approved "
                    "retention procedure exists.",
                    company=company.display_name,
                )
            )
        if not company.ls_audit_retention_days:
            raise UserError(
                _("No retention period is defined for company %(company)s.",
                  company=company.display_name)
            )
        if not company.ls_audit_retention_procedure:
            raise UserError(
                _(
                    "No retention procedure reference is recorded for company "
                    "%(company)s.",
                    company=company.display_name,
                )
            )
        if not self.entry_count:
            raise UserError(
                _("No audit entry is older than the retention period.")
            )
        if self.confirm_entry_count != self.entry_count:
            raise UserError(
                _(
                    "The confirmation count does not match. %(expected)s "
                    "entries are in scope.",
                    expected=self.entry_count,
                )
            )
        if not (self.justification or "").strip():
            raise UserError(_("A justification is required."))

    def action_execute(self):
        """Execute the retention run.

        The verification of the range is executed first: an already broken chain
        must not be silently replaced by an anchor. The anchor is then written
        and sealed, and only afterwards are the rows removed, so that a failure
        at any point leaves the chain intact.

        :return: an ``ir.actions.act_window`` dictionary showing the anchor.
        :raise UserError: when a precondition fails or when the chain does not
            verify before the run.
        """
        self.ensure_one()
        self._ls_check_preconditions()
        log_model = self.env["ls.audit_trail.log"].sudo()
        cutoff = self.cutoff_datetime
        entries = log_model.search(
            self._ls_scope_domain(cutoff), order="sequence_number asc"
        )
        outcome = log_model._ls_verify_chain(
            self.company_id, date_to=entries[-1].event_datetime
        )
        if not outcome["passed"]:
            raise UserError(
                _(
                    "The chain of company %(company)s does not verify and no "
                    "entry may be removed. Findings: %(details)s",
                    company=self.company_id.display_name,
                    details=outcome["details"],
                )
            )
        aggregate_digest = serialization.sha256_hex(
            "|".join(entry.hash_current or "" for entry in entries)
        )
        anchor_values = {
            "company_id": self.company_id.id,
            "entry_type": constants.ENTRY_TYPE_ANCHOR,
            "event_datetime": fields.Datetime.now(),
            "user_id": self.env.uid,
            "user_login": self.env.user.login,
            "remote_addr": log_model._ls_remote_addr(),
            "model_name": "ls.audit_trail.log",
            "res_id": 0,
            "res_name": _("Retention run"),
            "operation": False,
            "purged_from_sequence": entries[0].sequence_number,
            "purged_to_sequence": entries[-1].sequence_number,
            "purged_entry_count": len(entries),
            "purged_aggregate_digest": aggregate_digest,
            "purge_reason": (
                "%s | procedure: %s | retention: %s days | cut-off: %s"
                % (
                    self.justification.strip(),
                    self.company_id.ls_audit_retention_procedure,
                    self.company_id.ls_audit_retention_days,
                    fields.Datetime.to_string(cutoff),
                )
            ),
        }
        anchor = log_model.create(anchor_values)
        anchor._ls_seal()
        removed_ids = entries.ids
        self.env.flush_all()
        self.env.cr.execute(
            "DELETE FROM ls_audit_trail_log WHERE id = ANY(%s)",
            (removed_ids,),
        )
        self.env.invalidate_all()
        _logger.warning(
            "ls_audit_trail: retention run removed %s entries of company %s "
            "(chain positions %s to %s), anchor %s, executed by %s",
            len(removed_ids),
            self.company_id.id,
            anchor_values["purged_from_sequence"],
            anchor_values["purged_to_sequence"],
            anchor.sequence_number,
            self.env.user.login,
        )
        return {
            "type": "ir.actions.act_window",
            "name": _("Retention Anchor"),
            "res_model": "ls.audit_trail.log",
            "res_id": anchor.id,
            "view_mode": "form",
            "target": "current",
        }
