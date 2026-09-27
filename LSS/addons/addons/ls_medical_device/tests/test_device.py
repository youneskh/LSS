# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Tests of the device master record."""

from datetime import date

from dateutil.relativedelta import relativedelta

from psycopg2 import errors as pg_errors

from odoo.exceptions import UserError, ValidationError
from odoo.tests import tagged

from .common import MedicalDeviceCommon


@tagged("post_install", "-at_install")
class TestDevice(MedicalDeviceCommon):
    """Behaviour of ``ls.md.device``."""

    def test_reference_allocated_from_sequence(self):
        """A new device receives a reference from the dedicated sequence."""
        device = self.env["ls.md.device"].create(
            {"name": "Sequenced Device", "device_class_id": self.class_i.id}
        )
        self.assertNotEqual(device.reference, "New")
        self.assertTrue(device.reference)

    def test_display_name_includes_reference(self):
        """The display name combines the reference and the device name."""
        self.assertIn(self.device_iia.reference, self.device_iia.display_name)
        self.assertIn("Test Class IIa Device", self.device_iia.display_name)

    def test_retention_years_non_implantable(self):
        """A non-implantable device retains documentation for ten years."""
        self.assertEqual(self.device_iia.documentation_retention_years, 10)

    def test_retention_years_implantable(self):
        """An implantable device retains documentation for fifteen years."""
        self.assertEqual(self.device_iii.documentation_retention_years, 15)

    def test_periodic_report_obligation_from_class(self):
        """The periodic report obligation is read from the risk class."""
        self.assertEqual(self.device_i.periodic_report_type, "pmsr")
        self.assertEqual(self.device_iia.periodic_report_type, "psur")
        self.assertEqual(self.device_iia.periodic_report_interval_months, 24)
        self.assertEqual(self.device_iii.periodic_report_interval_months, 12)

    def test_annual_pmcf_update_required_for_class_iii(self):
        """A class III device requires an annual PMCF update."""
        self.assertTrue(self.device_iii.annual_pmcf_update_required)
        self.assertFalse(self.device_iia.annual_pmcf_update_required)

    def test_notified_body_required_from_class(self):
        """The notified body requirement is read from the risk class."""
        self.assertFalse(self.device_i.notified_body_required)
        self.assertTrue(self.device_iia.notified_body_required)

    def test_market_dates_order_rejected(self):
        """A withdrawal date preceding the placement date is rejected."""
        with self.assertRaises(ValidationError):
            self.device_iia.write(
                {
                    "market_placement_date": date(2026, 5, 1),
                    "market_withdrawal_date": date(2026, 4, 1),
                }
            )

    def test_transition_draft_to_development(self):
        """A draft device can be moved into development."""
        device = self.device_iia.with_user(self.user_regulatory)
        device.action_start_development()
        self.assertEqual(device.state, "development")

    def test_transition_requires_regulatory_authority(self):
        """A plain user cannot change the market status of a device."""
        device = self.device_iia.with_user(self.user_user)
        with self.assertRaises(UserError):
            device.action_start_development()

    def test_conformity_assessment_requires_intended_purpose(self):
        """A device without an intended purpose cannot enter assessment."""
        device = self.env["ls.md.device"].create(
            {"name": "No Purpose", "device_class_id": self.class_iia.id}
        )
        device = device.with_user(self.user_regulatory)
        device.action_start_development()
        with self.assertRaises(UserError):
            device.action_start_conformity_assessment()

    def test_place_on_market_requires_technical_documentation(self):
        """Placing a device on the market requires approved documentation."""
        device = self.device_iia.with_user(self.user_regulatory)
        device.action_start_development()
        device.action_start_conformity_assessment()
        with self.assertRaises(UserError):
            device.action_place_on_market()

    def test_wrong_order_transition_rejected(self):
        """A draft device cannot jump straight to conformity assessment."""
        device = self.device_iia.with_user(self.user_regulatory)
        with self.assertRaises(UserError):
            device.action_start_conformity_assessment()

    def test_suspend_requires_on_market(self):
        """Only a device on the market can be suspended."""
        device = self.device_iia.with_user(self.user_regulatory)
        with self.assertRaises(UserError):
            device.action_suspend()

    def test_copy_resets_identifiers(self):
        """Duplicating a device clears its identifiers and lifecycle data."""
        self.device_iia.write({"basic_udi_di": "TEST-BASIC-0001"})
        copy = self.device_iia.copy()
        self.assertFalse(copy.basic_udi_di)
        self.assertEqual(copy.state, "draft")
        self.assertNotEqual(copy.reference, self.device_iia.reference)

    def test_basic_udi_di_unique(self):
        """Two devices cannot share the same Basic UDI-DI."""
        self.device_iia.write({"basic_udi_di": "TEST-BASIC-UNIQUE"})
        self.device_iia.flush_recordset()
        with self.assertRaises(pg_errors.UniqueViolation):
            self.device_iii.write({"basic_udi_di": "TEST-BASIC-UNIQUE"})
            self.device_iii.flush_recordset()

    def test_related_counts(self):
        """The related record counters reflect the attached records."""
        self.assertEqual(self.device_iia.udi_count, 0)
        self.env["ls.md.udi"].create(
            {
                "device_id": self.device_iia.id,
                "udi_kind": "udi_di",
                "udi_di": "TEST-UDI-COUNT-1",
                "issuing_entity": "gs1",
                "packaging_level": "primary",
            }
        )
        self.device_iia.invalidate_recordset()
        self.assertEqual(self.device_iia.udi_count, 1)

    def test_periodic_report_not_due_before_market(self):
        """No periodic report is due while the device is not on the market."""
        self.assertFalse(self.device_iia.next_periodic_report_due)
        self.assertFalse(self.device_iia.periodic_report_overdue)

    def test_cron_returns_zero_without_devices_on_market(self):
        """The scheduled check creates no activity when nothing is due."""
        created = self.env["ls.md.device"]._cron_check_post_market_obligations()
        self.assertEqual(created, 0)

    def test_retention_until_requires_withdrawal_date(self):
        """The retention end date is only computed once withdrawal is known."""
        self.assertFalse(self.device_iia.documentation_retention_until)
        device = self.device_iia
        device.write(
            {
                "market_placement_date": date(2026, 1, 1),
                "market_withdrawal_date": date(2026, 6, 1),
            }
        )
        expected = date(2026, 6, 1) + relativedelta(
            years=device.documentation_retention_years
        )
        self.assertEqual(device.documentation_retention_until, expected)
