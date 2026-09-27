# Part of the Life Sciences Suite. See LICENSE file for full copyright details.
"""The immutable electronic signature record.

This model is the evidence object of the module. One row is one executed
signature. Rows are append only:

* :meth:`write` and :meth:`unlink` always raise.
* No security group is granted write or unlink rights.
* A PostgreSQL trigger refuses ``UPDATE`` and ``DELETE`` at the database level,
  so that a direct SQL connection cannot silently alter history either.

Each row carries, in plain readable columns, the three items that
21 CFR 11.50(a) requires a signed electronic record to indicate: the printed
name of the signer, the date and time the signature was executed, and the
meaning associated with the signature. Those values are stored as snapshots
taken at signing time rather than as live relations, so that later renaming a
user or a meaning cannot rewrite what a past signature said.

Linkage to the signed record, required by 21 CFR 11.70, is implemented as a
SHA-256 digest over a canonical serialisation of the signed content, chained to
the preceding signature of the same company.
"""

import logging

import psycopg2

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools import SQL

from ..tools import hashing

_logger = logging.getLogger(__name__)

#: Namespace passed to ``pg_advisory_xact_lock`` so that this module's chain
#: lock cannot collide with an advisory lock taken by another module.
ADVISORY_LOCK_NAMESPACE = 0x4C53_4553 & 0x7FFFFFFF

#: Name of the PostgreSQL trigger enforcing row immutability.
IMMUTABILITY_TRIGGER = "ls_signature_log_immutable_trg"

#: Name of the PostgreSQL function backing the trigger.
IMMUTABILITY_FUNCTION = "ls_signature_log_immutable_fn"


