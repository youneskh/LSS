# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Major equipment and lines used by a manufacturing batch."""

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class LsPharmaBatchEquipment(models.Model):
    """Identity of an individual item of major equipment or a line.

    21 CFR 211.188(b)(2) requires the batch production and control record to
    document the identity of the individual major equipment and lines used.
    21 CFR 211.182 requires a written record of cleaning and use of major
    equipment; the reference of that record is carried here so that the batch
    record points to the cleaning evidence.

    The model stores the equipment identity as text rather than as a link to
    the maintenance application, so that this module does not add a
    dependency that the functional specification does not require.
    """

    _name = "ls.pharma.batch.equipment"
    _description = "Batch Equipment and Line Usage"
    _order = "batch_id, sequence, id"

    sequence = fields.Integer(default=10)
    batch_id = fields.Many2one(comodel_name="ls.pharma.batch", required=True,
                               ondelete="cascade",
                               index=True,)
    company_id = fields.Many2one(comodel_name="res.company", related="batch_id.company_id",
                                 store=True,
                                 index=True,)
    name = fields.Char(
        string="Equipment or Line",
        required=True,
        help="Name of the individual item of major equipment or of the line.",
    )
    equipment_identifier = fields.Char(required=True,
                                       help=(
                                           "Unique identifier engraved on or assigned to the equipment, so "
                                           "that the individual item, and not merely its type, is recorded."),
                                       )
    operation = fields.Char(help="Manufacturing operation for which the equipment was used.",)
    cleaning_record_reference = fields.Char(help=(
            "Reference of the equipment cleaning and use record required by "
            "21 CFR 211.182."),
    )
    cleaning_verified_by_user_id = fields.Many2one(
        comodel_name="res.users",
        string="Cleaning Verified By",
    )
    date_used_start = fields.Datetime(string="Used From")
    date_used_end = fields.Datetime(string="Used Until")
    note = fields.Char(string="Remark")

    @api.constrains("date_used_start", "date_used_end")
    def _check_usage_window(self):
        """Reject a usage window that ends before it starts."""
        for equipment in self:
            if (
                equipment.date_used_start
                and equipment.date_used_end
                and equipment.date_used_end < equipment.date_used_start
            ):
                raise ValidationError(
                    self.env._(
                        "The usage of %(name)s cannot end before it starts.",
                        name=equipment.name,
                    )
                )
