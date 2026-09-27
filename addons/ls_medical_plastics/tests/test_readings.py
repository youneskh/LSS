# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Tests for the append-only behaviour of parameter readings."""

from odoo.exceptions import ValidationError
from odoo.tests import tagged

from .common import MedicalPlasticsCommon


@tagged("post_install", "-at_install")
class TestReadings(MedicalPlasticsCommon):
    """Immutability, criteria freezing and the correction chain."""

    def setUp(self):
        """Create a run in setup and expose its melt temperature parameter."""
        super().setUp()
        self.run = self._create_run()
        self.run.action_start_setup()
        self.run.action_start_startup_check()
        self.melt_line = self.spec.line_ids.filtered(
            lambda item: item.code == "MELT-T"
        )

    def _capture(self, value, **overrides):
        """Create one reading of the melt temperature parameter.

        :param float value: measured numeric value.
        :param overrides: field values overriding the defaults.
        :rtype: recordset of ``ls.mp.injection_molding.reading``
        """
        values = {
            "run_id": self.run.id,
            "parameter_line_id": self.melt_line.id,
            "reading_type": "startup",
            "value_numeric": value,
        }
        values.update(overrides)
        return self.env["ls.mp.injection_molding.reading"].create(values)

    def test_criteria_frozen_at_capture(self):
        """A reading copies the acceptance criteria in force when taken."""
        reading = self._capture(220.0)
        self.assertEqual(reading.parameter_name, "Melt Temperature")
        self.assertEqual(reading.parameter_code, "MELT-T")
        self.assertEqual(reading.parameter_uom, "degC")
        self.assertEqual(reading.min_value, 210.0)
        self.assertEqual(reading.max_value, 230.0)
        self.assertTrue(reading.is_critical)

    def test_in_tolerance_computed(self):
        """In-tolerance is evaluated against the frozen criteria."""
        self.assertTrue(self._capture(220.0).in_tolerance)
        self.assertFalse(self._capture(260.0).in_tolerance)

    def test_later_specification_change_does_not_alter_history(self):
        """Superseding the specification leaves historical readings unchanged."""
        reading = self._capture(220.0)
        action = self.spec.action_create_new_version()
        new_spec = self.env["ls.mp.molding_parameter"].browse(action["res_id"])
        new_spec.line_ids.filtered(
            lambda item: item.code == "MELT-T"
        ).write({"min_value": 100.0, "target_value": 150.0, "max_value": 200.0})
        reading.invalidate_recordset()
        self.assertEqual(reading.min_value, 210.0)
        self.assertEqual(reading.max_value, 230.0)
        self.assertTrue(reading.in_tolerance)

    def test_reading_cannot_be_modified(self):
        """A captured reading is immutable."""
        reading = self._capture(220.0)
        with self.assertRaises(ValidationError):
            reading.write({"value_numeric": 225.0})

    def test_reading_comment_cannot_be_modified(self):
        """Even a comment cannot be edited after capture."""
        reading = self._capture(220.0)
        with self.assertRaises(ValidationError):
            reading.write({"comment": "Adjusted afterwards."})

    def test_reading_cannot_be_deleted(self):
        """A captured reading cannot be deleted."""
        reading = self._capture(220.0)
        with self.assertRaises(ValidationError):
            reading.unlink()

    def test_correction_requires_reason(self):
        """Superseding a reading requires a stated reason."""
        original = self._capture(220.0)
        with self.assertRaises(ValidationError):
            self._capture(222.0, supersedes_id=original.id)

    def test_correction_creates_chain(self):
        """A correction supersedes the original without erasing it."""
        original = self._capture(260.0)
        correction = self._capture(
            220.0,
            supersedes_id=original.id,
            correction_reason="Transcription error at capture.",
        )
        self.assertTrue(original.is_superseded)
        self.assertFalse(correction.is_superseded)
        self.assertIn(correction, original.superseded_by_ids)
        self.assertEqual(original.value_numeric, 260.0)

    def test_correction_must_match_parameter(self):
        """A correction must address the same parameter."""
        original = self._capture(220.0)
        cooling = self.spec.line_ids.filtered(lambda item: item.code == "COOL-T")
        with self.assertRaises(ValidationError):
            self.env["ls.mp.injection_molding.reading"].create(
                {
                    "run_id": self.run.id,
                    "parameter_line_id": cooling.id,
                    "reading_type": "startup",
                    "value_numeric": 10.0,
                    "supersedes_id": original.id,
                    "correction_reason": "Wrong parameter.",
                }
            )

    def test_search_is_superseded(self):
        """The superseded flag can be used as a search criterion."""
        original = self._capture(260.0)
        self._capture(
            220.0,
            supersedes_id=original.id,
            correction_reason="Corrected after re-reading the display.",
        )
        superseded = self.env["ls.mp.injection_molding.reading"].search(
            [("run_id", "=", self.run.id), ("is_superseded", "=", True)]
        )
        effective = self.env["ls.mp.injection_molding.reading"].search(
            [("run_id", "=", self.run.id), ("is_superseded", "=", False)]
        )
        self.assertIn(original, superseded)
        self.assertNotIn(original, effective)

    def test_superseded_reading_excluded_from_statistics(self):
        """Superseded readings do not contribute to the deviation count."""
        original = self._capture(260.0)
        self.assertTrue(self.run.has_deviation)
        self._capture(
            220.0,
            supersedes_id=original.id,
            correction_reason="Corrected after instrument re-read.",
        )
        self.run.invalidate_recordset()
        self.assertFalse(self.run.has_deviation)
        self.assertEqual(self.run.out_of_tolerance_count, 0)

    def test_reading_rejected_on_closed_run(self):
        """A closed run cannot accept new readings."""
        run = self._create_run()
        self._run_to_completed(run)
        run.with_user(self.user_manager).action_review()
        run.with_user(self.user_manager).action_close()
        with self.assertRaises(ValidationError):
            self.env["ls.mp.injection_molding.reading"].create(
                {
                    "run_id": run.id,
                    "parameter_line_id": self.melt_line.id,
                    "reading_type": "in_process",
                    "value_numeric": 220.0,
                }
            )

    def test_qualitative_reading_requires_value(self):
        """A qualitative parameter reading requires an observed value."""
        line = self.env["ls.mp.molding_parameter.line"].create(
            {
                "spec_id": self.spec.id,
                "name": "Surface Appearance",
                "code": "APPEAR",
                "parameter_uom": "n/a",
                "value_type": "qualitative",
                "expected_text": "Conforming",
                "monitoring_frequency": "per_shift",
            }
        )
        with self.assertRaises(ValidationError):
            self.env["ls.mp.injection_molding.reading"].create(
                {
                    "run_id": self.run.id,
                    "parameter_line_id": line.id,
                    "reading_type": "in_process",
                }
            )

    def test_qualitative_reading_evaluated(self):
        """A qualitative reading matches its expected value case-insensitively."""
        line = self.env["ls.mp.molding_parameter.line"].create(
            {
                "spec_id": self.spec.id,
                "name": "Colour Check",
                "code": "COLOUR",
                "parameter_uom": "n/a",
                "value_type": "qualitative",
                "expected_text": "Conforming",
                "monitoring_frequency": "per_shift",
            }
        )
        matching = self.env["ls.mp.injection_molding.reading"].create(
            {
                "run_id": self.run.id,
                "parameter_line_id": line.id,
                "reading_type": "in_process",
                "value_text": "conforming",
            }
        )
        self.assertTrue(matching.in_tolerance)
        failing = self.env["ls.mp.injection_molding.reading"].create(
            {
                "run_id": self.run.id,
                "parameter_line_id": line.id,
                "reading_type": "in_process",
                "value_text": "Off shade",
            }
        )
        self.assertFalse(failing.in_tolerance)
