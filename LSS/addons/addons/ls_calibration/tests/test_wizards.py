# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Tests of the calibration wizards."""

from odoo.exceptions import UserError
from odoo.tests import tagged

from .common import LsCalibrationCommon


@tagged("post_install", "-at_install")
class TestLsCalibrationWizards(LsCalibrationCommon):
    """Behaviour of the generation and rejection wizards."""

    def test_generate_wizard_creates_records(self):
        """The wizard creates one record per due plan."""
        self.plan.write({"start_date": self.today})
        wizard = self.env["ls.calibration.record.generate"].create(
            {"date_to": self.today}
        )
        action = wizard.action_generate()
        self.assertEqual(action["res_model"], "ls.calibration.record")
        created = self.env["ls.calibration.record"].search(action["domain"])
        self.assertEqual(len(created), 1)
        self.assertEqual(created.plan_id, self.plan)
        self.assertEqual(len(created.line_ids), len(self.plan.point_ids))

    def test_generate_wizard_without_due_plan(self):
        """The wizard refuses to run when no plan is due."""
        self.plan.write({"start_date": self._months_later(12)})
        wizard = self.env["ls.calibration.record.generate"].create(
            {"date_to": self.today}
        )
        with self.assertRaises(UserError):
            wizard.action_generate()

    def test_generate_wizard_skips_open_records(self):
        """The wizard refuses to duplicate an open calibration record."""
        self.plan.write({"start_date": self.today})
        wizard = self.env["ls.calibration.record.generate"].create(
            {"date_to": self.today}
        )
        wizard.action_generate()
        second_wizard = self.env["ls.calibration.record.generate"].create(
            {"date_to": self.today}
        )
        with self.assertRaises(UserError):
            second_wizard.action_generate()

    def test_generate_wizard_restricted_to_selected_plans(self):
        """Only the selected plans are considered."""
        self.plan.write({"start_date": self.today})
        other_plan = self.env["ls.calibration.plan"].create(
            {
                "instrument_id": self.standard.id,
                "interval_number": 1,
                "interval_uom": "year",
                "start_date": self.today,
                "point_ids": [
                    (
                        0,
                        0,
                        {
                            "name": "Standard point",
                            "nominal_value": 10.0,
                            "tolerance_value": 0.001,
                        },
                    )
                ],
            }
        )
        other_plan.action_activate()
        wizard = self.env["ls.calibration.record.generate"].create(
            {"date_to": self.today, "plan_ids": [(6, 0, other_plan.ids)]}
        )
        wizard.action_generate()
        self.assertEqual(len(other_plan.record_ids), 1)
        self.assertEqual(len(self.plan.record_ids), 0)

    def test_generate_wizard_default_get_from_context(self):
        """The plans the wizard is started from are preselected."""
        wizard = (
            self.env["ls.calibration.record.generate"]
            .with_context(
                active_model="ls.calibration.plan", active_ids=self.plan.ids
            )
            .create({})
        )
        self.assertEqual(wizard.plan_ids, self.plan)

    def test_reject_wizard(self):
        """The wizard rejects the record with its justification."""
        record = self._create_record()
        self._fill_readings(record)
        record.action_start()
        record.action_submit_review()
        wizard = (
            self.env["ls.calibration.record.reject"]
            .with_user(self.user_manager)
            .create({"record_id": record.id, "reason": "Standard not traceable"})
        )
        result = wizard.action_reject()
        self.assertEqual(result["type"], "ir.actions.act_window_close")
        self.assertEqual(record.state, "rejected")
        self.assertEqual(record.rejection_reason, "Standard not traceable")
