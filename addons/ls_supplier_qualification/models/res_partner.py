# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Expose the qualification status of a supplier on its contact record."""
from odoo import _, api, fields, models
from odoo.exceptions import UserError

from .ls_supplier_qualification import APPROVED_STATES, STATE_SELECTION


class ResPartner(models.Model):
    """Add the supplier qualification status to the contact record."""

    _inherit = "res.partner"

    ls_qualification_ids = fields.One2many(
        comodel_name="ls.supplier.qualification",
        inverse_name="partner_id",
        string="Qualification Dossiers",
    )
    # These four fields are NOT stored on purpose. Their value depends on the
    # company of the reading user, and a stored computed field has a single
    # value shared by every company, which would leak the status of one
    # company into another. Searching is supported through the dedicated
    # search method below.
    # ``compute_sudo=True``: the status is displayed on the standard contact
    # form, which every internal user opens, while the dossiers themselves are
    # readable by the qualification roles only. Only the status is exposed.
    ls_qualification_id = fields.Many2one(
        comodel_name="ls.supplier.qualification",
        string="Current Dossier",
        compute="_compute_ls_qualification",
        compute_sudo=True,
        help="Live dossier of the supplier in the company of the current "
             "user.",
    )
    ls_qualification_state = fields.Selection(
        selection=STATE_SELECTION,
        string="Qualification Status",
        compute="_compute_ls_qualification",
        compute_sudo=True,
    )
    ls_qualification_expiry_date = fields.Date(
        string="Qualification Valid Until",
        compute="_compute_ls_qualification",
        compute_sudo=True,
    )
    ls_is_approved_supplier = fields.Boolean(
        string="Approved Supplier",
        compute="_compute_ls_qualification",
        compute_sudo=True,
        search="_search_ls_is_approved_supplier",
    )
    ls_qualification_count = fields.Integer(
        compute="_compute_ls_qualification_count",
        compute_sudo=True,
    )

    @api.depends(
        "ls_qualification_ids.state",
        "ls_qualification_ids.expiry_date",
        "ls_qualification_ids.active",
        "ls_qualification_ids.company_id",
    )
    @api.depends_context("company")
    def _compute_ls_qualification(self):
        """Expose the live dossier of the active company on the partner."""
        company = self.env.company
        for record in self:
            dossiers = record.ls_qualification_ids.filtered(
                lambda dossier: dossier.company_id == company
                and dossier.state != "disqualified"
            ).sorted(key=lambda dossier: dossier.id)
            dossier = dossiers[-1] if dossiers else False
            record.ls_qualification_id = dossier.id if dossier else False
            record.ls_qualification_state = dossier.state if dossier else False
            record.ls_qualification_expiry_date = (
                dossier.expiry_date if dossier else False
            )
            record.ls_is_approved_supplier = bool(
                dossier and dossier.state in APPROVED_STATES
            )

    def _search_ls_is_approved_supplier(self, operator, value):
        """Support searching partners on their approval status.

        :param str operator: ``=`` or ``!=``.
        :param bool value: value compared against.
        :return: a domain on ``res.partner``.
        :rtype: list
        :raise UserError: for an unsupported operator. Odoo 19 first calls
            the method with "in" / "not in" and, on a UserError, calls it
            again with "=" / "!=" for each value.
        """
        if operator not in ("=", "!="):
            raise UserError(
                _("Unsupported operator '%s' for the approved supplier "
                  "filter.", operator)
            )
        approved = self.env["ls.supplier.qualification"].sudo().search([
            ("company_id", "=", self.env.company.id),
            ("state", "in", list(APPROVED_STATES)),
        ]).mapped("partner_id")
        positive = bool(value) == (operator == "=")
        return [("id", "in" if positive else "not in", approved.ids)]

    @api.depends("ls_qualification_ids")
    def _compute_ls_qualification_count(self):
        """Count the dossiers of the partner across companies."""
        for record in self:
            record.ls_qualification_count = len(record.ls_qualification_ids)

    def action_view_ls_qualifications(self):
        """Open the qualification dossiers of this supplier."""
        self.ensure_one()
        action = self.env["ir.actions.act_window"]._for_xml_id(
            "ls_supplier_qualification.action_ls_supplier_qualification"
        )
        action["domain"] = [("partner_id", "=", self.id)]
        action["context"] = {"default_partner_id": self.id}
        return action

    def ls_get_qualification_blocking_message(self, products=None):
        """Return the qualification issue that blocks buying from this partner.

        :param products: optional ``product.product`` recordset whose presence
            in the qualified scope must be verified.
        :return: a translated message describing the issue, or an empty string
            when nothing blocks the purchase.
        :rtype: str
        """
        self.ensure_one()
        dossier = self.ls_qualification_id
        if not dossier:
            return _(
                "Supplier %s has no qualification dossier.",
                self.display_name,
            )
        if dossier.state not in APPROVED_STATES:
            return _(
                "Supplier %(partner)s is not approved (dossier %(dossier)s "
                "is in status '%(state)s').",
                partner=self.display_name,
                dossier=dossier.name,
                state=dict(STATE_SELECTION).get(dossier.state, dossier.state),
            )
        today = fields.Date.context_today(self)
        if dossier.expiry_date and dossier.expiry_date < today:
            return _(
                "The approval of supplier %(partner)s expired on %(date)s.",
                partner=self.display_name,
                date=dossier.expiry_date,
            )
        if products and self.env.company.ls_po_check_scope:
            qualified = dossier.material_ids.filtered(
                lambda material: material.state == "qualified"
                and not material.is_expired
            ).mapped("product_id")
            outside = products - qualified
            if outside:
                return _(
                    "The following products are outside the qualified scope "
                    "of supplier %(partner)s: %(products)s.",
                    partner=self.display_name,
                    products=", ".join(outside.mapped("display_name")),
                )
        return ""
