# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0.html).
"""Wizard generating the Article 19(1)(g) list of ingredients."""

from odoo import api, fields, models
from odoo.exceptions import UserError


class LsCosmeticLabelGenerate(models.TransientModel):
    """Preview and apply the list of ingredients built from a formulation.

    The wizard exists so that the two options permitted by Article 19(1)(g)
    for colorants can be chosen and the result reviewed before it is written
    onto the label.
    """

    _name = "ls.cosmetic.label.generate"
    _description = "Generate Cosmetic Ingredient List"

    label_id = fields.Many2one(comodel_name="ls.cosmetic.label", required=True,
                               ondelete="cascade",)
    formulation_id = fields.Many2one(related="label_id.formulation_id")
    colorants_last = fields.Boolean(
        string="List Colorants Last",
        help="Article 19(1)(g) permits colorants other than those intended to "
             "colour the hair to be listed in any order after the other "
             "cosmetic ingredients.",
    )
    may_contain = fields.Boolean(
        string="Use 'may contain' Marker",
        help="For decorative cosmetic products marketed in several colour "
             "shades, all colorants other than hair colorants used in the "
             "range may be listed provided that the marker is added.",
    )
    preview = fields.Text(compute="_compute_preview", store=False)
    excluded_summary = fields.Text(
        string="Excluded from the List",
        compute="_compute_preview",
        store=False,
        help="Impurities in raw materials and subsidiary technical materials, "
             "which Article 19(1)(g) does not regard as ingredients.",
    )

    @api.depends("label_id", "colorants_last", "may_contain")
    def _compute_preview(self):
        """Build the preview of the generated list and of the exclusions."""
        for wizard in self:
            formulation = wizard.label_id.formulation_id
            if not formulation:
                wizard.preview = False
                wizard.excluded_summary = False
                continue
            wizard.preview = formulation.build_ingredient_list(
                colorants_last=wizard.colorants_last,
                may_contain=wizard.may_contain,
            )
            excluded = formulation.line_ids.filtered("exclude_from_label")
            if excluded:
                wizard.excluded_summary = "\n".join(
                    line.ingredient_id.inci_name or "" for line in excluded
                )
            else:
                wizard.excluded_summary = False

    def action_apply(self):
        """Write the generated list onto the label.

        :return: ``True`` when the list has been written.
        """
        self.ensure_one()
        label = self.label_id
        if label.state in ("approved", "superseded"):
            raise UserError(
                self.env._(
                    "Label %(code)s is %(state)s and its ingredient list can "
                    "no longer be regenerated.",
                    code=label.code,
                    state=label.state,
                )
            )
        label.write(
            {
                "colorants_last": self.colorants_last,
                "may_contain": self.may_contain,
            }
        )
        label.action_generate_ingredient_list()
        return True
