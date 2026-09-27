# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Quality assurance decision to release or reject a batch."""

import hashlib

from odoo import api, fields, models
from odoo.exceptions import UserError

from ..constants import (
    HASH_ALGORITHM,
    HASH_FIELD_SEPARATOR,
    RELEASE_CHECKLIST,
    RELEASE_CHECKLIST_FIELDS,
    RELEASE_DECISIONS,
    RELEASE_IMMUTABLE_FIELDS,
)


class LsPharmaBatchRelease(models.Model):
    """The recorded decision of the quality unit on a batch.

    21 CFR 211.192 requires that all drug product production and control
    records, including those for packaging and labelling, be reviewed and
    approved by the quality control unit before a batch is released or
    distributed.  21 CFR 211.165 requires that acceptance criteria be
    adequate to support the release of the product for distribution.

    The decision is append only.  Once it has been recorded, the decision
    fields and the checklist can no longer be written, and the record cannot
    be deleted.  A digest over the canonical representation of the decision is
    stored so that a later alteration made outside the application, for
    example directly in the database, can be detected.

    What this model is not
    ----------------------
    The integrity digest is **not** an electronic signature within the
    meaning of 21 CFR Part 11.  It carries no signature manifestation, no
    re-authentication of the signer at the moment of signing and no link
    between a signature and a signer that could not be transferred.  Where
    electronic signatures are required, the ``ls_electronic_signature``
    module of the Life Sciences Suite provides them and this model is
    designed to be extended to reference such a signature.
    """

    _name = "ls.pharma.batch.release"
    _description = "Batch Release Decision"
    _inherit = ["mail.thread"]
    _order = "decision_date desc, id desc"

    _name_company_uniq = models.Constraint(
        "UNIQUE(name, company_id)",
        "The release decision reference must be unique per company.",
    )

    name = fields.Char(
        string="Decision Reference",
        required=True,
        copy=False,
        readonly=True,
        index=True,
        default=lambda self: self.env._("New"),
    )
    batch_id = fields.Many2one(comodel_name="ls.pharma.batch", required=True,
                               ondelete="restrict",
                               index=True,
                               tracking=True,)
    product_id = fields.Many2one(comodel_name="product.product", related="batch_id.product_id",
                                 store=True,)
    company_id = fields.Many2one(comodel_name="res.company", related="batch_id.company_id",
                                 store=True,
                                 index=True,)
    decision = fields.Selection(selection=RELEASE_DECISIONS, required=True,
                                tracking=True,)
    decision_date = fields.Datetime(required=True,
                                    default=fields.Datetime.now,
                                    tracking=True,)
    decided_by_user_id = fields.Many2one(
        comodel_name="res.users",
        string="Decided By",
        required=True,
        default=lambda self: self.env.user,
        tracking=True,
    )
    statement = fields.Text(
        string="Decision Statement",
        required=True,
        help=(
            "Written statement supporting the decision. It is retained "
            "verbatim in the release certificate."
        ),
    )

    # ------------------------------------------------------------------
    # Checklist -- each entry maps to a specific regulatory provision, see
    # RELEASE_CHECKLIST in constants.py
    # ------------------------------------------------------------------
    check_record_reviewed = fields.Boolean(
        string="Batch Records Reviewed and Approved"
    )
    check_discrepancies_closed = fields.Boolean(
        string="Discrepancies Investigated and Closed"
    )
    check_yield_within_limits = fields.Boolean(string="Yield Within Limits")
    check_components_verified = fields.Boolean(
        string="Component Charge-In Verified by a Second Person"
    )
    check_qc_conform = fields.Boolean(string="Laboratory Results Conform")
    check_labeling_reconciled = fields.Boolean(string="Labelling Reconciled")
    check_reserve_samples = fields.Boolean(string="Reserve Samples Retained")
    check_stability_programme = fields.Boolean(
        string="Covered by the Stability Programme"
    )
    checklist_complete = fields.Boolean(compute="_compute_checklist_complete",
                                        store=True,)
    integrity_hash = fields.Char(
        string="Integrity Digest",
        readonly=True,
        copy=False,
        help=(
            "Digest computed over the canonical representation of this "
            "decision. It makes an alteration made outside the application "
            "detectable. It is not an electronic signature."
        ),
    )
    integrity_verified = fields.Boolean(
        string="Digest Verified",
        compute="_compute_integrity_verified",
        help="Recomputes the digest and compares it with the stored value.",
    )

    # ------------------------------------------------------------------
    # Computed fields
    # ------------------------------------------------------------------
    @api.depends(*RELEASE_CHECKLIST_FIELDS)
    def _compute_checklist_complete(self):
        """Set when every entry of the release checklist has been confirmed."""
        for release in self:
            release.checklist_complete = all(
                release[field_name] for field_name in RELEASE_CHECKLIST_FIELDS
            )

    @api.depends(
        "name",
        "batch_id",
        "decision",
        "decision_date",
        "decided_by_user_id",
        "statement",
        "integrity_hash",
        *RELEASE_CHECKLIST_FIELDS,
    )
    def _compute_integrity_verified(self):
        """Recompute the digest and compare it with the stored value."""
        for release in self:
            if not release.integrity_hash:
                release.integrity_verified = False
            else:
                release.integrity_verified = (
                    release._build_integrity_hash() == release.integrity_hash
                )

    @api.depends("name", "batch_id", "decision")
    def _compute_display_name(self):
        """Show the decision reference together with the batch reference."""
        for release in self:
            if release.batch_id:
                release.display_name = "%s - %s" % (
                    release.name,
                    release.batch_id.name,
                )
            else:
                release.display_name = release.name or ""

    # ------------------------------------------------------------------
    # Reporting helpers
    # ------------------------------------------------------------------
    def get_checklist_report_lines(self):
        """Return the release checklist as printable lines.

        The lines are derived from ``RELEASE_CHECKLIST`` in ``constants.py``,
        which is the single place where a checklist entry is bound to the
        regulatory provision that it supports.  Deriving the printed
        certificate from that same list keeps the certificate and the model
        from drifting apart.

        :returns: one dictionary per checklist entry, each carrying the keys
            ``label``, ``reference`` and ``confirmed``.
        :rtype: list of dict
        """
        self.ensure_one()
        return [
            {
                "label": label,
                "reference": reference,
                "confirmed": bool(self[field_name]),
            }
            for field_name, label, reference in RELEASE_CHECKLIST
        ]

    # ------------------------------------------------------------------
    # Integrity digest
    # ------------------------------------------------------------------
    def _integrity_payload(self):
        """Return the ordered list of values covered by the integrity digest.

        The order of the values is fixed by this method and must never be
        changed for an existing installation, because doing so would
        invalidate every previously stored digest.

        :rtype: list of str
        """
        self.ensure_one()
        payload = [
            self.name or "",
            str(self.batch_id.id or 0),
            self.batch_id.name or "",
            self.decision or "",
            fields.Datetime.to_string(self.decision_date) or "",
            str(self.decided_by_user_id.id or 0),
            self.decided_by_user_id.login or "",
            self.statement or "",
        ]
        payload.extend(
            "1" if self[field_name] else "0"
            for field_name in RELEASE_CHECKLIST_FIELDS
        )
        return payload

    def _build_integrity_hash(self):
        """Return the digest of the canonical representation of the decision.

        :rtype: str
        """
        self.ensure_one()
        canonical = HASH_FIELD_SEPARATOR.join(self._integrity_payload())
        digest = hashlib.new(HASH_ALGORITHM)
        digest.update(canonical.encode("utf-8"))
        return digest.hexdigest()

    def action_verify_integrity(self):
        """Verify the digest and report the outcome in the chatter.

        :returns: ``True`` when every selected decision is intact.
        :rtype: bool
        """
        intact = True
        for release in self:
            recomputed = release._build_integrity_hash()
            if recomputed == release.integrity_hash:
                release.message_post(
                    body=self.env._(
                        "Integrity verification passed. The stored digest "
                        "matches the current content of the decision."
                    )
                )
            else:
                intact = False
                release.message_post(
                    body=self.env._(
                        "Integrity verification failed. The stored digest "
                        "does not match the current content of the decision. "
                        "The record has been altered outside the application."
                    )
                )
        return intact

    # ------------------------------------------------------------------
    # Overrides
    # ------------------------------------------------------------------
    @api.model_create_multi
    def create(self, vals_list):
        """Assign the reference, enforce the guards and stamp the digest."""
        for vals in vals_list:
            if not vals.get("name") or vals["name"] == self.env._("New"):
                sequence = self.env["ir.sequence"].next_by_code(
                    "ls.pharma.batch.release"
                )
                vals["name"] = sequence or self.env._("New")
        releases = super().create(vals_list)
        for release in releases:
            release._check_release_preconditions()
            # The digest is stamped through the parent ``write``: the
            # override below refuses any change to an immutable field,
            # including this first stamping.
            super(LsPharmaBatchRelease, release).write(
                {"integrity_hash": release._build_integrity_hash()}
            )
        return releases

    def write(self, vals):
        """Refuse to modify a decision that has already been recorded."""
        touched = set(RELEASE_IMMUTABLE_FIELDS).intersection(vals)
        if touched:
            raise UserError(
                self.env._(
                    "A batch release decision is an append-only record. The "
                    "fields %(fields)s can never be modified. Record a new "
                    "decision instead.",
                    fields=", ".join(sorted(touched)),
                )
            )
        return super().write(vals)

    @api.ondelete(at_uninstall=False)
    def _ls_unlink_check_ls_pharma_batch_release(self):
        """Refuse to delete a recorded decision."""
        raise UserError(
            self.env._(
                "A batch release decision cannot be deleted. It is the "
                "evidence that the quality unit reviewed and approved the "
                "batch production and control records before release, as "
                "required by 21 CFR 211.192."
            )
        )

    def copy_data(self, default=None):
        """Refuse to duplicate a recorded decision."""
        raise UserError(
            self.env._("A batch release decision cannot be duplicated.")
        )

    # ------------------------------------------------------------------
    # Business rules
    # ------------------------------------------------------------------
    def _check_release_preconditions(self):
        """Verify the conditions that must hold before a decision is recorded.

        :raises UserError: when a precondition is not met.
        """
        self.ensure_one()
        batch = self.batch_id
        if batch.state != "under_review":
            raise UserError(
                self.env._(
                    "Batch %(name)s is in state %(state)s. A release decision "
                    "may only be recorded while the batch is under quality "
                    "assurance review.",
                    name=batch.name,
                    state=batch.state,
                )
            )
        if batch.release_id:
            raise UserError(
                self.env._(
                    "Batch %(name)s already carries the release decision "
                    "%(decision)s.",
                    name=batch.name,
                    decision=batch.release_id.name,
                )
            )
        if (
            batch.user_manufactured_id
            and batch.user_manufactured_id.id == self.decided_by_user_id.id
        ):
            raise UserError(
                self.env._(
                    "Batch %(name)s was manufactured by %(user)s, who cannot "
                    "also take the release decision. The quality unit is "
                    "independent of production.",
                    name=batch.name,
                    user=batch.user_manufactured_id.display_name,
                )
            )
        if self.decision == "released":
            self._check_release_gate()

    def _check_release_gate(self):
        """Verify the conditions specific to a positive release decision.

        :raises UserError: when the batch may not be released.
        """
        self.ensure_one()
        batch = self.batch_id
        if not self.checklist_complete:
            missing = [
                label
                for field_name, label, _reference in RELEASE_CHECKLIST
                if not self[field_name]
            ]
            raise UserError(
                self.env._(
                    "Batch %(name)s cannot be released because the following "
                    "checks have not been confirmed: %(missing)s.",
                    name=batch.name,
                    missing="; ".join(missing),
                )
            )
        unapproved = batch.batch_record_ids.filtered(
            lambda record: record.state != "approved"
        )
        if unapproved:
            raise UserError(
                self.env._(
                    "Batch %(name)s cannot be released because %(count)s "
                    "batch record(s) have not been approved by the quality "
                    "unit, contrary to 21 CFR 211.192.",
                    name=batch.name,
                    count=len(unapproved),
                )
            )
        if (
            batch.yield_investigation_required
            and not batch.yield_investigation_reference
        ):
            raise UserError(
                self.env._(
                    "The yield of batch %(name)s falls outside its "
                    "established limits and no investigation reference has "
                    "been recorded. 21 CFR 211.192 requires that such a "
                    "discrepancy be thoroughly investigated before release.",
                    name=batch.name,
                )
            )
        if not batch.date_expiry:
            raise UserError(
                self.env._(
                    "Batch %(name)s cannot be released without an expiry "
                    "date.",
                    name=batch.name,
                )
            )

    def _apply_to_batch(self):
        """Propagate the decision to the batch.

        :returns: the batches that were updated.
        :rtype: recordset of ``ls.pharma.batch``
        """
        batches = self.env["ls.pharma.batch"]
        for release in self:
            target_state = (
                "released" if release.decision == "released" else "rejected"
            )
            release.batch_id.write(
                {"state": target_state, "release_id": release.id}
            )
            release.batch_id.message_post(
                body=self.env._(
                    "Release decision %(reference)s recorded by %(user)s: "
                    "%(decision)s.",
                    reference=release.name,
                    user=release.decided_by_user_id.display_name,
                    decision=release.decision,
                )
            )
            batches |= release.batch_id
        return batches

    def action_open_batch(self):
        """Open the batch that this decision applies to.

        :rtype: dict
        """
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": self.env._("Batch"),
            "res_model": "ls.pharma.batch",
            "res_id": self.batch_id.id,
            "view_mode": "form",
        }
