# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0.html).
"""Tests for the Article 19 labelling particulars."""

from datetime import date

from odoo.exceptions import UserError, ValidationError
from odoo.tests import tagged

from .common import LsCosmeticsCommon


@tagged("post_install", "-at_install")
class TestLsCosmeticLabel(LsCosmeticsCommon):
    """Verify the particulars, the durability rule and the generated list."""

    def setUp(self):
        """Approve the shared formulation before each test."""
        super().setUp()
        if self.formulation.state != "approved":
            self._approve_formulation()

    def _complete_label(self, **overrides):
        """Create a label carrying every Article 19(1) particular."""
        values = {
            "name": "Hydrating cream label",
            "formulation_id": self.formulation.id,
            "responsible_person_id": self.responsible_partner.id,
            "nominal_content": "50 ml",
            "durability_mode": "pao",
            "pao_months": 12,
            "precautions": "Avoid contact with the eyes.",
            "batch_reference_rule": "Ink-jet printed on the crimp.",
            "product_function": "Face moisturiser.",
        }
        values.update(overrides)
        label = self.label_model.create(values)
        label.action_generate_ingredient_list()
        return label

    def test_generated_list_matches_the_formulation(self):
        """The label list is built from the formulation composition."""
        label = self._complete_label()
        self.assertEqual(
            label.ingredient_list,
            "AQUA, GLYCERIN, TITANIUM DIOXIDE (nano), PHENOXYETHANOL, parfum",
        )
        self.assertTrue(label.ingredient_list_generated_on)

    def test_missing_particulars_are_reported(self):
        """Every absent particular is named."""
        label = self.label_model.create(
            {"name": "Empty label", "formulation_id": self.formulation.id}
        )
        missing = label._missing_particulars()
        self.assertGreaterEqual(len(missing), 5)

    def test_approval_requires_every_particular(self):
        """A label with missing particulars cannot be approved."""
        label = self.label_model.create(
            {"name": "Empty label", "formulation_id": self.formulation.id}
        )
        label.action_submit_review()
        with self.assertRaises(UserError):
            label.with_user(self.user_manager).action_approve()

    def test_complete_label_is_approved(self):
        """A complete label reaches the approved state."""
        label = self._complete_label()
        label.action_submit_review()
        label.with_user(self.user_manager).action_approve()
        self.assertEqual(label.state, "approved")

    def test_thirty_month_durability_rule(self):
        """Above thirty months a period after opening must be used."""
        with self.assertRaises(ValidationError):
            self._complete_label(
                durability_mode="min_durability",
                minimum_durability_date=date(2030, 1, 1),
                stated_durability_months=36,
                pao_months=0,
            )

    def test_period_after_opening_requires_months(self):
        """A period after opening with no months is refused."""
        with self.assertRaises(ValidationError):
            self._complete_label(durability_mode="pao", pao_months=0)

    def test_imported_product_requires_country_of_origin(self):
        """An imported product must state its country of origin.

        ``action_approve`` reports the missing particular and raises
        UserError before the constraint is reached; the constraint is
        covered separately below.
        """
        label = self._complete_label(is_imported=True)
        label.action_submit_review()
        with self.assertRaises(UserError):
            label.with_user(self.user_manager).action_approve()

    def test_country_of_origin_constraint_blocks_direct_write(self):
        """The constraint refuses approval even when the gate is bypassed."""
        label = self._complete_label(is_imported=True)
        label.action_submit_review()
        with self.assertRaises(ValidationError):
            label.sudo().write({"state": "approved"})

    def test_content_exemption_requires_a_reason(self):
        """Claiming the content exemption requires a documented reason."""
        label = self._complete_label(
            nominal_content=False, content_exempt=True
        )
        label.action_submit_review()
        with self.assertRaises(ValidationError):
            label.with_user(self.user_manager).action_approve()

    def test_function_may_be_clear_from_presentation(self):
        """Recording that the function is clear satisfies particular (f)."""
        label = self._complete_label(
            product_function=False, function_clear_from_presentation=True
        )
        self.assertNotIn(
            "(f) function of the product", label._missing_particulars()
        )

    def test_approved_label_is_frozen(self):
        """The particulars of an approved label cannot be modified."""
        label = self._complete_label()
        label.action_submit_review()
        label.with_user(self.user_manager).action_approve()
        with self.assertRaises(UserError):
            label.write({"nominal_content": "100 ml"})

    def test_regeneration_is_blocked_after_approval(self):
        """The ingredient list cannot be regenerated once approved."""
        label = self._complete_label()
        label.action_submit_review()
        label.with_user(self.user_manager).action_approve()
        with self.assertRaises(UserError):
            label.action_generate_ingredient_list()

    def test_suggested_pao_end_date(self):
        """The informative period-after-opening end date is computed."""
        label = self._complete_label(pao_months=6)
        self.assertEqual(
            label._suggested_pao_end_date(date(2026, 1, 1)), date(2026, 7, 1)
        )
