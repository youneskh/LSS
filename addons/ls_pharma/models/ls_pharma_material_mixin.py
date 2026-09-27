# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Shared behaviour of pharmaceutical material master records."""

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError

from ..constants import MATERIAL_STATES, PHARMACOPOEIA


class LsPharmaMaterialMixin(models.AbstractModel):
    """Common structure of an active ingredient or excipient master record.

    Both :class:`~odoo.addons.ls_pharma.models.ls_pharma_api.LsPharmaApi` and
    :class:`~odoo.addons.ls_pharma.models.ls_pharma_excipient.LsPharmaExcipient`
    inherit this mixin.  Keeping the shared fields in one place avoids the
    duplication that two independent concrete models would otherwise carry,
    while still exposing the two distinct menus that the functional
    specification requires.
    """

    _name = "ls.pharma.material.mixin"
    _description = "Pharmaceutical Material Master Data Mixin"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "code, name"

    name = fields.Char(
        string="Material Name",
        required=True,
        tracking=True,
        index=True,
    )
    code = fields.Char(
        string="Internal Code",
        required=True,
        tracking=True,
        index=True,
        copy=False,
        help="Unique internal identifier of the material within the company.",
    )
    product_id = fields.Many2one(
        comodel_name="product.product",
        string="Inventory Item",
        tracking=True,
        help=(
            "Stockable item that represents this material in inventory. "
            "Leaving the field empty is permitted for materials that are "
            "registered for regulatory purposes only and are not held in "
            "stock."
        ),
    )
    pharmacopoeia = fields.Selection(
        selection=PHARMACOPOEIA,
        string="Specification Basis",
        tracking=True,
    )
    monograph_reference = fields.Char(help="Identifier of the monograph or in-house specification applied.",)
    cas_number = fields.Char(help="Chemical Abstracts Service registry number, where one exists.",)
    manufacturer_partner_ids = fields.Many2many(
        comodel_name="res.partner",
        string="Approved Manufacturers",
        help=(
            "Manufacturing sites approved for this material. Qualification "
            "evidence is maintained outside this module."
        ),
    )
    retest_period_months = fields.Integer(
        string="Retest Period (Months)",
        help=(
            "Period after which a released consignment of this material must "
            "be re-examined before use. A value of zero means that no retest "
            "period has been established."
        ),
    )
    storage_condition = fields.Char(help="Storage condition stated on the approved specification.",)
    of_animal_origin = fields.Boolean(tracking=True,
                                      help=(
                                          "Indicates that the material is derived from animal sources and "
                                          "therefore requires a transmissible spongiform encephalopathy "
                                          "statement before use."),
                                      )
    tse_statement_reference = fields.Char(
        string="TSE/BSE Statement Reference",
        help=(
            "Reference of the supplier statement on transmissible spongiform "
            "encephalopathy and bovine spongiform encephalopathy risk."
        ),
    )
    state = fields.Selection(
        selection=MATERIAL_STATES,
        string="Status",
        default="draft",
        required=True,
        tracking=True,
        copy=False,
    )
    note = fields.Text(string="Internal Notes")
    company_id = fields.Many2one(comodel_name="res.company", required=True,
                                 default=lambda self: self.env.company,
                                 index=True,)
    active = fields.Boolean(default=True)

    @api.depends("code", "name")
    def _compute_display_name(self):
        """Show the internal code alongside the material name."""
        for material in self:
            if material.code:
                material.display_name = "[%s] %s" % (material.code, material.name)
            else:
                material.display_name = material.name or ""

    @api.constrains("of_animal_origin", "tse_statement_reference", "state")
    def _check_tse_statement(self):
        """Require a TSE statement before a material of animal origin is used.

        A material of animal origin may be recorded at any time, but it may
        not reach the qualified state without the reference of the supplier
        statement being present.
        """
        for material in self:
            if (
                material.state == "qualified"
                and material.of_animal_origin
                and not material.tse_statement_reference
            ):
                raise ValidationError(
                    self.env._(
                        "Material %(name)s is of animal origin and cannot be "
                        "qualified until the reference of its TSE/BSE "
                        "statement has been recorded.",
                        name=material.display_name,
                    )
                )

    @api.constrains("retest_period_months")
    def _check_retest_period(self):
        """Reject a negative retest period."""
        for material in self:
            if material.retest_period_months < 0:
                raise ValidationError(
                    self.env._("The retest period cannot be negative.")
                )

    def action_qualify(self):
        """Move the selected materials to the qualified state."""
        for material in self:
            if material.state == "qualified":
                raise UserError(
                    self.env._(
                        "Material %(name)s is already qualified.",
                        name=material.display_name,
                    )
                )
        self.write({"state": "qualified"})
        return True

    def action_restrict(self):
        """Restrict the selected materials from further use."""
        self.write({"state": "restricted"})
        return True

    def action_set_draft(self):
        """Return the selected materials to the draft state."""
        for material in self:
            if material.state == "obsolete":
                raise UserError(
                    self.env._(
                        "Material %(name)s is obsolete and cannot be returned "
                        "to draft.",
                        name=material.display_name,
                    )
                )
        self.write({"state": "draft"})
        return True

    def action_obsolete(self):
        """Mark the selected materials as obsolete and archive them."""
        self.write({"state": "obsolete", "active": False})
        return True
