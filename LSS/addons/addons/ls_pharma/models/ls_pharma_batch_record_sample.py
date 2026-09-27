# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Samples taken during the execution of a batch record."""

from odoo import api, fields, models
from odoo.exceptions import ValidationError

from ..constants import SAMPLE_TYPES


class LsPharmaBatchRecordSample(models.Model):
    """A sample taken during manufacture, packaging or holding.

    21 CFR 211.188(b)(10) requires that any sampling performed be documented
    in the batch production and control record.  21 CFR 211.170 establishes
    the reserve sample regime; a sample whose type is ``reserve`` therefore
    additionally carries a retention date.
    """

    _name = "ls.pharma.batch_record.sample"
    _description = "Batch Record Sample"
    _order = "record_id, date_taken, id"

    record_id = fields.Many2one(
        comodel_name="ls.pharma.batch_record",
        string="Batch Record",
        required=True,
        ondelete="cascade",
        index=True,
    )
    company_id = fields.Many2one(comodel_name="res.company", related="record_id.company_id",
                                 store=True,
                                 index=True,)
    name = fields.Char(string="Sample Reference", required=True)
    sample_type = fields.Selection(selection=SAMPLE_TYPES, required=True,
                                   default="in_process",
                                   index=True,)
    purpose = fields.Char()
    quantity = fields.Float(digits="Product Unit of Measure")
    uom_id = fields.Many2one(comodel_name="uom.uom", string="Unit of Measure")
    sampling_point = fields.Char(help="Location or process stage at which the sample was drawn.",)
    storage_location = fields.Char()
    date_taken = fields.Datetime(
        string="Taken On", required=True, default=fields.Datetime.now
    )
    taken_by_user_id = fields.Many2one(
        comodel_name="res.users",
        string="Taken By",
        default=lambda self: self.env.user,
    )
    retention_until = fields.Date(
        string="Retain Until",
        help=(
            "Date until which a reserve sample is retained under "
            "21 CFR 211.170. The retention period itself is established by "
            "the written procedures of the manufacturer."
        ),
    )
    result_reference = fields.Char(help="Reference of the laboratory record that carries the result.",)
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

    @api.constrains("sample_type", "retention_until", "date_taken")
    def _check_reserve_retention(self):
        """Require a coherent retention date for a reserve sample."""
        for sample in self:
            if sample.sample_type != "reserve":
                continue
            if not sample.retention_until:
                raise ValidationError(
                    self.env._(
                        "Reserve sample %(name)s must carry a retention date, "
                        "because 21 CFR 211.170 establishes a retention "
                        "period for reserve samples.",
                        name=sample.name,
                    )
                )
            if sample.date_taken and sample.retention_until <= sample.date_taken.date():
                raise ValidationError(
                    self.env._(
                        "The retention date of reserve sample %(name)s must "
                        "be later than the date on which it was taken.",
                        name=sample.name,
                    )
                )
