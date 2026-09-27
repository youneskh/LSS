# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Physical samples held in a stability study."""

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError

from ..constants import STABILITY_SAMPLE_STATES


class LsPharmaStabilitySample(models.Model):
    """A physical sample placed in a stability chamber.

    A sample belongs to a study and, once it has been allocated, to the time
    point at which it is to be pulled.  Keeping the sample distinct from the
    time point allows several samples to be allocated to the same pull point,
    for example one for the assay and one for the microbiological
    examination.
    """

    _name = "ls.pharma.stability.sample"
    _description = "Stability Sample"
    _order = "study_id, name, id"

    _name_company_uniq = models.Constraint(
        "UNIQUE(name, company_id)",
        "The stability sample reference must be unique per company.",
    )

    name = fields.Char(string="Sample Reference", required=True, copy=False)
    study_id = fields.Many2one(comodel_name="ls.pharma.stability_study", required=True,
                               ondelete="cascade",
                               index=True,)
    company_id = fields.Many2one(comodel_name="res.company", related="study_id.company_id",
                                 store=True,
                                 index=True,)
    timepoint_id = fields.Many2one(
        comodel_name="ls.pharma.stability.timepoint",
        string="Allocated Time Point",
        index=True,
        ondelete="set null",
    )
    condition_id = fields.Many2one(
        comodel_name="ls.pharma.stability.condition",
        string="Storage Condition",
        required=True,
        ondelete="restrict",
    )
    quantity = fields.Float(digits="Product Unit of Measure")
    uom_id = fields.Many2one(comodel_name="uom.uom", string="Unit of Measure")
    chamber_reference = fields.Char(help="Identifier of the stability chamber in which the sample is held.",)
    position_reference = fields.Char(string="Position in Chamber")
    date_placed = fields.Date(
        string="Placed On", required=True, default=fields.Date.context_today
    )
    date_removed = fields.Date(string="Removed On", copy=False)
    state = fields.Selection(
        selection=STABILITY_SAMPLE_STATES,
        string="Status",
        default="stored",
        required=True,
        copy=False,
        index=True,
    )
    remark = fields.Text()

    @api.constrains("quantity")
    def _check_quantity(self):
        """Reject a negative sample quantity."""
        for sample in self:
            if sample.quantity < 0.0:
                raise ValidationError(
                    self.env._(
                        "The quantity of sample %(name)s cannot be negative.",
                        name=sample.name,
                    )
                )

    @api.constrains("date_placed", "date_removed")
    def _check_dates(self):
        """Reject a removal date that precedes the placement date."""
        for sample in self:
            if (
                sample.date_removed
                and sample.date_placed
                and sample.date_removed < sample.date_placed
            ):
                raise ValidationError(
                    self.env._(
                        "Sample %(name)s cannot be removed before it was "
                        "placed.",
                        name=sample.name,
                    )
                )

    @api.constrains("timepoint_id", "study_id", "condition_id")
    def _check_timepoint_consistency(self):
        """Reject an allocation to a time point of another study or condition."""
        for sample in self:
            timepoint = sample.timepoint_id
            if not timepoint:
                continue
            if timepoint.study_id.id != sample.study_id.id:
                raise ValidationError(
                    self.env._(
                        "Sample %(name)s cannot be allocated to a time point "
                        "of another study.",
                        name=sample.name,
                    )
                )
            if timepoint.condition_id.id != sample.condition_id.id:
                raise ValidationError(
                    self.env._(
                        "Sample %(name)s is stored under a condition that "
                        "differs from the condition of its time point.",
                        name=sample.name,
                    )
                )

    def action_pull(self):
        """Record that the selected samples have been pulled."""
        for sample in self:
            if sample.state != "stored":
                raise UserError(
                    self.env._(
                        "Sample %(name)s is not in storage.", name=sample.name
                    )
                )
        self.write(
            {"state": "pulled", "date_removed": fields.Date.context_today(self)}
        )
        return True

    def action_consume(self):
        """Record that the selected samples have been consumed by testing."""
        self.write({"state": "consumed"})
        return True

    def action_discard(self):
        """Record that the selected samples have been discarded."""
        for sample in self:
            if not sample.remark:
                raise UserError(
                    self.env._(
                        "A remark is required to justify the discarding of "
                        "sample %(name)s.",
                        name=sample.name,
                    )
                )
        self.write(
            {"state": "discarded", "date_removed": fields.Date.context_today(self)}
        )
        return True
