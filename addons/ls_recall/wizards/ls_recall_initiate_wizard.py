# Part of the Life Sciences Suite for Odoo 19 Community Edition.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Wizard creating a recall from an approved plan.

The wizard exists so that a recall can be opened in one screen at the
moment the decision is taken, with the strategy defaults inherited from
the approved plan rather than retyped under time pressure.
"""

from odoo import api, fields, models
from odoo.exceptions import UserError

from ..models.constants import (
    ACTION_TYPE_SELECTION,
    CLASSIFICATION_HELP,
    CLASSIFICATION_SELECTION,
    DEPTH_SELECTION,
)


class LsRecallInitiateWizard(models.TransientModel):
    """Collect the decision and open the corresponding recall record."""

    _name = "ls.recall.initiate.wizard"
    _description = "Initiate Recall"

    company_id = fields.Many2one(
        comodel_name="res.company",
        required=True,
        default=lambda self: self.env.company,
    )
    plan_id = fields.Many2one(
        comodel_name="ls.recall.plan",
        string="Recall Plan",
        domain="[('state', '=', 'approved'), "
               "('company_id', '=', company_id)]",
    )
    action_type = fields.Selection(
        selection=ACTION_TYPE_SELECTION, required=True, default="recall"
    )
    product_id = fields.Many2one(comodel_name="product.product", required=True)
    lot_ids = fields.Many2many(
        comodel_name="stock.lot",
        string="Affected Lots",
        domain="[('product_id', '=', product_id)]",
    )
    classification = fields.Selection(
        selection=CLASSIFICATION_SELECTION,
        default="not_classified",
        required=True,
        help=CLASSIFICATION_HELP,
    )
    depth = fields.Selection(selection=DEPTH_SELECTION)
    reason = fields.Text(required=True)
    decision_date = fields.Datetime(
        required=True, default=fields.Datetime.now
    )
    target_completion_date = fields.Date()
    responsible_user_id = fields.Many2one(
        comodel_name="res.users",
        string="Recall Coordinator",
        required=True,
        default=lambda self: self.env.user,
    )
    trace_now = fields.Boolean(
        string="Trace distribution immediately",
        default=True,
        help="Scan completed stock movements for the selected lots as "
             "soon as the recall is created.",
    )

    @api.onchange("plan_id")
    def _onchange_plan_id(self):
        """Inherit the coordinator from the selected plan."""
        for wizard in self:
            if wizard.plan_id:
                wizard.responsible_user_id = (
                    wizard.plan_id.responsible_user_id
                )

    @api.onchange("product_id")
    def _onchange_product_id(self):
        """Drop lots that no longer match the selected product."""
        for wizard in self:
            wizard.lot_ids = wizard.lot_ids.filtered(
                lambda lot: lot.product_id == wizard.product_id
            )

    def action_create_recall(self):
        """Create the recall record and open it.

        :return: a window action on the created recall.
        :rtype: dict
        """
        self.ensure_one()
        if not self.lot_ids:
            raise UserError(
                self.env._(
                    "Select at least one lot before opening a recall."
                )
            )
        values = {
            "company_id": self.company_id.id,
            "plan_id": self.plan_id.id or False,
            "action_type": self.action_type,
            "product_id": self.product_id.id,
            "lot_ids": [(6, 0, self.lot_ids.ids)],
            "classification": self.classification,
            "depth": self.depth,
            "reason": self.reason,
            "decision_date": self.decision_date,
            "target_completion_date": self.target_completion_date,
            "responsible_user_id": self.responsible_user_id.id,
        }
        if self.plan_id:
            values["effectiveness_level"] = (
                self.plan_id.default_effectiveness_level
            )
        execution = self.env["ls.recall.execution"].create(values)
        if self.trace_now:
            execution.action_trace_distribution()
        return {
            "type": "ir.actions.act_window",
            "name": self.env._("Recall"),
            "res_model": "ls.recall.execution",
            "res_id": execution.id,
            "view_mode": "form",
            "target": "current",
        }
