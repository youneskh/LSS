# Part of the Life Sciences Suite. See LICENSE file for full copyright
# and licensing details.
"""Tests of the risk matrix configuration models."""

from psycopg2 import errors as pg_errors

from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tests.common import tagged

from .common import RiskCommon


@tagged("post_install", "-at_install")
class TestRiskMatrix(RiskCommon):
    """Verify matrix completeness, approval gating and cell resolution."""

    def test_generate_cells_fills_grid(self):
        """Cell generation covers the full grid exactly once."""
        matrix = self._build_matrix(self.env, self.company, "GEN-3X3", size=3)
        self.assertEqual(matrix.expected_cell_count, 9)
        self.assertEqual(matrix.cell_count, 9)
        self.assertTrue(matrix.is_complete)

    def test_generate_cells_is_idempotent(self):
        """Generating cells twice does not create duplicates."""
        matrix = self._build_matrix(self.env, self.company, "IDEM-3X3", size=3)
        matrix.action_generate_cells()
        self.assertEqual(matrix.cell_count, 9)

    def test_generate_cells_requires_draft(self):
        """Cells cannot be generated once the matrix is approved."""
        with self.assertRaises(UserError):
            self.matrix.action_generate_cells()

    def test_get_cell_resolves_coordinates(self):
        """get_cell returns the cell matching a coordinate pair."""
        cell = self.matrix.get_cell(3, 3)
        self.assertEqual(len(cell), 1)
        self.assertEqual(cell.risk_level, "very_high")
        self.assertEqual(cell.acceptability, "not_acceptable")

    def test_get_cell_unknown_returns_empty(self):
        """get_cell returns an empty recordset for an undefined pair."""
        self.assertFalse(self.matrix.get_cell(99, 99))

    def test_approval_requires_complete_matrix(self):
        """An incomplete matrix cannot be approved."""
        matrix = self.env["ls.risk.matrix"].create(
            {"name": "Incomplete", "code": "INC", "company_id": self.company.id}
        )
        self.env["ls.risk.matrix.level"].create(
            {
                "matrix_id": matrix.id,
                "scale": "severity",
                "value": 1,
                "name": "Only severity",
            }
        )
        with self.assertRaises(UserError):
            matrix.with_user(self.user_manager).action_approve()

    def test_approval_requires_levels(self):
        """A matrix with no levels cannot be approved."""
        matrix = self.env["ls.risk.matrix"].create(
            {"name": "Empty", "code": "EMPTY", "company_id": self.company.id}
        )
        with self.assertRaises(UserError):
            matrix.with_user(self.user_manager).action_approve()

    def test_approval_records_approver(self):
        """Approval records the approving user and the timestamp."""
        matrix = self._build_matrix(self.env, self.company, "APP-3X3")
        matrix.with_user(self.user_manager).action_approve()
        self.assertEqual(matrix.state, "approved")
        self.assertEqual(matrix.approved_by_id, self.user_manager)
        self.assertTrue(matrix.approval_date)

    def test_approval_requires_manager_role(self):
        """An analyst cannot approve a matrix even by calling the method."""
        matrix = self._build_matrix(self.env, self.company, "ROLE-3X3")
        with self.assertRaises(AccessError):
            matrix.with_user(self.user_analyst).action_approve()

    def test_obsolete_requires_approved(self):
        """A draft matrix cannot be made obsolete."""
        matrix = self._build_matrix(self.env, self.company, "OBS-3X3")
        with self.assertRaises(UserError):
            matrix.with_user(self.user_manager).action_set_obsolete()

    def test_obsolete_clears_default(self):
        """Making a matrix obsolete removes its default flag."""
        self.matrix.with_user(self.user_manager).action_set_obsolete()
        self.assertEqual(self.matrix.state, "obsolete")
        self.assertFalse(self.matrix.is_default)

    def test_single_default_per_company(self):
        """Two active default matrices cannot coexist in one company."""
        second = self._build_matrix(self.env, self.company, "DUP-3X3")
        with self.assertRaises(ValidationError):
            second.is_default = True

    def test_default_allowed_in_other_company(self):
        """A second company may have its own default matrix."""
        other = self._build_matrix(
            self.env, self.other_company, "OTHER-3X3", default=True
        )
        self.assertTrue(other.is_default)

    def test_duplicate_code_rejected(self):
        """The matrix code is unique per company."""
        with self.assertRaises(pg_errors.UniqueViolation):
            self.env["ls.risk.matrix"].create(
                {
                    "name": "Clash",
                    "code": self.matrix.code,
                    "company_id": self.company.id,
                }
            )
            self.env.flush_all()

    def test_cell_rejects_undeclared_level(self):
        """A cell cannot reference a level absent from its matrix."""
        matrix = self._build_matrix(self.env, self.company, "CELL-3X3")
        with self.assertRaises(ValidationError):
            self.env["ls.risk.matrix.cell"].create(
                {
                    "matrix_id": matrix.id,
                    "severity_value": 99,
                    "probability_value": 1,
                    "risk_level": "low",
                    "acceptability": "acceptable",
                }
            )

    def test_level_display_name(self):
        """A level displays its ordinal value and its label."""
        level = self._severity(2)
        self.assertEqual(level.display_name, "2 - Severity 2")

    def test_matrix_display_name(self):
        """A matrix displays its code and its name."""
        self.assertEqual(
            self.matrix.display_name, f"[{self.matrix.code}] {self.matrix.name}"
        )

    def test_cell_display_name(self):
        """A cell displays its coordinates and resulting band."""
        cell = self.matrix.get_cell(3, 3)
        self.assertEqual(cell.display_name, "S3 / P3 - Very High")

    def test_level_company_follows_matrix(self):
        """The stored company of a level follows its matrix."""
        self.assertEqual(self._severity(1).company_id, self.company)
