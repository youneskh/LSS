# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0.html).
"""Deterministic serialisation and hashing helpers.

Every value written to the audit trail passes through this module. The
functions are deliberately free of Odoo model logic so that they can be unit
tested in isolation and so that the exact byte sequence that is hashed is
defined in one single place.

Two representations are produced for every captured field value:

``technical``
    A stable, locale independent representation used for hashing and for exact
    comparison. Relational values are represented by their database
    identifiers, binary values by the SHA-256 digest and byte length of their
    content.

``display``
    A human readable representation used in the user interface, in the PDF
    report and in the CSV file of an evidence pack. It is never hashed, so a
    change of language or of a related record's name cannot invalidate a
    previously computed chain.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

#: Keyword arguments producing a canonical JSON document: keys sorted, no
#: insignificant whitespace, non-ASCII characters preserved.
_CANONICAL_JSON_KWARGS: dict[str, Any] = {
    "sort_keys": True,
    "separators": (",", ":"),
    "ensure_ascii": False,
}


def canonical_json(payload: dict) -> str:
    """Return the canonical JSON representation of ``payload``.

    :param payload: a dictionary whose values are JSON serialisable.
    :return: a JSON document with sorted keys and no insignificant whitespace.
    """
    return json.dumps(payload, **_CANONICAL_JSON_KWARGS)


def sha256_hex(data: str | bytes) -> str:
    """Return the hexadecimal SHA-256 digest of ``data``.

    :param data: the text or byte string to digest. Text is encoded as UTF-8.
    :return: a 64 character lowercase hexadecimal string.
    """
    if isinstance(data, str):
        data = data.encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def chain_digest(payload_digest: str, previous_digest: str) -> str:
    """Return the chain digest of an audit entry.

    The chain digest binds the content of the entry to the content of every
    entry that precedes it, so that removing, inserting or altering an entry
    invalidates every subsequent digest.

    :param payload_digest: SHA-256 digest of the canonical payload of the entry.
    :param previous_digest: chain digest of the preceding entry of the chain.
    :return: a 64 character lowercase hexadecimal string.
    """
    return sha256_hex(f"{payload_digest}|{previous_digest}")


def binary_fingerprint(value: bytes | str | bool) -> str:
    """Return the fingerprint stored in place of a binary field value.

    Binary content is never copied into the audit trail. Storing the digest and
    the length keeps the audit trail small while still detecting any change of
    the underlying content.

    :param value: the raw value read from a ``fields.Binary`` field.
    :return: a string of the form ``sha256:<digest>;bytes:<length>``.
    """
    if not value:
        payload = b""
    elif isinstance(value, str):
        payload = value.encode("utf-8")
    elif isinstance(value, memoryview):
        payload = value.tobytes()
    else:
        payload = bytes(value)
    return f"sha256:{sha256_hex(payload)};bytes:{len(payload)}"


def technical_value(record, field_name: str, field_type: str) -> str:
    """Return the technical representation of ``record[field_name]``.

    :param record: a singleton recordset of the audited model.
    :param field_name: name of the field to serialise.
    :param field_type: value of ``field.type`` for that field.
    :return: a stable text representation, empty when the value is not set.
    """
    value = record[field_name]
    if field_type == "many2one":
        return str(value.id) if value else ""
    if field_type in ("one2many", "many2many"):
        return ",".join(str(identifier) for identifier in sorted(value.ids))
    if field_type == "binary":
        return binary_fingerprint(value)
    if field_type == "boolean":
        return "true" if value else "false"
    if value is False or value is None:
        return ""
    return str(value)


def display_value(
    record, field_name: str, field_type: str, selection_labels: dict
) -> str:
    """Return the human readable representation of ``record[field_name]``.

    :param record: a singleton recordset of the audited model.
    :param field_name: name of the field to serialise.
    :param field_type: value of ``field.type`` for that field.
    :param selection_labels: mapping of stored value to label, obtained from
        ``fields_get``. It is empty for every field type other than
        ``selection``.
    :return: a text representation intended for human review.
    """
    value = record[field_name]
    if field_type == "many2one":
        return value.display_name if value else ""
    if field_type in ("one2many", "many2many"):
        return ", ".join(value.mapped("display_name"))
    if field_type == "binary":
        return binary_fingerprint(value)
    if field_type == "boolean":
        return "true" if value else "false"
    if field_type == "selection":
        if value is False or value is None:
            return ""
        return selection_labels.get(value, str(value))
    if value is False or value is None:
        return ""
    return str(value)
