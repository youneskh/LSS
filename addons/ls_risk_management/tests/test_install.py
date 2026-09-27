# Part of the Life Sciences Suite. See LICENSE file for full copyright
# and licensing details.
"""Installation and completeness tests.

These tests assert structural properties that a reviewer would otherwise
verify by hand: that every model declared by the module is registered, that
every model is covered by an access control list, and that the shipped
configuration data loaded in the expected state.
"""

from odoo.tests.common import tagged

from ..models import constants
from .common import RiskCommon

#: Every model this module is expected to declare.
EXPECTED_MODELS = [
    "ls.risk.category",
    "ls.risk.matrix",
    "ls.risk.matrix.level",
    "ls.risk.matrix.cell",
    "ls.risk.register",
    "ls.risk.assessment",
    "ls.risk.mitigation",
    "ls.risk.fmea",
    "ls.risk.fmea.line",
    "ls.risk.assess.wizard",
    "ls.risk.residual.wizard",
    "ls.risk.close.wizard",
    "ls.risk.cancel.wizard",
    "ls.risk.assessment.cancel.wizard",
    "ls.risk.mitigation.cancel.wizard",
    "ls.risk.fmea.cancel.wizard",
]


@tagged("post_install", "-at_install")
class TestRiskInstall(RiskCommon):
    """Verify module structure, ACL coverage and shipped data."""

    def test_all_models_registered(self):
        """Every expected model is present in the registry."""
        for model in EXPECTED_MODELS:
            self.assertIn(model, self.env, f"Model {model} is not registered.")

    def test_every_model_has_acl(self):
        """Every model of this module is covered by at least one ACL."""
        for model in EXPECTED_MODELS:
            acls = self.env["ir.model.access"].search(
                [("model_id.model", "=", model)]
            )
            self.assertTrue(acls, f"Model {model} has no access control list.")

    def test_groups_are_installed(self):
        """The three security groups exist and imply one another."""
        viewer = self.env.ref("ls_risk_management.group_risk_viewer")
        analyst = self.env.ref("ls_risk_management.group_risk_analyst")
        manager = self.env.ref("ls_risk_management.group_risk_manager")
        self.assertIn(viewer, analyst.implied_ids)
        self.assertIn(analyst, manager.implied_ids)

    def test_group_privilege_is_linked(self):
        """Each group is attached to the module's group privilege."""
        privilege = self.env.ref("ls_risk_management.res_groups_privilege_risk")
        for xmlid in (
            "group_risk_viewer",
            "group_risk_analyst",
            "group_risk_manager",
        ):
            group = self.env.ref(f"ls_risk_management.{xmlid}")
            self.assertEqual(group.privilege_id, privilege)

    def test_sequences_are_installed(self):
        """Every sequence code used by the models resolves to a sequence."""
        for code in (
            constants.SEQUENCE_RISK,
            constants.SEQUENCE_ASSESSMENT,
            constants.SEQUENCE_MITIGATION,
            constants.SEQUENCE_FMEA,
        ):
            sequence = self.env["ir.sequence"].search([("code", "=", code)], limit=1)
            self.assertTrue(sequence, f"No sequence found for code {code}.")

    def test_cron_is_installed(self):
        """The review notification scheduled action exists."""
        cron = self.env.ref("ls_risk_management.cron_notify_risk_review_due")
        self.assertEqual(cron.model_id.model, "ls.risk.register")
        self.assertEqual(cron.state, "code")

    def test_example_matrix_ships_unapproved(self):
        """The shipped example matrix is draft and is not the default."""
        example = self.env.ref("ls_risk_management.risk_matrix_example")
        self.assertEqual(example.state, "draft")
        self.assertFalse(example.is_default)

    def test_example_matrix_is_complete(self):
        """The shipped example matrix covers its whole grid."""
        example = self.env.ref("ls_risk_management.risk_matrix_example")
        self.assertEqual(example.severity_level_count, 5)
        self.assertEqual(example.probability_level_count, 5)
        self.assertEqual(example.cell_count, 25)
        self.assertTrue(example.is_complete)

    def test_shipped_categories_loaded(self):
        """The shipped taxonomy loaded with its hierarchy intact."""
        parent = self.env.ref("ls_risk_management.risk_category_product_quality")
        child = self.env.ref("ls_risk_management.risk_category_pq_purity")
        self.assertEqual(child.parent_id, parent)
        self.assertEqual(child.complete_name, "Product Quality / Purity")

    def test_reports_are_installed(self):
        """Both PDF report actions exist and target the right models."""
        risk_report = self.env.ref("ls_risk_management.action_report_ls_risk_register")
        fmea_report = self.env.ref("ls_risk_management.action_report_ls_risk_fmea")
        self.assertEqual(risk_report.model, "ls.risk.register")
        self.assertEqual(fmea_report.model, "ls.risk.fmea")

    def test_menus_are_installed(self):
        """The root menu and its main entries exist."""
        for xmlid in (
            "menu_ls_risk_root",
            "menu_ls_risk_register",
            "menu_ls_risk_assessment",
            "menu_ls_risk_mitigation",
            "menu_ls_risk_fmea",
            "menu_ls_risk_matrix",
            "menu_ls_risk_category",
        ):
            self.assertTrue(self.env.ref(f"ls_risk_management.{xmlid}"))

    def test_clause_map_targets_exist(self):
        """Every field named in the ISO 14971 clause map exists."""
        register_fields = self.env["ls.risk.register"]._fields
        mitigation_fields = self.env["ls.risk.mitigation"]._fields
        for field_name in (
            "intended_use",
            "safety_characteristics",
            "hazard",
            "hazardous_situation",
            "sequence_of_events",
            "harm",
            "benefit_risk_analysis",
            "control_completeness_confirmed",
            "overall_residual_risk_assessment",
            "next_review_date",
        ):
            self.assertIn(field_name, register_fields)
        for field_name in ("control_option", "introduces_new_risk", "new_risk_description"):
            self.assertIn(field_name, mitigation_fields)
        self.assertTrue(constants.ISO_14971_CLAUSE_MAP)
