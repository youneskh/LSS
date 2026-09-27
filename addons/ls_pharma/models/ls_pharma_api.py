# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Active pharmaceutical ingredient master data."""

from odoo import api, fields, models
from odoo.exceptions import ValidationError

from ..constants import POTENCY_BASIS


class LsPharmaApi(models.Model):
    """Master record of an active pharmaceutical ingredient.

    The potency basis and assay recorded here are used by
    :class:`~odoo.addons.ls_pharma.models.ls_pharma_batch_component.
    LsPharmaBatchComponent` to compute the potency-compensated charge
    quantity of an active ingredient.
    """

    _name = "ls.pharma.api"
    _description = "Active Pharmaceutical Ingredient"
    _inherit = ["ls.pharma.material.mixin"]

    _code_company_uniq = models.Constraint(
        "UNIQUE(code, company_id)",
        "The internal code of an active pharmaceutical ingredient must be "
        "unique per company.",
    )

    inn_name = fields.Char(
        string="International Nonproprietary Name",
        tracking=True,
        help=(
            "International Nonproprietary Name assigned by the World Health "
            "Organization, where one has been assigned."
        ),
    )
    active_moiety = fields.Char(help=(
            "Molecule or ion responsible for the pharmacological activity, "
            "recorded when the ingredient is supplied as a salt, ester or "
            "other derivative."),
    )
    potency_basis = fields.Selection(selection=POTENCY_BASIS, default="as_is",
                                     required=True,
                                     tracking=True,
                                     help=(
                                         "Basis on which the assay of the ingredient is expressed. The "
                                         "batch component lines use this value together with the assay to "
                                         "compute the potency-compensated charge quantity."),
                                     )
    label_assay_percentage = fields.Float(
        string="Label Assay (%)",
        default=100.0,
        digits=(16, 4),
        help=(
            "Assay declared on the approved specification, expressed as a "
            "percentage. It is used as the reference against which the assay "
            "of an individual consignment is compensated."
        ),
    )
    is_controlled_substance = fields.Boolean(
        string="Controlled Substance",
        tracking=True,
        help=(
            "Indicates that national legislation subjects this ingredient to "
            "controlled substance requirements."
        ),
    )
    controlled_schedule = fields.Char(
        string="Controlled Substance Schedule",
        help=(
            "Schedule or table under which the ingredient is controlled, as "
            "designated by the applicable national authority."
        ),
    )
    is_sterile = fields.Boolean(
        string="Supplied Sterile",
        help="Indicates that the ingredient is supplied in a sterile state.",
    )

    @api.constrains("label_assay_percentage")
    def _check_label_assay(self):
        """Reject an assay that cannot describe a real specification."""
        for api_record in self:
            if api_record.label_assay_percentage <= 0.0:
                raise ValidationError(
                    self.env._(
                        "The label assay of %(name)s must be strictly "
                        "positive.",
                        name=api_record.display_name,
                    )
                )

    @api.constrains("is_controlled_substance", "controlled_schedule", "state")
    def _check_controlled_schedule(self):
        """Require the schedule of a qualified controlled substance."""
        for api_record in self:
            if (
                api_record.state == "qualified"
                and api_record.is_controlled_substance
                and not api_record.controlled_schedule
            ):
                raise ValidationError(
                    self.env._(
                        "Ingredient %(name)s is a controlled substance and "
                        "cannot be qualified until its schedule has been "
                        "recorded.",
                        name=api_record.display_name,
                    )
                )
