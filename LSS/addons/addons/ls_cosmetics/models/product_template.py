# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0.html).
"""Cosmetic regulatory information carried by the product record."""

from odoo import api, fields, models


class ProductTemplate(models.Model):
    """Add the cosmetic regulatory dossier links to the product."""

    _inherit = "product.template"

    ls_is_cosmetic = fields.Boolean(
        string="Cosmetic Product",
        help="Article 2(1)(a) defines a cosmetic product as any substance or "
             "mixture intended to be placed in contact with the external parts "
             "of the human body, or with the teeth and the mucous membranes of "
             "the oral cavity, with a view exclusively or mainly to cleaning, "
             "perfuming, changing the appearance of, protecting, keeping in "
             "good condition or correcting the body odours of those parts.",
    )
    ls_formulation_ids = fields.One2many(
        comodel_name="ls.cosmetic.formulation",
        inverse_name="product_tmpl_id",
        string="Formulations",
    )
    ls_formulation_count = fields.Integer(
        string="Formulation Count", compute="_compute_ls_cosmetic_counts"
    )
    ls_pif_ids = fields.One2many(
        comodel_name="ls.cosmetic.pif",
        inverse_name="product_tmpl_id",
        string="Product Information Files",
    )
    ls_pif_count = fields.Integer(
        string="Product Information File Count",
        compute="_compute_ls_cosmetic_counts",
    )
    ls_label_ids = fields.One2many(
        comodel_name="ls.cosmetic.label",
        inverse_name="product_tmpl_id",
        string="Labels",
    )
    ls_label_count = fields.Integer(
        string="Label Count", compute="_compute_ls_cosmetic_counts"
    )
    ls_claim_ids = fields.One2many(
        comodel_name="ls.cosmetic.claim",
        inverse_name="product_tmpl_id",
        string="Claims",
    )
    ls_claim_count = fields.Integer(
        string="Claim Count", compute="_compute_ls_cosmetic_counts"
    )

    @api.depends("ls_formulation_ids", "ls_pif_ids", "ls_label_ids", "ls_claim_ids")
    def _compute_ls_cosmetic_counts(self):
        """Count the cosmetic regulatory records attached to the product."""
        for template in self:
            template.ls_formulation_count = len(template.ls_formulation_ids)
            template.ls_pif_count = len(template.ls_pif_ids)
            template.ls_label_count = len(template.ls_label_ids)
            template.ls_claim_count = len(template.ls_claim_ids)

    def action_view_ls_formulations(self):
        """Open the formulations of this product."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": self.env._("Formulations"),
            "res_model": "ls.cosmetic.formulation",
            "view_mode": "list,form",
            "domain": [("product_tmpl_id", "=", self.id)],
            "context": {"default_product_tmpl_id": self.id},
        }

    def action_view_ls_pifs(self):
        """Open the product information files of this product."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": self.env._("Product Information Files"),
            "res_model": "ls.cosmetic.pif",
            "view_mode": "list,form",
            "domain": [("product_tmpl_id", "=", self.id)],
            "context": {"default_product_tmpl_id": self.id},
        }

    def action_view_ls_labels(self):
        """Open the labels of this product."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": self.env._("Labels"),
            "res_model": "ls.cosmetic.label",
            "view_mode": "list,form",
            "domain": [("product_tmpl_id", "=", self.id)],
        }

    def action_view_ls_claims(self):
        """Open the claims of this product."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": self.env._("Claims"),
            "res_model": "ls.cosmetic.claim",
            "view_mode": "list,form",
            "domain": [("product_tmpl_id", "=", self.id)],
            "context": {"default_product_tmpl_id": self.id},
        }
