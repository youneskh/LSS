# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Tests of serialised units, of their generation and of their aggregation."""

from odoo.exceptions import UserError
from odoo.tests import tagged

from .. import gs1
from .common import DEMO_GTIN14, LsPharmaCommon


@tagged("post_install", "-at_install")
class TestSerialization(LsPharmaCommon):
    """Exercise the unique identifier, its generation and its aggregation."""

    def setUp(self):
        """Create a batch and the values shared by the tests."""
        super().setUp()
        self.batch = self._create_batch()
        self.batch_number = "BAT2026TEST"
        self.expiry = "2028-01-31"

    def _generate(self, quantity=5):
        """Generate serialised units through the wizard.

        :param int quantity: number of units to draw.
        :rtype: recordset of ``ls.pharma.serialization``
        """
        wizard = self.env["ls.pharma.serial.generate.wizard"].create(
            {
                "batch_id": self.batch.id,
                "gtin": DEMO_GTIN14,
                "batch_number": self.batch_number,
                "expiry_date": self.expiry,
                "quantity": quantity,
                "serial_length": 12,
            }
        )
        wizard.action_generate()
        return self.env["ls.pharma.serialization"].search(
            [("batch_id", "=", self.batch.id)]
        )

    def test_generation_creates_the_requested_quantity(self):
        """The wizard creates exactly the requested number of units."""
        units = self._generate(quantity=5)
        self.assertEqual(len(units), 5)
        self.assertEqual(self.batch.serialization_count, 5)

    def test_generated_serials_are_unique(self):
        """No two generated units share a serial number."""
        units = self._generate(quantity=25)
        serials = units.mapped("serial_number")
        self.assertEqual(len(serials), len(set(serials)))
        for serial in serials:
            self.assertEqual(len(serial), 12)

    def test_element_string_carries_the_four_data_fields(self):
        """The stored element string matches the GS1 helper output.

        Article 4 of Commission Delegated Regulation (EU) 2016/161 lists the
        product code, the serial number, the batch number and the expiry date
        among the data of the unique identifier.
        """
        unit = self._generate(quantity=1)[0]
        expected = gs1.build_unique_identifier(
            unit.gtin, unit.serial_number, unit.batch_number, unit.expiry_date
        )
        self.assertEqual(unit.element_string, expected)
        self.assertIn("(01)%s" % DEMO_GTIN14, unit.element_string)
        self.assertIn("(21)%s" % unit.serial_number, unit.element_string)
        self.assertIn("(10)%s" % self.batch_number, unit.element_string)
        self.assertIn("(17)280131", unit.element_string)

    def test_invalid_gtin_is_refused_by_the_wizard(self):
        """A product code with a wrong check digit is refused."""
        wizard = self.env["ls.pharma.serial.generate.wizard"].create(
            {
                "batch_id": self.batch.id,
                "gtin": "03612345000018",
                "batch_number": self.batch_number,
                "expiry_date": self.expiry,
                "quantity": 1,
                "serial_length": 12,
            }
        )
        with self.assertRaises(UserError):
            wizard.action_generate()

    def test_past_expiry_is_refused_by_the_wizard(self):
        """Units cannot be generated with an expiry date in the past."""
        wizard = self.env["ls.pharma.serial.generate.wizard"].create(
            {
                "batch_id": self.batch.id,
                "gtin": DEMO_GTIN14,
                "batch_number": self.batch_number,
                "expiry_date": "2020-01-31",
                "quantity": 1,
                "serial_length": 12,
            }
        )
        with self.assertRaises(UserError):
            wizard.action_generate()

    def test_invalid_gtin_is_refused_by_the_model(self):
        """The model refuses an invalid product code on direct creation."""
        with self.assertRaises(UserError):
            self.env["ls.pharma.serialization"].create(
                {
                    "batch_id": self.batch.id,
                    "gtin": "12345678901234",
                    "serial_number": "SER00000001",
                    "batch_number": self.batch_number,
                    "expiry_date": self.expiry,
                }
            )

    def test_unit_life_cycle(self):
        """A unit is commissioned, shipped and can be decommissioned."""
        unit = self._generate(quantity=1)[0]
        self.assertEqual(unit.state, "generated")
        unit.action_commission()
        self.assertEqual(unit.state, "commissioned")
        self.assertTrue(unit.date_commissioned)
        unit.action_mark_shipped()
        self.assertEqual(unit.state, "shipped")
        unit.action_decommission()
        self.assertEqual(unit.state, "decommissioned")
        self.assertTrue(unit.date_decommissioned)

    def test_aggregation_packs_commissioned_units(self):
        """A container aggregates the units that it holds."""
        units = self._generate(quantity=4)
        units.action_commission()
        sscc = gs1.build_sscc("0361234", "3", "10001")
        container = self.env["ls.pharma.aggregation"].create(
            {
                "sscc": sscc,
                "level": "case",
                "batch_id": self.batch.id,
                "serialization_ids": [(6, 0, units.ids)],
            }
        )
        self.assertEqual(container.unit_count, 4)
        container.action_pack()
        self.assertEqual(container.state, "packed")
        self.assertEqual(set(units.mapped("state")), {"aggregated"})
        self.assertEqual(
            container.element_string, gs1.build_sscc_element_string(sscc)
        )

    def test_empty_container_cannot_be_packed(self):
        """A container that holds nothing cannot be packed."""
        container = self.env["ls.pharma.aggregation"].create(
            {
                "sscc": gs1.build_sscc("0361234", "3", "10002"),
                "level": "case",
                "batch_id": self.batch.id,
            }
        )
        with self.assertRaises(UserError):
            container.action_pack()

    def test_uncommissioned_units_cannot_be_packed(self):
        """A container holding an uncommissioned unit cannot be packed."""
        units = self._generate(quantity=2)
        container = self.env["ls.pharma.aggregation"].create(
            {
                "sscc": gs1.build_sscc("0361234", "3", "10003"),
                "level": "case",
                "batch_id": self.batch.id,
                "serialization_ids": [(6, 0, units.ids)],
            }
        )
        with self.assertRaises(UserError):
            container.action_pack()

    def test_invalid_sscc_is_refused(self):
        """A Serial Shipping Container Code with a wrong check digit fails."""
        with self.assertRaises(UserError):
            self.env["ls.pharma.aggregation"].create(
                {
                    "sscc": "303612340000123450",
                    "level": "case",
                    "batch_id": self.batch.id,
                }
            )

    def test_disaggregation_returns_units_to_commissioned(self):
        """Disaggregating a container releases the units that it held."""
        units = self._generate(quantity=3)
        units.action_commission()
        container = self.env["ls.pharma.aggregation"].create(
            {
                "sscc": gs1.build_sscc("0361234", "3", "10004"),
                "level": "case",
                "batch_id": self.batch.id,
                "serialization_ids": [(6, 0, units.ids)],
            }
        )
        container.action_pack()
        container.action_disaggregate()
        self.assertEqual(container.state, "disaggregated")
        self.assertEqual(set(units.mapped("state")), {"commissioned"})
