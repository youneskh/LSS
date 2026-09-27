# Part of the Life Sciences Suite. See LICENSE file for full copyright details.
"""The capability mixin that makes a model signable.

A model becomes signable by inheriting this mixin::

    class LsDeviation(models.Model):
        _name = "ls.deviation"
        _inherit = ["ls.signature.mixin"]

        _ls_signature_field_whitelist = ("name", "state", "description")

Inheriting the mixin gives the model:

* the signature smart button and the signature list on its form;
* the payload definition used to compute the digest that links a signature to
  the record content, as required by 21 CFR 11.70;
* enforcement of field transition policies in :meth:`write`.
"""

import logging

from odoo import _, api, fields, models
from odoo.exceptions import UserError

from ..tools import hashing

_logger = logging.getLogger(__name__)

#: Field types that are never included in a signature payload. Binary content
#: has no canonical textual form and would make payloads unbounded; the
#: technical audit columns change on every write and would make every
#: signature immediately stale.
EXCLUDED_FIELD_TYPES = ("binary", "image", "html")

#: Field names that are never included in a signature payload.
EXCLUDED_FIELD_NAMES = (
    "id",
    "create_uid",
    "create_date",
    "write_uid",
    "write_date",
    "__last_update",
    "message_ids",
    "message_follower_ids",
    "message_main_attachment_id",
    "activity_ids",
    "access_token",
    "access_url",
    "access_warning",
)


