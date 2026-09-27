# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Calibration certificate of the Life Sciences calibration module.

A certificate is the document issued at the end of a calibration. It can be
produced internally from a calibration record or received from an external
calibration service provider.
"""

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError


class LsCalibrationCertificate(models.Model):
    """Calibration certificate attached to an instrument."""

    _name = "ls.calibration.certificate"
    _description = "Calibration Certificate"
    _inherit = ["mail.thread"]
    _order = "issue_date desc, id desc"
    _check_company_auto = True

    name = fields.Char(
        string="Certificate Number",
        required=True,
        copy=False,
        default="/",
        tracking=True,
    )
    instrument_id = fields.Many2one(
        comodel_name="ls.calibration.instrument",
        required=True,
        index=True,
        ondelete="restrict",
        check_company=True,
        tracking=True,
    )
    record_id = fields.Many2one(
        comodel_name="ls.calibration.record",
        string="Calibration Record",
        index=True,
        ondelete="set null",
        check_company=True,
        help="Calibration record documented by this certificate. It is empty "
        "for a certificate received from an external provider without a "
        "corresponding internal record.",
    )
    company_id = fields.Many2one(
        comodel_name="res.company",
        related="instrument_id.company_id",
        store=True,
        index=True,
        readonly=True,
    )
    issuer_type = fields.Selection(
        selection=[
            ("internal", "Internal"),
            ("external", "External"),
        ],
        required=True,
        default="internal",
        tracking=True,
    )
    issuer_partner_id = fields.Many2one(
        comodel_name="res.partner",
        string="Issuing Laboratory",
    )
    accreditation_reference = fields.Char(
        help="Accreditation number of the issuing laboratory, for example its "
        "ISO/IEC 17025 accreditation reference.",
    )
    issue_date = fields.Date(
        required=True,
        default=fields.Date.context_today,
        tracking=True,
    )
    valid_until = fields.Date(tracking=True)
    certificate_file = fields.Binary(attachment=True,)
    certificate_filename = fields.Char()
    note = fields.Text()
    state = fields.Selection(
        selection=[
            ("draft", "Draft"),
            ("issued", "Issued"),
            ("superseded", "Superseded"),
        ],
        required=True,
        default="draft",
        tracking=True,
        copy=False,
    )

    _name_company_unique = models.Constraint(
        "UNIQUE(name, company_id)",
        "The certificate number must be unique per company.",
    )

    @api.depends("name", "instrument_id.display_name")
    def _compute_display_name(self):
        """Show the certificate number together with the instrument."""
        for certificate in self:
            instrument_name = certificate.instrument_id.display_name or ""
            certificate.display_name = (
                f"{certificate.name or ''} - {instrument_name}"
            )

    @api.constrains("issue_date", "valid_until")
    def _check_validity_dates(self):
        """Ensure the validity end date follows the issue date."""
        for certificate in self:
            if (
                certificate.valid_until
                and certificate.valid_until < certificate.issue_date
            ):
                raise ValidationError(
                    self.env._(
                        "The validity end date of certificate %s cannot be "
                        "earlier than its issue date.",
                        certificate.display_name,
                    )
                )

    @api.constrains("record_id", "instrument_id")
    def _check_record_instrument(self):
        """Ensure the record belongs to the instrument of the certificate."""
        for certificate in self:
            if (
                certificate.record_id
                and certificate.record_id.instrument_id
                != certificate.instrument_id
            ):
                raise ValidationError(
                    self.env._(
                        "The calibration record %(record)s does not belong to "
                        "the instrument %(instrument)s.",
                        record=certificate.record_id.display_name,
                        instrument=certificate.instrument_id.display_name,
                    )
                )

    @api.onchange("record_id")
    def _onchange_record_id(self):
        """Align the instrument with the selected calibration record."""
        if self.record_id:
            self.instrument_id = self.record_id.instrument_id

    @api.model_create_multi
    def create(self, vals_list):
        """Assign the certificate number from the dedicated sequence."""
        for vals in vals_list:
            if not vals.get("name") or vals["name"] == "/":
                vals["name"] = self.env["ir.sequence"].next_by_code(
                    "ls.calibration.certificate"
                ) or "/"
        return super().create(vals_list)

    def copy_data(self, default=None):
        """Reset the number and the state of a duplicated certificate."""
        vals_list = super().copy_data(default=default)
        for vals in vals_list:
            vals["name"] = "/"
            vals["state"] = "draft"
        return vals_list

    def write(self, vals):
        """Refuse the modification of the content of an issued certificate."""
        locked = self.filtered(
            lambda certificate: certificate.state in ("issued", "superseded")
        )
        if locked and set(vals) - {"state", "note", "message_follower_ids",
                                   "message_ids", "message_partner_ids",
                                   "message_main_attachment_id"}:
            raise UserError(
                self.env._(
                    "Certificate %s is issued and its content can no longer "
                    "be modified.",
                    locked[0].display_name,
                )
            )
        return super().write(vals)

    @api.ondelete(at_uninstall=False)
    def _ls_unlink_check_ls_calibration_certificate(self):
        """Refuse the deletion of a certificate that has been issued."""
        not_draft = self.filtered(
            lambda certificate: certificate.state != "draft"
        )
        if not_draft:
            raise UserError(
                self.env._(
                    "Certificate %s has been issued and cannot be deleted.",
                    not_draft[0].display_name,
                )
            )

    def action_issue(self):
        """Issue the certificate."""
        for certificate in self:
            if certificate.state != "draft":
                raise UserError(
                    self.env._(
                        "Only a draft certificate can be issued. Certificate "
                        "%(certificate)s is in state %(state)s.",
                        certificate=certificate.display_name,
                        state=certificate.state,
                    )
                )
            if (
                certificate.issuer_type == "external"
                and not certificate.certificate_file
            ):
                raise UserError(
                    self.env._(
                        "The document of the external certificate %s must be "
                        "attached before issuing it.",
                        certificate.display_name,
                    )
                )
        self.write({"state": "issued"})
        return True

    def action_supersede(self):
        """Mark the certificate as replaced by a more recent one."""
        for certificate in self:
            if certificate.state != "issued":
                raise UserError(
                    self.env._(
                        "Only an issued certificate can be superseded. "
                        "Certificate %(certificate)s is in state %(state)s.",
                        certificate=certificate.display_name,
                        state=certificate.state,
                    )
                )
        self.write({"state": "superseded"})
        return True
