# Part of the Life Sciences Suite. See LICENSE file for full copyright and licensing details.
"""Refuse to deliver lots held by an out-of-specification investigation."""
from odoo import models
from odoo.exceptions import UserError

#: Investigation states in which the lot is still under investigation.
LS_LAB_OPEN_OOS_STATES = ("open", "phase1", "phase1_done", "phase2", "concluded")

#: Dispositions that keep the lot out of distribution once recorded.
LS_LAB_HOLDING_DISPOSITIONS = ("reject", "quarantine_pending", "further_investigation")


class StockMoveLine(models.Model):
    """Block customer deliveries of lots under an OOS investigation."""

    _inherit = "stock.move.line"

    def _action_done(self):
        """Verify the laboratory status of the lots before the stock moves.

        :raise UserError: when a lot sent to a customer location is held by
            an out-of-specification or out-of-trend investigation.
        """
        self._ls_lab_check_oos_hold()
        return super()._action_done()

    def _ls_lab_check_oos_hold(self):
        """Refuse customer deliveries of lots held by an investigation.

        A lot is held while an investigation on one of its samples is not
        closed or cancelled, or when the recorded product disposition is
        "Reject", "Remain In Quarantine" or "Further Investigation Required"
        (a cancelled investigation never holds the lot). The investigations
        are read with superuser rights because warehouse users do not hold
        a laboratory role; only the investigation reference is disclosed.

        :raise UserError: when at least one such lot is being delivered.
        """
        lines = self.filtered(
            lambda line: line.lot_id and line.location_dest_id.usage == "customer"
        )
        if not lines:
            return
        investigations = self.env["ls.lab.oos"].sudo().search(
            [
                ("sample_id.lot_id", "in", lines.lot_id.ids),
                ("state", "!=", "cancelled"),
                "|",
                ("state", "in", LS_LAB_OPEN_OOS_STATES),
                ("product_disposition", "in", LS_LAB_HOLDING_DISPOSITIONS),
            ]
        )
        if not investigations:
            return
        details = [
            self.env._(
                "Lot %(lot)s: investigation %(investigation)s.",
                lot=investigation.sample_id.lot_id.display_name,
                investigation=investigation.display_name,
            )
            for investigation in investigations
        ]
        raise UserError(
            self.env._(
                "The following lots cannot be delivered because they are held "
                "by a laboratory investigation:\n%(details)s",
                details="\n".join(details),
            )
        )
