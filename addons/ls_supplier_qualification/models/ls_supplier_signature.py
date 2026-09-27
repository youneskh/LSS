# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Append-only signature log for supplier qualification decisions.

Scope statement
---------------
This model records *who* took a decision, *when*, *on which record*, with
*which stated meaning*, and it chains the entries with SHA-256 so that a
later modification of the chain is detectable.

It does **not** implement a full electronic signature solution. In
particular it does not re-authenticate the signer with a password or a second
factor at the moment of signing. Re-authentication is delegated to the
`ls_electronic_signature` module described in the Life Sciences Suite
functional specification; until that module is deployed, the organisation
must cover the identity-verification component of its signature procedure by
other means (documented procedure, session policy, or an equivalent
compensating control). See doc/02_regulatory_analysis.md.
"""
import hashlib
import json

from odoo import _, api, fields, models
from odoo.exceptions import UserError

SIGNATURE_MEANING_SELECTION = [
    ("authored", "Authored"),
    ("reviewed", "Reviewed"),
    ("approved", "Approved"),
    ("conditionally_approved", "Conditionally Approved"),
    ("rejected", "Rejected"),
    ("suspended", "Suspended"),
    ("reinstated", "Reinstated"),
    ("disqualified", "Disqualified"),
    ("verified", "Verified"),
]


class LsSupplierSignature(models.Model):
    """One append-only entry of the supplier qualification signature log."""

    _name = "ls.supplier.signature"
    _description = "Life Sciences Supplier Signature Log Entry"
    _order = "id desc"

    name = fields.Char(
        compute="_compute_name",
        store=True,
    )
    qualification_id = fields.Many2one(
        comodel_name="ls.supplier.qualification",
        ondelete="restrict",
        index=True,
        help="Dossier the signed record belongs to, used for grouping and "
             "for the dossier report.",
    )
    res_model = fields.Char(
        string="Signed Model",
        required=True,
        readonly=True,
        index=True,
    )
    res_id = fields.Integer(
        string="Signed Record ID",
        required=True,
        readonly=True,
        index=True,
    )
    signed_record_name = fields.Char(readonly=True)
    user_id = fields.Many2one(
        comodel_name="res.users",
        string="Signed By",
        required=True,
        readonly=True,
        index=True,
    )
    login_used = fields.Char(
        readonly=True,
        help="Login typed by the signer in the signature dialog and matched "
             "against the login of the connected user.",
    )
    signed_on = fields.Datetime(required=True, readonly=True)
    meaning = fields.Selection(
        selection=SIGNATURE_MEANING_SELECTION,
        required=True,
        readonly=True,
    )
    reason = fields.Text(readonly=True)
    payload = fields.Text(
        readonly=True,
        help="JSON snapshot of the signed values at the moment of signing.",
    )
    sequence_number = fields.Integer(required=True, readonly=True, index=True)
    previous_hash = fields.Char(readonly=True)
    record_hash = fields.Char(required=True, readonly=True)
    company_id = fields.Many2one(
        comodel_name="res.company",
        required=True,
        readonly=True,
        default=lambda self: self.env.company,
        index=True,
    )

    _sequence_company_uniq = models.Constraint(
        "UNIQUE(company_id, sequence_number)",
        "The signature sequence number must be unique per company.",
    )

    @api.depends("meaning", "signed_record_name", "sequence_number")
    def _compute_name(self):
        """Build a readable label for the log entry."""
        meanings = dict(
            self._fields["meaning"]._description_selection(self.env)
        )
        for record in self:
            record.name = "#%s %s - %s" % (
                record.sequence_number,
                meanings.get(record.meaning, record.meaning or ""),
                record.signed_record_name or "",
            )

    # ------------------------------------------------------------------
    # Immutability
    # ------------------------------------------------------------------
    def write(self, vals):
        """Reject any modification of an existing log entry."""
        raise UserError(
            _("Signature log entries are append-only and cannot be modified.")
        )

    @api.ondelete(at_uninstall=False)
    def _ls_unlink_check_ls_supplier_signature(self):
        """Reject deletion of log entries."""
        raise UserError(
            _("Signature log entries are append-only and cannot be deleted.")
        )

    # ------------------------------------------------------------------
    # Signing
    # ------------------------------------------------------------------
    @api.model
    def _compute_hash(self, previous_hash, values):
        """Return the SHA-256 hexadecimal digest of one chain link.

        :param str previous_hash: digest of the preceding entry, or an empty
            string for the first entry of the company chain.
        :param dict values: canonical payload of the entry.
        :return: hexadecimal SHA-256 digest.
        :rtype: str
        """
        canonical = json.dumps(values, sort_keys=True, default=str)
        return hashlib.sha256(
            ((previous_hash or "") + canonical).encode("utf-8")
        ).hexdigest()

    @api.model
    def _last_entry(self, company):
        """Return the most recent entry of a company chain, or an empty set."""
        return self.sudo().search(
            [("company_id", "=", company.id)],
            order="sequence_number desc",
            limit=1,
        )

    @api.model
    def sign(self, record, meaning, reason=False, login=False, payload=None):
        """Append one entry to the signature log.

        :param record: singleton recordset being signed.
        :param str meaning: value of :attr:`meaning`.
        :param str reason: free-text justification.
        :param str login: login typed by the signer.
        :param dict payload: values snapshot to freeze with the signature.
        :return: the created :class:`LsSupplierSignature` record.
        """
        record.ensure_one()
        company = getattr(record, "company_id", False) or self.env.company
        previous = self._last_entry(company)
        signed_on = fields.Datetime.now()
        entry_payload = dict(payload or {})
        values = {
            "res_model": record._name,
            "res_id": record.id,
            "user_login": self.env.user.login,
            "signed_on": fields.Datetime.to_string(signed_on),
            "meaning": meaning,
            "reason": reason or "",
            "payload": entry_payload,
        }
        record_hash = self._compute_hash(previous.record_hash, values)
        return self.sudo().create({
            "res_model": record._name,
            "res_id": record.id,
            "signed_record_name": record.display_name,
            "qualification_id": self._extract_qualification_id(record),
            "user_id": self.env.user.id,
            "login_used": login or self.env.user.login,
            "signed_on": signed_on,
            "meaning": meaning,
            "reason": reason or False,
            "payload": json.dumps(entry_payload, sort_keys=True, default=str),
            "sequence_number": (previous.sequence_number or 0) + 1,
            "previous_hash": previous.record_hash or False,
            "record_hash": record_hash,
            "company_id": company.id,
        })

    @api.model
    def _extract_qualification_id(self, record):
        """Return the dossier id related to a signed record, if any."""
        if record._name == "ls.supplier.qualification":
            return record.id
        if "qualification_id" in record._fields:
            return record.qualification_id.id or False
        return False

    # ------------------------------------------------------------------
    # Verification
    # ------------------------------------------------------------------
    @api.model
    def verify_chain(self, company=None):
        """Recompute the chain and return the entries that do not match.

        :param company: company whose chain is verified. Defaults to the
            current company.
        :return: recordset of entries whose stored digest differs from the
            recomputed digest.
        """
        company = company or self.env.company
        entries = self.sudo().search(
            [("company_id", "=", company.id)], order="sequence_number asc"
        )
        broken = self.browse()
        previous_hash = False
        for entry in entries:
            values = {
                "res_model": entry.res_model,
                "res_id": entry.res_id,
                "user_login": entry.user_id.login,
                "signed_on": fields.Datetime.to_string(entry.signed_on),
                "meaning": entry.meaning,
                "reason": entry.reason or "",
                "payload": json.loads(entry.payload or "{}"),
            }
            expected = self._compute_hash(previous_hash, values)
            if expected != entry.record_hash:
                broken |= entry
            previous_hash = entry.record_hash
        return broken

    def action_verify_chain(self):
        """Verify the chain of the active company and report the outcome."""
        broken = self.verify_chain(self.env.company)
        if broken:
            message = _(
                "The signature chain verification failed for %s entries. "
                "Sequence numbers: %s.",
                len(broken),
                ", ".join(str(entry.sequence_number) for entry in broken),
            )
            level = "danger"
        else:
            message = _("The signature chain is consistent.")
            level = "success"
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Signature Chain Verification"),
                "message": message,
                "type": level,
                "sticky": bool(broken),
            },
        }
