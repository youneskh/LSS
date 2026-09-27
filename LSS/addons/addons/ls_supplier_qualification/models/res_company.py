# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Company-level configuration of the supplier qualification process."""
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

PO_CONTROL_SELECTION = [
    ("none", "No control"),
    ("warn", "Log a warning on the order"),
    ("block", "Block the confirmation"),
]


class ResCompany(models.Model):
    """Add the supplier qualification policy to the company record."""

    _inherit = "res.company"

    ls_enforce_sod = fields.Boolean(
        string="Enforce Segregation of Duties",
        default=True,
        help="When enabled, the approver of a dossier cannot be an assessor "
             "or a lead auditor of that dossier, and an assessment cannot be "
             "reviewed by its own assessor.",
    )
    ls_expiry_reminder_days = fields.Integer(
        string="Expiry Reminder (days)",
        default=60,
        help="Number of days before the end of validity at which the "
             "scheduled actions raise reminders.",
    )
    ls_audit_response_days = fields.Integer(
        string="Audit Response Lead Time (days)",
        default=30,
        help="Default number of days granted to the supplier to answer an "
             "issued audit report.",
    )
    ls_po_control_level = fields.Selection(
        selection=PO_CONTROL_SELECTION,
        string="Purchase Order Control",
        default="warn",
        required=True,
        help="Behaviour when a purchase order is confirmed for a supplier "
             "that is not approved.",
    )
    ls_po_check_scope = fields.Boolean(
        string="Check Qualified Scope on Purchase Orders",
        default=False,
        help="When enabled, the purchase order control also verifies that "
             "each ordered product belongs to the qualified scope of the "
             "supplier.",
    )
    ls_perf_weight_otd = fields.Float(
        string="Weight - On-Time Delivery", default=30.0, digits=(5, 2)
    )
    ls_perf_weight_quality = fields.Float(
        string="Weight - Quality Acceptance", default=40.0, digits=(5, 2)
    )
    ls_perf_weight_documentation = fields.Float(
        string="Weight - Documentation", default=15.0, digits=(5, 2)
    )
    ls_perf_weight_responsiveness = fields.Float(
        string="Weight - Responsiveness", default=15.0, digits=(5, 2)
    )
    ls_perf_threshold_a = fields.Float(
        string="Rating A Threshold", default=90.0, digits=(5, 2)
    )
    ls_perf_threshold_b = fields.Float(
        string="Rating B Threshold", default=75.0, digits=(5, 2)
    )
    ls_perf_threshold_c = fields.Float(
        string="Rating C Threshold", default=60.0, digits=(5, 2)
    )

    @api.constrains(
        "ls_expiry_reminder_days",
        "ls_audit_response_days",
    )
    def _check_ls_lead_times(self):
        """Lead times must be non-negative day counts."""
        for company in self:
            if company.ls_expiry_reminder_days < 0:
                raise ValidationError(
                    _("The expiry reminder lead time cannot be negative.")
                )
            if company.ls_audit_response_days < 0:
                raise ValidationError(
                    _("The audit response lead time cannot be negative.")
                )

    @api.constrains(
        "ls_perf_weight_otd",
        "ls_perf_weight_quality",
        "ls_perf_weight_documentation",
        "ls_perf_weight_responsiveness",
    )
    def _check_ls_perf_weights(self):
        """At least one performance weight must be strictly positive."""
        for company in self:
            weights = [
                company.ls_perf_weight_otd,
                company.ls_perf_weight_quality,
                company.ls_perf_weight_documentation,
                company.ls_perf_weight_responsiveness,
            ]
            if any(weight < 0 for weight in weights):
                raise ValidationError(
                    _("Performance weights cannot be negative.")
                )
            if not sum(weights):
                raise ValidationError(
                    _("At least one performance weight must be strictly "
                      "positive.")
                )

    @api.constrains(
        "ls_perf_threshold_a",
        "ls_perf_threshold_b",
        "ls_perf_threshold_c",
    )
    def _check_ls_perf_thresholds(self):
        """Rating thresholds must decrease from A to C inside 0-100."""
        for company in self:
            thresholds = [
                company.ls_perf_threshold_a,
                company.ls_perf_threshold_b,
                company.ls_perf_threshold_c,
            ]
            if any(not 0 <= value <= 100 for value in thresholds):
                raise ValidationError(
                    _("Rating thresholds must be between 0 and 100.")
                )
            if not (
                company.ls_perf_threshold_a
                >= company.ls_perf_threshold_b
                >= company.ls_perf_threshold_c
            ):
                raise ValidationError(
                    _("Rating thresholds must decrease from A to C.")
                )
