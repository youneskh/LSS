# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Inspections of the packaging and labelling area."""

from odoo import api, fields, models
from odoo.exceptions import ValidationError

from ..constants import CLEARANCE_MOMENTS

CLEARANCE_RESULTS = [
    ("pass", "Pass"),
    ("fail", "Fail"),
]


class LsPharmaBatchRecordClearance(models.Model):
    """An inspection of the packaging and labelling area.

    21 CFR 211.188(b)(6) requires the batch production and control record to
    document the inspection of the packaging and labelling area before and
    after use.  Each inspection is recorded with its moment, the area
    concerned, the person who performed it, the person who verified it and
    its outcome.
    """

    _name = "ls.pharma.batch_record.clearance"
    _description = "Batch Record Area Inspection"
    _order = "record_id, date_performed, id"

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
    moment = fields.Selection(selection=CLEARANCE_MOMENTS, required=True,
                              default="before",)
    area = fields.Char(string="Area or Line", required=True)
    date_performed = fields.Datetime(
        string="Performed On", required=True, default=fields.Datetime.now
    )
    performed_by_user_id = fields.Many2one(
        comodel_name="res.users",
        string="Performed By",
        default=lambda self: self.env.user,
    )
    verified_by_user_id = fields.Many2one(
        comodel_name="res.users", string="Verified By"
    )
    result = fields.Selection(selection=CLEARANCE_RESULTS, required=True,
                              default="pass",)
    previous_product = fields.Char(help="Product processed on the line before this batch, where applicable.",)
    findings = fields.Text()

    @api.constrains("result", "findings")
    def _check_failed_clearance(self):
        """Require findings to be recorded when an inspection fails."""
        for clearance in self:
            if clearance.result == "fail" and not clearance.findings:
                raise ValidationError(
                    self.env._(
                        "The inspection of area %(area)s failed. The findings "
                        "must be recorded.",
                        area=clearance.area,
                    )
                )

    @api.constrains("performed_by_user_id", "verified_by_user_id")
    def _check_independent_verification(self):
        """Reject an inspection verified by the person who performed it."""
        for clearance in self:
            performer = clearance.performed_by_user_id
            verifier = clearance.verified_by_user_id
            if performer and verifier and performer.id == verifier.id:
                raise ValidationError(
                    self.env._(
                        "The inspection of area %(area)s cannot be verified "
                        "by the person who performed it.",
                        area=clearance.area,
                    )
                )
