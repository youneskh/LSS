# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Cavity register of a moulding tool.

Multi-cavity moulds require cavity-level identification so that a defect can
be attributed to an individual cavity and that cavity blocked without taking
the whole tool out of service.
"""

from odoo import api, fields, models
from odoo.exceptions import ValidationError

from ..constants import CAVITY_STATES


class LsMpToolCavity(models.Model):
    """Individual cavity of a moulding tool."""

    _name = "ls.mp.tool.cavity"
    _description = "Medical Plastics Tool Cavity"
    _order = "tool_id, number"

    tool_id = fields.Many2one(comodel_name="ls.mp.tool", required=True,
                              ondelete="cascade",
                              index=True,)
    number = fields.Integer(string="Cavity Number", required=True)
    label = fields.Char(
        string="Cavity Marking",
        help="Marking engraved in the cavity, when it differs from the number.",
    )
    state = fields.Selection(
        selection=CAVITY_STATES,
        string="Status",
        default="active",
        required=True,
        copy=False,
    )
    blocked_reason = fields.Text(string="Blocking Reason", copy=False)
    blocked_date = fields.Datetime(string="Blocked On", readonly=True, copy=False)
    blocked_by_id = fields.Many2one(comodel_name="res.users", readonly=True,
                                    ondelete="restrict",
                                    copy=False,)
    company_id = fields.Many2one(comodel_name="res.company", related="tool_id.company_id",
                                 store=True,
                                 index=True,)

    _tool_number_unique = models.Constraint(
        "UNIQUE(tool_id, number)",
        "A cavity number must be unique within a tool.",
    )
    _number_positive = models.Constraint(
        "CHECK(number > 0)",
        "The cavity number must be strictly positive.",
    )

    @api.depends("tool_id.code", "number", "label")
    def _compute_display_name(self):
        """Render the cavity as ``TOOLCODE/NN``."""
        for cavity in self:
            tool_code = cavity.tool_id.code or ""
            marking = cavity.label or str(cavity.number)
            cavity.display_name = f"{tool_code}/{marking}" if tool_code else marking

    @api.constrains("state", "blocked_reason")
    def _check_blocked_reason(self):
        """A blocked or removed cavity must record why."""
        for cavity in self:
            if cavity.state in ("blocked", "removed") and not cavity.blocked_reason:
                raise ValidationError(
                    self.env._(
                        "Cavity %(cavity)s cannot be blocked or removed without a "
                        "recorded reason.",
                        cavity=cavity.display_name,
                    )
                )

    def action_block(self):
        """Block the cavity, stamping the acting user and timestamp."""
        for cavity in self:
            if cavity.state != "active":
                raise ValidationError(
                    self.env._(
                        "Cavity %(cavity)s is not active and cannot be blocked.",
                        cavity=cavity.display_name,
                    )
                )
        return self.write(
            {
                "state": "blocked",
                "blocked_date": fields.Datetime.now(),
                "blocked_by_id": self.env.user.id,
            }
        )

    def action_unblock(self):
        """Return a blocked cavity to active service."""
        for cavity in self:
            if cavity.state != "blocked":
                raise ValidationError(
                    self.env._(
                        "Cavity %(cavity)s is not blocked.",
                        cavity=cavity.display_name,
                    )
                )
        return self.write(
            {
                "state": "active",
                "blocked_reason": False,
                "blocked_date": False,
                "blocked_by_id": False,
            }
        )

    def action_remove(self):
        """Mark the cavity permanently removed from the tool."""
        for cavity in self:
            if cavity.state == "removed":
                raise ValidationError(
                    self.env._(
                        "Cavity %(cavity)s is already removed.",
                        cavity=cavity.display_name,
                    )
                )
        return self.write(
            {
                "state": "removed",
                "blocked_date": fields.Datetime.now(),
                "blocked_by_id": self.env.user.id,
            }
        )
