# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Wizard capturing the mandatory reason when a calibration is rejected."""

from odoo import fields, models
from odoo.exceptions import UserError


class LsCalibrationRecordReject(models.TransientModel):
    """Collect a rejection reason and apply it to a calibration record."""

    _name = "ls.calibration.record.reject"
    _description = "Reject Calibration Record"

    record_id = fields.Many2one(
        comodel_name="ls.calibration.record",
        string="Calibration Record",
        required=True,
        readonly=True,
    )
    instrument_id = fields.Many2one(comodel_name="ls.calibration.instrument", related="record_id.instrument_id",
                                    readonly=True,)
    reason = fields.Text(
        string="Rejection Reason",
        required=True,
        help="Reason the calibration record is returned. The reason is stored "
        "on the record and appears in its tracked history.",
    )

    def action_confirm(self) -> bool:
        """Apply the rejection to the target record."""
        self.ensure_one()
        if not self.reason.strip():
            raise UserError(
                self.env._("The rejection reason cannot be blank.")
            )
        self.record_id.action_reject(self.reason)
        self.record_id.message_post(
            body=self.env._(
                "Calibration record rejected. Reason: %(reason)s",
                reason=self.reason,
            )
        )
        return True
