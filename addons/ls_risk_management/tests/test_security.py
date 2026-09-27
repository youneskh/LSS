# Part of the Life Sciences Suite. See LICENSE file for full copyright
# and licensing details.
"""Security tests: access rights, role separation and company isolation."""

from odoo.exceptions import AccessError
from odoo.tests.common import tagged

from .common import RiskCommon


@tagged("post_install", "-at_install")
class TestRiskSecurity(RiskCommon):
    """Verify that access rights and record rules behave as designed."""

    def test_viewer_can_read_risks(self):
        """A viewer can read the risk register."""
        risk = self._make_risk()
        self.assertTrue(risk.with_user(self.user_viewer).read(["title"]))

    def test_viewer_cannot_create_risk(self):
        """A viewer cannot create a risk."""
        with self.assertRaises(AccessError):
            self.env["ls.risk.register"].with_user(self.user_viewer).create(
                {
                    "title": "Unauthorised",
                    "risk_type": "process",
                    "matrix_id": self.matrix.id,
                }
            )

    def test_viewer_cannot_write_risk(self):
        """A viewer cannot modify a risk."""
        risk = self._make_risk()
        with self.assertRaises(AccessError):
            risk.with_user(self.user_viewer).write({"title": "Changed"})

    def test_viewer_cannot_unlink_risk(self):
        """A viewer cannot delete a risk."""
        risk = self._make_risk()
        with self.assertRaises(AccessError):
            risk.with_user(self.user_viewer).unlink()

    def test_analyst_can_create_risk(self):
        """An analyst can create a risk."""
        risk = self._make_risk(user=self.user_analyst)
        self.assertTrue(risk.id)

    def test_analyst_cannot_write_matrix(self):
        """An analyst cannot alter the acceptability criteria."""
        with self.assertRaises(AccessError):
            self.matrix.with_user(self.user_analyst).write({"name": "Tampered"})

    def test_analyst_cannot_write_matrix_cell(self):
        """An analyst cannot alter a matrix cell."""
        cell = self.matrix.get_cell(1, 1)
        with self.assertRaises(AccessError):
            cell.with_user(self.user_analyst).write({"acceptability": "acceptable"})

    def test_analyst_cannot_create_category(self):
        """An analyst cannot extend the risk taxonomy."""
        with self.assertRaises(AccessError):
            self.env["ls.risk.category"].with_user(self.user_analyst).create(
                {"name": "Unauthorised", "code": "UNAUTH"}
            )

    def test_manager_can_write_matrix(self):
        """A manager can maintain the acceptability criteria."""
        draft = self._build_matrix(self.env, self.company, "MGR-3X3")
        draft.with_user(self.user_manager).write({"name": "Renamed by manager"})
        self.assertEqual(draft.name, "Renamed by manager")

    def test_analyst_cannot_use_close_wizard(self):
        """An analyst has no access to the closure wizard."""
        risk = self._make_risk()
        with self.assertRaises(AccessError):
            self.env["ls.risk.close.wizard"].with_user(self.user_analyst).create(
                {"risk_ids": [(6, 0, risk.ids)], "closure_reason": "Unauthorised."}
            )

    def test_analyst_cannot_use_residual_wizard(self):
        """An analyst has no access to the residual acceptance wizard."""
        risk = self._make_risk()
        with self.assertRaises(AccessError):
            self.env["ls.risk.residual.wizard"].with_user(self.user_analyst).create(
                {"risk_id": risk.id, "justification": "Unauthorised."}
            )

    def test_analyst_can_use_assess_wizard(self):
        """An analyst can use the assessment wizard."""
        risk = self._make_risk()
        wizard = self.env["ls.risk.assess.wizard"].with_user(self.user_analyst).create(
            {
                "risk_ids": [(6, 0, risk.ids)],
                "severity_level_id": self._severity(1).id,
                "probability_level_id": self._probability(1).id,
                "estimation_rationale": "Permitted.",
            }
        )
        self.assertTrue(wizard.id)

    def test_company_isolation_on_risks(self):
        """A user sees only risks of the companies they are allowed."""
        other_matrix = self._build_matrix(
            self.env, self.other_company, "ISO-3X3", default=True
        )
        foreign = self.env["ls.risk.register"].create(
            {
                "title": "Foreign company risk",
                "risk_type": "process",
                "company_id": self.other_company.id,
                "matrix_id": other_matrix.id,
                "owner_id": self.env.user.id,
            }
        )
        visible = self.env["ls.risk.register"].with_user(self.user_analyst).search([])
        self.assertNotIn(foreign, visible)

    def test_company_isolation_on_matrices(self):
        """Matrices of another company are not visible."""
        foreign = self._build_matrix(self.env, self.other_company, "ISO2-3X3")
        visible = self.env["ls.risk.matrix"].with_user(self.user_analyst).search([])
        self.assertNotIn(foreign, visible)

    def test_multi_company_user_sees_both(self):
        """A user allowed both companies sees risks of both."""
        other_matrix = self._build_matrix(
            self.env, self.other_company, "BOTH-3X3", default=True
        )
        foreign = self.env["ls.risk.register"].create(
            {
                "title": "Second company risk",
                "risk_type": "process",
                "company_id": self.other_company.id,
                "matrix_id": other_matrix.id,
                "owner_id": self.env.user.id,
            }
        )
        self.user_manager.write(
            {"company_ids": [(6, 0, [self.company.id, self.other_company.id])]}
        )
        visible = (
            self.env["ls.risk.register"]
            .with_user(self.user_manager)
            .with_context(allowed_company_ids=[self.company.id, self.other_company.id])
            .search([])
        )
        self.assertIn(foreign, visible)

    def test_record_rules_scope_company_only(self):
        """Every record rule of this module constrains the company only.

        The test asserts on ``domain_force``, which the official Odoo 19
        security reference documents by name. It deliberately does not read
        the groups field or the computed global flag of ``ir.rule``, whose
        names could not be verified for Odoo 19.
        """
        rules = self.env["ir.rule"].search([("model_id.model", "like", "ls.risk.%")])
        self.assertTrue(rules, "No record rule was installed for this module.")
        for rule in rules:
            self.assertIn(
                "company_id",
                rule.domain_force,
                f"Rule {rule.name} is expected to constrain company_id.",
            )

    def test_record_rule_count_matches_models(self):
        """One company rule exists for each model carrying a company."""
        rules = self.env["ir.rule"].search([("model_id.model", "like", "ls.risk.%")])
        covered = set(rules.mapped("model_id.model"))
        for model in (
            "ls.risk.register",
            "ls.risk.assessment",
            "ls.risk.mitigation",
            "ls.risk.fmea",
            "ls.risk.fmea.line",
            "ls.risk.category",
            "ls.risk.matrix",
            "ls.risk.matrix.level",
            "ls.risk.matrix.cell",
        ):
            self.assertIn(model, covered, f"No company rule for {model}.")
