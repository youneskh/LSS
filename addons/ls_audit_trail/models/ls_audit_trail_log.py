# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0.html).
"""Audit trail entry: capture engine, hash chain and integrity verification."""

from __future__ import annotations

import logging

from odoo import _, api, fields, models, tools
from odoo.exceptions import AccessError, UserError
from odoo.http import request

from ..tools import constants, serialization

_logger = logging.getLogger(__name__)


class LsAuditTrailLog(models.Model):
    """One entry per audited ORM operation on one record.

    An entry is immutable. It is created by the audit engine through
    :meth:`~._ls_capture`, sealed inside the same database transaction by
    :meth:`~._ls_seal`, and can afterwards never be modified or deleted through
    the ORM by any user, including the superuser.

    Entries form a chain per company. ``hash_current`` of an entry is derived
    from the canonical payload of that entry and from ``hash_current`` of the
    preceding entry. Removing, inserting or altering an entry therefore breaks
    every subsequent digest, which :meth:`~._ls_verify_chain` detects and
    reports.
    """

    _name = "ls.audit_trail.log"
    _description = "Audit Trail Entry"
    _order = "sequence_number desc, id desc"
    _rec_name = "res_name"

    _company_sequence_unique = models.Constraint(
        "UNIQUE(company_id, sequence_number)",
        "An audit chain position may be used only once per company.",
    )

    sequence_number = fields.Integer(
        string="Chain Position",
        readonly=True,
        index=True,
        help="Position of the entry in the audit chain of its company.",
    )
    company_id = fields.Many2one(comodel_name="res.company", required=True,
                                 readonly=True,
                                 index=True,
                                 ondelete="restrict",
                                 help=(
                                     "Company owning the audit chain of this entry. A company that owns "
                                     "audit entries cannot be deleted."),
                                 )
    entry_type = fields.Selection(
        selection=[
            (constants.ENTRY_TYPE_DATA, "Data Change"),
            (constants.ENTRY_TYPE_ANCHOR, "Retention Anchor"),
        ],
        required=True,
        readonly=True,
        default=constants.ENTRY_TYPE_DATA,
        index=True,
        help=(
            "A data change entry records an ORM operation. A retention anchor "
            "replaces a range of entries removed by an approved retention run "
            "and preserves the continuity of the chain."
        ),
    )
    event_datetime = fields.Datetime(
        string="Event Date",
        required=True,
        readonly=True,
        index=True,
        help="Server date and time, in UTC, at which the operation was captured.",
    )
    user_id = fields.Many2one(comodel_name="res.users", required=True,
                              readonly=True,
                              index=True,
                              ondelete="restrict",
                              help=(
                                  "User who performed the operation. A user referenced by an audit "
                                  "entry cannot be deleted and must be archived instead."),
                              )
    user_login = fields.Char(
        string="Login",
        required=True,
        readonly=True,
        help="Login of the user at the time of the operation.",
    )
    remote_addr = fields.Char(
        string="Remote Address",
        readonly=True,
        help=(
            "Network address of the client, when the operation was performed "
            "through an HTTP request. Empty for operations performed by a "
            "scheduled action or by the command line."
        ),
    )
    model_name = fields.Char(
        string="Model",
        required=True,
        readonly=True,
        index=True,
        help="Technical name of the audited model.",
    )
    model_id = fields.Many2one(
        comodel_name="ir.model",
        string="Model Record",
        readonly=True,
        ondelete="set null",
        help=(
            "Registry record of the audited model. It is cleared when the "
            "model is removed from the registry; the technical name above "
            "remains available."
        ),
    )
    res_id = fields.Integer(
        string="Record ID",
        required=True,
        readonly=True,
        index=True,
        help="Database identifier of the audited record.",
    )
    res_name = fields.Char(
        string="Record",
        readonly=True,
        help="Display name of the audited record at the time of the operation.",
    )
    operation = fields.Selection(
        selection=[
            (constants.OPERATION_CREATE, "Creation"),
            (constants.OPERATION_WRITE, "Modification"),
            (constants.OPERATION_UNLINK, "Deletion"),
        ],
        readonly=True,
        index=True,
        help="ORM operation captured by this entry.",
    )
    line_ids = fields.One2many(
        comodel_name="ls.audit_trail.log.line",
        inverse_name="log_id",
        string="Field Changes",
        readonly=True,
    )
    line_count = fields.Integer(
        string="Changed Fields",
        compute="_compute_line_count",
        store=True,
        readonly=True,
    )
    payload_digest = fields.Char(size=constants.DIGEST_LENGTH,
                                 readonly=True,
                                 help="SHA-256 digest of the canonical payload of this entry.",)
    hash_prev = fields.Char(
        string="Previous Chain Digest",
        size=constants.DIGEST_LENGTH,
        readonly=True,
        help="Chain digest of the preceding entry of the same company.",
    )
    hash_current = fields.Char(
        string="Chain Digest",
        size=constants.DIGEST_LENGTH,
        readonly=True,
        index=True,
        help=(
            "SHA-256 digest binding this entry to every entry that precedes it "
            "in the chain of its company."
        ),
    )
    purged_from_sequence = fields.Integer(
        string="Purged From",
        readonly=True,
        help="First chain position removed by the retention run of an anchor entry.",
    )
    purged_to_sequence = fields.Integer(
        string="Purged To",
        readonly=True,
        help="Last chain position removed by the retention run of an anchor entry.",
    )
    purged_entry_count = fields.Integer(
        string="Purged Entries",
        readonly=True,
        help="Number of entries removed by the retention run of an anchor entry.",
    )
    purged_aggregate_digest = fields.Char(size=constants.DIGEST_LENGTH,
                                          readonly=True,
                                          help=(
                                              "SHA-256 digest of the concatenated chain digests of the entries "
                                              "removed by the retention run of an anchor entry."),
                                          )
    purge_reason = fields.Text(
        string="Retention Justification",
        readonly=True,
        help="Documented reason recorded when a retention run was executed.",
    )

    # ------------------------------------------------------------------
    # Compute and display
    # ------------------------------------------------------------------
    @api.depends("line_ids")
    def _compute_line_count(self):
        """Store the number of field changes carried by the entry."""
        for entry in self:
            entry.line_count = len(entry.line_ids)

    @api.depends("model_name", "res_id", "res_name", "operation", "sequence_number")
    def _compute_display_name(self):
        """Build a display name identifying the chain position and the record."""
        labels = dict(self._fields["operation"].selection)
        for entry in self:
            target = entry.res_name or f"{entry.model_name},{entry.res_id}"
            operation = labels.get(entry.operation, entry.operation or "")
            entry.display_name = f"#{entry.sequence_number} {target} ({operation})"

    # ------------------------------------------------------------------
    # Immutability
    # ------------------------------------------------------------------
    def write(self, vals):
        """Reject every modification of a sealed entry.

        Only the sealing fields may be written, and only while the entry is
        still unsealed. Sealing happens inside the transaction that creates the
        entry, so an entry visible to a user is always already sealed.

        :param vals: field values requested by the caller.
        :raise AccessError: when the entry is sealed or when a field outside
            the sealing set is written.
        """
        sealing_fields = {
            "sequence_number",
            "hash_prev",
            "hash_current",
            "payload_digest",
        }
        forbidden = set(vals) - sealing_fields
        if forbidden:
            raise AccessError(
                _(
                    "Audit trail entries are immutable. The fields %(fields)s "
                    "cannot be modified.",
                    fields=", ".join(sorted(forbidden)),
                )
            )
        if any(entry.hash_current for entry in self):
            raise AccessError(
                _("A sealed audit trail entry cannot be modified.")
            )
        return super().write(vals)

    @api.ondelete(at_uninstall=False)
    def _ls_unlink_check_ls_audit_trail_log(self):
        """Reject every deletion performed through the ORM.

        Entries are removed only by an approved retention run, which deletes
        rows with a parameterised SQL statement after recording a retention
        anchor. See ``ls.audit_trail.purge.wizard``.

        :raise AccessError: always.
        """
        raise AccessError(
            _(
                "Audit trail entries cannot be deleted. Use the Retention Run "
                "wizard, which records a retention anchor preserving the "
                "integrity of the chain."
            )
        )

    # ------------------------------------------------------------------
    # Configuration cache
    # ------------------------------------------------------------------
    @api.model
    @tools.ormcache("model_name", "company_id")
    def _ls_audit_config_for(self, model_name, company_id):
        """Return the audit configuration of a model for a company.

        The result is cached per database registry and invalidated by
        :meth:`~._ls_clear_audit_config_cache` whenever a rule changes.

        :param model_name: technical name of the model being written to.
        :param company_id: identifier of the company owning the audited
            record, or ``False`` for the rules without company only.
        :return: a tuple ``(operations, field_names)`` where ``operations`` is a
            frozenset drawn from ``create``, ``write`` and ``unlink``, and
            ``field_names`` is a frozenset of audited field names or ``None``
            when every eligible field of the model is audited.
        """
        if model_name in constants.NON_AUDITABLE_MODELS:
            return constants.EMPTY_CONFIG
        rules = self.env["ls.audit_trail.rule"].sudo().search(
            [
                ("model_name", "=", model_name),
                ("company_id", "in", [False, company_id]),
            ]
        )
        if not rules:
            return constants.EMPTY_CONFIG
        operations = set()
        selected = set()
        excluded = set()
        audit_every_field = False
        for rule in rules:
            if rule.log_create:
                operations.add(constants.OPERATION_CREATE)
            if rule.log_write:
                operations.add(constants.OPERATION_WRITE)
            if rule.log_unlink:
                operations.add(constants.OPERATION_UNLINK)
            excluded.update(rule.excluded_field_ids.mapped("name"))
            if rule.field_ids:
                selected.update(rule.field_ids.mapped("name"))
            else:
                audit_every_field = True
        if not operations:
            return constants.EMPTY_CONFIG
        if audit_every_field:
            if not excluded:
                return (frozenset(operations), None)
            return (
                frozenset(operations),
                frozenset(
                    name
                    for name in self.env[model_name]._fields
                    if name not in excluded
                    and name not in constants.IMPLICIT_EXCLUDED_FIELDS
                ),
            )
        return (frozenset(operations), frozenset(selected - excluded))

    @api.model
    @tools.ormcache("model_name")
    def _ls_audit_rule_companies(self, model_name):
        """Return which companies hold an active audit rule for a model.

        :param model_name: technical name of the model.
        :return: a tuple ``(has_global_rule, company_ids)``: whether a rule
            without company exists, and the frozenset of the companies of the
            company-specific rules.
        """
        if model_name in constants.NON_AUDITABLE_MODELS:
            return (False, frozenset())
        rules = self.env["ls.audit_trail.rule"].sudo().search(
            [("model_name", "=", model_name)]
        )
        return (
            any(not rule.company_id for rule in rules),
            frozenset(rules.company_id.ids),
        )

    @api.model
    def _ls_clear_audit_config_cache(self):
        """Drop the cached audit configuration of every model.

        This is the single call site of the registry cache invalidation. If a
        future Odoo release renames the invalidation entry point, only this
        method has to be adapted.
        """
        self.env.registry.clear_cache()

    @api.model
    def _ls_eligible_field_names(self, model_name, configured_fields):
        """Return the field names that may be captured for a model.

        :param model_name: technical name of the audited model.
        :param configured_fields: frozenset of configured field names, or
            ``None`` when every eligible field is audited.
        :return: a tuple of field names, sorted alphabetically.
        """
        model = self.env[model_name]
        names = []
        for name, field in model._fields.items():
            if name in constants.IMPLICIT_EXCLUDED_FIELDS:
                continue
            if not field.store:
                continue
            if field.type in constants.NON_STORABLE_FIELD_TYPES:
                continue
            if configured_fields is not None and name not in configured_fields:
                continue
            names.append(name)
        return tuple(sorted(names))

    # ------------------------------------------------------------------
    # Capture
    # ------------------------------------------------------------------
    @api.model
    def _ls_snapshot(self, records, field_names):
        """Read the current value of ``field_names`` for every record.

        :param records: recordset of the audited model.
        :param field_names: tuple of field names to read.
        :return: a dictionary ``{record_id: {field_name: (technical, display)}}``.
        """
        if not field_names:
            return {}
        model = records.env[records._name]
        descriptions = model.fields_get(
            list(field_names), ["type", "string", "selection"]
        )
        snapshot = {}
        for record in records.sudo():
            values = {}
            for name in field_names:
                description = descriptions.get(name, {})
                field_type = description.get("type", "char")
                labels = dict(description.get("selection") or [])
                values[name] = (
                    serialization.technical_value(record, name, field_type),
                    serialization.display_value(record, name, field_type, labels),
                )
            snapshot[record.id] = values
        return snapshot

    @api.model
    def _ls_remote_addr(self):
        """Return the network address of the client, when one is available.

        ``odoo.http.request`` is a thread local proxy. Outside an HTTP request,
        for example during a scheduled action or a command line invocation, it
        is unbound and accessing it raises. The audit entry must be written in
        both situations.

        :return: the remote address, or an empty string when unavailable.
        """
        try:
            if not request:
                return ""
            return request.httprequest.remote_addr or ""
        except (AttributeError, RuntimeError):
            return ""

    @api.model
    def _ls_context_values(self, records):
        """Return the contextual values shared by every entry of a capture.

        :param records: recordset of the audited model.
        :return: a dictionary of field values for ``ls.audit_trail.log``.
        """
        user = records.env.user
        remote_addr = self._ls_remote_addr()
        model_record = records.env["ir.model"].sudo()._get(records._name)
        return {
            "event_datetime": fields.Datetime.now(),
            "user_id": user.id,
            "user_login": user.login,
            "remote_addr": remote_addr,
            "model_name": records._name,
            "model_id": model_record.id if model_record else False,
        }

    @api.model
    def _ls_record_company_id(self, record):
        """Return the company that owns the audit chain of ``record``.

        :param record: a singleton recordset of the audited model.
        :return: an integer company identifier.
        """
        company_field = record._fields.get("company_id")
        if company_field is not None and company_field.type == "many2one":
            company = record.sudo().company_id
            if company:
                return company.id
        return record.env.company.id

    @api.model
    def _ls_capture(self, records, operation, field_names, before, after):
        """Create and seal the audit entries of one ORM operation.

        :param records: recordset that was created, written to or deleted.
        :param operation: one of ``create``, ``write`` or ``unlink``.
        :param field_names: tuple of captured field names.
        :param before: snapshot taken before the operation, or an empty
            dictionary for a creation.
        :param after: snapshot taken after the operation, or an empty
            dictionary for a deletion.
        :return: the created ``ls.audit_trail.log`` recordset.
        """
        log_model = self.sudo()
        context_values = log_model._ls_context_values(records)
        values_list = []
        for record in records:
            before_values = before.get(record.id, {})
            after_values = after.get(record.id, {})
            company_id = log_model._ls_record_company_id(record)
            res_name = self._ls_safe_display_name(record)
            line_commands = []
            for name in field_names:
                old_technical, old_display = before_values.get(name, ("", ""))
                new_technical, new_display = after_values.get(name, ("", ""))
                if old_technical == new_technical:
                    continue
                line_commands.append(
                    fields.Command.create(
                        {
                            "field_name": name,
                            "old_value_technical": old_technical,
                            "new_value_technical": new_technical,
                            "old_value_display": old_display,
                            "new_value_display": new_display,
                            "company_id": company_id,
                            "event_datetime": context_values["event_datetime"],
                            "model_name": context_values["model_name"],
                            "res_id": record.id,
                            "res_name": res_name,
                            "operation": operation,
                            "user_id": context_values["user_id"],
                        }
                    )
                )
            if operation == constants.OPERATION_WRITE and not line_commands:
                continue
            values = dict(context_values)
            values.update(
                {
                    "company_id": company_id,
                    "res_id": record.id,
                    "res_name": res_name,
                    "operation": operation,
                    "entry_type": constants.ENTRY_TYPE_DATA,
                    "line_ids": line_commands,
                }
            )
            values_list.append(values)
        if not values_list:
            return log_model.browse()
        entries = log_model.create(values_list)
        entries._ls_seal()
        return entries

    @api.model
    def _ls_safe_display_name(self, record):
        """Return the display name of ``record`` without raising.

        A display name is computed by arbitrary business code that may depend
        on records already removed by the current transaction. A failure to
        compute it must never prevent the audit entry from being written.

        :param record: a singleton recordset of the audited model.
        :return: the display name, or the technical reference on failure.
        """
        try:
            return record.sudo().display_name or f"{record._name},{record.id}"
        except Exception:  # noqa: BLE001 - the audit entry must always be written
            _logger.warning(
                "ls_audit_trail: display name of %s,%s could not be computed",
                record._name,
                record.id,
            )
            return f"{record._name},{record.id}"

    # ------------------------------------------------------------------
    # Chain
    # ------------------------------------------------------------------
    def _ls_payload(self):
        """Return the canonical payload of the entry.

        Every stored value of the entry enters the payload, including the human
        readable snapshots. Those snapshots are taken once at capture time and
        are never recomputed, so hashing them is safe and it protects the
        evidence a reviewer actually reads.

        Two things are deliberately outside the payload, because neither is
        stored evidence: the label and the type of a changed field, which are
        resolved from the registry when a line is displayed, and the display
        name of any related record, which is resolved from that record.

        :return: a dictionary suitable for :func:`serialization.canonical_json`.
        """
        self.ensure_one()
        return {
            "sequence_number": self.sequence_number,
            "company_id": self.company_id.id,
            "entry_type": self.entry_type,
            "event_datetime": fields.Datetime.to_string(self.event_datetime),
            "user_id": self.user_id.id,
            "user_login": self.user_login,
            "remote_addr": self.remote_addr or "",
            "model_name": self.model_name,
            "res_id": self.res_id,
            "res_name": self.res_name or "",
            "operation": self.operation or "",
            "lines": [
                {
                    "field_name": line.field_name,
                    "old_value": line.old_value_technical or "",
                    "new_value": line.new_value_technical or "",
                    "old_display": line.old_value_display or "",
                    "new_display": line.new_value_display or "",
                }
                for line in self.line_ids.sorted("field_name")
            ],
            "purged_from_sequence": self.purged_from_sequence,
            "purged_to_sequence": self.purged_to_sequence,
            "purged_entry_count": self.purged_entry_count,
            "purged_aggregate_digest": self.purged_aggregate_digest or "",
        }

    @api.model
    def _ls_lock_chain(self, company_id):
        """Serialise chain appends of one company for the current transaction.

        The lock is released automatically when the transaction ends. It
        guarantees that two concurrent transactions cannot claim the same chain
        position for the same company.

        :param company_id: identifier of the company owning the chain.
        """
        self.env.cr.execute(
            "SELECT pg_advisory_xact_lock(%s, %s)",
            (constants.ADVISORY_LOCK_NAMESPACE, company_id),
        )

    @api.model
    def _ls_chain_tail(self, company_id):
        """Return the last sealed position and digest of a company chain.

        Odoo runs transactions in REPEATABLE READ: the snapshot of the current
        transaction is taken at its first query, before the chain lock is
        acquired. Another transaction that sealed and committed in between is
        therefore invisible to it, and reading the tail through the current
        cursor alone would hand out a chain position that is already taken.

        The tail is thus read twice, once through the current cursor (which
        sees the entries sealed earlier in this same transaction) and once
        through a fresh cursor whose snapshot starts after the lock was
        acquired (which sees every entry committed by other transactions).
        The higher position wins. The caller must hold the chain lock
        (:meth:`_ls_lock_chain`), which guarantees that no other transaction
        can seal between this read and the commit of the current one.

        :param company_id: identifier of the company owning the chain.
        :return: a tuple ``(sequence_number, hash_current)``. The genesis
            values ``(0, GENESIS_DIGEST)`` are returned for an empty chain.
        """
        tail = self._ls_read_chain_tail(self.env.cr, company_id)
        with self.env.registry.cursor() as committed_cr:
            committed_tail = self._ls_read_chain_tail(committed_cr, company_id)
        return max(tail, committed_tail, key=lambda item: item[0])

    @api.model
    def _ls_read_chain_tail(self, cr, company_id):
        """Read the last sealed position and digest through ``cr``.

        :param cr: the database cursor to read with.
        :param company_id: identifier of the company owning the chain.
        :return: a tuple ``(sequence_number, hash_current)``, the genesis
            values ``(0, GENESIS_DIGEST)`` for an empty chain.
        """
        cr.execute(
            """
            SELECT sequence_number, hash_current
              FROM ls_audit_trail_log
             WHERE company_id = %s
               AND hash_current IS NOT NULL
             ORDER BY sequence_number DESC
             LIMIT 1
            """,
            (company_id,),
        )
        row = cr.fetchone()
        if not row:
            return (0, constants.GENESIS_DIGEST)
        return (row[0], row[1])

    def _ls_seal(self):
        """Assign the chain position and the digests of unsealed entries.

        Entries are sealed in creation order, company by company, inside the
        transaction that created them. An entry that leaves this method carries
        a chain position, a payload digest and a chain digest, and can never be
        modified again.
        """
        unsealed = self.filtered(lambda entry: not entry.hash_current)
        if not unsealed:
            return
        for company in unsealed.mapped("company_id"):
            self._ls_lock_chain(company.id)
            # The chain tail is read with SQL. Pending ORM writes of previously
            # sealed entries must reach the database first, otherwise a second
            # capture in the same transaction would reuse a chain position.
            self.env.flush_all()
            position, previous_digest = self._ls_chain_tail(company.id)
            company_entries = unsealed.filtered(
                lambda entry, c=company: entry.company_id == c
            ).sorted("id")
            for entry in company_entries:
                position += 1
                entry.sudo().write({"sequence_number": position})
                payload_digest = serialization.sha256_hex(
                    serialization.canonical_json(entry._ls_payload())
                )
                current_digest = serialization.chain_digest(
                    payload_digest, previous_digest
                )
                entry.sudo().write(
                    {
                        "payload_digest": payload_digest,
                        "hash_prev": previous_digest,
                        "hash_current": current_digest,
                    }
                )
                previous_digest = current_digest

    # ------------------------------------------------------------------
    # Verification
    # ------------------------------------------------------------------
    @api.model
    def _ls_verify_chain(self, company, date_from=None, date_to=None):
        """Recompute and compare the digests of a company chain.

        :param company: a ``res.company`` singleton recordset.
        :param date_from: optional lower bound on ``event_datetime``.
        :param date_to: optional upper bound on ``event_datetime``.
        :return: a dictionary with the keys ``checked``, ``passed``,
            ``first_failure_id``, ``first_failure_sequence`` and ``details``.
        """
        domain = [("company_id", "=", company.id)]
        if date_from:
            domain.append(("event_datetime", ">=", date_from))
        if date_to:
            domain.append(("event_datetime", "<=", date_to))
        entries = self.sudo().search(domain, order="sequence_number asc")
        result = {
            "checked": len(entries),
            "passed": True,
            "first_failure_id": False,
            "first_failure_sequence": 0,
            "details": "",
        }
        if not entries:
            result["details"] = _("No audit entry in the selected range.")
            return result
        first = entries[0]
        expected_previous = first.hash_prev
        expected_position = first.sequence_number
        failures = []
        if not date_from:
            # The verified range starts at the head of the chain, so the head
            # itself can be checked. Position 1 is an untruncated chain. Any
            # other starting position is legitimate only when a retention
            # anchor states that the preceding positions were removed by an
            # approved run.
            head_finding = self._ls_check_chain_head(company, first)
            if head_finding:
                return {
                    "checked": len(entries),
                    "passed": False,
                    "first_failure_id": first.id,
                    "first_failure_sequence": first.sequence_number,
                    "details": head_finding,
                }
        for entry in entries:
            if entry.sequence_number != expected_position:
                failures.append(
                    _(
                        "Chain position %(found)s found where %(expected)s was "
                        "expected. Entries are missing or were reordered.",
                        found=entry.sequence_number,
                        expected=expected_position,
                    )
                )
            if entry.hash_prev != expected_previous:
                failures.append(
                    _(
                        "Entry %(position)s does not link to the preceding "
                        "entry.",
                        position=entry.sequence_number,
                    )
                )
            payload_digest = serialization.sha256_hex(
                serialization.canonical_json(entry._ls_payload())
            )
            if payload_digest != entry.payload_digest:
                failures.append(
                    _(
                        "The content of entry %(position)s does not match its "
                        "recorded payload digest.",
                        position=entry.sequence_number,
                    )
                )
            expected_current = serialization.chain_digest(
                payload_digest, entry.hash_prev or constants.GENESIS_DIGEST
            )
            if expected_current != entry.hash_current:
                failures.append(
                    _(
                        "The chain digest of entry %(position)s does not match "
                        "its content.",
                        position=entry.sequence_number,
                    )
                )
            if failures:
                result.update(
                    {
                        "passed": False,
                        "first_failure_id": entry.id,
                        "first_failure_sequence": entry.sequence_number,
                        "details": "\n".join(failures),
                    }
                )
                return result
            expected_previous = entry.hash_current
            expected_position = entry.sequence_number + 1
        result["details"] = _(
            "%(count)s entries verified from chain position %(first)s to "
            "%(last)s.",
            count=len(entries),
            first=entries[0].sequence_number,
            last=entries[-1].sequence_number,
        )
        return result

    @api.model
    def _ls_check_chain_head(self, company, first_entry):
        """Check that nothing was removed from the head of a company chain.

        A hash chain cannot detect the removal of its own first entries, because
        there is no surviving entry that references them. This module closes that
        gap by requiring that every truncation of the head be documented by a
        retention anchor stating the last position it removed.

        :param company: a ``res.company`` singleton recordset.
        :param first_entry: the earliest surviving entry of the chain.
        :return: an empty string when the head is intact, otherwise the finding.
        """
        if first_entry.sequence_number <= 1:
            return ""
        anchors = self.sudo().search(
            [
                ("company_id", "=", company.id),
                ("entry_type", "=", constants.ENTRY_TYPE_ANCHOR),
            ]
        )
        covered = max(anchors.mapped("purged_to_sequence") or [0])
        if covered == first_entry.sequence_number - 1:
            return ""
        return _(
            "The chain of company %(company)s starts at position "
            "%(first)s, but retention anchors account for removals only up to "
            "position %(covered)s. Positions %(gap_from)s to %(gap_to)s are "
            "unaccounted for.",
            company=company.display_name,
            first=first_entry.sequence_number,
            covered=covered,
            gap_from=covered + 1,
            gap_to=first_entry.sequence_number - 1,
        )

    @api.model
    def _ls_cron_verify_chain(self):
        """Verify the recent part of every company chain.

        Executed by the scheduled action ``Audit Trail: Verify Integrity``. A
        verification record is created for every company. A failure is written
        to the server log and posted on the verification record.
        """
        window = int(
            self.env["ir.config_parameter"]
            .sudo()
            .get_param(
                constants.PARAM_VERIFICATION_WINDOW,
                constants.DEFAULT_VERIFICATION_WINDOW_DAYS,
            )
        )
        date_from = fields.Datetime.subtract(fields.Datetime.now(), days=window)
        verification_model = self.env["ls.audit_trail.verification"].sudo()
        for company in self.env["res.company"].sudo().search([]):
            verification_model._ls_run(
                company=company,
                date_from=date_from,
                date_to=fields.Datetime.now(),
                source="cron",
            )

    # ------------------------------------------------------------------
    # User actions
    # ------------------------------------------------------------------
    def action_open_audited_record(self):
        """Open the record described by the entry.

        :return: an ``ir.actions.act_window`` dictionary.
        :raise UserError: when the model is no longer present in the registry
            or when the record no longer exists.
        """
        self.ensure_one()
        model = self.env.get(self.model_name)
        if model is None:
            raise UserError(
                _(
                    "The model %(model)s is no longer present in the registry.",
                    model=self.model_name,
                )
            )
        record = model.browse(self.res_id)
        if not record.exists():
            raise UserError(
                _(
                    "The record %(model)s,%(res_id)s no longer exists.",
                    model=self.model_name,
                    res_id=self.res_id,
                )
            )
        return {
            "type": "ir.actions.act_window",
            "res_model": self.model_name,
            "res_id": self.res_id,
            "view_mode": "form",
            "target": "current",
        }
