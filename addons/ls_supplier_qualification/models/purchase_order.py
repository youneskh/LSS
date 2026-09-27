# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Purchase order control against the supplier qualification status."""
from odoo import _, api, fields, models
from odoo.exceptions import UserError


class PurchaseOrder(models.Model):
    """Verify the supplier qualification when a purchase order is confirmed."""

    _inherit = "purchase.order"

    ls_qualification_id = fields.Many2one(
        related="partner_id.ls_qualification_id",
        string="Supplier Qualification Dossier",
    )
    ls_qualification_state = fields.Selection(
        related="partner_id.ls_qualification_state",
        string="Supplier Qualification Status",
    )
    ls_qualification_warning = fields.Text(
        compute="_compute_ls_qualification_warning",
        compute_sudo=True,
        string="Qualification Warning",
    )

    @api.depends(
        "partner_id.ls_qualification_state",
        "partner_id.ls_qualification_expiry_date",
        "order_line.product_id",
        "state",
    )
    def _compute_ls_qualification_warning(self):
        """Show the qualification issue on the order form, if any.

        The dossier is resolved in the company of the order, not in the
        company active in the user session.
        """
        for order in self:
            if not order.partner_id:
                order.ls_qualification_warning = False
                continue
            message = order._ls_partner_in_order_company(
            ).ls_get_qualification_blocking_message(
                products=order.order_line.mapped("product_id"),
            )
            order.ls_qualification_warning = message or False

    def _ls_partner_in_order_company(self):
        """Return the supplier evaluated in the company of the order.

        The qualification dossiers are readable by the qualification roles
        only, while any purchase user confirms orders; the status is therefore
        read with superuser rights, restricted to this supplier and company.

        :return: the ``res.partner`` of the order, in the order company.
        :rtype: odoo.models.Model
        """
        self.ensure_one()
        return self.partner_id.sudo().with_company(self.company_id)

    def _ls_check_supplier_qualification(self):
        """Apply the company control policy to the orders of the recordset.

        The behaviour depends on ``res.company.ls_po_control_level``:

        * ``none`` - no verification;
        * ``warn`` - the issue is posted in the order chatter;
        * ``block`` - the confirmation is refused.

        :raise UserError: when the policy is ``block`` and at least one order
            of the recordset is not compliant.
        """
        blocking = []
        for order in self:
            level = order.company_id.ls_po_control_level
            if level == "none":
                continue
            message = order._ls_partner_in_order_company(
            ).ls_get_qualification_blocking_message(
                products=order.order_line.mapped("product_id"),
            )
            if not message:
                continue
            if level == "warn":
                order.message_post(body=_(
                    "Supplier qualification warning: %s", message
                ))
            else:
                blocking.append("%s: %s" % (order.name, message))
        if blocking:
            raise UserError(
                _("The following purchase orders cannot be confirmed because "
                  "of the supplier qualification status:\n- %s",
                  "\n- ".join(blocking))
            )

    def button_confirm(self):
        """Run the qualification control before the standard confirmation."""
        self._ls_check_supplier_qualification()
        return super().button_confirm()
