# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Reference standards used to perform calibrations.

Recording which reference standard was used, and the traceability of that
standard, is what makes a calibration result defensible. This model holds the
standard master data and its own validity window.
"""

from odoo import api, fields, models
from odoo.exceptions import UserError

from . import constants


class LsCalibrationStandard(models.Model):
    """Reference standard, master or working, used during a calibration."""

    _name = "ls.calibration.standard"
    _description = "Calibration Reference Standard"
    _inherit = ["mail.thread"]
    _order = "code, id"

    name = fields.Char(string="Standard Name", required=True, tracking=True)
    code = fields.Char(
        string="Standard ID",
        required=True,
        tracking=True,
        index=True,
    )
    manufacturer = fields.Char()
    model_reference = fields.Char(string="Model")
    serial_number = fields.Char(index=True)
    description = fields.Text()

    traceability_reference = fields.Char(
        string="Traceability Certificate No.",
        tracking=True,
        help="Identifier of the calibration certificate that establishes the "
        "traceability of this standard.",
    )
    issuing_body = fields.Char(
        string="Issuing Laboratory",
        help="Laboratory that issued the traceability certificate.",
    )
    accreditation_reference = fields.Char(help="Accreditation number quoted by the issuing laboratory. Recorded "
                                          "as supplied; this module performs no verification against any "
                                          "accreditation register.",)
    certificate_date = fields.Date(tracking=True)
    valid_until = fields.Date(required=True, tracking=True)
    is_valid = fields.Boolean(
        string="Currently Valid",
        compute="_compute_is_valid",
        store=True,
        help="Computed from the Valid Until date against the current date.",
    )
    certificate_document = fields.Binary(attachment=True,)
    certificate_filename = fields.Char()

    uncertainty = fields.Float(
        string="Measurement Uncertainty",
        digits=constants.MEASUREMENT_DIGITS,
        help="Expanded measurement uncertainty of the standard, expressed in "
        "the unit recorded below.",
    )
    uncertainty_unit = fields.Char()

    record_ids = fields.Many2many(
        comodel_name="ls.calibration.record",
        relation="ls_calibration_record_standard_rel",
        column1="standard_id",
        column2="record_id",
        string="Calibration Records",
    )
    record_count = fields.Integer(compute="_compute_record_count")
    company_id = fields.Many2one(comodel_name="res.company", required=True,
                                 index=True,
                                 default=lambda self: self.env.company,)
    active = fields.Boolean(default=True)

    _code_company_uniq = models.Constraint(
        "UNIQUE(code, company_id)",
        "The reference standard ID must be unique per company.",
    )

    @api.depends("valid_until")
    def _compute_is_valid(self) -> None:
        """Flag standards whose traceability certificate is still in date."""
        today = fields.Date.context_today(self)
        for standard in self:
            standard.is_valid = bool(
                standard.valid_until and standard.valid_until >= today
            )

    @api.depends("record_ids")
    def _compute_record_count(self) -> None:
        """Count the calibration records that used each standard."""
        for standard in self:
            standard.record_count = len(standard.record_ids)

    @api.depends("code", "name")
    def _compute_display_name(self) -> None:
        """Show the standard ID together with its name."""
        for standard in self:
            standard.display_name = f"[{standard.code}] {standard.name}"

    def unlink(self) -> bool:
        """Forbid deletion of standards already cited by a calibration record."""
        for standard in self:
            if standard.record_ids:
                raise UserError(
                    self.env._(
                        "Reference standard %(code)s is cited by "
                        "%(count)s calibration record(s) and cannot be "
                        "deleted. Archive it instead.",
                        code=standard.code,
                        count=len(standard.record_ids),
                    )
                )
        return super().unlink()

    @api.model
    def _cron_refresh_validity(self) -> bool:
        """Recompute the stored validity flag of every active standard."""
        standards = self.search([])
        standards.invalidate_recordset(["is_valid"])
        standards._compute_is_valid()
        standards.flush_recordset(["is_valid"])
        return True
