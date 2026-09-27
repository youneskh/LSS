# Copyright 2026 Life Sciences Suite
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Wizard extending the target closure date of a deviation."""

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class LsDeviationDueDateWizard(models.TransientModel):
    """Extend the target closure date against a documented justification.

    Extending a closure target without recording why is a common inspection
    finding. Routing every change through this wizard forces the
    justification and writes it to the chatter of the deviation.
    """

    _name = "ls.deviation.due.date.wizard"
    _description = "Extend Deviation Target Closure Date Wizard"

    deviation_id = fields.Many2one(
        comodel_name="ls.deviation",
        required=True,
        ondelete="cascade",
    )
    current_due_date = fields.Date(
        related="deviation_id.due_date",
        string="Current Target Closure Date",
        readonly=True,
    )
    new_due_date = fields.Date(required=True)
    justification = fields.Text(required=True)

    @api.model
    def default_get(self, fields_list):
        """Pre-fill the proposed date with the current target."""
        defaults = super().default_get(fields_list)
        deviation_id = defaults.get("deviation_id") or self.env.context.get(
            "default_deviation_id"
        )
        if deviation_id and "new_due_date" in fields_list:
            deviation = self.env["ls.deviation"].browse(deviation_id)
            defaults.setdefault("new_due_date", deviation.due_date)
        return defaults

    def action_confirm(self):
        """Apply the new target closure date and log the justification."""
        self.ensure_one()
        deviation = self.deviation_id
        if deviation.state in ("closed", "cancelled"):
            raise UserError(
                _(
                    "The target closure date of a closed or cancelled "
                    "deviation cannot be changed."
                )
            )
        if deviation.due_date and self.new_due_date <= deviation.due_date:
            raise UserError(
                _(
                    "The new target closure date must be later than the "
                    "current one (%(current)s).",
                    current=deviation.due_date,
                )
            )
        previous = deviation.due_date
        deviation.due_date = self.new_due_date
        deviation.message_post(
            body=_(
                "Target closure date extended from %(previous)s to "
                "%(new)s. Justification: %(justification)s",
                previous=previous or _("not set"),
                new=self.new_due_date,
                justification=self.justification,
            )
        )
        return {"type": "ir.actions.act_window_close"}
