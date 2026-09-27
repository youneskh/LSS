# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Calibration certificates.

A certificate is the issued document evidencing a calibration. Internal
certificates are produced from the calibration record by the QWeb report
shipped with this module; external certificates are received from a service
provider and stored as an attachment.
"""

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError

from . import constants


class LsCalibrationCertificate(models.Model):
    """Document evidencing the result of a calibration."""

    _name = "ls.calibration.certificate"
    _description = "Calibration Certificate"
    _inherit = ["mail.thread"]
    _order = "issue_date desc, name desc, id desc"

    name = fields.Char(
        string="Certificate Number",
        required=True,
        copy=False,
        default=lambda self: constants.NEW_SEQUENCE_PLACEHOLDER,
        tracking=True,
        index=True,
        help="Certificate number. For an external certificate, enter the "
        "number issued by the calibration laboratory. Left as '/' an internal "
        "number is drawn from the certificate sequence.",
    )
    record_id = fields.Many2one(
        comodel_name="ls.calibration.record",
        string="Calibration Record",
        required=True,
        ondelete="restrict",
        tracking=True,
        index=True,
    )
    instrument_id = fields.Many2one(comodel_name="ls.calibration.instrument", related="record_id.instrument_id",
                                    store=True,
                                    readonly=True,
                                    index=True,)
    certificate_type = fields.Selection(selection=constants.CERTIFICATE_TYPE_SELECTION, required=True,
                                        default=constants.PROVIDER_INTERNAL,
                                        tracking=True,)
    issue_date = fields.Date(required=True,
                             default=fields.Date.context_today,
                             tracking=True,)
    issuer_name = fields.Char(
        string="Issued By",
        tracking=True,
        help="Name of the issuing laboratory or of the internal function that "
        "issued the certificate.",
    )
    issuer_partner_id = fields.Many2one(
        comodel_name="res.partner",
        string="Issuing Organisation",
    )
    accreditation_reference = fields.Char(help="Accreditation number quoted on the certificate. Recorded as "
                                          "supplied; this module performs no verification against any "
                                          "accreditation register.",)
    valid_until = fields.Date(related="record_id.next_due_date",
                              store=True,
                              readonly=True,)
    document = fields.Binary(string="Certificate Document", attachment=True)
    document_filename = fields.Char()
    overall_result = fields.Selection(
        related="record_id.overall_result",
        string="Result",
        store=True,
        readonly=True,
    )
    notes = fields.Text()
    company_id = fields.Many2one(comodel_name="res.company", related="record_id.company_id",
                                 store=True,
                                 index=True,
                                 readonly=True,)
    active = fields.Boolean(default=True)

    _name_company_uniq = models.Constraint(
        "UNIQUE(name, company_id)",
        "The certificate number must be unique per company.",
    )

    # ------------------------------------------------------------------
    # Compute
    # ------------------------------------------------------------------
    @api.depends("name", "instrument_id.code")
    def _compute_display_name(self) -> None:
        """Show the certificate number together with the instrument ID."""
        for certificate in self:
            certificate.display_name = (
                f"{certificate.name} - {certificate.instrument_id.code}"
            )

    # ------------------------------------------------------------------
    # Constraints
    # ------------------------------------------------------------------
    @api.constrains("record_id", "issue_date")
    def _check_issue_date(self) -> None:
        """A certificate cannot be issued before the calibration was performed."""
        for certificate in self:
            performed = certificate.record_id.performed_date
            if performed and certificate.issue_date < performed:
                raise ValidationError(
                    self.env._(
                        "Certificate %(certificate)s is dated before the "
                        "calibration was performed on %(performed)s.",
                        certificate=certificate.name,
                        performed=performed,
                    )
                )

    @api.constrains("certificate_type", "document")
    def _check_external_document(self) -> None:
        """An external certificate must carry the received document."""
        for certificate in self:
            if (
                certificate.certificate_type == constants.PROVIDER_EXTERNAL
                and not certificate.document
            ):
                raise ValidationError(
                    self.env._(
                        "External certificate %(certificate)s must carry the "
                        "document received from the issuing laboratory.",
                        certificate=certificate.name,
                    )
                )

    @api.constrains("record_id")
    def _check_record_approved(self) -> None:
        """A certificate may only be attached to an approved calibration."""
        for certificate in self:
            if certificate.record_id.state != constants.RECORD_STATE_APPROVED:
                raise ValidationError(
                    self.env._(
                        "Calibration record %(record)s is not approved. A "
                        "certificate can only be issued for an approved "
                        "calibration.",
                        record=certificate.record_id.name,
                    )
                )

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------
    @api.model_create_multi
    def create(self, vals_list: list) -> "LsCalibrationCertificate":
        """Draw the certificate number from the sequence when left as '/'."""
        for vals in vals_list:
            if vals.get("name", constants.NEW_SEQUENCE_PLACEHOLDER) in (
                False,
                constants.NEW_SEQUENCE_PLACEHOLDER,
            ):
                vals["name"] = self.env["ir.sequence"].next_by_code(
                    constants.SEQUENCE_CODE_CERTIFICATE
                ) or constants.NEW_SEQUENCE_PLACEHOLDER
        return super().create(vals_list)

    def unlink(self) -> bool:
        """Forbid deletion of issued certificates.

        A certificate is issued evidence. Superseded certificates are archived
        so that the audit trail of what was issued remains complete.
        """
        raise UserError(
            self.env._(
                "Calibration certificates cannot be deleted. Archive the "
                "certificate instead."
            )
        )

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------
    def action_print(self) -> dict:
        """Return the report action printing the internal certificate."""
        self.ensure_one()
        if self.certificate_type != constants.PROVIDER_INTERNAL:
            raise UserError(
                self.env._(
                    "Certificate %(certificate)s is external. Open the stored "
                    "document instead of printing an internal certificate.",
                    certificate=self.name,
                )
            )
        return self.env.ref(
            "ls_calibration.action_report_ls_calibration_certificate"
        ).report_action(self)
