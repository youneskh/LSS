# Part of the Life Sciences Suite. See LICENSE file for full copyright and licensing details.
"""Access-right, record-rule and installation integrity tests."""

from odoo.exceptions import AccessError
from odoo.tests import tagged

from .common import LsLabCommon

LS_LAB_MODELS = [
    "ls.lab.storage_condition",
    "ls.lab.test_method",
    "ls.lab.specification",
    "ls.lab.specification_line",
    "ls.lab.sample",
    "ls.lab.test_result",
    "ls.lab.oos",
    "ls.lab.stability_study",
    "ls.lab.stability_timepoint",
    "ls.lab.coa",
]

LS_LAB_GROUPS = [
    "ls_lab.ls_lab_group_viewer",
    "ls_lab.ls_lab_group_analyst",
    "ls_lab.ls_lab_group_reviewer",
    "ls_lab.ls_lab_group_manager",
]


@tagged("post_install", "-at_install")
class TestLsLabSecurity(LsLabCommon):
    """Cover the ACL matrix, group hierarchy and record rules."""

    def test_group_hierarchy(self):
        """Each role implies the one below it."""
        viewer = self.env.ref("ls_lab.ls_lab_group_viewer")
        analyst = self.env.ref("ls_lab.ls_lab_group_analyst")
        reviewer = self.env.ref("ls_lab.ls_lab_group_reviewer")
        manager = self.env.ref("ls_lab.ls_lab_group_manager")
        self.assertIn(viewer, analyst.implied_ids)
        self.assertIn(analyst, reviewer.implied_ids)
        self.assertIn(reviewer, manager.implied_ids)

    def test_groups_carry_privilege(self):
        """Every group is attached to the module privilege."""
        privilege = self.env.ref("ls_lab.ls_lab_privilege")
        for xmlid in LS_LAB_GROUPS:
            group = self.env.ref(xmlid)
            self.assertEqual(
                group.privilege_id, privilege,
                f"{xmlid} must carry the ls_lab privilege",
            )

    def test_every_model_has_acl_for_every_group(self):
        """The ACL matrix is complete: ten models times four groups."""
        for model_name in LS_LAB_MODELS:
            model = self.env["ir.model"].search([("model", "=", model_name)])
            self.assertTrue(model, f"Model {model_name} must exist")
            for xmlid in LS_LAB_GROUPS:
                group = self.env.ref(xmlid)
                acl = self.env["ir.model.access"].search([
                    ("model_id", "=", model.id),
                    ("group_id", "=", group.id),
                ])
                self.assertTrue(
                    acl,
                    f"Missing ACL for {model_name} and {xmlid}",
                )

    def test_viewer_cannot_write(self):
        """A viewer has read-only access to samples."""
        sample = self._create_sample()
        with self.assertRaises(AccessError):
            sample.with_user(self.viewer).write({"batch_reference": "X"})

    def test_viewer_cannot_create_sample(self):
        """A viewer cannot register a sample."""
        specification = self._create_approved_specification()
        with self.assertRaises(AccessError):
            self.env["ls.lab.sample"].with_user(self.viewer).create({
                "product_id": self.product.id,
                "specification_id": specification.id,
            })

    def test_analyst_cannot_write_test_method(self):
        """Method maintenance is restricted to the manager role."""
        method = self._create_approved_method(name="Restricted method")
        with self.assertRaises(AccessError):
            method.with_user(self.analyst).write({"obsolete_reason": "x"})

    def test_analyst_cannot_create_investigation(self):
        """Analysts have no direct create right on investigations."""
        specification = self._create_approved_specification()
        sample = self._create_sample(specification)
        sample.action_start()
        sample.action_start_testing()
        result = sample.result_ids[0]
        with self.assertRaises(AccessError):
            self.env["ls.lab.oos"].with_user(self.analyst).create({
                "test_result_id": result.id,
            })

    def test_analyst_may_create_sample(self):
        """An analyst can register samples."""
        specification = self._create_approved_specification()
        sample = self.env["ls.lab.sample"].with_user(self.analyst).create({
            "product_id": self.product.id,
            "specification_id": specification.id,
        })
        self.assertTrue(sample.exists())

    def test_multi_company_rules_are_global(self):
        """Each multi-company record rule applies to every user."""
        rule_xmlids = [
            "ls_lab.ls_lab_rule_sample_company",
            "ls_lab.ls_lab_rule_test_result_company",
            "ls_lab.ls_lab_rule_oos_company",
            "ls_lab.ls_lab_rule_coa_company",
            "ls_lab.ls_lab_rule_specification_company",
        ]
        for xmlid in rule_xmlids:
            rule = self.env.ref(xmlid)
            self.assertTrue(
                rule["global"],
                f"{xmlid} must be a global rule so it applies to all users",
            )

    def test_crons_are_registered_and_notification_only(self):
        """The three scheduled actions exist and call known methods."""
        expected = {
            "ls_lab.ls_lab_cron_stability_timepoint_due":
                "_cron_notify_due_timepoints",
            "ls_lab.ls_lab_cron_sample_overdue":
                "_cron_notify_overdue_samples",
            "ls_lab.ls_lab_cron_method_review_due":
                "_cron_notify_method_review_due",
        }
        for xmlid, method_name in expected.items():
            cron = self.env.ref(xmlid)
            self.assertIn(method_name, cron.code)
            self.assertTrue(hasattr(self.env[cron.model_id.model], method_name))

    def test_sequences_are_registered(self):
        """Every document sequence used by the module exists."""
        for code in [
            "ls.lab.test_method",
            "ls.lab.specification",
            "ls.lab.sample",
            "ls.lab.oos",
            "ls.lab.stability_study",
            "ls.lab.coa",
        ]:
            sequence = self.env["ir.sequence"].search([("code", "=", code)])
            self.assertTrue(sequence, f"Sequence {code} must be installed")

    def test_reports_are_registered(self):
        """Both QWeb report actions are installed and bound."""
        for xmlid in [
            "ls_lab.ls_lab_action_report_coa",
            "ls_lab.ls_lab_action_report_oos",
        ]:
            report = self.env.ref(xmlid)
            self.assertEqual(report.report_type, "qweb-pdf")
            self.assertTrue(report.report_name)
