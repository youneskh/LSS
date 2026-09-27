# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Wizard planning the revalidation of an item.

Revalidation reuses the test strategy of a previous protocol: the wizard copies
an existing protocol into a new draft version, keeping its test cases, and
links it to the master plan and the planned dates chosen by the user. The copy
is created in draft so that it goes through the normal review and approval
path before any execution.
"""

from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class LsValidationRevalidationWizard(models.TransientModel):
    """Transient model creating the protocol of the next validation cycle."""

    _name = "ls.validation.revalidation.wizard"
    _description = "Validation Revalidation Wizard"

    item_id = fields.Many2one(
        comodel_name="ls.validation.item",
        string="Validation Item",
        required=True,
    )
    source_protocol_id = fields.Many2one(
        comodel_name="ls.validation.protocol",
        string="Protocol to Reuse",
        required=True,
        domain="[('item_id', '=', item_id)]",
        help="The test cases of this protocol are copied into the new draft "
             "protocol.",
    )
    master_plan_id = fields.Many2one(comodel_name="ls.validation.master.plan", domain="[('state', '=', 'active')]",
                                     )
    new_title = fields.Char(string="New Protocol Title", required=True)
    planned_start_date = fields.Date(
        string="Planned Start",
        default=fields.Date.context_today,
        required=True,
    )
    planned_end_date = fields.Date(string="Planned End")

    @api.onchange("item_id")
    def _onchange_item_id(self):
        """Propose the latest protocol and a default title for the item."""
        for wizard in self:
            wizard.source_protocol_id = False
            if not wizard.item_id:
                continue
            protocol = self.env["ls.validation.protocol"].search(
                [
                    ("item_id", "=", wizard.item_id._origin.id),
                    ("state", "in", ("approved", "execution", "executed", "closed")),
                ],
                order="id desc",
                limit=1,
            )
            wizard.source_protocol_id = protocol
            wizard.new_title = _("Revalidation of %s") % wizard.item_id.display_name

    @api.onchange("source_protocol_id", "planned_start_date")
    def _onchange_source_protocol_id(self):
        """Propose an end date one month after the planned start."""
        for wizard in self:
            if wizard.planned_start_date and not wizard.planned_end_date:
                wizard.planned_end_date = (
                    wizard.planned_start_date + relativedelta(months=1)
                )

    def action_create_protocol(self):
        """Create the draft protocol of the next validation cycle.

        :return: a window action opening the newly created protocol.
        :rtype: dict
        """
        self.ensure_one()
        if self.source_protocol_id.item_id != self.item_id:
            raise UserError(
                _("The selected protocol does not belong to the chosen item.")
            )
        if not self.source_protocol_id.test_ids:
            raise UserError(
                _("The protocol to reuse has no test case to copy.")
            )
        new_protocol = self.source_protocol_id.copy(
            {
                "name": self.new_title,
                "reference": self.source_protocol_id.reference,
                "version": self.source_protocol_id.version + 1,
                "previous_version_id": self.source_protocol_id.id,
                "state": "draft",
                "master_plan_id": self.master_plan_id.id or False,
                "planned_start_date": self.planned_start_date,
                "planned_end_date": self.planned_end_date,
                "approver_id": False,
                "approval_date": False,
            }
        )
        new_protocol.message_post(
            body=_("Created by the revalidation wizard from %s.")
            % self.source_protocol_id.display_name
        )
        return {
            "type": "ir.actions.act_window",
            "name": _("Revalidation Protocol"),
            "res_model": "ls.validation.protocol",
            "res_id": new_protocol.id,
            "view_mode": "form",
        }
