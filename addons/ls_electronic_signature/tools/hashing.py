# Part of the Life Sciences Suite. See LICENSE file for full copyright details.
"""Deterministic serialisation and hashing helpers for electronic signatures.

Regulatory rationale
--------------------
21 CFR 11.70 requires that electronic signatures executed to electronic records
be linked to their respective records so that the signatures "cannot be excised,
copied, or otherwise transferred to falsify an electronic record by ordinary
means".

This module implements that linkage as a SHA-256 digest computed over a
*canonical* serialisation of the signed payload, and chains each signature to
the preceding signature of the same company so that the removal or substitution
of any single entry is detectable.

Canonicalisation rules
----------------------
The following rules are normative. A change to any of them invalidates every
previously computed digest and therefore constitutes a change requiring impact
assessment under the change control procedure.

1. The payload is a mapping whose keys are ``str``.
2. Keys are ordered with :func:`sorted`, i.e. by Unicode code point.
3. JSON separators are ``","`` and ``":"`` with no surrounding whitespace.
4. Non-ASCII characters are preserved (``ensure_ascii=False``); the resulting
   text is encoded as UTF-8.
5. :class:`datetime.datetime` and :class:`datetime.date` values are converted to
   ISO-8601 text before serialisation. Naive datetimes are treated as UTC, which
   matches the Odoo ORM storage convention for ``fields.Datetime``.
6. :class:`decimal.Decimal` values are converted to their canonical string form
   so that binary floating point representation never influences a digest.
7. ``bytes`` values are rejected. Binary content must be reduced to its own
   SHA-256 digest by the caller before being placed in a payload.
8. The Odoo ``False`` placeholder used for unset Char, Text, Date, Datetime and
   Many2one fields is normalised to ``None``, so that an unset value and an
   empty value produce the same digest. Boolean ``False`` on a
   :class:`odoo.fields.Boolean` field is preserved by the caller passing a real
   ``bool``; see :func:`normalise_value`.

Genesis value
-------------
The first entry of a chain uses :data:`GENESIS_HASH`, a string of 64 ASCII
zeroes, as its previous hash.
"""

import datetime
import decimal
import hashlib
import json

__all__ = [
    "GENESIS_HASH",
    "HASH_ALGORITHM",
    "HASH_HEX_LENGTH",
    "canonical_dumps",
    "chain_digest",
    "digest_payload",
    "normalise_value",
    "sha256_hex",
]

#: Name of the digest algorithm, recorded in evidence output for traceability.
HASH_ALGORITHM = "sha256"

#: Length in characters of a lowercase hexadecimal SHA-256 digest.
HASH_HEX_LENGTH = 64

#: Previous-hash value used by the first entry of every chain.
GENESIS_HASH = "0" * HASH_HEX_LENGTH


def normalise_value(value):
    """Return a JSON-serialisable, canonical representation of ``value``.

    :param value: A value taken from an Odoo record or supplied by a caller.
    :returns: A value composed only of ``None``, ``bool``, ``int``, ``float``,
        ``str``, ``list`` and ``dict``.
    :raises TypeError: If ``value`` is of a type that has no deterministic
        canonical representation, in particular ``bytes``.
    """
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, str)):
        return value
    if isinstance(value, float):
        return value
    if isinstance(value, decimal.Decimal):
        return str(value)
    if isinstance(value, datetime.datetime):
        moment = value
        if moment.tzinfo is None:
            moment = moment.replace(tzinfo=datetime.timezone.utc)
        return moment.astimezone(datetime.timezone.utc).isoformat(
            timespec="microseconds"
        )
    if isinstance(value, datetime.date):
        return value.isoformat()
    if isinstance(value, (list, tuple)):
        return [normalise_value(item) for item in value]
    if isinstance(value, dict):
        return {str(key): normalise_value(item) for key, item in value.items()}
    if isinstance(value, (bytes, bytearray, memoryview)):
        raise TypeError(
            "Binary values have no canonical payload representation. Reduce the "
            "content to its own SHA-256 digest before hashing."
        )
    raise TypeError(
        "Value of type %r has no canonical representation for signature "
        "hashing." % type(value).__name__
    )


def canonical_dumps(payload):
    """Serialise ``payload`` to canonical UTF-8 bytes.

    :param dict payload: Mapping of string keys to normalisable values.
    :returns bytes: The canonical UTF-8 encoded JSON document.
    :raises TypeError: If ``payload`` is not a mapping or contains a value with
        no canonical representation.
    """
    if not isinstance(payload, dict):
        raise TypeError("A signature payload must be a mapping.")
    normalised = {str(key): normalise_value(value) for key, value in payload.items()}
    return json.dumps(
        normalised,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def sha256_hex(data):
    """Return the lowercase hexadecimal SHA-256 digest of ``data``.

    :param bytes data: The bytes to digest.
    :returns str: A 64 character lowercase hexadecimal string.
    """
    if not isinstance(data, (bytes, bytearray, memoryview)):
        raise TypeError("sha256_hex expects bytes.")
    return hashlib.sha256(bytes(data)).hexdigest()


def digest_payload(payload):
    """Return the record digest of ``payload``.

    :param dict payload: Mapping of string keys to normalisable values.
    :returns str: A 64 character lowercase hexadecimal string.
    """
    return sha256_hex(canonical_dumps(payload))


def chain_digest(previous_hash, record_hash):
    """Return the chain digest binding ``record_hash`` to ``previous_hash``.

    The chain digest is ``SHA-256(previous_hash + ":" + record_hash)`` computed
    over the ASCII encoding of the concatenation. The separator prevents any
    ambiguity between the two fixed length operands.

    :param str previous_hash: Chain hash of the preceding entry, or
        :data:`GENESIS_HASH` for the first entry of a chain.
    :param str record_hash: Digest returned by :func:`digest_payload`.
    :returns str: A 64 character lowercase hexadecimal string.
    :raises ValueError: If either operand is not a 64 character hexadecimal
        string.
    """
    for label, value in (("previous_hash", previous_hash), ("record_hash", record_hash)):
        if not isinstance(value, str) or len(value) != HASH_HEX_LENGTH:
            raise ValueError("%s must be a %d character string." % (label, HASH_HEX_LENGTH))
        if any(character not in "0123456789abcdef" for character in value):
            raise ValueError("%s must be lowercase hexadecimal." % label)
    return sha256_hex(("%s:%s" % (previous_hash, record_hash)).encode("ascii"))
