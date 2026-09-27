# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Scrap lines of a moulding run.

Rejected parts are recorded by reason and, where a multi-cavity tool makes it
possible, by cavity. Attributing defects to a cavity is what allows a single
cavity to be blocked rather than the whole tool taken out of service.
"""

from odoo import api, fields, models
from odoo.exceptions import ValidationError

from ..constants import QUANTITY_DIGITS


class LsMpInjectionMoldingScrap(models.Model):
    """Quantity of parts rejected for one reason during a moulding run."""

    _name = "ls.mp.injection_molding.scrap"
    _description = "Medical Plastics Moulding Scrap"
    _order = "run_id, id"

    run_id = fields.Many2one(
        comodel_name="ls.mp.injection_molding",
        string="Moulding Run",
        required=True,
        ondelete="cascade",
        index=True,
    )
    reason_id = fields.Many2one(
        comodel_name="ls.mp.scrap.reason",
        string="Scrap Reason",
        required=True,
        ondelete="restrict",
        index=True,
    )
    cavity_id = fields.Many2one(comodel_name="ls.mp.tool.cavity", ondelete="restrict",
                                help="Cavity to which the defect was attributed, where identifiable.",)
    quantity = fields.Float(
        string="Quantity Rejected",
        digits=QUANTITY_DIGITS,
        required=True,
    )
    detected_by_id = fields.Many2one(comodel_name="res.users", default=lambda self: self.env.user,
                                     ondelete="restrict",)
    detection_date = fields.Datetime(
        string="Detected On",
        default=fields.Datetime.now,
        required=True,
    )
    is_startup = fields.Boolean(
        string="Start-up Scrap",
        related="reason_id.is_startup",
        store=True,
        readonly=True,
    )
    requires_investigation = fields.Boolean(related="reason_id.requires_investigation",
                                            store=True,
                                            readonly=True,)
    comment = fields.Char()
    company_id = fields.Many2one(comodel_name="res.company", related="run_id.company_id",
                                 store=True,
                                 index=True,
                                 readonly=True,)

    _quantity_positive = models.Constraint(
        "CHECK(quantity > 0)",
        "The rejected quantity must be strictly positive.",
    )

    @api.depends("reason_id.name", "quantity")
    def _compute_display_name(self):
        """Render the line as ``Reason: quantity``."""
        for line in self:
            line.display_name = f"{line.reason_id.name}: {line.quantity}"

    @api.constrains("run_id", "quantity")
    def _check_run_scrap_total(self):
        """Refuse rejects beyond the parts produced by the run.

        The rule of the run is declared on its one2many, which the ORM does
        not re-check when a reject line is created or changed on its own.
        """
        self.run_id._check_scrap_not_exceeding_production()

    @api.constrains("cavity_id", "run_id")
    def _check_cavity_belongs_to_tool(self):
        """A cavity may only be cited if it belongs to the tool used."""
        for line in self:
            if line.cavity_id and line.cavity_id.tool_id != line.run_id.tool_id:
                raise ValidationError(
                    self.env._(
                        "Cavity %(cavity)s does not belong to tool %(tool)s used by "
                        "this run.",
                        cavity=line.cavity_id.display_name,
                        tool=line.run_id.tool_id.display_name,
                    )
                )
