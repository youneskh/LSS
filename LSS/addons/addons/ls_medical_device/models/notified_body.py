# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Notified body register.

A notified body is a conformity assessment body designated by a Member State.
This module keeps a local register of the bodies an organisation works with so
that certificates and declarations of conformity can reference them.

No notified body designation data is shipped with this module. Designations
change over time and are published by the European Commission; asserting a
designation here would risk stating an out-of-date fact. The register is
populated by the implementing organisation.
"""

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class LsMdNotifiedBody(models.Model):
    """Conformity assessment body referenced by certificates."""

    _name = "ls.md.notified_body"
    _description = "Notified Body"
    _order = "name"

    name = fields.Char(required=True,
                       help="Registered name of the notified body.",)
    identification_number = fields.Char(required=True,
                                        help=(
                                            "Four-digit identification number assigned to the notified body. "
                                            "Recorded as free text so that identifiers of any length and "
                                            "format can be captured."),
                                        )
    partner_id = fields.Many2one(
        comodel_name="res.partner",
        string="Contact",
        ondelete="restrict",
        help="Contact record holding the address and communication details.",
    )
    country_id = fields.Many2one(comodel_name="res.country", ondelete="restrict",
                                 help="Country in which the notified body is established.",)
    designation_scope = fields.Text(help=(
            "Scope of the designation as recorded by the organisation, "
            "including the device codes covered."),
    )
    designation_reference = fields.Char(help=(
            "Reference of the public source from which the designation was "
            "confirmed, together with the date of confirmation."),
    )
    designation_verified_date = fields.Date(
        string="Designation Verified On",
        help=(
            "Date on which the designation was last confirmed against the "
            "public source recorded above."
        ),
    )
    active = fields.Boolean(default=True,
                            help="Uncheck to hide the notified body without deleting it.",)
    notes = fields.Text()
    ce_marking_ids = fields.One2many(
        comodel_name="ls.md.ce_marking",
        inverse_name="notified_body_id",
        string="Certificates",
        help="Certificates issued by this notified body.",
    )
    ce_marking_count = fields.Integer(
        string="Certificate Count",
        compute="_compute_ce_marking_count",
        help="Number of certificate records referencing this notified body.",
    )

    _identification_number_unique = models.Constraint(
        "UNIQUE(identification_number)",
        "The notified body identification number must be unique.",
    )

    @api.depends("ce_marking_ids")
    def _compute_ce_marking_count(self):
        """Count the certificates issued by each notified body."""
        grouped = self.env["ls.md.ce_marking"]._read_group(
            domain=[("notified_body_id", "in", self.ids)],
            groupby=["notified_body_id"],
            aggregates=["__count"],
        )
        counts = {body.id: count for body, count in grouped}
        for record in self:
            record.ce_marking_count = counts.get(record.id, 0)

    @api.depends("name", "identification_number")
    def _compute_display_name(self):
        """Prefix the notified body name with its identification number."""
        for record in self:
            if record.identification_number:
                record.display_name = (
                    f"{record.identification_number} - {record.name or ''}".strip(" -")
                )
            else:
                record.display_name = record.name or ""

    @api.constrains("designation_verified_date")
    def _check_designation_verified_date(self):
        """Reject a verification date in the future."""
        today = fields.Date.context_today(self)
        for record in self:
            if (
                record.designation_verified_date
                and record.designation_verified_date > today
            ):
                raise ValidationError(
                    self.env._(
                        "The designation verification date of notified body "
                        "'%(name)s' cannot be in the future.",
                        name=record.display_name,
                    )
                )

    def action_view_certificates(self):
        """Open the certificates issued by the selected notified body."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": self.env._("Certificates"),
            "res_model": "ls.md.ce_marking",
            "view_mode": "list,form",
            "domain": [("notified_body_id", "=", self.id)],
            "context": {"default_notified_body_id": self.id},
        }
