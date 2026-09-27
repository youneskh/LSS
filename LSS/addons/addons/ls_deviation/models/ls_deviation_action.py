# Copyright 2026 Life Sciences Suite
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Immediate, containment and correction actions attached to a deviation."""

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

ACTION_TYPE_SELECTION = [
    ("immediate", "Immediate Action"),
    ("containment", "Containment Action"),
    ("correction", "Correction"),
]

ACTION_STATE_SELECTION = [
    ("todo", "To Do"),
    ("done", "Done"),
    ("cancelled", "Cancelled"),
]


class LsDeviationAction(models.Model):
    """An action taken to contain or correct the immediate effect.

    These are distinct from corrective and preventive actions, which address
    root cause and are managed as a CAPA.
    """

    _name = "ls.deviation.action"
    _description = "Deviation Immediate Action"
    _order = "deadline, id"

    deviation_id = fields.Many2one(
        comodel_name="ls.deviation",
        required=True,
        ondelete="cascade",
        index=True,
    )
    company_id = fields.Many2one(
        related="deviation_id.company_id",
        store=True,
        index=True,
    )
    name = fields.Char(string="Action", required=True)
    action_type = fields.Selection(
        selection=ACTION_TYPE_SELECTION,
        required=True,
        default="immediate",
    )
    description = fields.Text()
    responsible_id = fields.Many2one(comodel_name="res.users", required=True,
                                     ondelete="restrict",)
    deadline = fields.Date()
    date_done = fields.Datetime(readonly=True, copy=False)
    completion_evidence = fields.Text(
        help="Objective evidence that the action was performed.",
    )
    state = fields.Selection(
        selection=ACTION_STATE_SELECTION,
        required=True,
        default="todo",
    )

    @api.constrains("state", "completion_evidence")
    def _check_completion_evidence(self):
        """A completed action must record its objective evidence."""
        for record in self:
            if record.state == "done" and not (
                record.completion_evidence or ""
            ).strip():
                raise ValidationError(
                    _(
                        "Action '%(action)s' cannot be marked done without "
                        "completion evidence.",
                        action=record.name,
                    )
                )

    def action_done(self):
        """Mark the action as performed and stamp the completion date."""
        return self.write(
            {"state": "done", "date_done": fields.Datetime.now()}
        )

    def action_cancel(self):
        """Void the action without deleting it."""
        return self.write({"state": "cancelled"})
