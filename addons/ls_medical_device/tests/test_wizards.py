# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Tests of the wizards of the module."""

from datetime import date

from odoo.exceptions import UserError
from odoo.tests import tagged

from .common import MedicalDeviceCommon


@tagged("post_install", "-at_install")
class TestDeviceStateWizard(MedicalDeviceCommon):
    """Behaviour of ``ls.md.device.state.wizard``."""

    def test_apply_records_justification(self):
        """Applying a transition stores the justification on the device."""
        wizard = (
            self.env["ls.md.device.state.wizard"]
            .with_user(self.user_regulatory)
            .create(
                {
                    "device_id": self.device_iia.id,
                    "target_state": "development",
                    "reason": "Design inputs approved.",
                    "effective_date": date.today(),
                }
            )
        )
        wizard.action_apply()
        self.device_iia.invalidate_recordset()
        self.assertEqual(self.device_iia.state, "development")
        self.assertEqual(
            self.device_iia.state_change_reason, "Design inputs approved."
        )

    def test_disallowed_transition_rejected(self):
        """A transition outside the declared map is rejected."""
        wizard = (
            self.env["ls.md.device.state.wizard"]
            .with_user(self.user_regulatory)
            .create(
                {
                    "device_id": self.device_iia.id,
                    "target_state": "on_market",
                    "reason": "Attempted shortcut.",
                    "effective_date": date.today(),
                }
            )
        )
        with self.assertRaises(UserError):
            wizard.action_apply()

    def test_rework_transition_back_to_development(self):
        """A device in conformity assessment can return to development."""
        device = self.device_iia.with_user(self.user_regulatory)
        device.action_start_development()
        device.action_start_conformity_assessment()
        wizard = (
            self.env["ls.md.device.state.wizard"]
            .with_user(self.user_regulatory)
            .create(
                {
                    "device_id": device.id,
                    "target_state": "development",
                    "reason": "Assessment revealed a design gap.",
                    "effective_date": date.today(),
                }
            )
        )
        wizard.action_apply()
        device.invalidate_recordset()
        self.assertEqual(device.state, "development")

    def test_plain_user_cannot_apply(self):
        """A plain user cannot apply a market status change."""
        wizard = (
            self.env["ls.md.device.state.wizard"]
            .with_user(self.user_user)
            .create(
                {
                    "device_id": self.device_iia.id,
                    "target_state": "development",
                    "reason": "Attempted without authority.",
                    "effective_date": date.today(),
                }
            )
        )
        with self.assertRaises(UserError):
            wizard.action_apply()

    def test_withdrawal_records_effective_date(self):
        """Withdrawing through the wizard stores the effective date."""
        device = self.device_iia.with_user(self.user_regulatory)
        device.action_start_development()
        device.action_start_conformity_assessment()
        device.write(
            {"state": "on_market", "market_placement_date": date(2026, 1, 1)}
        )
        wizard = (
            self.env["ls.md.device.state.wizard"]
            .with_user(self.user_regulatory)
            .create(
                {
                    "device_id": device.id,
                    "target_state": "withdrawn",
                    "reason": "Commercial decision.",
                    "effective_date": date(2026, 7, 1),
                }
            )
        )
        wizard.action_apply()
        device.invalidate_recordset()
        self.assertEqual(device.state, "withdrawn")
        self.assertEqual(device.market_withdrawal_date, date(2026, 7, 1))


@tagged("post_install", "-at_install")
class TestPmsReportWizard(MedicalDeviceCommon):
    """Behaviour of ``ls.md.pms.report.wizard``."""

    def setUp(self):
        """Place a device on the market so a report can be opened for it."""
        super().setUp()
        self.device_iia.write(
            {"state": "on_market", "market_placement_date": date(2025, 1, 1)}
        )

    def test_report_created_for_device_on_market(self):
        """The wizard opens one draft report for the selected device."""
        wizard = self.env["ls.md.pms.report.wizard"].create(
            {
                "device_ids": [(6, 0, [self.device_iia.id])],
                "period_end": date(2025, 12, 31),
            }
        )
        wizard.action_create_reports()
        self.assertEqual(len(wizard.created_report_ids), 1)
        report = wizard.created_report_ids
        self.assertEqual(report.state, "draft")
        self.assertEqual(report.device_id, self.device_iia)
        self.assertEqual(report.period_end, date(2025, 12, 31))

    def test_report_type_follows_device_class(self):
        """The created report carries the report type of the risk class."""
        wizard = self.env["ls.md.pms.report.wizard"].create(
            {
                "device_ids": [(6, 0, [self.device_iia.id])],
                "period_end": date(2025, 12, 31),
            }
        )
        wizard.action_create_reports()
        self.assertEqual(wizard.created_report_ids.report_type, "psur")

    def test_period_start_derived_from_market_placement(self):
        """Without an approved report the period starts at market placement."""
        wizard = self.env["ls.md.pms.report.wizard"].create(
            {
                "device_ids": [(6, 0, [self.device_iia.id])],
                "period_end": date(2025, 12, 31),
            }
        )
        wizard.action_create_reports()
        self.assertEqual(
            wizard.created_report_ids.period_start, date(2025, 1, 1)
        )

    def test_device_not_on_market_rejected(self):
        """A device never placed on the market has no report due."""
        wizard = self.env["ls.md.pms.report.wizard"].create(
            {
                "device_ids": [(6, 0, [self.device_iii.id])],
                "period_end": date(2025, 12, 31),
            }
        )
        with self.assertRaises(UserError):
            wizard.action_create_reports()

    def test_explicit_period_start_wins(self):
        """An explicit period start overrides the derived one."""
        wizard = self.env["ls.md.pms.report.wizard"].create(
            {
                "device_ids": [(6, 0, [self.device_iia.id])],
                "period_start": date(2025, 6, 1),
                "period_end": date(2025, 12, 31),
            }
        )
        wizard.action_create_reports()
        self.assertEqual(
            wizard.created_report_ids.period_start, date(2025, 6, 1)
        )

    def test_action_returns_window_on_created_reports(self):
        """The wizard returns an action listing the created reports."""
        wizard = self.env["ls.md.pms.report.wizard"].create(
            {
                "device_ids": [(6, 0, [self.device_iia.id])],
                "period_end": date(2025, 12, 31),
            }
        )
        action = wizard.action_create_reports()
        self.assertEqual(action["res_model"], "ls.md.pms_report")
        self.assertEqual(action["type"], "ir.actions.act_window")
