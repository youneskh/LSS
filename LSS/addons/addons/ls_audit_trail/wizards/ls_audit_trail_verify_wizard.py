# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0.html).
"""Wizard running an on-demand integrity verification of an audit chain."""

from __future__ import annotations

from odoo import _, api, fields, models

from ..tools import constants


class LsAuditTrailVerifyWizard(models.TransientModel):
    """Run an integrity verification over a chosen range and open the outcome.

    The wizard performs no verification logic of its own. It collects the range,
    delegates to ``ls.audit_trail.verification._ls_run`` and opens the resulting
    immutable verification record, so that a manual run and a scheduled run
    produce exactly the same evidence.
    """

    _name = "ls.audit_trail.verify.wizard"
    _description = "Verify Audit Trail Integrity"

    company_id = fields.Many2one(comodel_name="res.company", required=True,
                                 default=lambda self: self.env.company,
                                 help="Company whose audit chain is verified.",)
    scope = fields.Selection(
        selection=[
            ("window", "Recent window"),
            ("range", "Explicit range"),
            ("full", "Complete chain"),
        ],
        required=True,
        default="window",
    )
    window_days = fields.Integer(
        string="Window (days)",
        default=constants.DEFAULT_VERIFICATION_WINDOW_DAYS,
        help="Number of days back from now that are verified.",
    )
    date_from = fields.Datetime(
        string="From",
        help="Earliest event date verified.",
    )
    date_to = fields.Datetime(
        string="To",
        help="Latest event date verified.",
    )
    entry_estimate = fields.Integer(
        string="Entries In Scope",
        compute="_compute_entry_estimate",
        help=(
            "Number of entries the verification will recompute. Verifying a "
            "complete chain of a large database is a long running operation."
        ),
    )

    @api.depends("company_id", "scope", "window_days", "date_from", "date_to")
    def _compute_entry_estimate(self):
        """Count the entries that the selected scope would verify."""
        log_model = self.env["ls.audit_trail.log"].sudo()
        for wizard in self:
            date_from, date_to = wizard._ls_resolved_range()
            domain = [("company_id", "=", wizard.company_id.id)]
            if date_from:
                domain.append(("event_datetime", ">=", date_from))
            if date_to:
                domain.append(("event_datetime", "<=", date_to))
            wizard.entry_estimate = log_model.search_count(domain)

    def _ls_resolved_range(self):
        """Return the effective date bounds of the selected scope.

        :return: a tuple ``(date_from, date_to)``. Either bound may be ``False``
            when the complete chain is verified.
        """
        self.ensure_one()
        if self.scope == "full":
            return (False, False)
        if self.scope == "range":
            return (self.date_from, self.date_to)
        window = self.window_days or constants.DEFAULT_VERIFICATION_WINDOW_DAYS
        now = fields.Datetime.now()
        return (fields.Datetime.subtract(now, days=window), now)

    def action_verify(self):
        """Run the verification and open the resulting record.

        :return: an ``ir.actions.act_window`` dictionary showing the outcome.
        """
        self.ensure_one()
        date_from, date_to = self._ls_resolved_range()
        verification = self.env["ls.audit_trail.verification"].sudo()._ls_run(
            company=self.company_id,
            date_from=date_from,
            date_to=date_to,
            source="manual",
        )
        return {
            "type": "ir.actions.act_window",
            "name": _("Integrity Verification"),
            "res_model": "ls.audit_trail.verification",
            "res_id": verification.id,
            "view_mode": "form",
            "target": "current",
        }
