# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Unit tests of the pure GS1 helper functions."""

import datetime

from odoo.tests import tagged
from odoo.tests.common import TransactionCase

from .. import gs1


@tagged("post_install", "-at_install")
class TestGs1(TransactionCase):
    """Exercise the GS1 identification key helpers.

    These functions touch no model, but they are executed inside a
    ``TransactionCase`` so that the whole suite runs under one command.
    """

    def test_check_digit_published_example(self):
        """Reproduce the worked example published by GS1.

        GS1 US, "How to Calculate a Check Digit Manually", shows the twelve
        data digits 629104150021 of a GTIN-13 yielding the check digit 3.
        """
        self.assertEqual(gs1.compute_check_digit("629104150021"), 3)

    def test_check_digit_rejects_non_digits(self):
        """A key that is not made of digits has no check digit."""
        with self.assertRaises(gs1.Gs1Error):
            gs1.compute_check_digit("6291041500A1")

    def test_valid_gtin14(self):
        """A fourteen-digit key with the right check digit is accepted."""
        body = "0361234500001"
        gtin = body + str(gs1.compute_check_digit(body))
        self.assertTrue(gs1.is_valid_gtin14(gtin))

    def test_invalid_gtin14_wrong_check_digit(self):
        """A wrong check digit is rejected."""
        body = "0361234500001"
        wrong = (gs1.compute_check_digit(body) + 1) % 10
        self.assertFalse(gs1.is_valid_gtin14(body + str(wrong)))

    def test_invalid_gtin14_wrong_length(self):
        """A key of the wrong length is rejected."""
        self.assertFalse(gs1.is_valid_gtin14("036123450000"))
        self.assertFalse(gs1.is_valid_gtin14(""))

    def test_build_sscc(self):
        """A Serial Shipping Container Code has eighteen valid digits."""
        sscc = gs1.build_sscc("0361234", "3", "12345")
        self.assertEqual(len(sscc), 18)
        self.assertTrue(sscc.startswith("30361234"))
        self.assertTrue(gs1.is_valid_sscc(sscc))

    def test_build_sscc_rejects_long_serial_reference(self):
        """A serial reference that does not fit the code is rejected."""
        with self.assertRaises(gs1.Gs1Error):
            gs1.build_sscc("0361234", "3", "1234567890")

    def test_format_expiry(self):
        """An expiry date is encoded in the six-digit form of AI (17)."""
        self.assertEqual(
            gs1.format_expiry(datetime.date(2027, 5, 31)), "270531"
        )

    def test_format_expiry_requires_a_date(self):
        """A missing expiry date raises rather than producing an empty field."""
        with self.assertRaises(gs1.Gs1Error):
            gs1.format_expiry(False)

    def test_unique_identifier_element_string(self):
        """The unique identifier carries the four data fields in order."""
        body = "0361234500001"
        gtin = body + str(gs1.compute_check_digit(body))
        element_string = gs1.build_unique_identifier(
            gtin, "SER0001", "BAT2026001", datetime.date(2027, 5, 31)
        )
        self.assertEqual(
            element_string,
            "(01)%s(21)SER0001(10)BAT2026001(17)270531" % gtin,
        )

    def test_sscc_element_string(self):
        """A Serial Shipping Container Code is presented under AI (00)."""
        sscc = gs1.build_sscc("0361234", "3", "12345")
        self.assertEqual(
            gs1.build_sscc_element_string(sscc), "(00)%s" % sscc
        )

    def test_variable_field_length_limit(self):
        """A data field longer than twenty characters is rejected."""
        gs1.validate_variable_field("A" * 20, "serial number")
        with self.assertRaises(gs1.Gs1Error):
            gs1.validate_variable_field("A" * 21, "serial number")

    def test_generated_serials_have_the_requested_length(self):
        """A generated serial number has exactly the requested length."""
        for length in (8, 12, 20):
            self.assertEqual(len(gs1.generate_random_serial(length)), length)

    def test_generated_serials_use_the_permitted_alphabet(self):
        """A generated serial number uses upper-case alphanumerics only."""
        serial = gs1.generate_random_serial(20)
        self.assertTrue(serial.isalnum())
        self.assertEqual(serial, serial.upper())

    def test_generated_serials_are_not_sequential(self):
        """Two hundred generated serial numbers are not all identical.

        Article 4 of Commission Delegated Regulation (EU) 2016/161 requires
        the serial number to be a sequence whose value it is not possible to
        deduce.  A collision-free draw is not proof of unpredictability, but a
        generator that returned a constant or an increment would fail here.
        """
        serials = {gs1.generate_random_serial(16) for _index in range(200)}
        self.assertEqual(len(serials), 200)
