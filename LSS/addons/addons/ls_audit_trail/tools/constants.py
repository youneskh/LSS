# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0.html).
"""Constants shared by the ``ls_audit_trail`` module.

This module contains no Odoo model and no side effect. It is imported by the
audit engine, by the wizards and by the automated tests.
"""

from __future__ import annotations

#: Length, in hexadecimal characters, of a SHA-256 digest.
DIGEST_LENGTH: int = 64

#: Digest value used as ``hash_prev`` for the first entry of a chain.
GENESIS_DIGEST: str = "0" * DIGEST_LENGTH

#: First key of the PostgreSQL transaction advisory lock that serialises chain
#: appends. The second key is the company identifier. The value is an arbitrary
#: but fixed 32-bit integer owned by this module.
ADVISORY_LOCK_NAMESPACE: int = 1_970_010_101

#: Models that are never auditable. Auditing them would make the audit engine
#: recurse into itself.
NON_AUDITABLE_MODELS: frozenset[str] = frozenset(
    {
        "ls.audit_trail.log",
        "ls.audit_trail.log.line",
        "ls.audit_trail.rule",
        "ls.audit_trail.verification",
        "ls.audit_trail.evidence_pack",
        "ls.audit_trail.verify.wizard",
        "ls.audit_trail.purge.wizard",
    }
)

#: Technical fields that carry no business meaning and are therefore excluded
#: from the "all fields" selection of an audit rule. They remain selectable
#: explicitly through the ``field_ids`` list of a rule.
IMPLICIT_EXCLUDED_FIELDS: frozenset[str] = frozenset(
    {
        "id",
        "create_uid",
        "create_date",
        "write_uid",
        "write_date",
        "display_name",
        "__last_update",
    }
)

#: Field types that cannot be stored in a database column and are therefore
#: never captured.
NON_STORABLE_FIELD_TYPES: frozenset[str] = frozenset({"one2many", "many2many"})

#: Operations recognised by the audit engine.
OPERATION_CREATE: str = "create"
OPERATION_WRITE: str = "write"
OPERATION_UNLINK: str = "unlink"
OPERATIONS: tuple[str, ...] = (OPERATION_CREATE, OPERATION_WRITE, OPERATION_UNLINK)

#: Entry types of ``ls.audit_trail.log``.
ENTRY_TYPE_DATA: str = "data"
ENTRY_TYPE_ANCHOR: str = "anchor"

#: Empty audit configuration returned by the guard when a model is not audited.
#: The tuple layout is ``(operations, field_names)`` where ``field_names`` is
#: ``None`` when every eligible field of the model is audited.
EMPTY_CONFIG: tuple[frozenset, None] = (frozenset(), None)

#: Name of the ``ir.config_parameter`` holding the number of days verified by
#: the scheduled integrity check.
PARAM_VERIFICATION_WINDOW: str = "ls_audit_trail.verification_window_days"

#: Default number of days verified by the scheduled integrity check.
DEFAULT_VERIFICATION_WINDOW_DAYS: int = 7

#: Files written inside an evidence pack archive.
EVIDENCE_FILE_ENTRIES_JSON: str = "audit_entries.json"
EVIDENCE_FILE_ENTRIES_CSV: str = "audit_entries.csv"
EVIDENCE_FILE_MANIFEST: str = "manifest.json"

#: Column order of ``audit_entries.csv`` inside an evidence pack.
EVIDENCE_CSV_COLUMNS: tuple[str, ...] = (
    "sequence_number",
    "event_datetime",
    "company",
    "user_login",
    "user_name",
    "remote_addr",
    "model_name",
    "res_id",
    "res_name",
    "operation",
    "entry_type",
    "field_name",
    "field_label",
    "old_value_display",
    "new_value_display",
    "old_value_technical",
    "new_value_technical",
    "payload_digest",
    "hash_prev",
    "hash_current",
)
