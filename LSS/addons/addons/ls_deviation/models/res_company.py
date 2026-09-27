# Copyright 2026 Life Sciences Suite
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Company-level configuration of deviation closure targets."""

from odoo import fields, models

#: Fallback closure targets in days, applied when no company value is set.
DEFAULT_TARGET_DAYS = {"minor": 30, "major": 30, "critical": 30}


class ResCompany(models.Model):
    """Add deviation closure targets to the company."""

    _inherit = "res.company"

    ls_deviation_target_days_minor = fields.Integer(
        string="Minor Deviation Closure Target (days)",
        default=30,
    )
    ls_deviation_target_days_major = fields.Integer(
        string="Major Deviation Closure Target (days)",
        default=30,
    )
    ls_deviation_target_days_critical = fields.Integer(
        string="Critical Deviation Closure Target (days)",
        default=30,
    )

    def _ls_deviation_target_days(self, severity):
        """Return the configured closure target in days for ``severity``.

        :param str severity: one of ``minor``, ``major`` or ``critical``.
        :return: the configured number of days, or the documented fallback.
        :rtype: int
        """
        self.ensure_one()
        field_name = "ls_deviation_target_days_%s" % severity
        value = self[field_name] if field_name in self._fields else 0
        return value or DEFAULT_TARGET_DAYS.get(severity, 30)
