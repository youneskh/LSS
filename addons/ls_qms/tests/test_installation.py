# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0.html).
"""Integrity of the data shipped with the module."""

from .common import LsQmsCommon

#: Models that must be covered by an access control list.
MODELS_REQUIRING_ACL = (
    "ls.qms.policy",
    "ls.qms.sop",
    "ls.qms.work_instruction",
    "ls.qms.quality_plan",
    "ls.qms.quality_plan.line",
    "ls.qms.objective",
    "ls.qms.objective.measurement",
    "ls.qms.quality_record",
    "ls.qms.new.revision.wizard",
    "ls.qms.reject.wizard",
)

#: Numbering sequences that must exist after installation.
SEQUENCE_CODES = (
    "ls.qms.policy",
    "ls.qms.sop",
    "ls.qms.work_instruction",
    "ls.qms.quality_plan",
    "ls.qms.objective",
    "ls.qms.quality_record",
)

#: System parameters that must exist after installation.
PARAMETER_KEYS = (
    "ls_qms.default_review_period_months",
    "ls_qms.review_reminder_lead_days",
    "ls_qms.enforce_segregation_of_duties",
    "ls_qms.default_retention_period_months",
)


class TestInstallation(LsQmsCommon):
    """Sequences, parameters, security and reports are installed."""

    def test_01_sequences_exist(self):
        """Every numbering sequence is installed."""
        for code in SEQUENCE_CODES:
            sequence = self.env["ir.sequence"].search([("code", "=", code)])
            self.assertTrue(sequence, "Missing sequence %s" % code)

    def test_02_parameters_exist(self):
        """Every system parameter is installed."""
        config = self.env["ir.config_parameter"].sudo()
        for key in PARAMETER_KEYS:
            self.assertTrue(config.get_param(key), "Missing parameter %s" % key)

    def test_03_every_model_has_an_acl(self):
        """No model is left without an access control list."""
        for model_name in MODELS_REQUIRING_ACL:
            access = self.env["ir.model.access"].search(
                [("model_id.model", "=", model_name)]
            )
            self.assertTrue(access, "No ACL for %s" % model_name)

    def test_04_record_rules_exist(self):
        """Every stored model carries its record rule."""
        for external_id in (
            "ls_qms.rule_ls_qms_policy",
            "ls_qms.rule_ls_qms_sop",
            "ls_qms.rule_ls_qms_work_instruction",
            "ls_qms.rule_ls_qms_quality_plan",
            "ls_qms.rule_ls_qms_quality_plan_line",
            "ls_qms.rule_ls_qms_objective",
            "ls_qms.rule_ls_qms_objective_measurement",
            "ls_qms.rule_ls_qms_quality_record",
        ):
            self.assertTrue(self.env.ref(external_id))

    def test_05_activity_types_exist(self):
        """The three activity types are installed."""
        for external_id in (
            "ls_qms.mail_activity_type_ls_qms_review",
            "ls_qms.mail_activity_type_ls_qms_objective",
            "ls_qms.mail_activity_type_ls_qms_retention",
        ):
            self.assertTrue(self.env.ref(external_id))

    def test_06_scheduled_actions_exist(self):
        """The three scheduled actions are installed and active."""
        for external_id in (
            "ls_qms.ir_cron_ls_qms_document_review",
            "ls_qms.ir_cron_ls_qms_objective_monitoring",
            "ls_qms.ir_cron_ls_qms_record_retention",
        ):
            cron = self.env.ref(external_id)
            self.assertTrue(cron.active)

    def test_07_reports_exist(self):
        """The three printable documents are installed."""
        for external_id in (
            "ls_qms.action_report_ls_qms_policy",
            "ls_qms.action_report_ls_qms_sop",
            "ls_qms.action_report_ls_qms_quality_plan",
        ):
            report = self.env.ref(external_id)
            self.assertEqual(report.report_type, "qweb-pdf")

    def test_08_groups_and_privilege_exist(self):
        """The privilege and the four groups are installed."""
        privilege = self.env.ref("ls_qms.res_groups_privilege_ls_qms")
        self.assertTrue(privilege)
        for external_id in (
            "ls_qms.group_ls_qms_viewer",
            "ls_qms.group_ls_qms_user",
            "ls_qms.group_ls_qms_approver",
            "ls_qms.group_ls_qms_manager",
        ):
            self.assertTrue(self.env.ref(external_id))

    def test_09_menus_exist(self):
        """The root menu and its children are installed."""
        root = self.env.ref("ls_qms.menu_ls_qms_root")
        self.assertTrue(root)
        for external_id in (
            "ls_qms.menu_ls_qms_policy",
            "ls_qms.menu_ls_qms_objective",
            "ls_qms.menu_ls_qms_sop",
            "ls_qms.menu_ls_qms_work_instruction",
            "ls_qms.menu_ls_qms_quality_plan",
            "ls_qms.menu_ls_qms_quality_record",
        ):
            self.assertEqual(self.env.ref(external_id).parent_id, root)

    def test_10_module_is_installed(self):
        """The module is registered as installed."""
        module = self.env["ir.module.module"].search(
            [("name", "=", "ls_qms")]
        )
        self.assertEqual(module.state, "installed")
