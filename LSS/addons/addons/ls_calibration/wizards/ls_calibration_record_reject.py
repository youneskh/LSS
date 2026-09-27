# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Wizard collecting the justification of a calibration record rejection."""

from odoo import fields, models


class LsCalibrationRecordReject(models.TransientModel):
    """Rejection of a calibration record with a mandatory justification."""

    _name = "ls.calibration.record.reject"
    _description = "Reject Calibration Record"

    record_id = fields.Many2one(
        comodel_name="ls.calibration.record",
        string="Calibration Record",
        required=True,
        ondelete="cascade",
    )
    reason = fields.Text(
        string="Rejection Reason",
        required=True,
    )

    def action_reject(self):
        """Reject the calibration record with the collected reason.

        :return: an action closing the wizard dialog.
        """
        self.ensure_one()
        self.record_id.action_reject(reason=self.reason)
        return {"type": "ir.actions.act_window_close"}
