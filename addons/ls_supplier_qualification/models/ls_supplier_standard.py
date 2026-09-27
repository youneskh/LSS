# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Reference library of standards and regulatory frameworks.

Records of this model are *identifiers only*. The module stores the
designation of a framework so that an assessment, an audit or a criterion can
be traced back to it. The module does not embed, reproduce or interpret the
content of any standard: the normative text remains the property of the
issuing body and must be obtained from that body.
"""
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class LsSupplierStandard(models.Model):
    """A standard or regulatory framework used as an audit/assessment basis."""

    _name = "ls.supplier.standard"
    _description = "Life Sciences Supplier Reference Standard"
    _order = "sequence, name"

    name = fields.Char(
        string="Designation",
        required=True,
        translate=True,
        help="Official designation of the standard or framework, "
             "for example 'ISO 13485:2016'.",
    )
    code = fields.Char(
        required=True,
        help="Short technical code used in reports and exports.",
    )
    issuing_body = fields.Char(
        help="Organisation that issues and maintains the framework.",
    )
    scope_note = fields.Text(
        translate=True,
        help="Free-text note describing why the organisation applies this "
             "framework to suppliers. Entered by the quality department; the "
             "module does not pre-fill any normative interpretation.",
    )
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)

    _code_uniq = models.Constraint(
        "UNIQUE(code)",
        "The standard code must be unique.",
    )

    @api.constrains("code")
    def _check_code(self):
        """Forbid blank or whitespace-only codes."""
        for record in self:
            if not (record.code or "").strip():
                raise ValidationError(
                    _("The standard code cannot be empty.")
                )

    @api.depends("name", "code")
    def _compute_display_name(self):
        """Show 'CODE - Designation' in relational widgets."""
        for record in self:
            record.display_name = "%s - %s" % (record.code, record.name)
