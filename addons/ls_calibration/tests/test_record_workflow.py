# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Tests of the calibration record workflow and of its data integrity rules."""

from odoo import fields
from odoo.exceptions import UserError
from odoo.tests import tagged

from .common import LsCalibrationCommon


@tagged("post_install", "-at_install")
class TestLsCalibrationRecordWorkflow(LsCalibrationCommon):
    """Behaviour of the ``ls.calibration.record`` model."""

    def test_full_workflow(self):
        """A compliant record can be started, submitted and approved."""
        record = self._create_record()
        self.assertTrue(record.name.startswith("CAL/"))
        self.assertEqual(record.state, "draft")
        self._fill_readings(record)
        record.action_start()
        self.assertEqual(record.state, "in_progress")
        record.with_user(self.user_technician).action_submit_review()
        self.assertEqual(record.state, "to_review")
        self.assertEqual(record.submitted_by_id, self.user_technician)
        self.assertTrue(record.submission_date)
        record.with_user(self.user_manager).action_approve()
        self.assertEqual(record.state, "approved")
        self.assertEqual(record.approved_by_id, self.user_manager)
        self.assertTrue(record.approval_date)

    def test_result_pass(self):
        """Readings inside the limits give a pass result."""
        record = self._create_record()
        self._fill_readings(record)
        self.assertEqual(record.as_found_status, "in_tolerance")
        self.assertEqual(record.as_left_status, "in_tolerance")
        self.assertEqual(record.result, "pass")

    def test_result_pass_after_adjustment(self):
        """An out-of-tolerance as-found corrected by an adjustment passes."""
        record = self._create_record()
        self._fill_readings(record, as_found=[10.5, 100.0], as_left=[10.0, 100.0])
        self.assertEqual(record.as_found_status, "out_of_tolerance")
        self.assertEqual(record.as_left_status, "in_tolerance")
        self.assertEqual(record.result, "pass_adjusted")

    def test_result_fail(self):
        """An out-of-tolerance as-left reading fails."""
        record = self._create_record()
        self._fill_readings(record, as_found=[10.5, 100.0], as_left=[10.5, 100.0])
        self.assertEqual(record.result, "fail")

    def test_result_without_lines(self):
        """A record without test point has no result."""
        record = self._create_record({"line_ids": []})
        self.assertEqual(record.as_found_status, "not_assessed")
        self.assertFalse(record.result)

    def test_deviations(self):
        """The deviation of each reading is computed."""
        record = self._create_record()
        self._fill_readings(record, as_found=[10.005, 100.0])
        line = record.line_ids[0]
        self.assertAlmostEqual(line.as_found_deviation, 0.005, places=6)
        self.assertTrue(line.as_found_in_tolerance)

    def test_submit_requires_calibration_date(self):
        """The calibration date is mandatory before review."""
        record = self._create_record({"calibration_date": False})
        self._fill_readings(record)
        record.action_start()
        with self.assertRaises(UserError):
            record.action_submit_review()

    def test_submit_requires_performer(self):
        """The performer is mandatory before review."""
        record = self._create_record({"performed_by_id": False})
        self._fill_readings(record)
        record.action_start()
        with self.assertRaises(UserError):
            record.action_submit_review()

    def test_submit_requires_lines(self):
        """A record without test point cannot be submitted."""
        record = self._create_record({"line_ids": []})
        record.action_start()
        with self.assertRaises(UserError):
            record.action_submit_review()

    def test_submit_requires_standard(self):
        """A reference standard is mandatory before review."""
        record = self._create_record({"standard_ids": []})
        self._fill_readings(record)
        record.action_start()
        with self.assertRaises(UserError):
            record.action_submit_review()

    def test_submit_accepts_external_standard(self):
        """An external standard reference replaces a registered standard."""
        record = self._create_record(
            {
                "standard_ids": [],
                "external_standard_reference": "EXT-STD-001",
            }
        )
        self._fill_readings(record)
        record.action_start()
        record.action_submit_review()
        self.assertEqual(record.state, "to_review")

    def test_submit_requires_oot_assessment(self):
        """An out-of-tolerance as-found requires an impact assessment."""
        record = self._create_record()
        self._fill_readings(record, as_found=[10.5, 100.0], as_left=[10.0, 100.0])
        record.action_start()
        with self.assertRaises(UserError):
            record.action_submit_review()
        record.write({"oot_impact_assessment": "No batch impacted."})
        record.action_submit_review()
        self.assertEqual(record.state, "to_review")

    def test_submit_refuses_overdue_standard(self):
        """A standard whose own calibration is overdue is refused."""
        standard_plan = self.env["ls.calibration.plan"].create(
            {
                "instrument_id": self.standard.id,
                "interval_number": 1,
                "interval_uom": "year",
                "start_date": self._months_later(-24),
                "point_ids": [
                    fields.Command.create(
                        {
                            "name": "Standard point",
                            "nominal_value": 10.0,
                            "tolerance_value": 0.001,
                        }
                    )
                ],
            }
        )
        standard_plan.action_activate()
        record = self._create_record()
        self._fill_readings(record)
        record.action_start()
        with self.assertRaises(UserError):
            record.action_submit_review()

    def test_approval_segregation_of_duties(self):
        """The performer cannot approve the record."""
        record = self._create_record(
            {"performed_by_id": self.user_manager.id}
        )
        self._fill_readings(record)
        record.action_start()
        record.action_submit_review()
        with self.assertRaises(UserError):
            record.with_user(self.user_manager).action_approve()

    def test_approved_record_is_locked(self):
        """An approved record can no longer be modified or deleted."""
        record = self._create_record()
        self._fill_readings(record)
        record.action_start()
        record.action_submit_review()
        record.with_user(self.user_manager).action_approve()
        with self.assertRaises(UserError):
            record.write({"conclusion": "Modified after approval"})
        with self.assertRaises(UserError):
            record.unlink()
        with self.assertRaises(UserError):
            record.line_ids[0].write({"as_found_value": 1.0})
        with self.assertRaises(UserError):
            record.line_ids[0].unlink()

    def test_line_cannot_be_added_to_locked_record(self):
        """A test point cannot be added to an approved record."""
        record = self._create_record()
        self._fill_readings(record)
        record.action_start()
        record.action_submit_review()
        record.with_user(self.user_manager).action_approve()
        with self.assertRaises(UserError):
            self.env["ls.calibration.record.line"].create(
                {
                    "record_id": record.id,
                    "name": "Added afterwards",
                    "nominal_value": 1.0,
                    "tolerance_value": 0.1,
                }
            )

    def test_reject_and_reset(self):
        """A rejected record returns to the draft state."""
        record = self._create_record()
        self._fill_readings(record)
        record.action_start()
        record.action_submit_review()
        record.with_user(self.user_manager).action_reject(reason="Wrong standard")
        self.assertEqual(record.state, "rejected")
        self.assertEqual(record.rejection_reason, "Wrong standard")
        record.action_reset_to_draft()
        self.assertEqual(record.state, "draft")
        self.assertFalse(record.submitted_by_id)

    def test_reject_requires_reason(self):
        """A rejection without justification is refused."""
        record = self._create_record()
        self._fill_readings(record)
        record.action_start()
        record.action_submit_review()
        with self.assertRaises(UserError):
            record.with_user(self.user_manager).action_reject()

    def test_cancel(self):
        """A record that will not be completed can be cancelled."""
        record = self._create_record()
        record.action_cancel()
        self.assertEqual(record.state, "cancelled")
        with self.assertRaises(UserError):
            record.write({"conclusion": "Modified after cancellation"})

    def test_unlink_only_in_draft(self):
        """Only a draft record can be deleted."""
        record = self._create_record()
        record.action_start()
        with self.assertRaises(UserError):
            record.unlink()
        record.action_cancel()
        with self.assertRaises(UserError):
            record.unlink()
        draft_record = self._create_record()
        draft_record.unlink()

    def test_invalid_transitions(self):
        """The state machine refuses the transitions it does not allow."""
        record = self._create_record()
        with self.assertRaises(UserError):
            record.action_submit_review()
        with self.assertRaises(UserError):
            record.with_user(self.user_manager).action_approve()
        with self.assertRaises(UserError):
            record.action_reset_to_draft()

    def test_next_due_date_preview(self):
        """The record shows the due date derived from the plan interval."""
        record = self._create_record()
        expected = self.plan._add_interval(record.calibration_date.date())
        self.assertEqual(record.next_due_date, expected)

    def test_onchange_plan_loads_points(self):
        """Selecting a plan loads its test points on an empty record."""
        record_form = self.env["ls.calibration.record"].new(
            {"instrument_id": self.instrument.id, "plan_id": self.plan.id}
        )
        record_form._onchange_plan_id()
        self.assertEqual(len(record_form.line_ids), len(self.plan.point_ids))

    def test_onchange_instrument_resets_plan(self):
        """Changing the instrument clears an inconsistent plan."""
        other_instrument = self.env["ls.calibration.instrument"].create(
            {"name": "Other instrument", "state": "in_service"}
        )
        record_form = self.env["ls.calibration.record"].new(
            {"instrument_id": self.instrument.id, "plan_id": self.plan.id}
        )
        record_form.instrument_id = other_instrument
        record_form._onchange_instrument_id()
        self.assertFalse(record_form.plan_id)

    def test_open_reject_wizard_action(self):
        """The reject button returns the wizard action."""
        record = self._create_record()
        action = record.action_open_reject_wizard()
        self.assertEqual(action["res_model"], "ls.calibration.record.reject")
        self.assertEqual(action["context"]["default_record_id"], record.id)
