# Part of the Life Sciences Suite. See LICENSE file for full copyright details.
"""Tests for signature meanings and their authorisation."""

from psycopg2 import IntegrityError

from odoo.exceptions import ValidationError
from odoo.tests import TransactionCase, tagged
from odoo.tools import mute_logger


@tagged("post_install", "-at_install", "ls_signature")
class TestSignatureMeaning(TransactionCase):
    """Meaning codes must be unique, well formed and access controlled."""

    @classmethod
    def setUpClass(cls):
        """Create the meaning model handle and resolve the active company."""
        super().setUpClass()
        cls.Meaning = cls.env["ls.signature.meaning"]
        cls.company = cls.env.company

    def test_shipped_meanings_cover_the_regulation_examples(self):
        """The four meanings named in 21 CFR 11.50(a)(3) are supplied."""
        codes = set(
            self.Meaning.search([("company_id", "=", self.company.id)]).mapped("code")
        )
        self.assertLessEqual(
            {"REVIEWED", "APPROVED", "RESPONSIBLE", "AUTHORED"}, codes
        )

    def test_rejected_meaning_requires_a_reason(self):
        """The supplied rejection meaning makes a reason mandatory."""
        rejected = self.env.ref("ls_electronic_signature.meaning_rejected")
        self.assertTrue(rejected.require_reason)

    def test_code_must_be_upper_case(self):
        """A lower case code is refused."""
        with self.assertRaises(ValidationError):
            self.Meaning.create({"code": "approved", "name": "Approved"})

    def test_code_must_not_contain_spaces(self):
        """A code containing a space is refused."""
        with self.assertRaises(ValidationError):
            self.Meaning.create({"code": "TWO WORDS", "name": "Two words"})

    def test_code_must_be_long_enough(self):
        """A single character code is refused."""
        with self.assertRaises(ValidationError):
            self.Meaning.create({"code": "A", "name": "A"})

    @mute_logger("odoo.sql_db")
    def test_code_is_unique_per_company(self):
        """Two meanings of one company cannot share a code."""
        self.Meaning.create({"code": "UNIQUE_PROBE", "name": "Probe"})
        with self.assertRaises(IntegrityError):
            with self.env.cr.savepoint():
                self.Meaning.create({"code": "UNIQUE_PROBE", "name": "Probe 2"})

    def test_availability_without_groups_is_open(self):
        """A meaning with no group restriction is available to everyone."""
        meaning = self.Meaning.create({"code": "OPEN_PROBE", "name": "Open"})
        self.assertEqual(
            meaning.is_available_to(self.env.user), meaning
        )

    def test_availability_is_restricted_by_group(self):
        """A meaning restricted to a group excludes non-members."""
        group = self.env["res.groups"].create({"name": "Signature probe group"})
        meaning = self.Meaning.create(
            {"code": "CLOSED_PROBE", "name": "Closed", "group_ids": [(6, 0, group.ids)]}
        )
        outsider = self.env["res.users"].create(
            {
                "name": "Outsider",
                "login": "ls.meaning.outsider",
                "group_ids": [(6, 0, [self.env.ref("base.group_user").id])],
            }
        )
        self.assertFalse(meaning.is_available_to(outsider))
        outsider.write({"group_ids": [(4, group.id)]})
        self.assertEqual(meaning.is_available_to(outsider), meaning)
