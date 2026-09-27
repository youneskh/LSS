# Copyright 2026 Life Sciences Suite
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Append-only record of workflow transitions."""

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class LsDeviationStageLog(models.Model):
    """Append-only log of every state transition of a deviation.

    This log records who moved a deviation between states, when, and why. It
    is application-level append-only: :meth:`write` and :meth:`unlink` are
    blocked for every user.

    This model is not an electronic signature and does not by itself satisfy
    FDA 21 CFR Part 11. It records the transition only; it performs no
    identity re-verification at the point of signing and applies no
    cryptographic protection. Part 11 electronic signature and audit trail
    functionality is the scope of the separate ``ls_electronic_signature`` and
    ``ls_audit_trail`` modules described in the Functional Specification
    sections 7.14 and 7.15.
    """

    _name = "ls.deviation.stage.log"
    _description = "Deviation Transition Log"
    _order = "create_date desc, id desc"

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
    from_state = fields.Char(readonly=True)
    to_state = fields.Char(required=True, readonly=True)
    user_id = fields.Many2one(
        comodel_name="res.users",
        string="Performed By",
        required=True,
        readonly=True,
        ondelete="restrict",
    )
    reason = fields.Text(readonly=True)

    def write(self, vals):
        """Block modification of the transition log."""
        raise UserError(
            _("The deviation transition log is append-only and cannot be edited.")
        )

    @api.ondelete(at_uninstall=False)
    def _unlink_never(self):
        """Block deletion of the transition log."""
        raise UserError(
            _("The deviation transition log is append-only and cannot be deleted.")
        )
