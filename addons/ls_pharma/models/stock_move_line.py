# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Refuse to deliver lots whose pharmaceutical batch is not released."""
from odoo import models
from odoo.exceptions import UserError

#: Batch states that allow the lot to leave the company. A cancelled batch
#: records a batch that was never made and does not hold the lot back.
LS_PHARMA_SHIPPABLE_BATCH_STATES = ("released", "cancelled")


class StockMoveLine(models.Model):
    """Block customer deliveries of lots without a batch release decision."""

    _inherit = "stock.move.line"

    def _action_done(self):
        """Verify the batch release status before the stock is moved.

        :raise UserError: when a lot sent to a customer location belongs to
            a batch that is not released.
        """
        self._ls_pharma_check_batch_release()
        return super()._action_done()

    def _ls_pharma_check_batch_release(self):
        """Refuse customer deliveries of lots linked to an unreleased batch.

        A lot is held back while at least one active ``ls.pharma.batch``
        names it and is neither released nor cancelled,
        which includes rejected batches and batches still under review
        (21 CFR 211.165(a), EU GMP Part I 1.4(xv): no batch is distributed
        before its release by the quality unit). The batches are read with
        superuser rights because warehouse users do not hold a
        pharmaceutical role; only the batch reference is disclosed.

        :raise UserError: when at least one such lot is being delivered.
        """
        lines = self.filtered(
            lambda line: line.lot_id and line.location_dest_id.usage == "customer"
        )
        if not lines:
            return
        batches = self.env["ls.pharma.batch"].sudo().search(
            [
                ("lot_id", "in", lines.lot_id.ids),
                ("state", "not in", LS_PHARMA_SHIPPABLE_BATCH_STATES),
            ]
        )
        if not batches:
            return
        states = dict(batches._fields["state"]._description_selection(self.env))
        details = [
            self.env._(
                "Lot %(lot)s: batch %(batch)s is in status '%(state)s'.",
                lot=batch.lot_id.display_name,
                batch=batch.name,
                state=states.get(batch.state, batch.state),
            )
            for batch in batches
        ]
        raise UserError(
            self.env._(
                "The following lots cannot be delivered because their batch "
                "has not been released by the quality unit:\n%(details)s",
                details="\n".join(details),
            )
        )
