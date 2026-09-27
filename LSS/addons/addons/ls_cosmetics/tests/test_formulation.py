# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0.html).
"""Tests for the formulation state machine and the label list builder."""

from datetime import date

from psycopg2 import errors as pg_errors

from odoo.exceptions import UserError, ValidationError
from odoo.tests import tagged

from .common import LsCosmeticsCommon


@tagged("post_install", "-at_install")
class TestLsCosmeticFormulation(LsCosmeticsCommon):
    """Verify composition rules, approval and ingredient list generation."""

    def test_sequence_assigns_code(self):
        """A created formulation receives a code from the sequence."""
        self.assertNotEqual(self.formulation.code, "New")
        self.assertTrue(self.formulation.code.startswith("CFM/"))

    def test_total_percentage_is_summed(self):
        """The composition total is the sum of the line concentrations."""
        self.assertAlmostEqual(self.formulation.total_percentage, 100.0, places=6)
        self.assertEqual(self.formulation.line_count, 5)

    def test_review_requires_total_of_one_hundred(self):
        """A composition that does not total 100 % cannot be reviewed."""
        formulation = self.formulation_model.create(
            {
                "name": "Incomplete base",
                "line_ids": [
                    (0, 0, {"ingredient_id": self.aqua.id, "concentration": 50.0})
                ],
            }
        )
        with self.assertRaises(ValidationError):
            formulation.action_submit_review()

    def test_duplicate_ingredient_is_rejected(self):
        """The same ingredient cannot appear twice in one formulation."""
        with self.assertRaises(pg_errors.UniqueViolation):
            with self.env.cr.savepoint():
                self.formulation.line_ids = [
                    (0, 0, {"ingredient_id": self.aqua.id, "concentration": 1.0})
                ]

    def test_negative_concentration_is_rejected(self):
        """A line concentration must be strictly positive."""
        with self.assertRaises(pg_errors.CheckViolation):
            with self.env.cr.savepoint():
                self.formulation_model.create(
                    {
                        "name": "Negative base",
                        "line_ids": [
                            (
                                0,
                                0,
                                {
                                    "ingredient_id": self.aqua.id,
                                    "concentration": -1.0,
                                },
                            )
                        ],
                    }
                )

    def test_segregation_of_duties_on_approval(self):
        """The submitter cannot approve their own formulation."""
        self.formulation.with_user(self.user_formulator).action_submit_review()
        with self.assertRaises(UserError):
            self.formulation.with_user(self.user_formulator).action_approve()

    def test_approval_by_second_user_succeeds(self):
        """A different user can approve the formulation."""
        self._approve_formulation()
        self.assertEqual(self.formulation.state, "approved")
        self.assertEqual(self.formulation.approved_by_id, self.user_manager)

    def test_approved_composition_is_frozen(self):
        """The composition of an approved formulation cannot be changed."""
        self._approve_formulation()
        with self.assertRaises(UserError):
            self.formulation.write({"name": "Renamed after approval"})

    def test_approved_formulation_cannot_be_deleted(self):
        """Only draft formulations may be deleted."""
        self._approve_formulation()
        with self.assertRaises(UserError):
            self.formulation.unlink()

    def test_restriction_status_reports_absence_of_data(self):
        """Without annex data the status is 'no_reference_data'."""
        statuses = set(self.formulation.line_ids.mapped("restriction_status"))
        self.assertEqual(statuses, {"no_reference_data"})
        self.assertEqual(self.formulation.unevaluated_line_count, 5)

    def test_over_limit_is_detected(self):
        """A concentration above a recorded numeric limit is flagged."""
        restriction = self.restriction_model.create(
            {
                "annex": "v",
                "reference_number": "29",
                "substance_name": "Phenoxyethanol",
                "source_reference": "Test consolidated text",
                "consolidation_date": date(2026, 1, 21),
                "has_numeric_limit": True,
                "max_concentration": 0.5,
            }
        )
        self.preservative.restriction_ids = [(4, restriction.id)]
        line = self.formulation.line_ids.filtered(
            lambda item: item.ingredient_id == self.preservative
        )
        self.assertEqual(line.restriction_status, "over_limit")
        self.assertEqual(self.formulation.blocking_finding_count, 1)

    def test_within_limit_is_detected(self):
        """A concentration below the recorded limit is reported as within it."""
        restriction = self.restriction_model.create(
            {
                "annex": "v",
                "reference_number": "30",
                "substance_name": "Phenoxyethanol",
                "source_reference": "Test consolidated text",
                "consolidation_date": date(2026, 1, 21),
                "has_numeric_limit": True,
                "max_concentration": 1.0,
            }
        )
        self.preservative.restriction_ids = [(4, restriction.id)]
        line = self.formulation.line_ids.filtered(
            lambda item: item.ingredient_id == self.preservative
        )
        self.assertEqual(line.restriction_status, "within_limit")
        self.assertEqual(self.formulation.blocking_finding_count, 0)

    def test_blocking_finding_prevents_approval(self):
        """A formulation with a blocking finding cannot be approved."""
        restriction = self.restriction_model.create(
            {
                "annex": "v",
                "reference_number": "31",
                "substance_name": "Phenoxyethanol",
                "source_reference": "Test consolidated text",
                "consolidation_date": date(2026, 1, 21),
                "has_numeric_limit": True,
                "max_concentration": 0.1,
            }
        )
        self.preservative.restriction_ids = [(4, restriction.id)]
        self.formulation.with_user(self.user_formulator).action_submit_review()
        with self.assertRaises(UserError):
            self.formulation.with_user(self.user_manager).action_approve()

    def test_ingredient_list_is_in_descending_order(self):
        """The generated list follows descending order of weight."""
        generated = self.formulation.build_ingredient_list()
        self.assertEqual(
            generated,
            "AQUA, GLYCERIN, TITANIUM DIOXIDE (nano), PHENOXYETHANOL, parfum",
        )

    def test_ingredient_list_excludes_impurities(self):
        """Impurities are not regarded as ingredients for labelling."""
        impurity = self.ingredient_model.create(
            {"inci_name": "TEST IMPURITY", "is_impurity": True}
        )
        self.formulation.line_ids = [
            (0, 0, {"ingredient_id": impurity.id, "concentration": 0.001})
        ]
        self.assertNotIn("TEST IMPURITY", self.formulation.build_ingredient_list())

    def test_ingredient_list_can_place_colorants_last(self):
        """Colorants may be listed after the other cosmetic ingredients."""
        colorant = self.ingredient_model.create(
            {
                "inci_name": "CI 77491",
                "regulatory_category": "colorant",
                "colour_index": "77491",
            }
        )
        self.formulation.line_ids = [
            (0, 0, {"ingredient_id": colorant.id, "concentration": 50.0})
        ]
        generated = self.formulation.build_ingredient_list(colorants_last=True)
        self.assertTrue(generated.endswith("CI 77491"))

    def test_may_contain_marker_is_added(self):
        """The permitted marker precedes the colorant block when requested."""
        colorant = self.ingredient_model.create(
            {"inci_name": "CI 19140", "regulatory_category": "colorant"}
        )
        self.formulation.line_ids = [
            (0, 0, {"ingredient_id": colorant.id, "concentration": 0.5})
        ]
        generated = self.formulation.build_ingredient_list(
            colorants_last=True, may_contain=True
        )
        self.assertIn("+/-, CI 19140", generated)

    def test_annex_wording_is_collected(self):
        """Label wording carried by linked annex entries is collected."""
        restriction = self.restriction_model.create(
            {
                "annex": "iii",
                "reference_number": "100",
                "substance_name": "Test restricted substance",
                "source_reference": "Test consolidated text",
                "consolidation_date": date(2026, 1, 21),
                "label_wording": "Do not use on damaged skin.",
            }
        )
        self.glycerin.restriction_ids = [(4, restriction.id)]
        wordings = self.formulation._get_annex_iii_other_warnings()
        self.assertEqual(wordings, ["Do not use on damaged skin."])
