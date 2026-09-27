# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Tests of the active ingredient and excipient master data."""

from psycopg2 import IntegrityError

from odoo.exceptions import UserError
from odoo.tests import tagged
from odoo.tools import mute_logger

from .common import LsPharmaCommon


@tagged("post_install", "-at_install")
class TestMaterial(LsPharmaCommon):
    """Exercise the shared material mixin and its two concrete models."""

    def test_api_carries_the_mixin_fields(self):
        """An active ingredient carries the fields of the shared mixin."""
        self.assertEqual(self.api.code, "API-TEST")
        self.assertEqual(self.api.pharmacopoeia, "ph_eur")
        self.assertEqual(self.api.state, "qualified")
        self.assertTrue(self.api.active)

    def test_excipient_carries_its_own_fields(self):
        """An excipient carries the fields specific to excipients."""
        self.assertEqual(self.excipient.excipient_function, "diluent")
        self.assertFalse(self.excipient.is_novel)

    def test_code_is_unique_per_company(self):
        """Two active ingredients of one company cannot share one code."""
        with self.assertRaises(IntegrityError):
            with mute_logger("odoo.sql_db"):
                self.env["ls.pharma.api"].create(
                    {"name": "Duplicate", "code": "API-TEST"}
                )
                self.env.flush_all()

    def test_lifecycle(self):
        """A material moves through its four states."""
        material = self.env["ls.pharma.api"].create(
            {"name": "Lifecycle Substance", "code": "API-LIFE"}
        )
        self.assertEqual(material.state, "draft")
        material.action_qualify()
        self.assertEqual(material.state, "qualified")
        material.action_restrict()
        self.assertEqual(material.state, "restricted")
        material.action_qualify()
        self.assertEqual(material.state, "qualified")
        material.action_obsolete()
        self.assertEqual(material.state, "obsolete")
        self.assertFalse(material.active)
        with self.assertRaises(UserError):
            material.action_set_draft()

    def test_animal_origin_may_be_recorded_but_not_qualified(self):
        """A material of animal origin cannot be qualified without a statement.

        The material may be recorded at any time. It is the qualified state
        that requires the reference of the supplier statement on transmissible
        spongiform encephalopathy.
        """
        material = self.env["ls.pharma.excipient"].create(
            {
                "name": "Animal Derived",
                "code": "EXC-ANIMAL",
                "excipient_function": "lubricant",
                "of_animal_origin": True,
            }
        )
        self.assertEqual(material.state, "draft")
        with self.assertRaises(UserError):
            material.action_qualify()

    def test_animal_origin_with_a_statement_is_accepted(self):
        """The same material is accepted once the statement is recorded."""
        material = self.env["ls.pharma.excipient"].create(
            {
                "name": "Animal Derived",
                "code": "EXC-ANIMAL-OK",
                "excipient_function": "lubricant",
                "of_animal_origin": True,
                "tse_statement_reference": "TSE-2026-001",
            }
        )
        material.action_qualify()
        self.assertEqual(material.state, "qualified")

    def test_negative_retest_period_is_rejected(self):
        """A negative retest period is refused."""
        with self.assertRaises(UserError):
            self.env["ls.pharma.api"].create(
                {
                    "name": "Negative Retest",
                    "code": "API-NEG",
                    "retest_period_months": -1,
                }
            )

    def test_display_name(self):
        """The display name shows the code together with the name."""
        self.assertIn("API-TEST", self.api.display_name)
        self.assertIn("Test Active Substance", self.api.display_name)