class LsSignatureMixin(models.AbstractModel):
    """Adds electronic signature capability to a model."""

    _name = "ls.signature.mixin"
    _description = "Electronic Signature Capability"

    #: Marker used by policies, requests and the log to confirm that a model
    #: can carry signatures. Testing for this attribute is explicit and does
    #: not depend on registry internals.
    _ls_signature_enabled = True

    #: Optional tuple of field names forming the signature payload. When empty,
    #: :meth:`_ls_signature_fields` derives the payload from the stored fields
    #: of the model. Concrete models should set it, because an explicit list is
    #: stable across upgrades whereas a derived list changes whenever a field is
    #: added.
    _ls_signature_field_whitelist = ()

    ls_signature_ids = fields.Many2many(
        comodel_name="ls.signature.log",
        string="Electronic Signatures",
        compute="_compute_ls_signature_ids",
    )
    ls_signature_count = fields.Integer(
        string="Signature Count",
        compute="_compute_ls_signature_ids",
    )
    ls_last_signature_id = fields.Many2one(
        comodel_name="ls.signature.log",
        string="Last Signature",
        compute="_compute_ls_signature_ids",
    )
    ls_signature_current = fields.Boolean(
        string="Signature Covers Current Content",
        compute="_compute_ls_signature_ids",
        help="False when the record changed after its most recent signature, "
             "so that the signature no longer attests to the present content.",
    )

    # ------------------------------------------------------------------
    # Computed access to the signature log
    # ------------------------------------------------------------------
    @api.depends_context("uid")
    def _compute_ls_signature_ids(self):
        """Attach the signatures recorded against each record."""
        log_model = self.env["ls.signature.log"]
        grouped = {}
        real_records = self.filtered("id")
        if real_records:
            logs = log_model.search(
                [
                    ("res_model", "=", self._name),
                    ("res_id", "in", real_records.ids),
                ],
                order="chain_sequence asc",
            )
            # ``is_current`` compares the live record against a digest taken
            # in the past. It is not stored, so the ORM would serve a value
            # cached earlier in the same transaction and would not react to an
            # edit made since. Discard that cache before reading it.
            logs.invalidate_recordset(["is_current"])
            for log in logs:
                grouped.setdefault(log.res_id, log_model.browse())
                grouped[log.res_id] |= log
        for record in self:
            logs = grouped.get(record.id, log_model.browse())
            record.ls_signature_ids = logs
            record.ls_signature_count = len(logs)
            last = logs[-1] if logs else log_model.browse()
            record.ls_last_signature_id = last
            record.ls_signature_current = bool(last) and last.is_current

    # ------------------------------------------------------------------
    # Payload definition
    # ------------------------------------------------------------------
    def _ls_signature_fields(self):
        """Return the ordered field names included in the signature payload.

        The explicit whitelist is used when the model declares one. Otherwise
        every stored field is included except technical audit columns and the
        field types listed in :data:`EXCLUDED_FIELD_TYPES`.

        :returns tuple: Field names, sorted so that the payload is stable.
        """
        self.ensure_one()
        if self._ls_signature_field_whitelist:
            return tuple(sorted(self._ls_signature_field_whitelist))
        names = []
        for name, field in self._fields.items():
            if name in EXCLUDED_FIELD_NAMES:
                continue
            if name.startswith("ls_signature"):
                continue
            if field.type in EXCLUDED_FIELD_TYPES:
                continue
            if not field.store:
                continue
            names.append(name)
        return tuple(sorted(names))

    def _ls_signature_field_value(self, field_name):
        """Return the canonical value of ``field_name`` for the payload.

        Relational fields are reduced to identifiers rather than display names,
        because a display name can change without the underlying relation
        changing, which would make a signature look stale for no reason.

        :param str field_name: A field name of this model.
        :returns: A value acceptable to :func:`..tools.hashing.normalise_value`.
        """
        self.ensure_one()
        field = self._fields[field_name]
        value = self[field_name]
        if field.type == "many2one":
            return value.id or None
        if field.type in ("one2many", "many2many"):
            return sorted(value.ids)
        if field.type == "monetary" or field.type == "float":
            return float(value)
        if field.type in ("char", "text", "selection") and value is False:
            return None
        if field.type in ("date", "datetime") and not value:
            return None
        return value

    def _ls_signature_payload(self, meaning, signed_at, signer):
        """Return the mapping whose digest links a signature to this record.

        The payload deliberately contains both the record content and the
        identity of the signature, so that a digest cannot be transferred from
        one signature to another. This is the mechanism by which the module
        addresses 21 CFR 11.70.

        :param meaning: The ``ls.signature.meaning`` recordset being applied.
        :param signed_at: The signing instant, a naive UTC ``datetime``.
        :param signer: The ``res.users`` recordset executing the signature.
        :returns dict: The payload.
        """
        self.ensure_one()
        content = {}
        for field_name in self._ls_signature_fields():
            if field_name not in self._fields:
                continue
            content[field_name] = self._ls_signature_field_value(field_name)
        return {
            "schema": 1,
            "res_model": self._name,
            "res_id": self.id,
            "res_name": self.display_name,
            "meaning_code": meaning.code,
            "signer_login": signer.login,
            "signer_id": signer.id,
            "signed_at": signed_at,
            "content": content,
        }

    def _ls_current_record_hash(self, meaning, signed_at, signer):
        """Return the digest that a signature executed now would carry."""
        self.ensure_one()
        payload = self._ls_signature_payload(meaning, signed_at, signer)
        return hashing.digest_payload(payload)

    # ------------------------------------------------------------------
    # Policy evaluation
    # ------------------------------------------------------------------
    def _ls_applicable_policies(self, trigger=None):
        """Return the policies that govern this record.

        :param str trigger: Optional trigger filter.
        :returns: A ``ls.signature.policy`` recordset.
        """
        self.ensure_one()
        candidates = self.env["ls.signature.policy"]._policies_for_model(
            self._name, trigger=trigger
        )
        return candidates.filtered(lambda policy: policy.is_applicable_to(self))

    def _ls_satisfying_signatures(self, policy):
        """Return the signatures that currently satisfy ``policy``.

        A signature satisfies a policy when it carries the policy's meaning,
        was executed by an authorised signer, and still covers the present
        content of the record.

        :param policy: A single ``ls.signature.policy`` recordset.
        :returns: A ``ls.signature.log`` recordset.
        """
        self.ensure_one()
        signatures = self.env["ls.signature.log"].search(
            [
                ("res_model", "=", self._name),
                ("res_id", "=", self.id),
                ("meaning_id", "=", policy.meaning_id.id),
            ],
            order="chain_sequence asc",
        )
        signatures.invalidate_recordset(["is_current"])
        signatures = signatures.filtered("is_current")
        if policy.signer_group_ids:
            signatures = signatures.filtered(
                lambda log: log.user_id.all_group_ids & policy.signer_group_ids
            )
        if policy.distinct_signers:
            seen = set()
            kept = self.env["ls.signature.log"]
            for signature in signatures:
                if signature.user_id.id in seen:
                    continue
                seen.add(signature.user_id.id)
                kept |= signature
            signatures = kept
        return signatures

    def _ls_check_policy_satisfied(self, policy):
        """Raise when ``policy`` is not satisfied for this record.

        :param policy: A single ``ls.signature.policy`` recordset.
        :raises UserError: When the required signatures are missing or stale.
        """
        self.ensure_one()
        satisfying = self._ls_satisfying_signatures(policy)
        if len(satisfying) >= policy.required_signature_count:
            return True
        raise UserError(
            _(
                "The operation on %(record)s requires %(required)s signature(s) "
                "with the meaning '%(meaning)s' and only %(present)s valid "
                "signature(s) are present. Signatures executed before the last "
                "change to this record no longer count.",
                record=self.display_name,
                required=policy.required_signature_count,
                meaning=policy.meaning_id.name,
                present=len(satisfying),
            )
        )

    # ------------------------------------------------------------------
    # Transition enforcement
    # ------------------------------------------------------------------
    def write(self, vals):
        """Enforce field transition policies before writing.

        Enforcement is skipped when the context flag ``ls_signature_bypass`` is
        set. That flag is used only by :meth:`_ls_write_signed`, which is called
        after the required signatures have been verified.
        """
        if not self.env.context.get("ls_signature_bypass"):
            self._ls_check_transitions(vals)
        return super().write(vals)

    def _ls_check_transitions(self, vals):
        """Verify every transition policy triggered by ``vals``.

        :param dict vals: The values about to be written.
        :raises UserError: When a triggered policy is not satisfied.
        """
        policies = self.env["ls.signature.policy"]._policies_for_model(
            self._name, trigger="transition"
        )
        if not policies:
            return True
        for policy in policies:
            if policy.field_name not in vals:
                continue
            target = vals[policy.field_name]
            if str(target) != str(policy.value_to):
                continue
            for record in self:
                if policy.value_from and str(
                    record[policy.field_name]
                ) != str(policy.value_from):
                    continue
                if not policy.is_applicable_to(record):
                    continue
                record._ls_check_policy_satisfied(policy)
        return True

    # ------------------------------------------------------------------
    # User interface entry points
    # ------------------------------------------------------------------
    def action_ls_sign(self):
        """Open the signature wizard for this record."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Execute Electronic Signature"),
            "res_model": "ls.signature.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_res_model": self._name,
                "default_res_id": self.id,
            },
        }

    def action_ls_view_signatures(self):
        """Open the signatures recorded against this record."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Electronic Signatures"),
            "res_model": "ls.signature.log",
            "view_mode": "list,form",
            "domain": [("res_model", "=", self._name), ("res_id", "=", self.id)],
            "context": {"create": False},
        }

    def action_ls_request_signature(self):
        """Open a draft signature request for this record."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Request Electronic Signature"),
            "res_model": "ls.signature.request",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_res_model": self._name,
                "default_res_id": self.id,
                "default_res_name": self.display_name,
            },
        }
