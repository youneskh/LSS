# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Tests of the scheduled actions of the calibration module."""

from odoo.tests import tagged

from .common import LsCalibrationCommon


@tagged("post_install", "-at_install")
class TestLsCalibrationCron(LsCalibrationCommon):
    """Behaviour of the notification and generation scheduled actions."""

    def test_notify_due_creates_one_activity(self):
        """An activity is scheduled once for a due instrument."""
        self.plan.write({"start_date": self.today})
        instrument_model = self.env["ls.calibration.instrument"]
        scheduled = instrument_model._cron_notify_due_calibrations()
        self.assertGreaterEqual(scheduled, 1)
        activities = self.instrument.activity_ids
        self.assertTrue(activities)
        again = instrument_model._cron_notify_due_calibrations()
        self.assertEqual(again, 0)
        self.assertEqual(len(self.instrument.activity_ids), len(activities))

    def test_notify_due_ignores_valid_instruments(self):
        """An instrument calibrated in time receives no activity."""
        self.plan.write({"start_date": self._months_later(6)})
        self.env["ls.calibration.instrument"]._cron_notify_due_calibrations()
        self.assertFalse(self.instrument.activity_ids)

    def test_notify_due_ignores_instruments_out_of_service(self):
        """An instrument out of service receives no activity."""
        self.plan.write({"start_date": self.today})
        self.instrument.action_set_out_of_service()
        self.env["ls.calibration.instrument"]._cron_notify_due_calibrations()
        self.assertFalse(self.instrument.activity_ids)

    def test_generate_records_creates_one_record(self):
        """A due plan without open record generates a calibration record."""
        self.plan.write({"start_date": self.today})
        plan_model = self.env["ls.calibration.plan"]
        created = plan_model._cron_generate_calibration_records()
        self.assertGreaterEqual(created, 1)
        self.assertEqual(len(self.plan.record_ids), 1)
        record = self.plan.record_ids
        self.assertEqual(record.state, "draft")
        self.assertEqual(len(record.line_ids), len(self.plan.point_ids))

    def test_generate_records_skips_open_records(self):
        """No second record is generated while one is still open."""
        self.plan.write({"start_date": self.today})
        plan_model = self.env["ls.calibration.plan"]
        plan_model._cron_generate_calibration_records()
        plan_model._cron_generate_calibration_records()
        self.assertEqual(len(self.plan.record_ids), 1)

    def test_generate_records_uses_the_horizon_parameter(self):
        """The generation horizon is read from the system parameters."""
        self.plan.write({"start_date": self._months_later(2)})
        plan_model = self.env["ls.calibration.plan"]
        self.assertEqual(plan_model._cron_generate_calibration_records(), 0)
        self.env["ir.config_parameter"].sudo().set_param(
            "ls_calibration.generation_horizon_days", "120"
        )
        self.assertGreaterEqual(
            plan_model._cron_generate_calibration_records(), 1
        )

    def test_generate_records_ignores_inactive_plans(self):
        """A suspended plan does not generate calibration records."""
        self.plan.write({"start_date": self.today})
        self.plan.action_suspend()
        self.assertEqual(
            self.env["ls.calibration.plan"]._cron_generate_calibration_records(),
            0,
        )

    def test_cron_records_are_installed(self):
        """Both scheduled actions are created by the module."""
        notify_cron = self.env.ref(
            "ls_calibration.ls_calibration_cron_notify_due"
        )
        generate_cron = self.env.ref(
            "ls_calibration.ls_calibration_cron_generate_records"
        )
        self.assertTrue(notify_cron.active)
        self.assertTrue(generate_cron.active)
        self.assertEqual(notify_cron.interval_type, "days")
        self.assertEqual(generate_cron.interval_type, "days")

    def test_sequences_are_installed(self):
        """The four sequences of the module are created."""
        codes = [
            "ls.calibration.instrument",
            "ls.calibration.plan",
            "ls.calibration.record",
            "ls.calibration.certificate",
        ]
        for code in codes:
            with self.subTest(code=code):
                sequence = self.env["ir.sequence"].search(
                    [("code", "=", code)], limit=1
                )
                self.assertTrue(sequence)

    def test_last_calibration_date_of_instrument(self):
        """The instrument shows the date of its last approved record."""
        record = self._create_record()
        self._fill_readings(record)
        record.action_start()
        record.action_submit_review()
        record.with_user(self.user_manager).action_approve()
        self.assertEqual(
            self.instrument.last_calibration_date,
            record.calibration_date.date(),
        )
