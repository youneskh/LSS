# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Instrument category master data."""

from odoo import api, fields, models
from odoo.exceptions import ValidationError

from . import constants


class LsCalibrationInstrumentCategory(models.Model):
    """Classification of measuring instruments.

    Categories carry the default calibration interval and default criticality
    applied to new instruments. They exist so that the instrument register can
    be grouped and filtered by instrument family (balances, thermometers,
    pressure gauges, pipettes and any other family defined by the organisation).
    """

    _name = "ls.calibration.instrument.category"
    _description = "Calibration Instrument Category"
    _order = "complete_name"
    _parent_name = "parent_id"
    _parent_store = True

    name = fields.Char(
        string="Category Name",
        required=True,
        translate=True,
        index=True,
    )
    complete_name = fields.Char(compute="_compute_complete_name",
                                recursive=True,
                                store=True,)
    code = fields.Char(required=True,
                       help="Short unique code used in reports and exports.",)
    parent_id = fields.Many2one(
        comodel_name="ls.calibration.instrument.category",
        string="Parent Category",
        ondelete="restrict",
        index=True,
    )
    parent_path = fields.Char(index=True, unaccent=False)
    child_ids = fields.One2many(
        comodel_name="ls.calibration.instrument.category",
        inverse_name="parent_id",
        string="Child Categories",
    )
    default_interval_value = fields.Integer(
        string="Default Interval",
        default=1,
        help="Default calibration interval proposed for instruments created "
        "in this category.",
    )
    default_interval_uom = fields.Selection(
        selection=constants.INTERVAL_UOM_SELECTION,
        string="Default Interval Unit",
        default=constants.INTERVAL_UOM_YEAR,
    )
    default_criticality = fields.Selection(selection=constants.CRITICALITY_SELECTION, default=constants.CRITICALITY_MAJOR,)
    description = fields.Text(translate=True)
    instrument_ids = fields.One2many(
        comodel_name="ls.calibration.instrument",
        inverse_name="category_id",
        string="Instruments",
    )
    instrument_count = fields.Integer(compute="_compute_instrument_count",)
    company_id = fields.Many2one(comodel_name="res.company", required=True,
                                 index=True,
                                 default=lambda self: self.env.company,)
    active = fields.Boolean(default=True)

    _code_company_uniq = models.Constraint(
        "UNIQUE(code, company_id)",
        "The instrument category code must be unique per company.",
    )
    _default_interval_positive = models.Constraint(
        "CHECK(default_interval_value > 0)",
        "The default calibration interval must be strictly positive.",
    )

    @api.depends("name", "parent_id.complete_name")
    def _compute_complete_name(self) -> None:
        """Build the slash-separated hierarchical name."""
        for category in self:
            if category.parent_id:
                category.complete_name = (
                    f"{category.parent_id.complete_name} / {category.name}"
                )
            else:
                category.complete_name = category.name

    @api.depends("instrument_ids")
    def _compute_instrument_count(self) -> None:
        """Count the instruments directly attached to each category."""
        grouped = self.env["ls.calibration.instrument"]._read_group(
            domain=[("category_id", "in", self.ids)],
            groupby=["category_id"],
            aggregates=["__count"],
        )
        counts = {category.id: count for category, count in grouped}
        for category in self:
            category.instrument_count = counts.get(category.id, 0)

    @api.constrains("parent_id")
    def _check_category_recursion(self) -> None:
        """Forbid cycles in the category hierarchy.

        The parent chain is walked explicitly rather than delegating to an ORM
        helper, so that the constraint does not depend on the name of a private
        framework method that may differ between Odoo releases.
        """
        for category in self:
            seen_ids = {category.id}
            ancestor = category.parent_id
            while ancestor:
                if ancestor.id in seen_ids:
                    raise ValidationError(
                        self.env._("A category cannot be its own ancestor.")
                    )
                seen_ids.add(ancestor.id)
                ancestor = ancestor.parent_id

    @api.depends("complete_name", "code")
    def _compute_display_name(self) -> None:
        """Display the code together with the hierarchical name."""
        for category in self:
            category.display_name = f"[{category.code}] {category.complete_name}"

    def action_open_instruments(self) -> dict:
        """Return the window action listing the instruments of this category."""
        self.ensure_one()
        action = self.env["ir.actions.act_window"]._for_xml_id(
            "ls_calibration.action_ls_calibration_instrument"
        )
        action["domain"] = [("category_id", "=", self.id)]
        action["context"] = {
            "default_category_id": self.id,
            "default_company_id": self.company_id.id,
        }
        return action
