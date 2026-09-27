# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Tests of the instrument register."""

from dateutil.relativedelta import relativedelta

from odoo.exceptions import UserError
from odoo.tests import tagged

from .common import LsCalibrationCommon


@tagged("post_install", "-at_install")
class TestLsCalibrationInstrument(LsCalibrationCommon):
    """Behaviour of the ``ls.calibration.instrument`` model."""

    def test_sequence_is_assigned_on_create(self):
        """The reference is taken from the dedicated sequence."""
        self.assertTrue(self.instrument.code.startswith("INS/"))
        self.assertNotEqual(self.instrument.code, "/")

    def test_explicit_code_is_kept(self):
        """A reference given by the user is not overwritten."""
        instrument = self.env["ls.calibration.instrument"].create(
            {"name": "Manual reference", "code": "INS-MANUAL-1"}
        )
        self.assertEqual(instrument.code, "INS-MANUAL-1")

    def test_display_name(self):
        """The display name is prefixed by the reference."""
        self.assertEqual(
            self.instrument.display_name,
            f"[{self.instrument.code}] {self.instrument.name}",
        )

    def test_copy_resets_reference(self):
        """A duplicated instrument receives a new reference."""
        duplicate = self.instrument.copy()
        self.assertNotEqual(duplicate.code, self.instrument.code)
        self.assertTrue(duplicate.code.startswith("INS/"))

    def test_counts(self):
        """The stat buttons count the related documents."""
        self.assertEqual(self.instrument.plan_count, 1)
        self.assertEqual(self.instrument.record_count, 0)
        self.assertEqual(self.instrument.certificate_count, 0)

    def test_status_not_scheduled(self):
        """An instrument without active plan is not scheduled."""
        instrument = self.env["ls.calibration.instrument"].create(
            {"name": "Without plan", "state": "in_service"}
        )
        self.assertEqual(instrument.calibration_status, "not_scheduled")

    def test_status_due_soon_and_overdue(self):
        """The status is derived from the next due date."""
        self.plan.write({"start_date": self.today})
        self.assertEqual(self.instrument.calibration_status, "due_soon")
        self.plan.write({"start_date": self.today - relativedelta(days=1)})
        self.assertEqual(self.instrument.calibration_status, "overdue")

    def test_status_valid(self):
        """A due date beyond the lead time gives a valid status."""
        self.plan.write({"start_date": self._months_later(6)})
        self.assertEqual(self.instrument.calibration_status, "valid")

    def test_status_not_applicable(self):
        """A retired instrument is not applicable for calibration."""
        self.instrument.action_retire()
        self.assertEqual(self.instrument.calibration_status, "not_applicable")

    def test_search_calibration_status(self):
        """The status field is searchable through its search method."""
        self.plan.write({"start_date": self.today})
        model = self.env["ls.calibration.instrument"]
        due_soon = model.search([("calibration_status", "=", "due_soon")])
        self.assertIn(self.instrument, due_soon)
        not_due_soon = model.search([("calibration_status", "!=", "due_soon")])
        self.assertNotIn(self.instrument, not_due_soon)
        in_list = model.search(
            [("calibration_status", "in", ["due_soon", "overdue"])]
        )
        self.assertIn(self.instrument, in_list)
        not_in_list = model.search(
            [("calibration_status", "not in", ["due_soon", "overdue"])]
        )
        self.assertNotIn(self.instrument, not_in_list)

    def test_search_calibration_status_unsupported_operator(self):
        """An unsupported operator is refused."""
        with self.assertRaises(UserError):
            self.env["ls.calibration.instrument"].search(
                [("calibration_status", "like", "due")]
            )

    def test_state_workflow(self):
        """The life cycle of the instrument follows its state machine."""
        instrument = self.env["ls.calibration.instrument"].create(
            {"name": "Life cycle"}
        )
        self.assertEqual(instrument.state, "draft")
        instrument.action_set_in_service()
        self.assertEqual(instrument.state, "in_service")
        instrument.action_set_out_of_service()
        self.assertEqual(instrument.state, "out_of_service")
        instrument.action_set_in_service()
        self.assertEqual(instrument.state, "in_service")
        instrument.action_retire()
        self.assertEqual(instrument.state, "retired")
        instrument.action_reset_to_draft()
        self.assertEqual(instrument.state, "draft")

    def test_state_workflow_errors(self):
        """Invalid state transitions are refused."""
        instrument = self.env["ls.calibration.instrument"].create(
            {"name": "Invalid transitions"}
        )
        with self.assertRaises(UserError):
            instrument.action_set_out_of_service()
        with self.assertRaises(UserError):
            instrument.action_reset_to_draft()
        instrument.action_retire()
        with self.assertRaises(UserError):
            instrument.action_retire()

    def test_retire_makes_plans_obsolete(self):
        """Retiring an instrument closes its active calibration plans."""
        self.instrument.action_retire()
        self.assertEqual(self.plan.state, "obsolete")
        self.assertFalse(self.plan.next_due_date)

    def test_action_view_plans(self):
        """The stat button returns a filtered action."""
        action = self.instrument.action_view_plans()
        self.assertEqual(action["res_model"], "ls.calibration.plan")
        self.assertEqual(
            action["domain"], [("instrument_id", "=", self.instrument.id)]
        )

    def test_action_view_records_and_certificates(self):
        """The record and certificate stat buttons return actions."""
        record_action = self.instrument.action_view_records()
        self.assertEqual(record_action["res_model"], "ls.calibration.record")
        certificate_action = self.instrument.action_view_certificates()
        self.assertEqual(
            certificate_action["res_model"], "ls.calibration.certificate"
        )
