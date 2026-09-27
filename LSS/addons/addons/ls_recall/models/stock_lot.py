# Part of the Life Sciences Suite for Odoo 19 Community Edition.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Extension of stock lots with their recall history.

Making the link visible from the lot answers the question an operator
actually asks: "is this lot affected by a recall?" The inverse of the
many2many declared on the recall is used, so no additional storage is
introduced.
"""

from odoo import api, fields, models

from .constants import EXECUTION_FINAL_STATES, REAL_ACTION_TYPES


class StockLot(models.Model):
    """Add recall visibility to lots and serial numbers."""

    _inherit = "stock.lot"

    ls_recall_execution_ids = fields.Many2many(
        comodel_name="ls.recall.execution",
        relation="ls_recall_execution_lot_rel",
        column1="lot_id",
        column2="execution_id",
        string="Recalls",
        help="Field actions in which this lot is named.",
    )
    ls_recall_count = fields.Integer(
        compute="_compute_ls_recall_state",
        compute_sudo=True,
        string="Recall Count",
    )
    ls_recall_open = fields.Boolean(
        compute="_compute_ls_recall_state",
        compute_sudo=True,
        string="Under Recall",
        help="Set while the lot is named in a field action that has not "
             "yet been closed or cancelled. Rehearsals are ignored.",
    )

    @api.depends(
        "ls_recall_execution_ids.state",
        "ls_recall_execution_ids.action_type",
    )
    def _compute_ls_recall_state(self):
        """Summarise the recall history of each lot.

        The executions are read through ``sudo`` (``compute_sudo=True``,
        so the relation itself is also read as superuser: reading it as
        the current user would raise an access error for users without a
        recall role, because the Many2many read checks the access rights
        on ``ls.recall.execution``). This is deliberate and
        is limited to two non-confidential attributes, the action type
        and the workflow state. A warehouse operator who holds no recall
        role must still be warned that a lot is under recall before
        shipping it; withholding that warning would be the greater risk.
        The smart button leading to the recall records themselves is
        restricted to the recall roles in the view.
        """
        for lot in self:
            real = lot.sudo().ls_recall_execution_ids.filtered(
                lambda e: e.action_type in REAL_ACTION_TYPES
            )
            lot.ls_recall_count = len(real)
            lot.ls_recall_open = bool(
                real.filtered(lambda e: e.state not in EXECUTION_FINAL_STATES)
            )

    def action_view_ls_recalls(self):
        """Open the field actions naming this lot."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": self.env._("Recalls"),
            "res_model": "ls.recall.execution",
            "view_mode": "list,form",
            "domain": [("id", "in", self.ls_recall_execution_ids.ids)],
        }
