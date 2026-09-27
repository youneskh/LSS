# Part of the Life Sciences Suite. See LICENSE file for full copyright
# and licensing details.
"""Role enforcement shared by the risk management models.

Restricting a button with the ``groups`` attribute of a view hides it, but it
does not prevent the underlying method from being called through the ORM, an
imported automation, or the external API. The checks below are therefore
performed inside the workflow methods themselves.

``res.users.has_group`` is used rather than a comparison against a groups
field on ``res.users``, because the name of that field changed in Odoo 19 and
could not be verified from official documentation. ``has_group`` takes an
external identifier and is stable across versions.
"""

from odoo import models
from odoo.exceptions import AccessError

#: External identifier of the group permitted to approve, accept residual
#: risk and close records.
GROUP_RISK_MANAGER = "ls_risk_management.group_risk_manager"


class LsRiskRoleMixin(models.AbstractModel):
    """Provide a reusable Risk Manager role assertion."""

    _name = "ls.risk.role.mixin"
    _description = "Risk Management Role Checks"

    def _ensure_risk_manager(self, operation):
        """Raise unless the current user belongs to the Risk Manager group.

        :param str operation: human readable name of the operation, included
            in the error message.
        :raise AccessError: when the current user is not a Risk Manager.
        :return: ``True`` when the check passed.
        :rtype: bool
        """
        if not self.env.user.has_group(GROUP_RISK_MANAGER):
            raise AccessError(
                self.env._(
                    "Only a Risk Manager may %(operation)s. User %(user)s does "
                    "not hold that role.",
                    operation=operation,
                    user=self.env.user.display_name,
                )
            )
        return True
