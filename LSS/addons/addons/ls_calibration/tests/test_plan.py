# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Tests of the calibration plan and of its test points."""

from dateutil.relativedelta import relativedelta

from odoo.exceptions import UserError
from odoo.tests import tagged

from .common import LsCalibrationCommon


@tagged("post_install", "-at_install")
class TestLsCalibrationPlan(LsCalibrationCommon):
    """Behaviour of the ``ls.calibration.plan`` model."""

    def test_sequence_and_display_name(self):
        """The plan receives a reference and a readable display name."""
        self.assertTrue(self.plan.name.startswith("CP/"))
        self.assertIn(self.instrument.name, self.plan.display_name)

    def test_add_interval_units(self):
        """Every interval unit shifts the date accordingly."""
        cases = [
            ("day", 10, relativedelta(days=10)),
            ("week", 2, relativedelta(weeks=2)),
            ("month", 6, relativedelta(months=6)),
            ("year", 1, relativedelta(years=1)),
        ]
        for unit, number, delta in cases:
            with self.subTest(unit=unit):
                self.plan.write(
                    {"interval_uom": unit, "interval_number": number}
                )
                self.assertEqual(
                    self.plan._add_interval(self.today), self.today + delta
                )

    def test_next_due_date_without_record(self):
        """Without approved record the due date is the start date."""
        self.assertEqual(self.plan.next_due_date, self.plan.start_date)
        self.assertFalse(self.plan.last_calibration_date)

    def test_next_due_date_after_approval(self):
        """After approval the due date is shifted by the interval."""
        record = self._create_record()
        self._fill_readings(record)
        record.action_start()
        record.action_submit_review()
        record.with_user(self.user_manager).action_approve()
        expected = self.plan._add_interval(record.calibration_date.date())
        self.assertEqual(self.plan.next_due_date, expected)
        self.assertEqual(
            self.plan.last_calibration_date, record.calibration_date.date()
        )
        self.assertEqual(self.instrument.next_calibration_date, expected)

    def test_activation_requires_points(self):
        """A plan without test point cannot be activated."""
        plan = self.env["ls.calibration.plan"].create(
            {
                "instrument_id": self.instrument.id,
                "interval_number": 1,
                "interval_uom": "year",
                "start_date": self.today,
            }
        )
        with self.assertRaises(UserError):
            plan.action_activate()

    def test_state_workflow(self):
        """The life cycle of the plan follows its state machine."""
        self.assertEqual(self.plan.state, "active")
        self.plan.action_suspend()
        self.assertEqual(self.plan.state, "suspended")
        self.assertFalse(self.plan.next_due_date)
        self.plan.action_activate()
        self.assertEqual(self.plan.state, "active")
        self.plan.action_set_obsolete()
        self.assertEqual(self.plan.state, "obsolete")
        self.plan.action_reset_to_draft()
        self.assertEqual(self.plan.state, "draft")

    def test_state_workflow_errors(self):
        """Invalid state transitions are refused."""
        with self.assertRaises(UserError):
            self.plan.action_reset_to_draft()
        self.plan.action_set_obsolete()
        with self.assertRaises(UserError):
            self.plan.action_set_obsolete()
        with self.assertRaises(UserError):
            self.plan.action_suspend()

    def test_create_record_from_plan(self):
        """The plan generates a record carrying its test points."""
        action = self.plan.action_create_calibration_record()
        record = self.env["ls.calibration.record"].browse(action["res_id"])
        self.assertEqual(record.plan_id, self.plan)
        self.assertEqual(record.instrument_id, self.instrument)
        self.assertEqual(len(record.line_ids), len(self.plan.point_ids))
        self.assertEqual(
            sorted(record.line_ids.mapped("nominal_value")),
            sorted(self.plan.point_ids.mapped("nominal_value")),
        )

    def test_create_record_requires_active_plan(self):
        """An inactive plan cannot generate a calibration record."""
        self.plan.action_suspend()
        with self.assertRaises(UserError):
            self.plan.action_create_calibration_record()

    def test_copy_resets_reference_and_state(self):
        """A duplicated plan restarts in the draft state."""
        duplicate = self.plan.copy()
        self.assertEqual(duplicate.state, "draft")
        self.assertNotEqual(duplicate.name, self.plan.name)
        self.assertEqual(len(duplicate.point_ids), len(self.plan.point_ids))

    def test_point_limits_absolute(self):
        """Absolute tolerances give symmetric limits."""
        point = self.plan.point_ids[0]
        self.assertAlmostEqual(point.limit_min, 9.99, places=6)
        self.assertAlmostEqual(point.limit_max, 10.01, places=6)

    def test_point_limits_relative(self):
        """Relative tolerances are a percentage of the nominal value."""
        point = self.plan.point_ids[0]
        point.write({"tolerance_type": "relative", "tolerance_value": 1.0})
        self.assertAlmostEqual(point.limit_min, 9.9, places=6)
        self.assertAlmostEqual(point.limit_max, 10.1, places=6)

    def test_point_display_name(self):
        """The test point shows its nominal value and unit."""
        point = self.plan.point_ids[0]
        self.assertIn("10.0", point.display_name)
        self.assertIn("g", point.display_name)

    def test_record_count(self):
        """The plan counts the calibration records it generated."""
        self.assertEqual(self.plan.record_count, 0)
        self._create_record()
        self.assertEqual(self.plan.record_count, 1)

    def test_action_view_records(self):
        """The stat button returns a filtered action."""
        action = self.plan.action_view_records()
        self.assertEqual(action["domain"], [("plan_id", "=", self.plan.id)])
