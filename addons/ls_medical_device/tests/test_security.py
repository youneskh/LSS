# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Tests of the access rights and record rules of the module.

The module implements segregation of duties in two complementary layers:
``ir.model.access`` records control the create, read, write and unlink
permissions, while the business methods of each model check the approval
authority in Python. Both layers are exercised here, because a check that
exists only in the user interface would not survive programmatic access.
"""

from odoo.exceptions import AccessError, UserError
from odoo.tests import tagged

from .common import MedicalDeviceCommon


@tagged("post_install", "-at_install")
class TestAccessRights(MedicalDeviceCommon):
    """Access rights granted to each of the four access levels."""

    def test_viewer_can_read_devices(self):
        """A viewer reads the device register."""
        device = self.device_iia.with_user(self.user_viewer)
        self.assertTrue(device.name)

    def test_viewer_cannot_create_device(self):
        """A viewer cannot create a device."""
        with self.assertRaises(AccessError):
            self.env["ls.md.device"].with_user(self.user_viewer).create(
                {"name": "Forbidden", "device_class_id": self.class_i.id}
            )

    def test_viewer_cannot_write_device(self):
        """A viewer cannot modify a device."""
        with self.assertRaises(AccessError):
            self.device_iia.with_user(self.user_viewer).write(
                {"name": "Changed by viewer"}
            )

    def test_user_can_create_device(self):
        """A user creates a device."""
        device = self.env["ls.md.device"].with_user(self.user_user).create(
            {"name": "Created by user", "device_class_id": self.class_i.id}
        )
        self.assertTrue(device.reference)

    def test_user_cannot_unlink_device(self):
        """A user cannot delete a device."""
        device = self.env["ls.md.device"].with_user(self.user_user).create(
            {"name": "To delete", "device_class_id": self.class_i.id}
        )
        with self.assertRaises(AccessError):
            device.unlink()

    def test_manager_can_unlink_device(self):
        """A manager deletes a device."""
        device = self.env["ls.md.device"].with_user(self.user_manager).create(
            {"name": "Manager deletes", "device_class_id": self.class_i.id}
        )
        device.unlink()
        self.assertFalse(device.exists())

    def test_only_manager_configures_device_classes(self):
        """Risk classes are configuration data reserved to managers."""
        with self.assertRaises(AccessError):
            self.env["ls.md.device_class"].with_user(self.user_user).create(
                {"name": "Forbidden Class", "code": "ZZZ"}
            )

    def test_manager_configures_device_classes(self):
        """A manager creates a risk class."""
        device_class = (
            self.env["ls.md.device_class"]
            .with_user(self.user_manager)
            .create({"name": "Test Class", "code": "TESTCLS"})
        )
        self.assertTrue(device_class.id)

    def test_user_cannot_unlink_notified_body(self):
        """A regulatory user maintains but does not delete notified bodies."""
        with self.assertRaises(AccessError):
            self.notified_body.with_user(self.user_regulatory).unlink()

    def test_viewer_cannot_create_udi(self):
        """A viewer cannot create a UDI assignment."""
        with self.assertRaises(AccessError):
            self.env["ls.md.udi"].with_user(self.user_viewer).create(
                {
                    "device_id": self.device_iia.id,
                    "udi_kind": "udi_di",
                    "udi_di": "FORBIDDEN-UDI",
                    "issuing_entity": "gs1",
                    "packaging_level": "primary",
                }
            )


@tagged("post_install", "-at_install")
class TestSegregationOfDuties(MedicalDeviceCommon):
    """Approval authority enforced at model level rather than in the views."""

    def test_market_status_change_requires_regulatory_level(self):
        """Changing the market status requires regulatory authority."""
        with self.assertRaises(UserError):
            self.device_iia.with_user(self.user_user).action_start_development()

    def test_market_status_change_allowed_for_manager(self):
        """A manager holds the regulatory authority by implication."""
        device = self.device_iia.with_user(self.user_manager)
        device.action_start_development()
        self.assertEqual(device.state, "development")

    def test_risk_file_approval_requires_regulatory_level(self):
        """A plain user cannot approve a risk management file."""
        risk_file = self.env["ls.md.risk_assessment"].create(
            {
                "title": "Authority Test",
                "device_id": self.device_iia.id,
                "overall_benefit_risk_conclusion": "Acceptable.",
                "overall_risk_acceptable": True,
                "responsible_id": self.user_second.id,
            }
        )
        # A file can only be submitted with at least one risk recorded.
        self.env["ls.md.risk_item"].create(
            {
                "risk_assessment_id": risk_file.id,
                "reference": "R-AUTH",
                "hazard": "Test hazard",
                "hazardous_situation": "Test hazardous situation",
                "harm": "Test harm",
                "initial_severity": "4",
                "initial_probability": "3",
                "control_option": "protective_measure",
                "control_measure": "Test control measure",
                "residual_severity": "4",
                "residual_probability": "1",
                "residual_acceptability": "acceptable",
                "acceptability_justification": "Test justification",
            }
        )
        risk_file.action_submit_for_review()
        with self.assertRaises(UserError):
            risk_file.with_user(self.user_user).action_approve()

    def test_group_implication_chain(self):
        """Each access level implies the level below it."""
        self.assertTrue(
            self.user_manager.has_group("ls_medical_device.group_ls_md_regulatory")
        )
        self.assertTrue(
            self.user_regulatory.has_group("ls_medical_device.group_ls_md_user")
        )
        self.assertTrue(
            self.user_user.has_group("ls_medical_device.group_ls_md_viewer")
        )

    def test_plain_user_is_not_regulatory(self):
        """A plain user does not hold the regulatory access level."""
        self.assertFalse(
            self.user_user.has_group("ls_medical_device.group_ls_md_regulatory")
        )


@tagged("post_install", "-at_install")
class TestRecordRules(MedicalDeviceCommon):
    """Multi-company scoping applied by the global record rules."""

    def test_device_rule_exists_and_scopes_by_company(self):
        """The multi-company rule on the device model scopes by company.

        The assertion inspects the stored domain rather than the field that
        marks a rule as global. The name of that field in Odoo 19.0 could not
        be verified from official documentation, so the test avoids it and
        checks the property that matters instead.
        """
        rule = self.env.ref("ls_medical_device.rule_ls_md_device_company")
        self.assertTrue(rule.exists())
        self.assertIn("company_ids", rule.domain_force)

    def test_device_of_other_company_is_hidden(self):
        """A device of a company the user cannot access is not readable."""
        other_company = self.env["res.company"].create({"name": "Other Company"})
        device = self.env["ls.md.device"].create(
            {
                "name": "Other Company Device",
                "device_class_id": self.class_i.id,
                "company_id": other_company.id,
            }
        )
        visible = (
            self.env["ls.md.device"]
            .with_user(self.user_user)
            .search([("id", "=", device.id)])
        )
        self.assertFalse(visible)
