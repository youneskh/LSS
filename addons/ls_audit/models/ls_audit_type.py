# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Audit type configuration.

An audit type classifies an audit engagement (for example internal system
audit, supplier audit or regulatory inspection).  Types are organisation
configurable on purpose: no classification scheme is imposed by this module.
"""

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class LsAuditType(models.Model):
    """Classification of an audit engagement."""

    _name = "ls.audit.type"
    _description = "Audit Type"
    _order = "sequence, name"

    name = fields.Char(required=True,
                       translate=True,
                       help="Label of the audit type shown in audit records and reports.",)
    code = fields.Char(required=True,
                       help="Short unique code used in references and exports.",)
    sequence = fields.Integer(default=10,
                              help="Display order of the audit type in selection lists.",)
    description = fields.Text(translate=True,
                              help="Free text describing when this audit type is used.",)
    is_external = fields.Boolean(
        string="External Audit",
        help="Tick when the audit is performed by or at an external party "
             "(supplier audit, notified body audit, regulatory inspection).",
    )
    default_checklist_id = fields.Many2one(comodel_name="ls.audit.checklist", help="Checklist template proposed by default on audits of this type.",)
    company_id = fields.Many2one(comodel_name="res.company", required=True,
                                 default=lambda self: self.env.company,
                                 help="Company owning this configuration record.",)
    active = fields.Boolean(default=True,
                            help="Archived audit types remain on historical audits but can no "
                            "longer be selected on new audits.",)

    _code_company_uniq = models.Constraint(
        "UNIQUE(code, company_id)",
        "The audit type code must be unique per company.",
    )

    @api.constrains("default_checklist_id", "company_id")
    def _check_default_checklist_company(self):
        """Forbid a default checklist belonging to another company."""
        for audit_type in self:
            checklist = audit_type.default_checklist_id
            if checklist and checklist.company_id != audit_type.company_id:
                raise ValidationError(
                    _(
                        "The default checklist '%(checklist)s' belongs to "
                        "another company than the audit type '%(type)s'.",
                        checklist=checklist.display_name,
                        type=audit_type.name,
                    )
                )
