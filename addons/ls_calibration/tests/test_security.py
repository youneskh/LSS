# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Tests of the access rights and of the record rules."""

from odoo.exceptions import AccessError, UserError
from odoo.tests import tagged
from odoo.tools import mute_logger

from .common import LsCalibrationCommon


@tagged("post_install", "-at_install")
class TestLsCalibrationSecurity(LsCalibrationCommon):
    """Access rights granted to the three calibration groups."""

    @mute_logger("odoo.addons.base.models.ir_model")
    def test_viewer_cannot_create_instrument(self):
        """A viewer has read-only access to the instrument register."""
        with self.assertRaises(AccessError):
            self.env["ls.calibration.instrument"].with_user(
                self.user_viewer
            ).create({"name": "Created by a viewer"})

    @mute_logger("odoo.addons.base.models.ir_model")
    def test_viewer_cannot_create_record(self):
        """A viewer cannot record a calibration."""
        with self.assertRaises(AccessError):
            self.env["ls.calibration.record"].with_user(
                self.user_viewer
            ).create({"instrument_id": self.instrument.id})

    def test_viewer_can_read(self):
        """A viewer reads the instruments, plans and records."""
        instrument = self.instrument.with_user(self.user_viewer)
        self.assertEqual(instrument.name, self.instrument.name)
        plan = self.plan.with_user(self.user_viewer)
        self.assertEqual(plan.name, self.plan.name)

    @mute_logger("odoo.addons.base.models.ir_model")
    def test_technician_cannot_write_instrument(self):
        """A technician does not maintain the instrument master data."""
        with self.assertRaises(AccessError):
            self.instrument.with_user(self.user_technician).write(
                {"location": "Moved by a technician"}
            )

    @mute_logger("odoo.addons.base.models.ir_model")
    def test_technician_cannot_write_plan(self):
        """A technician does not maintain the calibration plans."""
        with self.assertRaises(AccessError):
            self.plan.with_user(self.user_technician).write(
                {"interval_number": 24}
            )

    def test_technician_can_create_record(self):
        """A technician records a calibration and its readings."""
        record = self.env["ls.calibration.record"].with_user(
            self.user_technician
        ).create(
            {
                "instrument_id": self.instrument.id,
                "plan_id": self.plan.id,
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "name": "Point 1",
                            "nominal_value": 10.0,
                            "tolerance_value": 0.01,
                            "as_found_value": 10.0,
                            "as_left_value": 10.0,
                        },
                    )
                ],
            }
        )
        self.assertEqual(record.state, "draft")
        self.assertEqual(len(record.line_ids), 1)

    @mute_logger("odoo.addons.base.models.ir_model")
    def test_technician_cannot_delete_record(self):
        """A technician cancels a record instead of deleting it."""
        record = self._create_record()
        with self.assertRaises(AccessError):
            record.with_user(self.user_technician).unlink()

    def test_technician_cannot_approve(self):
        """The approval is reserved to the calibration manager."""
        record = self._create_record()
        self._fill_readings(record)
        record.action_start()
        record.action_submit_review()
        with self.assertRaises(UserError):
            record.with_user(self.user_technician).action_approve()

    def test_manager_can_approve(self):
        """The calibration manager approves the record."""
        record = self._create_record()
        self._fill_readings(record)
        record.action_start()
        record.action_submit_review()
        record.with_user(self.user_manager).action_approve()
        self.assertEqual(record.state, "approved")

    def test_group_hierarchy(self):
        """Each group implies the rights of the lower one."""
        self.assertTrue(
            self.user_manager.has_group(
                "ls_calibration.group_ls_calibration_technician"
            )
        )
        self.assertTrue(
            self.user_manager.has_group(
                "ls_calibration.group_ls_calibration_viewer"
            )
        )
        self.assertTrue(
            self.user_technician.has_group(
                "ls_calibration.group_ls_calibration_viewer"
            )
        )
        self.assertFalse(
            self.user_technician.has_group(
                "ls_calibration.group_ls_calibration_manager"
            )
        )

    def test_multi_company_rules_exist(self):
        """Every model of the module carries a multi-company record rule."""
        rules = self.env["ir.rule"].search(
            [
                (
                    "model_id.model",
                    "in",
                    [
                        "ls.calibration.instrument",
                        "ls.calibration.plan",
                        "ls.calibration.plan.point",
                        "ls.calibration.record",
                        "ls.calibration.record.line",
                        "ls.calibration.certificate",
                    ],
                )
            ]
        )
        self.assertEqual(len(rules), 6)
        for rule in rules:
            self.assertIn("company_id", rule.domain_force)
            self.assertIn("company_ids", rule.domain_force)
