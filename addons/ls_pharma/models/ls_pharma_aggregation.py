# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Aggregation of serialised units into logistics containers."""

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError

from .. import gs1
from ..constants import AGGREGATION_LEVELS, AGGREGATION_STATES


class LsPharmaAggregation(models.Model):
    """A logistics container identified by a Serial Shipping Container Code.

    A container holds serialised saleable units, other containers, or both,
    so that the parent-child relationship between a pallet, a case and a
    saleable unit can be represented.  The Serial Shipping Container Code is
    carried by GS1 Application Identifier (00) and has eighteen digits ending
    with a modulo-10 check digit.
    """

    _name = "ls.pharma.aggregation"
    _description = "Serialisation Aggregation Container"
    _order = "level desc, sscc"

    _sscc_company_uniq = models.Constraint(
        "UNIQUE(sscc, company_id)",
        "A Serial Shipping Container Code must be unique per company.",
    )

    sscc = fields.Char(required=True,
                       index=True,
                       help="Serial Shipping Container Code carried by Application Identifier (00).",
                       )
    level = fields.Selection(
        selection=AGGREGATION_LEVELS,
        string="Container Level",
        required=True,
        default="case",
    )
    batch_id = fields.Many2one(comodel_name="ls.pharma.batch", index=True,
                               ondelete="restrict",
                               help=(
                                   "Batch to which the container belongs. It is empty for a mixed "
                                   "container that holds units of more than one batch."),
                               )
    company_id = fields.Many2one(comodel_name="res.company", required=True,
                                 default=lambda self: self.env.company,
                                 index=True,)
    parent_id = fields.Many2one(
        comodel_name="ls.pharma.aggregation",
        string="Parent Container",
        index=True,
        ondelete="set null",
    )
    child_ids = fields.One2many(
        comodel_name="ls.pharma.aggregation",
        inverse_name="parent_id",
        string="Child Containers",
    )
    serialization_ids = fields.One2many(
        comodel_name="ls.pharma.serialization",
        inverse_name="aggregation_id",
        string="Contained Units",
    )
    unit_count = fields.Integer(
        string="Contained Units", compute="_compute_counts", store=True
    )
    child_count = fields.Integer(
        string="Child Containers", compute="_compute_counts", store=True
    )
    element_string = fields.Char(
        string="GS1 Element String",
        compute="_compute_element_string",
        store=True,
    )
    state = fields.Selection(
        selection=AGGREGATION_STATES,
        string="Status",
        default="draft",
        required=True,
        index=True,
        copy=False,
    )
    date_packed = fields.Datetime(string="Packed On", copy=False)
    note = fields.Char(string="Remark")

    @api.depends("serialization_ids", "child_ids")
    def _compute_counts(self):
        """Count the direct contents of the container."""
        for container in self:
            container.unit_count = len(container.serialization_ids)
            container.child_count = len(container.child_ids)

    @api.depends("sscc")
    def _compute_element_string(self):
        """Build the element string of the container."""
        for container in self:
            try:
                container.element_string = gs1.build_sscc_element_string(
                    container.sscc
                )
            except gs1.Gs1Error:
                container.element_string = False

    @api.depends("sscc", "level")
    def _compute_display_name(self):
        """Show the container level and its code."""
        for container in self:
            container.display_name = "%s %s" % (
                dict(AGGREGATION_LEVELS).get(container.level, ""),
                container.sscc or "",
            )

    @api.constrains("sscc")
    def _check_sscc(self):
        """Reject a code that is not a valid Serial Shipping Container Code."""
        for container in self:
            if not gs1.is_valid_sscc(container.sscc):
                raise ValidationError(
                    self.env._(
                        "The value %(sscc)s is not a valid SSCC. An SSCC has "
                        "eighteen digits and ends with a modulo-10 check "
                        "digit.",
                        sscc=container.sscc,
                    )
                )

    @api.constrains("parent_id")
    def _check_parent(self):
        """Reject a container hierarchy that would form a loop."""
        for container in self:
            seen_ids = set()
            ancestor = container.parent_id
            while ancestor:
                if ancestor.id == container.id or ancestor.id in seen_ids:
                    raise ValidationError(
                        self.env._(
                            "Container %(sscc)s cannot contain itself.",
                            sscc=container.sscc,
                        )
                    )
                seen_ids.add(ancestor.id)
                ancestor = ancestor.parent_id

    def action_pack(self):
        """Mark the selected containers as packed and aggregate their units."""
        for container in self:
            if container.state != "draft":
                raise UserError(
                    self.env._(
                        "Container %(sscc)s is not in the draft state.",
                        sscc=container.sscc,
                    )
                )
            if not container.serialization_ids and not container.child_ids:
                raise UserError(
                    self.env._(
                        "Container %(sscc)s is empty and cannot be packed.",
                        sscc=container.sscc,
                    )
                )
            not_commissioned = container.serialization_ids.filtered(
                lambda unit: unit.state != "commissioned"
            )
            if not_commissioned:
                raise UserError(
                    self.env._(
                        "Container %(sscc)s holds %(count)s unit(s) that have "
                        "not been commissioned.",
                        sscc=container.sscc,
                        count=len(not_commissioned),
                    )
                )
            container.serialization_ids.write({"state": "aggregated"})
            container.write(
                {"state": "packed", "date_packed": fields.Datetime.now()}
            )
        return True

    def action_disaggregate(self):
        """Disaggregate the selected containers."""
        for container in self:
            if container.state == "shipped":
                raise UserError(
                    self.env._(
                        "Container %(sscc)s has been shipped and can no "
                        "longer be disaggregated in this system.",
                        sscc=container.sscc,
                    )
                )
            container.serialization_ids.filtered(
                lambda unit: unit.state == "aggregated"
            ).write({"state": "commissioned"})
            container.write({"state": "disaggregated"})
        return True

    def action_mark_shipped(self):
        """Record that the selected containers have been shipped."""
        for container in self:
            if container.state != "packed":
                raise UserError(
                    self.env._(
                        "Container %(sscc)s must be packed before it can be "
                        "shipped.",
                        sscc=container.sscc,
                    )
                )
            container.serialization_ids.write({"state": "shipped"})
            container.write({"state": "shipped"})
        return True
