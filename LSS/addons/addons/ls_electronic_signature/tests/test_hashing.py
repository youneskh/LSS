# Part of the Life Sciences Suite. See LICENSE file for full copyright details.
"""Unit tests for the canonical serialisation and hash chain helpers."""

import datetime
import decimal
import hashlib

from odoo.tests import TransactionCase, tagged

from ..tools import hashing


@tagged("post_install", "-at_install", "ls_signature")
class TestHashing(TransactionCase):
    """The digest must be deterministic and independent of input ordering."""

    def test_key_order_does_not_change_digest(self):
        """Two mappings differing only in insertion order hash identically."""
        first = hashing.digest_payload({"b": 2, "a": 1})
        second = hashing.digest_payload({"a": 1, "b": 2})
        self.assertEqual(first, second)

    def test_digest_is_sha256_of_canonical_bytes(self):
        """The digest equals the SHA-256 of the canonical serialisation."""
        payload = {"alpha": 1, "beta": "x"}
        expected = hashlib.sha256(hashing.canonical_dumps(payload)).hexdigest()
        self.assertEqual(hashing.digest_payload(payload), expected)

    def test_canonical_form_has_no_whitespace(self):
        """The serialisation uses compact separators."""
        self.assertEqual(
            hashing.canonical_dumps({"a": 1, "b": [1, 2]}),
            b'{"a":1,"b":[1,2]}',
        )

    def test_non_ascii_is_preserved(self):
        """Non-ASCII characters survive serialisation as UTF-8."""
        self.assertEqual(
            hashing.canonical_dumps({"name": "Contrôle"}),
            '{"name":"Contrôle"}'.encode("utf-8"),
        )

    def test_naive_datetime_is_treated_as_utc(self):
        """A naive datetime is normalised to an explicit UTC offset."""
        naive = datetime.datetime(2026, 7, 28, 10, 30, 0)
        aware = datetime.datetime(
            2026, 7, 28, 10, 30, 0, tzinfo=datetime.timezone.utc
        )
        self.assertEqual(
            hashing.normalise_value(naive), hashing.normalise_value(aware)
        )

    def test_false_and_none_normalise_identically(self):
        """The Odoo empty placeholder and None produce the same value."""
        self.assertIsNone(hashing.normalise_value(None))

    def test_decimal_is_serialised_as_text(self):
        """Decimals never pass through binary floating point."""
        self.assertEqual(
            hashing.normalise_value(decimal.Decimal("1.10")), "1.10"
        )

    def test_bytes_are_rejected(self):
        """Binary content has no canonical form and must be refused."""
        with self.assertRaises(TypeError):
            hashing.canonical_dumps({"blob": b"\x00\x01"})

    def test_unknown_type_is_rejected(self):
        """A type with no canonical representation is refused."""
        with self.assertRaises(TypeError):
            hashing.canonical_dumps({"thing": object()})

    def test_payload_must_be_a_mapping(self):
        """A non-mapping payload is refused."""
        with self.assertRaises(TypeError):
            hashing.canonical_dumps([1, 2, 3])

    def test_chain_digest_is_order_sensitive(self):
        """Swapping the operands changes the chain digest."""
        left = "a" * 64
        right = "b" * 64
        self.assertNotEqual(
            hashing.chain_digest(left, right), hashing.chain_digest(right, left)
        )

    def test_chain_digest_rejects_malformed_operands(self):
        """Operands that are not 64 character hexadecimal are refused."""
        with self.assertRaises(ValueError):
            hashing.chain_digest("short", "b" * 64)
        with self.assertRaises(ValueError):
            hashing.chain_digest("Z" * 64, "b" * 64)

    def test_genesis_hash_shape(self):
        """The genesis value is a valid operand for the chain digest."""
        self.assertEqual(len(hashing.GENESIS_HASH), hashing.HASH_HEX_LENGTH)
        self.assertTrue(hashing.chain_digest(hashing.GENESIS_HASH, "c" * 64))

    def test_sha256_hex_rejects_text(self):
        """The digest helper refuses anything that is not bytes."""
        with self.assertRaises(TypeError):
            hashing.sha256_hex("text")
