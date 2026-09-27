# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Approval template lines defining the approval matrix of a category."""

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

#: Approval roles available in the module.
#:
#: The list is intentionally closed so that the approval matrix of a site is
#: deterministic and auditable. It is an extension point: a downstream module
#: may extend it with ``selection_add`` on the ``approval_role`` field of both
#: ``ls.change_control.approval_template`` and ``ls.change_control.approval``.
APPROVAL_ROLES = [
    ("quality_assurance", "Quality Assurance"),
    ("quality_control", "Quality Control"),
    ("production", "Production"),
    ("engineering", "Engineering and Maintenance"),
    ("validation", "Validation"),
    ("regulatory_affairs", "Regulatory Affairs"),
    ("research_development", "Research and Development"),
    ("supply_chain", "Supply Chain"),
    ("information_technology", "Information Technology"),
    ("site_management", "Site Management"),
    ("qualified_person", "Qualified Person"),
]


class LsChangeControlApprovalTemplate(models.Model):
    """One expected approval role for a given change category."""

    _name = "ls.change_control.approval_template"
    _description = "Change Control Approval Template"
    _order = "category_id, sequence, id"

    category_id = fields.Many2one(comodel_name="ls.change_control.category", required=True,
                                  ondelete="cascade",
                                  index=True,)
    sequence = fields.Integer(default=10,
                              help="Order in which the approvals are presented. The module does "
                              "not enforce a sequential approval order; all approvals of a "
                              "request may be granted in any order.",)
    approval_role = fields.Selection(selection=APPROVAL_ROLES, required=True,
                                     help="Function that must approve the change.",)
    user_id = fields.Many2one(
        comodel_name="res.users",
        string="Default Approver",
        domain="[('share', '=', False)]",
        help="User proposed as approver when the approval is generated. "
             "When empty, the approver must be assigned manually by the "
             "change control manager during the review.",
    )
    mandatory = fields.Boolean(default=True,
                               help="A mandatory approval must be granted before the change request "
                               "can reach the Approved state. A non-mandatory approval may be "
                               "removed by the change control manager during the review.",)

    _role_uniq_per_category = models.Constraint(
        "UNIQUE(category_id, approval_role)",
        "An approval role can only be defined once per change category.",
    )

    @api.constrains("user_id")
    def _check_user_is_internal(self):
        """Reject portal or public users as default approvers."""
        for template in self:
            if template.user_id and template.user_id.share:
                raise ValidationError(
                    _("The default approver must be an internal user.")
                )
