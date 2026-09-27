# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Change categories: templates for impact areas, approvals and deadlines."""

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class LsChangeControlCategory(models.Model):
    """Classification of a change, driving the applicable workflow template.

    The category is the single configuration point that determines, for a
    given type of change:

    * which impact areas must be assessed;
    * which approval roles must sign;
    * which deadlines apply to implementation and verification.
    """

    _name = "ls.change_control.category"
    _description = "Change Control Category"
    _order = "sequence, name"

    name = fields.Char(
        string="Category",
        required=True,
        translate=True,
    )
    code = fields.Char(required=True,
                       help="Short unique code used in reports and exports.",)
    sequence = fields.Integer(default=10,
                              help="Display order of the category in selection lists.",)
    description = fields.Text(translate=True,
                              help="Scope of the category, used as guidance for the requester.",)
    impact_area_ids = fields.Many2many(
        comodel_name="ls.change_control.impact_area",
        relation="ls_cc_category_impact_area_rel",
        column1="category_id",
        column2="impact_area_id",
        string="Default Impact Areas",
        help="Impact areas proposed on a change request that uses this "
             "category. The requester may add areas but may not remove an "
             "area whose assessment is mandatory.",
    )
    approval_template_ids = fields.One2many(comodel_name="ls.change_control.approval_template",
                                            inverse_name="category_id", help="Ordered list of approval roles generated on a change request "
                                            "of this category when it is submitted for review.",)
    implementation_delay = fields.Integer(
        string="Implementation Deadline (days)",
        default=90,
        help="Number of days after approval used to propose a planned "
             "implementation date. Set to 0 to propose no date.",
    )
    verification_delay = fields.Integer(
        string="Verification Delay (days)",
        default=0,
        help="Number of days after the actual implementation date used to "
             "compute the planned verification date. When 0, the company "
             "default verification delay applies.",
    )
    requires_verification = fields.Boolean(
        string="Effectiveness Verification Required",
        default=True,
        help="When disabled, a change of this category may be closed without "
             "a completed effectiveness verification.",
    )
    active = fields.Boolean(default=True,
                            help="Archived categories remain on existing change requests but can "
                            "no longer be selected on new ones.",)

    _code_unique = models.Constraint(
        "UNIQUE(code)",
        "The change category code must be unique.",
    )
    _implementation_delay_positive = models.Constraint(
        "CHECK(implementation_delay >= 0)",
        "The implementation deadline cannot be negative.",
    )
    _verification_delay_positive = models.Constraint(
        "CHECK(verification_delay >= 0)",
        "The verification delay cannot be negative.",
    )

    @api.constrains("requires_verification", "verification_delay")
    def _check_verification_configuration(self):
        """Forbid a mandatory verification without a usable delay source."""
        for category in self:
            if not category.requires_verification:
                continue
            company_delay = self.env.company.ls_cc_default_verification_delay
            if not category.verification_delay and company_delay <= 0:
                raise ValidationError(
                    _(
                        "Category '%(name)s' requires an effectiveness "
                        "verification but no verification delay is defined, "
                        "neither on the category nor on company '%(company)s'.",
                        name=category.name,
                        company=self.env.company.name,
                    )
                )

    def get_verification_delay(self, company):
        """Return the applicable verification delay in days.

        :param company: ``res.company`` record used as fallback source.
        :return: integer number of days, always greater than or equal to 0.
        """
        self.ensure_one()
        if self.verification_delay:
            return self.verification_delay
        return max(company.ls_cc_default_verification_delay, 0)
