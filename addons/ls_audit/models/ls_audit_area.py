# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Auditable area.

An auditable area is any organisational unit, process, site or system that can
be placed in the scope of an audit.  Areas are hierarchical so that a site can
contain departments and a department can contain processes.
"""

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class LsAuditArea(models.Model):
    """Organisational unit, process or system that can be audited."""

    _name = "ls.audit.area"
    _description = "Auditable Area"
    _order = "complete_name"
    _parent_store = True
    _parent_name = "parent_id"
    _rec_name = "complete_name"

    name = fields.Char(required=True,
                       translate=True,
                       help="Name of the auditable area, process or system.",)
    complete_name = fields.Char(compute="_compute_complete_name",
                                recursive=True,
                                store=True,
                                help="Full hierarchical path of the area, parents included.",)
    code = fields.Char(required=True,
                       help="Short unique code used in references and exports.",)
    parent_id = fields.Many2one(
        comodel_name="ls.audit.area",
        string="Parent Area",
        ondelete="restrict",
        index=True,
        help="Higher level area this area belongs to.",
    )
    parent_path = fields.Char(index=True, unaccent=False)
    child_ids = fields.One2many(
        comodel_name="ls.audit.area",
        inverse_name="parent_id",
        string="Sub-Areas",
        help="Areas directly contained in this area.",
    )
    department_id = fields.Many2one(comodel_name="hr.department", help="Department accountable for the area, used for reporting.",)
    responsible_id = fields.Many2one(
        comodel_name="res.users",
        string="Area Owner",
        help="User accountable for the area.  This user is proposed as "
             "auditee and is prevented from auditing this same area.",
    )
    description = fields.Text(translate=True,
                              help="Free text describing the boundaries of the area.",)
    company_id = fields.Many2one(comodel_name="res.company", required=True,
                                 default=lambda self: self.env.company,
                                 help="Company owning this configuration record.",)
    active = fields.Boolean(default=True,
                            help="Archived areas remain on historical audits but can no longer "
                            "be selected on new audits.",)

    _code_company_uniq = models.Constraint(
        "UNIQUE(code, company_id)",
        "The auditable area code must be unique per company.",
    )

    @api.depends("name", "parent_id.complete_name")
    def _compute_complete_name(self):
        """Build the hierarchical display name of the area."""
        for area in self:
            if area.parent_id:
                area.complete_name = "%s / %s" % (
                    area.parent_id.complete_name,
                    area.name,
                )
            else:
                area.complete_name = area.name

    @api.constrains("parent_id")
    def _check_area_recursion(self):
        """Forbid cycles in the area hierarchy.

        The ancestor chain is walked explicitly rather than through an ORM
        helper, because the name of the framework helper for recursion
        detection has changed between Odoo major versions.  Walking the chain
        depends only on documented ORM behaviour and is therefore stable.
        """
        for area in self:
            seen_ids = set()
            ancestor = area
            while ancestor:
                if ancestor.id in seen_ids:
                    raise ValidationError(
                        _("An auditable area cannot be its own ancestor.")
                    )
                seen_ids.add(ancestor.id)
                ancestor = ancestor.parent_id

    @api.constrains("parent_id", "company_id")
    def _check_parent_company(self):
        """Forbid a parent area belonging to another company."""
        for area in self:
            if area.parent_id and area.parent_id.company_id != area.company_id:
                raise ValidationError(
                    _(
                        "The parent area '%(parent)s' belongs to another "
                        "company than the area '%(area)s'.",
                        parent=area.parent_id.display_name,
                        area=area.name,
                    )
                )
