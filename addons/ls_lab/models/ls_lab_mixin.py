# Part of the Life Sciences Suite. See LICENSE file for full copyright and licensing details.
"""Shared behaviour for controlled Life Sciences laboratory records.

This module implements, once, the three behaviours that recur across the
controlled objects of :mod:`ls_lab`:

* immutability of approved records (business rules BRU-01, BRU-02, BRU-23);
* assignment of a document code from an ``ir.sequence`` at creation time;
* creation of a successor version that supersedes an approved predecessor.

Concrete models opt in by inheriting :class:`LsLabControlledMixin` and
declaring ``_CONTROLLED_FIELDS`` and ``_FROZEN_STATES``.
"""

from odoo import api, fields, models
from odoo.exceptions import UserError


class LsLabControlledMixin(models.AbstractModel):
    """Abstract behaviour for records that become immutable once approved.

    Concrete models must define:

    ``_CONTROLLED_FIELDS``
        Tuple of field names that may not change while the record sits in one
        of ``_FROZEN_STATES``. Extending modules may append to this tuple
        without modifying the guard itself.

    ``_FROZEN_STATES``
        Tuple of values of the ``state`` field during which the record is
        frozen.

    ``_SEQUENCE_CODE``
        External identifier of the ``ir.sequence`` used to populate the code
        field, or ``False`` when the model assigns no code.

    ``_SEQUENCE_FIELD``
        Name of the field the sequence value is written to.
    """

    _name = "ls.lab.controlled.mixin"
    _description = "Life Sciences Laboratory Controlled Record Mixin"

    _CONTROLLED_FIELDS = ()
    _FROZEN_STATES = ("approved",)
    _SEQUENCE_CODE = False
    _SEQUENCE_FIELD = "code"

    # ------------------------------------------------------------------
    # Sequence assignment
    # ------------------------------------------------------------------
    @api.model_create_multi
    def create(self, vals_list):
        """Assign the document code from the model's sequence when absent."""
        if self._SEQUENCE_CODE:
            field = self._SEQUENCE_FIELD
            for vals in vals_list:
                if not vals.get(field) or vals.get(field) == "New":
                    vals[field] = self.env["ir.sequence"].next_by_code(
                        self._SEQUENCE_CODE
                    ) or "New"
        return super().create(vals_list)

    # ------------------------------------------------------------------
    # Immutability guard
    # ------------------------------------------------------------------
    def write(self, vals):
        """Refuse changes to controlled fields while the record is frozen.

        The ``state`` field itself is never treated as controlled: state
        transitions are performed by the model's own action methods, which
        apply their own preconditions.
        """
        controlled = set(self._CONTROLLED_FIELDS) & set(vals)
        if controlled:
            frozen = self.filtered(lambda rec: rec.state in rec._FROZEN_STATES)
            if frozen:
                raise UserError(
                    self.env._(
                        "%(count)s record(s) are approved and cannot be modified.\n"
                        "Blocked field(s): %(fields)s.\n"
                        "Create a new version instead of editing an approved record.",
                        count=len(frozen),
                        fields=", ".join(sorted(controlled)),
                    )
                )
        return super().write(vals)

    @api.ondelete(at_uninstall=False)
    def _ls_unlink_check_ls_lab_controlled_mixin(self):
        """Refuse deletion of records that have left the draft state."""
        undeletable = self.filtered(lambda rec: rec.state != "draft")
        if undeletable:
            raise UserError(
                self.env._(
                    "Only draft records may be deleted. %(count)s record(s) have "
                    "left the draft state and must be made obsolete or cancelled "
                    "instead, so that the audit history is preserved.",
                    count=len(undeletable),
                )
            )

    # ------------------------------------------------------------------
    # Version succession
    # ------------------------------------------------------------------
    def _create_successor_version(self, extra_defaults=None):
        """Return a new draft record superseding ``self``.

        The predecessor is left untouched by this helper; the calling action
        is responsible for moving it to ``obsolete`` once the successor has
        been created, so that the two operations remain explicit.
        """
        self.ensure_one()
        defaults = {
            "version": self.version + 1,
            "state": "draft",
            "predecessor_id": self.id,
            "approved_by_id": False,
            "approval_date": False,
        }
        if self._SEQUENCE_CODE:
            defaults[self._SEQUENCE_FIELD] = self[self._SEQUENCE_FIELD]
        if extra_defaults:
            defaults.update(extra_defaults)
        successor = self.copy(defaults)
        self.sudo().write({"successor_id": successor.id})
        return successor

    def _assert_state(self, expected, action_label):
        """Raise a :class:`UserError` unless every record is in ``expected``."""
        expected = expected if isinstance(expected, (list, tuple, set)) else (expected,)
        wrong = self.filtered(lambda rec: rec.state not in expected)
        if wrong:
            raise UserError(
                self.env._(
                    "Action '%(action)s' is not available for record(s) %(records)s "
                    "in their current state.",
                    action=action_label,
                    records=", ".join(wrong.mapped("display_name")),
                )
            )


class LsLabSignedMixin(models.AbstractModel):
    """Records that can carry a signature-intent confirmation.

    IMPORTANT LIMITATION. This mixin records the identity of the signing user,
    a UTC timestamp and the declared meaning of the signature. It does **not**
    re-authenticate the user at the moment of signing, does not implement two
    distinct identification components, and does not cryptographically bind the
    signature to the record. FDA 21 CFR Part 11 compliance is **not** claimed.
    """

    _name = "ls.lab.signed.mixin"
    _description = "Life Sciences Laboratory Signature Intent Mixin"

    signature_user_id = fields.Many2one(
        comodel_name="res.users",
        string="Signed By",
        readonly=True,
        copy=False,
        help="User who confirmed signature intent. This is not a "
             "21 CFR Part 11 electronic signature.",
    )
    signature_date = fields.Datetime(readonly=True,
                                     copy=False,)
    signature_meaning = fields.Char(readonly=True,
                                    copy=False,
                                    help="Declared meaning of the signature intent, for example "
                                    "'Reviewed' or 'Approved'.",)

    def action_signature_apply(self, meaning):
        """Record signature intent and run the model's signed action.

        Concrete models override :meth:`_signature_target_action` to declare
        what the signature authorises.
        """
        self.ensure_one()
        self.sudo().write({
            "signature_user_id": self.env.user.id,
            "signature_date": fields.Datetime.now(),
            "signature_meaning": meaning,
        })
        return self._signature_target_action()

    def _signature_target_action(self):
        """Perform the action the signature authorises. Overridden downstream."""
        return True
