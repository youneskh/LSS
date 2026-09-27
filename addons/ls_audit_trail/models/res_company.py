# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0.html).
"""Company level configuration of the audit trail."""

from __future__ import annotations

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class ResCompany(models.Model):
    """Carry the retention policy of the audit chain of a company.

    The configuration lives on ``res.company`` rather than in a settings view,
    because each company of a multi company database owns an independent audit
    chain and an independent retention decision.
    """

    _inherit = "res.company"

    ls_audit_retention_days = fields.Integer(
        string="Audit Trail Retention (days)",
        default=0,
        help=(
            "Minimum age, in days, that an audit entry must reach before a "
            "retention run may remove it. Zero means that no retention period "
            "has been defined and that no entry may be removed."
        ),
    )
    ls_audit_allow_purge = fields.Boolean(
        string="Allow Audit Trail Retention Runs",
        default=False,
        help=(
            "When disabled, no audit entry can ever be removed from this "
            "company's chain. Enable it only once a retention period has been "
            "approved by the quality organisation and recorded in a procedure."
        ),
    )
    ls_audit_retention_procedure = fields.Char(
        string="Retention Procedure Reference",
        help=(
            "Identifier of the approved procedure authorising retention runs, "
            "for example the controlled number of the records retention SOP."
        ),
    )
    ls_audit_entry_count = fields.Integer(
        string="Audit Entries",
        compute="_compute_ls_audit_entry_count",
        help="Number of audit entries currently held in this company's chain.",
    )

    @api.depends_context("uid")
    def _compute_ls_audit_entry_count(self):
        """Count the audit entries held in the chain of each company."""
        log_model = self.env["ls.audit_trail.log"].sudo()
        grouped = log_model._read_group(
            domain=[("company_id", "in", self.ids)],
            groupby=["company_id"],
            aggregates=["__count"],
        )
        counts = {company.id: count for company, count in grouped}
        for company in self:
            company.ls_audit_entry_count = counts.get(company.id, 0)

    @api.constrains("ls_audit_retention_days", "ls_audit_allow_purge")
    def _check_ls_audit_retention(self):
        """Reject an incoherent retention configuration."""
        for company in self:
            if company.ls_audit_retention_days < 0:
                raise ValidationError(
                    _("The audit trail retention period cannot be negative.")
                )
            if company.ls_audit_allow_purge and not company.ls_audit_retention_days:
                raise ValidationError(
                    _(
                        "A retention period in days must be defined before "
                        "retention runs can be allowed for company "
                        "%(company)s.",
                        company=company.display_name,
                    )
                )
            if (
                company.ls_audit_allow_purge
                and not company.ls_audit_retention_procedure
            ):
                raise ValidationError(
                    _(
                        "A retention procedure reference must be recorded "
                        "before retention runs can be allowed for company "
                        "%(company)s.",
                        company=company.display_name,
                    )
                )
