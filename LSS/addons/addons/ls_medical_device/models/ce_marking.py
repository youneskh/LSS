# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""CE marking, declaration of conformity and certificate records.

Article 19 of Regulation (EU) 2017/745 requires the manufacturer to draw up an
EU declaration of conformity, and Article 20 governs the affixing of the CE
marking of conformity. Where the conformity assessment route involves a notified
body, the certificate issued by that body underpins the declaration.

One record holds the declaration of conformity for one device together with the
certificate that supports it, because the two share a validity period and are
withdrawn together in practice. Where a device carries several certificates,
one record is created per certificate.
"""

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError

from . import constants


class LsMdCeMarking(models.Model):
    """Declaration of conformity and supporting certificate for one device."""

    _name = "ls.md.ce_marking"
    _description = "CE Marking and Declaration of Conformity"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "device_id, issue_date desc, id desc"

    name = fields.Char(
        string="Reference",
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: self.env._("New"),
    )
    device_id = fields.Many2one(comodel_name="ls.md.device", required=True,
                                ondelete="cascade",
                                index=True,
                                tracking=True,)
    company_id = fields.Many2one(comodel_name="res.company", related="device_id.company_id",
                                 store=True,
                                 index=True,)
    state = fields.Selection(
        selection=constants.CE_MARKING_STATE_SELECTION,
        string="Status",
        default="draft",
        required=True,
        tracking=True,
        index=True,
        copy=False,
    )
    conformity_route = fields.Selection(
        selection=constants.CONFORMITY_ROUTE_SELECTION,
        string="Conformity Assessment Route",
        required=True,
        default="annex_ix",
        tracking=True,
        help=(
            "Route followed for the conformity assessment of the device. The "
            "applicable route is determined by the manufacturer and, where "
            "required, agreed with the notified body."
        ),
    )
    notified_body_id = fields.Many2one(comodel_name="ls.md.notified_body", ondelete="restrict",
                                       tracking=True,
                                       help="Notified body involved in the conformity assessment, where applicable.",)
    certificate_number = fields.Char(tracking=True,
                                     copy=False,
                                     help="Number of the certificate issued by the notified body.",)
    declaration_number = fields.Char(
        string="Declaration of Conformity Number",
        tracking=True,
        copy=False,
        help="Reference of the EU declaration of conformity drawn up under Article 19.",
    )
    declaration_date = fields.Date(tracking=True,
                                   copy=False,
                                   help="Date on which the EU declaration of conformity was drawn up.",)
    basic_udi_di = fields.Char(
        string="Basic UDI-DI",
        related="device_id.basic_udi_di",
        store=True,
        help=(
            "Basic UDI-DI of the device. The declaration of conformity refers "
            "to it as the key linking the device to its documentation."
        ),
    )
    issue_date = fields.Date(
        string="Certificate Issue Date",
        tracking=True,
        copy=False,
    )
    expiry_date = fields.Date(
        string="Certificate Expiry Date",
        tracking=True,
        copy=False,
        index=True,
    )
    days_to_expiry = fields.Integer(compute="_compute_expiry_status",
                                    help="Number of days remaining before the certificate expires.",)
    is_expired = fields.Boolean(
        string="Expired",
        compute="_compute_expiry_status",
        search="_search_is_expired",
        help="True when the expiry date has passed.",
    )
    ce_marking_affixed = fields.Boolean(tracking=True,
                                        help="The CE marking has been affixed in accordance with Article 20.",)
    ce_marking_date = fields.Date(copy=False)
    scope = fields.Text(help="Scope of the certificate, including the device variants covered.",)
    conditions = fields.Text(
        string="Conditions and Restrictions",
        help="Conditions or restrictions attached to the certificate.",
    )
    suspension_reason = fields.Text(
        string="Suspension or Withdrawal Reason",
        copy=False,
        tracking=True,
    )
    suspension_date = fields.Date(
        string="Suspension or Withdrawal Date", copy=False, tracking=True
    )
    surveillance_audit_due = fields.Date(
        string="Next Surveillance Audit Due",
        help="Planned date of the next surveillance activity of the notified body.",
    )
    notes = fields.Text()

    _certificate_number_unique = models.Constraint(
        "UNIQUE(certificate_number, company_id)",
        "The certificate number must be unique within a company.",
    )
    _validity_order = models.Constraint(
        "CHECK(expiry_date IS NULL OR issue_date IS NULL OR expiry_date >= issue_date)",
        "The certificate expiry date cannot precede its issue date.",
    )

    # ------------------------------------------------------------------
    # Compute and search methods
    # ------------------------------------------------------------------
    @api.depends("expiry_date")
    def _compute_expiry_status(self):
        """Derive the remaining validity of the certificate."""
        today = fields.Date.context_today(self)
        for record in self:
            if record.expiry_date:
                record.days_to_expiry = (record.expiry_date - today).days
                record.is_expired = record.expiry_date < today
            else:
                record.days_to_expiry = 0
                record.is_expired = False

    def _search_is_expired(self, operator, value):
        """Allow searching on the computed expiry flag."""
        today = fields.Date.context_today(self)
        if operator not in ("=", "!="):
            raise UserError(
                self.env._(
                    "The expired flag supports only the equality and "
                    "inequality operators."
                )
            )
        looking_for_expired = bool(value) if operator == "=" else not value
        if looking_for_expired:
            return [("expiry_date", "!=", False), ("expiry_date", "<", today)]
        return ["|", ("expiry_date", "=", False), ("expiry_date", ">=", today)]

    @api.depends("name", "certificate_number", "device_id")
    def _compute_display_name(self):
        """Show the certificate number when available."""
        for record in self:
            if record.certificate_number:
                record.display_name = (
                    f"{record.name or ''} - {record.certificate_number}".strip(" -")
                )
            else:
                record.display_name = record.name or ""

    # ------------------------------------------------------------------
    # Constraints
    # ------------------------------------------------------------------
    @api.constrains("conformity_route", "notified_body_id", "state")
    def _check_notified_body_required(self):
        """Require a notified body for routes that involve one.

        A draft may be saved without it; the notified body is required from
        the submission onwards. ``state`` is a trigger of the constraint so
        that the submission itself is checked.
        """
        for record in self:
            if (
                record.conformity_route != "self_declaration"
                and record.state in ("submitted", "issued", "valid")
                and not record.notified_body_id
            ):
                raise ValidationError(
                    self.env._(
                        "Record '%(name)s' follows a conformity assessment "
                        "route that involves a notified body, so a notified "
                        "body must be selected.",
                        name=record.name or "",
                    )
                )

    @api.constrains("state", "certificate_number", "issue_date")
    def _check_issued_certificate_details(self):
        """Require certificate details once the certificate is issued."""
        for record in self:
            if record.state in ("issued", "valid") and (
                record.conformity_route != "self_declaration"
            ):
                if not record.certificate_number:
                    raise ValidationError(
                        self.env._(
                            "Record the certificate number of '%(name)s' "
                            "before marking it issued.",
                            name=record.name or "",
                        )
                    )
                if not record.issue_date:
                    raise ValidationError(
                        self.env._(
                            "Record the certificate issue date of '%(name)s' "
                            "before marking it issued.",
                            name=record.name or "",
                        )
                    )

    @api.constrains("ce_marking_affixed", "ce_marking_date")
    def _check_ce_marking_date(self):
        """Require a date whenever the CE marking is declared affixed."""
        for record in self:
            if record.ce_marking_affixed and not record.ce_marking_date:
                raise ValidationError(
                    self.env._(
                        "Record the date on which the CE marking was affixed "
                        "for '%(name)s'.",
                        name=record.name or "",
                    )
                )

    # ------------------------------------------------------------------
    # ORM overrides
    # ------------------------------------------------------------------
    @api.model_create_multi
    def create(self, vals_list):
        """Allocate the record reference from the dedicated sequence."""
        placeholder = self.env._("New")
        for vals in vals_list:
            if not vals.get("name") or vals["name"] == placeholder:
                vals["name"] = self.env["ir.sequence"].next_by_code(
                    "ls.md.ce_marking"
                ) or self.env._("CE/UNSEQUENCED")
        return super().create(vals_list)

    def write(self, vals):
        """Freeze the certificate identity once it has been issued."""
        protected = {
            "certificate_number",
            "issue_date",
            "notified_body_id",
            "conformity_route",
            "device_id",
        }
        if protected.intersection(vals):
            for record in self:
                if record.state in ("issued", "valid", "withdrawn", "expired"):
                    raise UserError(
                        self.env._(
                            "Certificate record '%(name)s' has been issued and "
                            "its identifying data can no longer be modified.",
                            name=record.name or "",
                        )
                    )
        return super().write(vals)

    @api.ondelete(at_uninstall=False)
    def _ls_unlink_check_ls_md_ce_marking(self):
        """Prevent deletion of records that left the draft status."""
        for record in self:
            if record.state != "draft":
                raise UserError(
                    self.env._(
                        "Certificate record '%(name)s' can no longer be "
                        "deleted.",
                        name=record.name or "",
                    )
                )

    def copy_data(self, default=None):
        """Reset identifiers and status when duplicating a certificate record."""
        default = dict(default or {})
        default.setdefault("name", self.env._("New"))
        default.setdefault("state", "draft")
        default.setdefault("certificate_number", False)
        default.setdefault("declaration_number", False)
        default.setdefault("issue_date", False)
        default.setdefault("expiry_date", False)
        return super().copy_data(default=default)

    # ------------------------------------------------------------------
    # Business methods
    # ------------------------------------------------------------------
    def _check_regulatory_authority(self):
        """Raise unless the current user holds regulatory authority."""
        if not (
            self.env.user.has_group(constants.GROUP_REGULATORY)
            or self.env.user.has_group(constants.GROUP_MANAGER)
        ):
            raise UserError(
                self.env._(
                    "Managing certificate status requires the Medical Devices "
                    "Regulatory Affairs or Manager access level."
                )
            )

    def action_submit(self):
        """Record submission of the application to the notified body."""
        self._check_regulatory_authority()
        for record in self:
            if record.state != "draft":
                raise UserError(
                    self.env._(
                        "Only a draft certificate record can be submitted."
                    )
                )
            record.state = "submitted"
        return True

    def action_mark_issued(self):
        """Record issuance of the certificate."""
        self._check_regulatory_authority()
        for record in self:
            if record.state not in ("draft", "submitted"):
                raise UserError(
                    self.env._(
                        "Only a draft or submitted certificate record can be "
                        "marked issued."
                    )
                )
            record.state = "issued"
        return True

    def action_activate(self):
        """Move an issued certificate into the valid status."""
        self._check_regulatory_authority()
        today = fields.Date.context_today(self)
        for record in self:
            if record.state != "issued":
                raise UserError(
                    self.env._(
                        "Only an issued certificate record can be activated."
                    )
                )
            if record.expiry_date and record.expiry_date < today:
                raise UserError(
                    self.env._(
                        "Certificate '%(name)s' expired on %(expiry)s and "
                        "cannot be activated.",
                        name=record.name or "",
                        expiry=record.expiry_date,
                    )
                )
            record.state = "valid"
        return True

    def action_suspend(self):
        """Suspend a valid certificate."""
        self._check_regulatory_authority()
        today = fields.Date.context_today(self)
        for record in self:
            if record.state != "valid":
                raise UserError(
                    self.env._("Only a valid certificate can be suspended.")
                )
            if not record.suspension_reason:
                raise UserError(
                    self.env._(
                        "Record the suspension reason for certificate "
                        "'%(name)s'.",
                        name=record.name or "",
                    )
                )
            record.write({"state": "suspended", "suspension_date": today})
        return True

    def action_withdraw(self):
        """Withdraw a certificate."""
        self._check_regulatory_authority()
        today = fields.Date.context_today(self)
        for record in self:
            if record.state not in ("issued", "valid", "suspended"):
                raise UserError(
                    self.env._(
                        "Only an issued, valid or suspended certificate can "
                        "be withdrawn."
                    )
                )
            if not record.suspension_reason:
                raise UserError(
                    self.env._(
                        "Record the withdrawal reason for certificate "
                        "'%(name)s'.",
                        name=record.name or "",
                    )
                )
            record.write({"state": "withdrawn", "suspension_date": today})
        return True

    @api.model
    def _cron_expire_certificates(self):
        """Move certificates past their expiry date into the expired status.

        The job only transitions records that are in the issued or valid
        status, so that a suspended or withdrawn certificate keeps the status
        that records the reason for its removal.
        """
        today = fields.Date.context_today(self)
        expired = self.search(
            [
                ("state", "in", ("issued", "valid")),
                ("expiry_date", "!=", False),
                ("expiry_date", "<", today),
            ]
        )
        for record in expired:
            record.state = "expired"
            record.message_post(
                body=self.env._(
                    "Certificate marked expired: the expiry date %(expiry)s "
                    "has passed.",
                    expiry=record.expiry_date,
                )
            )
        return len(expired)
