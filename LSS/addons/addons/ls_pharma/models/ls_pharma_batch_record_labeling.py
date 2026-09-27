# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Labelling control and reconciliation of a batch record."""

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class LsPharmaBatchRecordLabeling(models.Model):
    """Issuance, use, return and destruction of one labelling item.

    21 CFR 211.188(b)(8) requires complete labelling control records,
    including specimens or copies of all labelling used, in the batch
    production and control record.  21 CFR 211.125 governs the issuance and
    reconciliation of labelling.  This model records the four quantities that
    a reconciliation compares and computes the resulting discrepancy.

    The specimen or copy of the labelling itself is stored as an attachment
    on the batch record, which carries the messaging mixin.
    """

    _name = "ls.pharma.batch_record.labeling"
    _description = "Batch Record Labelling Control"
    _order = "record_id, sequence, id"

    sequence = fields.Integer(default=10)
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
    name = fields.Char(string="Labelling Item", required=True)
    label_version = fields.Char(string="Version", required=True)
    label_code = fields.Char(string="Item Code")
    quantity_issued = fields.Float(string="Issued", digits=(16, 2))
    quantity_used = fields.Float(string="Used", digits=(16, 2))
    quantity_returned = fields.Float(string="Returned", digits=(16, 2))
    quantity_destroyed = fields.Float(string="Destroyed", digits=(16, 2))
    quantity_difference = fields.Float(
        string="Difference",
        compute="_compute_reconciliation",
        store=True,
        digits=(16, 2),
        help=(
            "Quantity issued less the quantities used, returned and "
            "destroyed. A non-zero difference is an unexplained discrepancy "
            "within the meaning of 21 CFR 211.192."
        ),
    )
    is_reconciled = fields.Boolean(
        string="Reconciled",
        compute="_compute_reconciliation",
        store=True,
    )
    tolerance = fields.Float(digits=(16, 2),
                             help=(
            "Absolute difference below which the reconciliation is considered "
            "acceptable. A tolerance is only meaningful where the written "
            "procedures of the manufacturer establish one."
        ),
    )
    checked_by_user_id = fields.Many2one(
        comodel_name="res.users", string="Reconciled By"
    )
    date_checked = fields.Datetime(string="Reconciled On")
    remark = fields.Text()

    @api.depends(
        "quantity_issued",
        "quantity_used",
        "quantity_returned",
        "quantity_destroyed",
        "tolerance",
    )
    def _compute_reconciliation(self):
        """Compute the reconciliation difference and its acceptability."""
        for label in self:
            difference = label.quantity_issued - (
                label.quantity_used + label.quantity_returned + label.quantity_destroyed
            )
            label.quantity_difference = difference
            label.is_reconciled = abs(difference) <= abs(label.tolerance)

    @api.constrains(
        "quantity_issued",
        "quantity_used",
        "quantity_returned",
        "quantity_destroyed",
        "tolerance",
    )
    def _check_quantities(self):
        """Reject negative labelling quantities."""
        for label in self:
            values = (
                label.quantity_issued,
                label.quantity_used,
                label.quantity_returned,
                label.quantity_destroyed,
                label.tolerance,
            )
            if any(value < 0.0 for value in values):
                raise ValidationError(
                    self.env._(
                        "The labelling quantities of %(name)s cannot be "
                        "negative.",
                        name=label.name,
                    )
                )
