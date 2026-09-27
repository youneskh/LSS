# Part of the Life Sciences Suite for Odoo 19 Community Edition.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Refuse to deliver lots named in an open recall."""

from odoo import models
from odoo.exceptions import UserError


class StockMoveLine(models.Model):
    """Block customer deliveries of lots under an open recall."""

    _inherit = "stock.move.line"

    def _action_done(self):
        """Verify the recall status of the lots before the stock moves.

        :raise UserError: when a lot sent to a customer location is under
            an open recall.
        """
        self._ls_recall_check_open_recall()
        return super()._action_done()

    def _ls_recall_check_open_recall(self):
        """Refuse customer deliveries of lots under an open recall.

        The lot indicator ``ls_recall_open`` is computed with superuser
        rights and ignores rehearsals and closed or cancelled recalls.

        :raise UserError: when at least one such lot is being delivered.
        """
        lots = self.filtered(
            lambda line: line.lot_id and line.location_dest_id.usage == "customer"
        ).lot_id
        recalled = lots.filtered("ls_recall_open")
        if not recalled:
            return
        raise UserError(
            self.env._(
                "The following lots are under an open recall and cannot be "
                "delivered: %(lots)s.",
                lots=", ".join(recalled.mapped("display_name")),
            )
        )
