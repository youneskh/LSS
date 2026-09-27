# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0.html).
"""Wizard creating the next version of an approved formulation."""

from odoo import api, fields, models
from odoo.exceptions import UserError


class LsCosmeticFormulationRevise(models.TransientModel):
    """Create a new draft version of an approved formulation.

    An approved formulation is frozen because the product information file
    must remain reconstructable for the ten year retention period of
    Article 11(1).  A change is therefore made by issuing a new version: the
    composition is copied into a draft, and the previous version is marked as
    superseded only once the new version is itself approved.
    """

    _name = "ls.cosmetic.formulation.revise"
    _description = "Revise Cosmetic Formulation"

    formulation_id = fields.Many2one(comodel_name="ls.cosmetic.formulation", required=True,
                                     ondelete="cascade",)
    current_version = fields.Integer(related="formulation_id.version")
    new_version = fields.Integer(compute="_compute_new_version", store=False)
    change_reason = fields.Text(
        string="Reason for the Change",
        required=True,
        help="Recorded on both versions so that the reason for superseding "
             "the previous composition is traceable.",
    )
    copy_lines = fields.Boolean(
        string="Copy the Composition",
        default=True,
        help="Untick to start the new version from an empty composition.",
    )

    @api.depends("formulation_id")
    def _compute_new_version(self):
        """Propose the next version number for the formulation code."""
        for wizard in self:
            formulation = wizard.formulation_id
            if not formulation:
                wizard.new_version = 0
                continue
            highest = self.env["ls.cosmetic.formulation"].search(
                [
                    ("code", "=", formulation.code),
                    ("company_id", "=", formulation.company_id.id),
                ],
                order="version desc",
                limit=1,
            )
            wizard.new_version = (highest.version if highest else 0) + 1

    def action_revise(self):
        """Create the new draft version and open it.

        :return: an ``ir.actions.act_window`` opening the new version.
        """
        self.ensure_one()
        source = self.formulation_id
        if source.state != "approved":
            raise UserError(
                self.env._(
                    "Only an approved formulation can be revised. %(name)s is "
                    "%(state)s.",
                    name=source.display_name,
                    state=source.state,
                )
            )
        if source.successor_id:
            raise UserError(
                self.env._(
                    "Formulation %(name)s has already been revised into "
                    "%(successor)s.",
                    name=source.display_name,
                    successor=source.successor_id.display_name,
                )
            )
        new_version = self.new_version
        line_values = []
        if self.copy_lines:
            for line in source.line_ids:
                line_values.append(
                    (
                        0,
                        0,
                        {
                            "sequence": line.sequence,
                            "ingredient_id": line.ingredient_id.id,
                            "concentration": line.concentration,
                            "function_in_product": line.function_in_product,
                            "note": line.note,
                        },
                    )
                )
        revision = self.env["ls.cosmetic.formulation"].create(
            {
                "code": source.code,
                "name": source.name,
                "version": new_version,
                "state": "draft",
                "company_id": source.company_id.id,
                "product_tmpl_id": source.product_tmpl_id.id,
                "bom_id": source.bom_id.id,
                "intended_use": source.intended_use,
                "target_population": source.target_population,
                "for_children_under_three": source.for_children_under_three,
                "for_intimate_hygiene": source.for_intimate_hygiene,
                "predecessor_id": source.id,
                "line_ids": line_values,
            }
        )
        revision.message_post(
            body=self.env._(
                "Created as version %(version)s of %(code)s. Reason: %(reason)s",
                version=new_version,
                code=source.code,
                reason=self.change_reason,
            )
        )
        source.message_post(
            body=self.env._(
                "Revision %(version)s created. Reason: %(reason)s",
                version=new_version,
                reason=self.change_reason,
            )
        )
        source.sudo().write({"successor_id": revision.id})
        return {
            "type": "ir.actions.act_window",
            "name": self.env._("Formulation"),
            "res_model": "ls.cosmetic.formulation",
            "res_id": revision.id,
            "view_mode": "form",
            "target": "current",
        }
