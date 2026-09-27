# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Free-form categorisation tags for controlled documents."""

from odoo import fields, models


class LsDocumentTag(models.Model):
    """Tag used to categorise controlled documents."""

    _name = "ls.document.tag"
    _description = "Life Sciences Document Tag"
    _order = "name"

    name = fields.Char(
        string="Tag Name",
        required=True,
        translate=True,
    )
    active = fields.Boolean(default=True)
    color = fields.Integer(string="Colour Index", default=0)
    company_id = fields.Many2one(comodel_name="res.company", required=True,
                                 default=lambda self: self.env.company,
                                 index=True,)
    document_ids = fields.Many2many(
        comodel_name="ls.document.document",
        relation="ls_document_document_tag_rel",
        column1="tag_id",
        column2="document_id",
        string="Documents",
    )

    _name_company_uniq = models.Constraint(
        "UNIQUE(name, company_id)",
        "A document tag with this name already exists for this company.",
    )
