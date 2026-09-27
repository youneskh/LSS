# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Finding category configuration.

A finding category carries the severity, the response deadline and whether a
corrective and preventive action is mandatory.  Categories are configuration
records rather than a hard-coded list, because finding classification schemes
differ between organisations and between certification bodies.
"""

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class LsAuditFindingCategory(models.Model):
    """Classification applied to an audit finding."""

    _name = "ls.audit.finding.category"
    _description = "Audit Finding Category"
    _order = "sequence, name"

    name = fields.Char(required=True,
                       translate=True,
                       help="Label of the finding category.",)
    code = fields.Char(required=True,
                       help="Short unique code used in references and exports.",)
    sequence = fields.Integer(default=10,
                              help="Display order, most severe categories first by convention.",)
    severity = fields.Selection(
        selection=[
            ("critical", "Critical"),
            ("major", "Major"),
            ("minor", "Minor"),
            ("observation", "Observation"),
            ("improvement", "Opportunity for Improvement"),
        ],
        required=True,
        default="minor",
        help="Severity level used for escalation, reporting and metrics.",
    )
    response_deadline_days = fields.Integer(
        string="Response Deadline (days)",
        default=30,
        help="Number of calendar days granted to the auditee to submit a "
             "response, counted from the date the finding is issued.",
    )
    requires_capa = fields.Boolean(help="Tick when a corrective and preventive action is mandatory for "
                                   "findings of this category. A CAPA reference is then required "
                                   "before the finding can be closed.",)
    requires_root_cause = fields.Boolean(default=True,
                                         help="Tick when a documented root cause is mandatory before the "
                                         "finding response can be accepted.",)
    color = fields.Integer(
        string="Colour Index",
        help="Colour used in kanban views for findings of this category.",
    )
    description = fields.Text(translate=True,
                              help="Definition of the category, used as guidance for auditors.",)
    company_id = fields.Many2one(comodel_name="res.company", required=True,
                                 default=lambda self: self.env.company,
                                 help="Company owning this configuration record.",)
    active = fields.Boolean(default=True,
                            help="Archived categories remain on historical findings but can no "
                            "longer be selected on new findings.",)

    _code_company_uniq = models.Constraint(
        "UNIQUE(code, company_id)",
        "The finding category code must be unique per company.",
    )

    @api.constrains("response_deadline_days")
    def _check_response_deadline_days(self):
        """Forbid a negative response deadline."""
        for category in self:
            if category.response_deadline_days < 0:
                raise ValidationError(
                    _(
                        "The response deadline of category '%(name)s' cannot "
                        "be negative.",
                        name=category.name,
                    )
                )
