# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0.html).
"""Typed access to the system parameters used by the QMS module."""

from odoo import api, models

#: Values interpreted as boolean false in ``ir.config_parameter``.
FALSE_VALUES = ("false", "0", "no", "off", "")


class LsQmsParameterMixin(models.AbstractModel):
    """Read ``ir.config_parameter`` entries with validated fallbacks."""

    _name = "ls.qms.parameter.mixin"
    _description = "Life Sciences QMS Parameter Access Mixin"

    @api.model
    def _get_int_parameter(self, key, fallback):
        """Return ``key`` as a non negative integer.

        :param str key: system parameter key.
        :param int fallback: value returned when the parameter is missing or
            cannot be interpreted as a non negative integer.
        :rtype: int
        """
        raw_value = self.env["ir.config_parameter"].sudo().get_param(key)
        if raw_value is False or raw_value is None:
            return fallback
        try:
            value = int(str(raw_value).strip())
        except (TypeError, ValueError):
            return fallback
        return value if value >= 0 else fallback

    @api.model
    def _get_bool_parameter(self, key, fallback):
        """Return ``key`` as a boolean.

        :param str key: system parameter key.
        :param bool fallback: value returned when the parameter is missing.
        :rtype: bool
        """
        raw_value = self.env["ir.config_parameter"].sudo().get_param(key)
        if raw_value is False or raw_value is None:
            return fallback
        return str(raw_value).strip().lower() not in FALSE_VALUES
