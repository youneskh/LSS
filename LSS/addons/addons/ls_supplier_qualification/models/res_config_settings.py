# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Expose the supplier qualification policy in the settings screen."""
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    """Settings proxy for the company-level qualification policy."""

    _inherit = "res.config.settings"

    ls_enforce_sod = fields.Boolean(
        related="company_id.ls_enforce_sod",
        readonly=False,
    )
    ls_expiry_reminder_days = fields.Integer(
        related="company_id.ls_expiry_reminder_days",
        readonly=False,
    )
    ls_audit_response_days = fields.Integer(
        related="company_id.ls_audit_response_days",
        readonly=False,
    )
    ls_po_control_level = fields.Selection(
        related="company_id.ls_po_control_level",
        readonly=False,
    )
    ls_po_check_scope = fields.Boolean(
        related="company_id.ls_po_check_scope",
        readonly=False,
    )
    ls_perf_weight_otd = fields.Float(
        related="company_id.ls_perf_weight_otd",
        readonly=False,
    )
    ls_perf_weight_quality = fields.Float(
        related="company_id.ls_perf_weight_quality",
        readonly=False,
    )
    ls_perf_weight_documentation = fields.Float(
        related="company_id.ls_perf_weight_documentation",
        readonly=False,
    )
    ls_perf_weight_responsiveness = fields.Float(
        related="company_id.ls_perf_weight_responsiveness",
        readonly=False,
    )
    ls_perf_threshold_a = fields.Float(
        related="company_id.ls_perf_threshold_a",
        readonly=False,
    )
    ls_perf_threshold_b = fields.Float(
        related="company_id.ls_perf_threshold_b",
        readonly=False,
    )
    ls_perf_threshold_c = fields.Float(
        related="company_id.ls_perf_threshold_c",
        readonly=False,
    )
