# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Tests for access rights, role separation and multi-company isolation."""

from odoo.exceptions import AccessError, UserError
from odoo.tests import tagged

from .test_common import (
    MANAGER_GROUP,
    TECHNICIAN_GROUP,
    VIEWER_GROUP,
    EnvMonitoringCommon,
)


@tagged("post_install", "-at_install")
class TestSecurity(EnvMonitoringCommon):
    """Roles are separated at the model layer, not only in the interface."""

    def test_group_membership(self):
        self.assertTrue(self.manager.has_group(MANAGER_GROUP))
        self.assertTrue(self.technician.has_group(TECHNICIAN_GROUP))
        self.assertTrue(self.viewer.has_group(VIEWER_GROUP))
        self.assertFalse(self.technician.has_group(MANAGER_GROUP))
        self.assertFalse(self.viewer.has_group(TECHNICIAN_GROUP))

    def test_viewer_can_read_configuration(self):
        self.assertTrue(
            self.env["ls.env.grade"].with_user(self.viewer).search([]))

    def test_viewer_cannot_create_a_sample(self):
        with self.assertRaises(AccessError):
            self.env["ls.env.sample"].with_user(self.viewer).create(
                {"sampling_point_id": self.point.id})

    def test_viewer_cannot_modify_configuration(self):
        with self.assertRaises(AccessError):
            self.grade.with_user(self.viewer).write({"name": "Changed"})

    def test_technician_can_create_a_sample(self):
        sample = self.env["ls.env.sample"].with_user(self.technician).create(
            {"sampling_point_id": self.point.id})
        self.assertTrue(sample)

    def test_technician_cannot_delete_a_sample(self):
        sample = self.env["ls.env.sample"].with_user(self.technician).create(
            {"sampling_point_id": self.point.id})
        with self.assertRaises(AccessError):
            sample.with_user(self.technician).unlink()

    def test_technician_cannot_modify_configuration(self):
        with self.assertRaises(AccessError):
            self.grade.with_user(self.technician).write({"name": "Changed"})

    def test_technician_cannot_author_limits_or_plans(self):
        """Limits and plans are authored by managers only (README role table)."""
        with self.assertRaises(AccessError):
            self.env["ls.env.limit"].with_user(self.technician).create(
                {
                    "sampling_point_id": self.point.id,
                    "parameter_id": self.parameter_count.id,
                    "occupancy_state": "any",
                    "direction": "upper",
                    "action_set": True,
                    "action_value": 10.0,
                }
            )
        with self.assertRaises(AccessError):
            self.env["ls.env.plan"].with_user(self.technician).create(
                {"name": "Technician plan", "code": "PLAN-TECH"}
            )

    def test_technician_cannot_review_a_sample(self):
        limit = self._create_limit(self.point, self.parameter_count)
        self._approve_limit(limit)
        sample = self._create_sample()
        sample.action_schedule()
        sample.with_user(self.technician).action_collect()
        sample.with_user(self.technician).action_start_analysis()
        sample.result_ids.write({"value_numeric": 1.0, "value_set": True})
        sample.with_user(self.technician).action_enter_results()
        with self.assertRaises(UserError):
            sample.with_user(self.second_technician).action_review()

    def test_manager_can_manage_configuration(self):
        self.grade.with_user(self.manager).write({"name": "Updated Grade"})
        self.assertEqual(self.grade.name, "Updated Grade")

    def test_technician_cannot_run_the_trend_wizard(self):
        with self.assertRaises(AccessError):
            self.env["ls.env.trend.wizard"].with_user(self.technician).create(
                {
                    "name": "Unauthorised",
                    "date_from": "2026-01-01",
                    "date_to": "2026-02-01",
                }
            )

    def test_technician_can_run_the_scheduling_wizard(self):
        wizard = self.env["ls.env.schedule.wizard"].with_user(
            self.technician).create({"date_to": "2026-01-01"})
        self.assertTrue(wizard)

    def test_every_model_is_covered_by_an_access_rule(self):
        """No model of this module may be left without an access rule."""
        module_models = self.env["ir.model"].search(
            [("model", "=like", "ls.env.%")])
        self.assertTrue(module_models)
        for model in module_models:
            rules = self.env["ir.model.access"].search(
                [("model_id", "=", model.id)])
            self.assertTrue(
                rules,
                "model %s has no access rule" % model.model,
            )


@tagged("post_install", "-at_install")
class TestMultiCompany(EnvMonitoringCommon):
    """Records of another company are not visible."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.other_company = cls.env["res.company"].create(
            {"name": "Second Site"})
        cls.other_grade = cls.env["ls.env.grade"].create(
            {
                "name": "Other Grade",
                "code": "OG",
                "company_id": cls.other_company.id,
            }
        )

    def test_records_of_another_company_are_hidden(self):
        visible = self.env["ls.env.grade"].with_user(self.manager).search([])
        self.assertIn(self.grade, visible)
        self.assertNotIn(self.other_grade, visible)

    def test_cross_company_reference_is_rejected(self):
        from odoo.exceptions import ValidationError
        with self.assertRaises(ValidationError):
            self.env["ls.env.area"].create(
                {
                    "name": "Cross company area",
                    "code": "XC01",
                    "parent_id": self.area.id,
                    "company_id": self.other_company.id,
                }
            )