class LsSignatureLog(models.Model):
    """An executed electronic signature."""

    _name = "ls.signature.log"
    _description = "Electronic Signature Log"
    _order = "signed_at desc, id desc"
    _rec_name = "name"

    # -- Identification ---------------------------------------------------
    name = fields.Char(required=True, readonly=True, index=True)
    chain_sequence = fields.Integer(required=True, readonly=True, index=True)
    company_id = fields.Many2one(
        comodel_name="res.company",
        required=True,
        readonly=True,
        index=True,
        ondelete="restrict",
    )

    # -- 21 CFR 11.50(a)(1): printed name of the signer -------------------
    user_id = fields.Many2one(
        comodel_name="res.users",
        string="Signer",
        required=True,
        readonly=True,
        index=True,
        ondelete="restrict",
        help="Deletion of a signer is refused so that historical signatures "
             "always resolve to a real account.",
    )
    signer_name = fields.Char(
        required=True,
        readonly=True,
        help="Printed name of the signer as it stood when the signature was "
             "executed.",
    )
    signer_login = fields.Char(
        required=True,
        readonly=True,
        help="Identification code of the signer as it stood when the "
             "signature was executed.",
    )

    # -- 21 CFR 11.50(a)(2): date and time --------------------------------
    signed_at = fields.Datetime(
        required=True,
        readonly=True,
        index=True,
        help="Instant at which the signature was executed, stored in UTC.",
    )

    # -- 21 CFR 11.50(a)(3): meaning --------------------------------------
    meaning_id = fields.Many2one(
        comodel_name="ls.signature.meaning",
        required=True,
        readonly=True,
        ondelete="restrict",
    )
    meaning_code = fields.Char(required=True, readonly=True)
    meaning_name = fields.Char(required=True, readonly=True)

    # -- 21 CFR 11.70: the signed record ----------------------------------
    res_model = fields.Char(
        string="Record Model",
        required=True,
        readonly=True,
        index=True,
    )
    res_model_name = fields.Char(string="Record Model Label", readonly=True)
    res_id = fields.Integer(
        string="Record ID",
        required=True,
        readonly=True,
        index=True,
    )
    res_name = fields.Char(string="Record", readonly=True)
    payload_json = fields.Text(
        required=True,
        readonly=True,
        help="Canonical serialisation of the content that was signed. Retained "
             "so that the digest can be recomputed and the signature verified "
             "without relying on the current state of the record.",
    )
    record_hash = fields.Char(required=True, readonly=True, index=True)
    previous_hash = fields.Char(required=True, readonly=True)
    chain_hash = fields.Char(required=True, readonly=True, index=True)
    hash_algorithm = fields.Char(
        required=True,
        readonly=True,
        default=hashing.HASH_ALGORITHM,
    )

    # -- Execution context -------------------------------------------------
    reason = fields.Text(readonly=True)
    policy_id = fields.Many2one(
        comodel_name="ls.signature.policy",
        readonly=True,
        ondelete="restrict",
    )
    request_id = fields.Many2one(
        comodel_name="ls.signature.request",
        readonly=True,
        ondelete="restrict",
    )
    authentication_method = fields.Selection(
        selection=[
            ("full", "Identification code and password"),
            ("single", "Password only, continuous session"),
        ],
        required=True,
        readonly=True,
        help="Which signature components were presented, as distinguished by "
             "21 CFR 11.200(a)(1)(i) and (ii).",
    )
    session_id = fields.Many2one(
        comodel_name="ls.signature.session",
        readonly=True,
        ondelete="restrict",
    )
    ip_address = fields.Char(readonly=True)
    user_agent = fields.Char(readonly=True)

    # -- Derived -----------------------------------------------------------
    is_current = fields.Boolean(
        compute="_compute_is_current",
        string="Covers Current Content",
        help="False when the signed record has changed since it was signed, "
             "so that the signature no longer attests to its present content.",
    )

    _chain_sequence_uniq = models.Constraint(
        "UNIQUE(company_id, chain_sequence)",
        "The signature chain sequence must be unique within a company.",
    )
    _chain_hash_uniq = models.Constraint(
        "UNIQUE(chain_hash)",
        "The signature chain hash must be unique.",
    )
    _record_hash_length = models.Constraint(
        "CHECK(char_length(record_hash) = 64)",
        "A record hash must be a 64 character hexadecimal digest.",
    )
    _chain_hash_length = models.Constraint(
        "CHECK(char_length(chain_hash) = 64)",
        "A chain hash must be a 64 character hexadecimal digest.",
    )
    _previous_hash_length = models.Constraint(
        "CHECK(char_length(previous_hash) = 64)",
        "A previous hash must be a 64 character hexadecimal digest.",
    )
    _chain_sequence_positive = models.Constraint(
        "CHECK(chain_sequence > 0)",
        "The signature chain sequence starts at 1.",
    )

    # ------------------------------------------------------------------
    # Database level immutability
    # ------------------------------------------------------------------
    def init(self):
        """Install the PostgreSQL trigger that refuses UPDATE and DELETE.

        Installation failure is logged rather than raised: a database role
        without trigger privileges must still be able to install the module,
        because the Python level protections remain in force. Whether the
        trigger is active is recorded in a system parameter so that the
        installation qualification can state it as a fact rather than an
        assumption.
        """
        parameter = self.env["ir.config_parameter"].sudo()
        try:
            self._install_immutability_trigger()
        except psycopg2.Error as error:
            _logger.warning(
                "Could not install the electronic signature immutability "
                "trigger: %s. Python level protections remain active.",
                error,
            )
            parameter.set_param(
                "ls_electronic_signature.db_immutability_trigger", "absent"
            )
        else:
            parameter.set_param(
                "ls_electronic_signature.db_immutability_trigger", "installed"
            )

    def _install_immutability_trigger(self):
        """Create the trigger function and the trigger inside a savepoint.

        A failure rolls back to the savepoint only, never the whole module
        installation transaction.

        :raises psycopg2.Error: when the database role cannot create them.
        """
        # Identifiers are quoted by SQL.identifier; no value is interpolated.
        function = SQL.identifier(IMMUTABILITY_FUNCTION)
        trigger = SQL.identifier(IMMUTABILITY_TRIGGER)
        with self.env.cr.savepoint():
            self.env.cr.execute(
                SQL(
                    """
                    CREATE OR REPLACE FUNCTION %s() RETURNS trigger AS $ls$
                    BEGIN
                        RAISE EXCEPTION
                            'ls_signature_log rows are append only (21 CFR 11.70).';
                    END;
                    $ls$ LANGUAGE plpgsql;
                    """,
                    function,
                )
            )
            self.env.cr.execute(
                SQL("DROP TRIGGER IF EXISTS %s ON ls_signature_log", trigger)
            )
            self.env.cr.execute(
                SQL(
                    """
                    CREATE TRIGGER %s
                    BEFORE UPDATE OR DELETE ON ls_signature_log
                    FOR EACH ROW EXECUTE PROCEDURE %s();
                    """,
                    trigger,
                    function,
                )
            )

    # ------------------------------------------------------------------
    # Append only enforcement
    # ------------------------------------------------------------------
    @api.model_create_multi
    def create(self, vals_list):
        """Append signatures, computing every security relevant value here.

        Values that a caller must not be able to choose are recomputed from the
        server side context and overwrite anything supplied. This keeps the
        creation entry point safe even when it is reached from custom code
        rather than from the signature wizard.
        """
        if not vals_list:
            return self.browse()
        prepared = []
        for vals in vals_list:
            prepared.append(
                self._prepare_chain_values(self._force_signer_identity(dict(vals)))
            )
        records = super().create(prepared)
        for record in records:
            _logger.info(
                "Electronic signature %s executed by %s (%s) on %s,%s with "
                "meaning %s.",
                record.name,
                record.signer_name,
                record.signer_login,
                record.res_model,
                record.res_id,
                record.meaning_code,
            )
        return records

    def write(self, vals):
        """Refuse every modification.

        :raises UserError: Always.
        """
        raise UserError(
            _(
                "Electronic signature records cannot be modified. To correct a "
                "signature, execute a new one with the appropriate meaning and "
                "record the justification in the reason field."
            )
        )

    @api.ondelete(at_uninstall=False)
    def _ls_unlink_check_ls_signature_log(self):
        """Refuse every deletion.

        :raises UserError: Always.
        """
        raise UserError(
            _(
                "Electronic signature records cannot be deleted. They are the "
                "evidence that a signature was executed."
            )
        )

    # ------------------------------------------------------------------
    # Chain construction
    # ------------------------------------------------------------------
    def _force_signer_identity(self, vals):
        """Overwrite the signer identity with that of the calling account.

        Signers hold create rights on this model, because creating a signature
        is what signing means. Without this method a crafted call could record
        a signature attributed to a different person, defeating the whole
        control. The identity and the signing instant are therefore taken from
        the server and any value supplied by the caller is discarded.

        The only exception is a call made with elevated rights, which is how
        data migration and recovery tooling must operate; such calls are
        already outside the security boundary.

        :param dict vals: Values proposed by the caller.
        :returns dict: Values with the identity fields pinned.
        """
        if self.env.su:
            return vals
        user = self.env.user
        vals.update(
            {
                "user_id": user.id,
                "signer_name": user.name,
                "signer_login": user.login,
                "signed_at": fields.Datetime.now(),
            }
        )
        return vals

    def _prepare_chain_values(self, vals):
        """Return ``vals`` completed with server computed chain values.

        The advisory lock serialises chain appends for a company within the
        current transaction, so that two concurrent signatures cannot be given
        the same sequence number or the same predecessor.

        :param dict vals: Values proposed by the caller.
        :returns dict: Values ready for insertion.
        :raises UserError: If mandatory linkage values are missing.
        """
        company_id = vals.get("company_id") or self.env.company.id
        for required in ("res_model", "res_id", "meaning_id", "payload_json"):
            if not vals.get(required):
                raise UserError(
                    _(
                        "An electronic signature cannot be recorded without "
                        "'%(field)s'.",
                        field=required,
                    )
                )

        self.env.cr.execute(
            "SELECT pg_advisory_xact_lock(%s, %s)",
            (ADVISORY_LOCK_NAMESPACE, company_id),
        )
        # Odoo runs transactions in REPEATABLE READ, so the snapshot of this
        # transaction may predate a signature committed by another transaction
        # while this one waited for the lock. The tail is therefore also read
        # through a fresh cursor whose snapshot starts after the lock was
        # acquired, and the higher position wins.
        row = self._read_chain_tail(self.env.cr, company_id)
        with self.env.registry.cursor() as committed_cr:
            committed_row = self._read_chain_tail(committed_cr, company_id)
        if committed_row and (not row or committed_row[0] > row[0]):
            row = committed_row
        if row:
            chain_sequence = row[0] + 1
            previous_hash = row[1]
        else:
            chain_sequence = 1
            previous_hash = hashing.GENESIS_HASH

        record_hash = vals.get("record_hash") or hashing.sha256_hex(
            vals["payload_json"].encode("utf-8")
        )
        vals.update(
            {
                "company_id": company_id,
                "chain_sequence": chain_sequence,
                "previous_hash": previous_hash,
                "record_hash": record_hash,
                "chain_hash": hashing.chain_digest(previous_hash, record_hash),
                "hash_algorithm": hashing.HASH_ALGORITHM,
                "name": "ESIG/%08d" % chain_sequence,
            }
        )
        return vals

    @api.model
    def _read_chain_tail(self, cr, company_id):
        """Return the last chain position and digest visible through ``cr``.

        :param cr: the database cursor to read with.
        :param int company_id: the company owning the chain.
        :returns: a tuple ``(chain_sequence, chain_hash)`` or ``None`` for an
            empty chain.
        """
        cr.execute(
            """
            SELECT chain_sequence, chain_hash
              FROM ls_signature_log
             WHERE company_id = %s
             ORDER BY chain_sequence DESC
             LIMIT 1
            """,
            (company_id,),
        )
        return cr.fetchone()

    # ------------------------------------------------------------------
    # Verification
    # ------------------------------------------------------------------
    @api.depends("record_hash", "res_model", "res_id")
    def _compute_is_current(self):
        """Recompute the digest of the live record and compare it."""
        for signature in self:
            signature.is_current = signature._recompute_record_hash() == signature.record_hash

    def _recompute_record_hash(self):
        """Return the digest the live record would produce today.

        :returns: A digest string, or ``False`` when the record or its model no
            longer exists, or when the model does not implement the mixin.
        """
        self.ensure_one()
        model = self.env.get(self.res_model)
        if model is None or not getattr(model, "_ls_signature_enabled", False):
            return False
        record = model.browse(self.res_id).exists()
        if not record:
            return False
        payload = record.sudo()._ls_signature_payload(
            meaning=self.meaning_id.sudo(),
            signed_at=self.signed_at,
            signer=self.user_id.sudo(),
        )
        return hashing.digest_payload(payload)

    def verify(self):
        """Verify the integrity of each signature in ``self``.

        Two independent checks are performed:

        * the stored chain hash equals the recomputation from the stored
          previous hash and record hash;
        * the stored record hash equals the digest of the stored payload.

        The linkage to the *current* state of the signed record is reported
        separately by :attr:`is_current`, because a legitimate later edit makes
        a signature stale without making it forged.

        :returns dict: Mapping of signature id to a dict with keys
            ``chain_ok``, ``payload_ok`` and ``messages``.
        """
        results = {}
        for signature in self:
            messages = []
            expected_chain = hashing.chain_digest(
                signature.previous_hash, signature.record_hash
            )
            chain_ok = expected_chain == signature.chain_hash
            if not chain_ok:
                messages.append(
                    _("The chain hash does not match its previous and record hashes.")
                )
            payload_ok = (
                hashing.sha256_hex((signature.payload_json or "").encode("utf-8"))
                == signature.record_hash
            )
            if not payload_ok:
                messages.append(
                    _("The record hash does not match the stored signed payload.")
                )
            results[signature.id] = {
                "chain_ok": chain_ok,
                "payload_ok": payload_ok,
                "messages": messages,
            }
        return results

    @api.model
    def verify_chain(self, company):
        """Walk a company's chain from its first entry and report divergence.

        :param company: A single ``res.company`` recordset.
        :returns dict: Keys ``entries_checked``, ``passed``,
            ``first_divergence_id`` and ``messages``.
        """
        company.ensure_one()
        signatures = self.sudo().search(
            [("company_id", "=", company.id)], order="chain_sequence asc"
        )
        expected_previous = hashing.GENESIS_HASH
        expected_sequence = 1
        messages = []
        first_divergence_id = False
        for signature in signatures:
            local = signature.verify()[signature.id]
            if signature.chain_sequence != expected_sequence:
                messages.append(
                    _(
                        "Signature %(name)s carries sequence %(actual)s where "
                        "%(expected)s was expected, which indicates a removed "
                        "or inserted entry.",
                        name=signature.name,
                        actual=signature.chain_sequence,
                        expected=expected_sequence,
                    )
                )
            elif signature.previous_hash != expected_previous:
                messages.append(
                    _(
                        "Signature %(name)s does not follow its predecessor.",
                        name=signature.name,
                    )
                )
            elif local["messages"]:
                messages.extend(
                    _("Signature %(name)s: %(detail)s", name=signature.name, detail=detail)
                    for detail in local["messages"]
                )
            else:
                expected_previous = signature.chain_hash
                expected_sequence += 1
                continue
            if not first_divergence_id:
                first_divergence_id = signature.id
            expected_previous = signature.chain_hash
            expected_sequence = signature.chain_sequence + 1
        return {
            "entries_checked": len(signatures),
            "passed": not messages,
            "first_divergence_id": first_divergence_id,
            "messages": messages,
        }

    # ------------------------------------------------------------------
    # User interface helpers
    # ------------------------------------------------------------------
    def action_open_signed_record(self):
        """Open the record that this signature was executed against."""
        self.ensure_one()
        model = self.env.get(self.res_model)
        if model is None or not model.browse(self.res_id).exists():
            raise UserError(
                _(
                    "The signed record %(model)s,%(res_id)s no longer exists.",
                    model=self.res_model,
                    res_id=self.res_id,
                )
            )
        return {
            "type": "ir.actions.act_window",
            "res_model": self.res_model,
            "res_id": self.res_id,
            "view_mode": "form",
            "target": "current",
        }

    def action_verify(self):
        """Verify the selected signatures and report the outcome."""
        results = self.verify()
        failures = [
            signature
            for signature in self
            if results[signature.id]["messages"]
        ]
        if failures:
            detail = "\n".join(
                "%s: %s" % (signature.name, "; ".join(results[signature.id]["messages"]))
                for signature in failures
            )
            raise UserError(
                _("Integrity verification failed:\n%(detail)s", detail=detail)
            )
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "type": "success",
                "title": _("Integrity verified"),
                "message": _(
                    "%(count)s signature(s) verified successfully.",
                    count=len(self),
                ),
                "sticky": False,
            },
        }
