# Part of the Life Sciences Suite. See LICENSE file for full copyright
# and licensing details.
"""Shared fixtures for the risk management test suite.

Users are created with :func:`odoo.tests.common.new_test_user` and role
membership is expressed with group external identifiers, so that the tests do
not depend on the name of the groups field of ``res.users``, which changed in
Odoo 19 and could not be verified from official documentation.
"""

from odoo.tests.common import TransactionCase, new_test_user


class RiskCommon(TransactionCase):
    """Base class providing users, a matrix, a category and a risk."""

    @classmethod
    def setUpClass(cls):
        """Create the role-separated users and the approved test matrix."""
        super().setUpClass()
        cls.company = cls.env.company
        cls.other_company = cls.env["res.company"].create(
            {"name": "Risk Test Second Company"}
        )

        cls.user_manager = new_test_user(
            cls.env,
            login="risk_manager",
            name="Risk Manager",
            groups="base.group_user,ls_risk_management.group_risk_manager",
            company_id=cls.company.id,
        )
        cls.user_manager_two = new_test_user(
            cls.env,
            login="risk_manager_two",
            name="Second Risk Manager",
            groups="base.group_user,ls_risk_management.group_risk_manager",
            company_id=cls.company.id,
        )
        cls.user_analyst = new_test_user(
            cls.env,
            login="risk_analyst",
            name="Risk Analyst",
            groups="base.group_user,ls_risk_management.group_risk_analyst",
            company_id=cls.company.id,
        )
        cls.user_viewer = new_test_user(
            cls.env,
            login="risk_viewer",
            name="Risk Viewer",
            groups="base.group_user,ls_risk_management.group_risk_viewer",
            company_id=cls.company.id,
        )

        cls.category = cls.env["ls.risk.category"].create(
            {"name": "Test Purity", "code": "T-PU", "company_id": cls.company.id}
        )
        cls.matrix = cls._build_matrix(cls.env, cls.company, "T-3X3", default=True)
        cls.matrix.with_user(cls.user_manager).action_approve()

    @classmethod
    def _build_matrix(cls, env, company, code, default=False, size=3):
        """Create a complete square matrix in the draft state.

        :param env: environment used to create the records.
        :param company: company owning the matrix.
        :param str code: unique matrix code.
        :param bool default: whether the matrix is the company default.
        :param int size: number of levels on each scale.
        :return: the created matrix.
        :rtype: :class:`odoo.models.Model`
        """
        matrix = env["ls.risk.matrix"].create(
            {
                "name": f"Matrix {code}",
                "code": code,
                "company_id": company.id,
                "is_default": default,
            }
        )
        levels = []
        for value in range(1, size + 1):
            for scale in ("severity", "probability"):
                levels.append(
                    {
                        "matrix_id": matrix.id,
                        "scale": scale,
                        "value": value,
                        "name": f"{scale.title()} {value}",
                        "description": f"Test definition for {scale} {value}.",
                    }
                )
        env["ls.risk.matrix.level"].create(levels)
        matrix.action_generate_cells()
        # Raise the top-right corner so that the fixture exercises every
        # acceptability branch rather than only the acceptable one.
        top = matrix.get_cell(size, size)
        top.write({"risk_level": "very_high", "acceptability": "not_acceptable"})
        middle = matrix.get_cell(size, 1)
        middle.write(
            {"risk_level": "medium", "acceptability": "acceptable_with_control"}
        )
        return matrix

    def _severity(self, value, matrix=None):
        """Return the severity level of the given ordinal value.

        :param int value: ordinal value to look up.
        :param matrix: matrix to search; defaults to the fixture matrix.
        :return: the matching level.
        :rtype: :class:`odoo.models.Model`
        """
        matrix = matrix or self.matrix
        return matrix.severity_level_ids.filtered(lambda lvl: lvl.value == value)

    def _probability(self, value, matrix=None):
        """Return the probability level of the given ordinal value.

        :param int value: ordinal value to look up.
        :param matrix: matrix to search; defaults to the fixture matrix.
        :return: the matching level.
        :rtype: :class:`odoo.models.Model`
        """
        matrix = matrix or self.matrix
        return matrix.probability_level_ids.filtered(lambda lvl: lvl.value == value)

    def _make_risk(self, user=None, **overrides):
        """Create a risk register entry.

        :param user: user creating the record; defaults to the analyst.
        :param overrides: field values overriding the defaults.
        :return: the created risk.
        :rtype: :class:`odoo.models.Model`
        """
        values = {
            "title": "Test risk",
            "risk_type": "process",
            "category_id": self.category.id,
            "matrix_id": self.matrix.id,
            "company_id": self.company.id,
            "owner_id": (user or self.user_analyst).id,
        }
        values.update(overrides)
        model = self.env["ls.risk.register"].with_user(user or self.user_analyst)
        return model.create(values)

    def _make_assessment(self, risk, severity=1, probability=1, user=None, **overrides):
        """Create an assessment for a risk.

        :param risk: risk being assessed.
        :param int severity: severity ordinal value.
        :param int probability: probability ordinal value.
        :param user: user performing the assessment; defaults to the analyst.
        :param overrides: field values overriding the defaults.
        :return: the created assessment.
        :rtype: :class:`odoo.models.Model`
        """
        actor = user or self.user_analyst
        values = {
            "risk_id": risk.id,
            "severity_level_id": self._severity(severity, risk.matrix_id).id,
            "probability_level_id": self._probability(probability, risk.matrix_id).id,
            "assessed_by_id": actor.id,
            "estimation_rationale": "Test rationale for the selected levels.",
        }
        values.update(overrides)
        return self.env["ls.risk.assessment"].with_user(actor).create(values)

    def _approved_assessment(self, risk, severity=1, probability=1):
        """Create, confirm and approve an assessment with two distinct users.

        :param risk: risk being assessed.
        :param int severity: severity ordinal value.
        :param int probability: probability ordinal value.
        :return: the approved assessment.
        :rtype: :class:`odoo.models.Model`
        """
        assessment = self._make_assessment(risk, severity, probability)
        assessment.with_user(self.user_analyst).action_confirm()
        assessment.with_user(self.user_manager).action_approve()
        return assessment

    def _make_fmea(self, user=None, **overrides):
        """Create an FMEA worksheet.

        :param user: user creating the record; defaults to the analyst.
        :param overrides: field values overriding the defaults.
        :return: the created worksheet.
        :rtype: :class:`odoo.models.Model`
        """
        values = {
            "title": "Test FMEA",
            "fmea_type": "process",
            "scope": "Test scope covering the unit under analysis.",
            "company_id": self.company.id,
            "facilitator_id": (user or self.user_analyst).id,
        }
        values.update(overrides)
        model = self.env["ls.risk.fmea"].with_user(user or self.user_analyst)
        return model.create(values)

    def _make_fmea_line(self, fmea, severity=5, occurrence=4, detection=3, **overrides):
        """Create a failure mode row on a worksheet.

        :param fmea: worksheet owning the row.
        :param int severity: severity rating.
        :param int occurrence: occurrence rating.
        :param int detection: detection rating.
        :param overrides: field values overriding the defaults.
        :return: the created row.
        :rtype: :class:`odoo.models.Model`
        """
        values = {
            "fmea_id": fmea.id,
            "item": "Test item",
            "item_function": "Test function",
            "failure_mode": "Test failure mode",
            "failure_effect": "Test effect",
            "failure_cause": "Test cause",
            "severity": severity,
            "occurrence": occurrence,
            "detection": detection,
        }
        values.update(overrides)
        return self.env["ls.risk.fmea.line"].create(values)
