# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Tests of the tolerance algebra and the acceptance limits."""

from odoo.exceptions import UserError, ValidationError
from odoo.tests import tagged

from .common import CalibrationCommon


@tagged("post_install", "-at_install")
class TestCalibrationTolerance(CalibrationCommon):
    """Conversion of declared tolerances into acceptance limits."""

    def test_absolute_tolerance(self):
        """An absolute tolerance is applied directly in measurement units."""
        point = self.env["ls.calibration.point"].create(
            {
                "name": "Absolute point",
                "instrument_id": self.instrument.id,
                "nominal_value": 50.0,
                "tolerance_type": "absolute",
                "tolerance_value": 0.25,
            }
        )
        self.assertAlmostEqual(point.tolerance_absolute, 0.25)
        self.assertAlmostEqual(point.lower_limit, 49.75)
        self.assertAlmostEqual(point.upper_limit, 50.25)

    def test_percent_of_reading_tolerance(self):
        """A percent-of-reading tolerance scales with the nominal value."""
        point = self.env["ls.calibration.point"].create(
            {
                "name": "Percent of reading point",
                "instrument_id": self.instrument.id,
                "nominal_value": 80.0,
                "tolerance_type": "percent_of_reading",
                "tolerance_value": 0.5,
            }
        )
        # 0.5 % of 80 = 0.4
        self.assertAlmostEqual(point.tolerance_absolute, 0.4)
        self.assertAlmostEqual(point.lower_limit, 79.6)
        self.assertAlmostEqual(point.upper_limit, 80.4)

    def test_percent_of_span_tolerance(self):
        """A percent-of-span tolerance scales with the instrument span."""
        point = self.env["ls.calibration.point"].create(
            {
                "name": "Percent of span point",
                "instrument_id": self.instrument.id,
                "nominal_value": 100.0,
                "tolerance_type": "percent_of_span",
                "tolerance_value": 1.0,
            }
        )
        # Instrument span is 200; 1 % of span = 2.0
        self.assertAlmostEqual(point.tolerance_absolute, 2.0)
        self.assertAlmostEqual(point.lower_limit, 98.0)
        self.assertAlmostEqual(point.upper_limit, 102.0)

    def test_percent_is_not_a_ratio(self):
        """A percentage tolerance of 0.5 means 0.5 %, not 50 %.

        This guards a defect pattern seen elsewhere in the suite, where a
        percentage field was interpreted as a 0-to-1 ratio.
        """
        point = self.env["ls.calibration.point"].create(
            {
                "name": "Percent semantics",
                "instrument_id": self.instrument.id,
                "nominal_value": 100.0,
                "tolerance_type": "percent_of_reading",
                "tolerance_value": 0.5,
            }
        )
        self.assertAlmostEqual(point.tolerance_absolute, 0.5)
        self.assertNotAlmostEqual(point.tolerance_absolute, 50.0)

    def test_negative_tolerance_rejected(self):
        """A negative tolerance is refused by the database constraint."""
        with self.assertRaises(Exception):
            self.env["ls.calibration.point"].create(
                {
                    "name": "Negative tolerance",
                    "instrument_id": self.instrument.id,
                    "nominal_value": 10.0,
                    "tolerance_type": "absolute",
                    "tolerance_value": -1.0,
                }
            )
            self.env.flush_all()

    def test_nominal_outside_range_rejected(self):
        """A nominal value outside the instrument range is refused."""
        with self.assertRaises(ValidationError):
            self.env["ls.calibration.point"].create(
                {
                    "name": "Out of range",
                    "instrument_id": self.instrument.id,
                    "nominal_value": 500.0,
                    "tolerance_type": "absolute",
                    "tolerance_value": 0.1,
                }
            )

    def test_percent_of_span_requires_span(self):
        """A percent-of-span tolerance needs a non-zero instrument span."""
        instrument = self.env["ls.calibration.instrument"].create(
            {
                "name": "Zero span device",
                "category_id": self.category.id,
                "range_min": 0.0,
                "range_max": 0.0,
            }
        )
        with self.assertRaises(ValidationError):
            self.env["ls.calibration.point"].create(
                {
                    "name": "Span point",
                    "instrument_id": instrument.id,
                    "nominal_value": 0.0,
                    "tolerance_type": "percent_of_span",
                    "tolerance_value": 1.0,
                }
            )

    def test_is_within_tolerance_boundaries(self):
        """Values exactly on a limit are inside tolerance."""
        point = self.point_mid
        self.assertTrue(point.is_within_tolerance(point.lower_limit))
        self.assertTrue(point.is_within_tolerance(point.upper_limit))
        self.assertTrue(point.is_within_tolerance(point.nominal_value))
        self.assertFalse(
            point.is_within_tolerance(point.upper_limit + 0.001)
        )
        self.assertFalse(
            point.is_within_tolerance(point.lower_limit - 0.001)
        )

    def test_duplicate_point_name_rejected(self):
        """Two points of one instrument cannot share a name."""
        with self.assertRaises(Exception):
            self.env["ls.calibration.point"].create(
                {
                    "name": self.point_mid.name,
                    "instrument_id": self.instrument.id,
                    "nominal_value": 50.0,
                    "tolerance_type": "absolute",
                    "tolerance_value": 0.1,
                }
            )
            self.env.flush_all()

    def test_acceptance_criteria_frozen_after_use(self):
        """Acceptance criteria cannot change once used in a committed record."""
        record = self._create_record()
        self._perform_and_submit(record)
        with self.assertRaises(UserError):
            self.point_mid.tolerance_value = 5.0

    def test_point_may_still_be_renamed_after_use(self):
        """Non-acceptance fields remain editable after use."""
        record = self._create_record()
        self._perform_and_submit(record)
        self.point_mid.name = "Renamed mid-scale"
        self.assertEqual(self.point_mid.name, "Renamed mid-scale")

    def test_point_with_readings_cannot_be_deleted(self):
        """A point carrying readings cannot be deleted."""
        self._create_record()
        with self.assertRaises(UserError):
            self.point_mid.unlink()
