# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0.html).
"""Tests for the cosmetic ingredient register and annex restrictions."""

from datetime import date

from psycopg2 import errors as pg_errors

from odoo.exceptions import ValidationError
from odoo.tests import tagged

from .common import LsCosmeticsCommon


@tagged("post_install", "-at_install")
class TestLsCosmeticIngredient(LsCosmeticsCommon):
    """Verify identification, flags and annex linkage of ingredients."""

    def test_inci_name_is_unique_per_company(self):
        """A second ingredient with the same INCI name is rejected."""
        with self.assertRaises(pg_errors.UniqueViolation):
            with self.env.cr.savepoint():
                self.ingredient_model.create({"inci_name": "AQUA"})

    def test_cmr_flag_requires_category(self):
        """A CMR flag without a category is refused."""
        with self.assertRaises(ValidationError):
            self.ingredient_model.create(
                {"inci_name": "TEST CMR SUBSTANCE", "is_cmr": True}
            )

    def test_cmr_category_requires_flag(self):
        """A CMR category without the flag is refused."""
        with self.assertRaises(ValidationError):
            self.ingredient_model.create(
                {"inci_name": "TEST CMR CATEGORY", "cmr_category": "1a"}
            )

    def test_exclusion_flags_are_mutually_exclusive(self):
        """An ingredient cannot be both an impurity and a processing aid."""
        with self.assertRaises(ValidationError):
            self.ingredient_model.create(
                {
                    "inci_name": "TEST EXCLUSION",
                    "is_impurity": True,
                    "is_processing_aid": True,
                }
            )

    def test_label_token_appends_nano_suffix(self):
        """A nanomaterial token carries the word nano in brackets."""
        self.assertEqual(self.nano._label_token(), "TITANIUM DIOXIDE (nano)")

    def test_label_token_uses_perfume_term(self):
        """A perfume composition is referred to by the term parfum."""
        self.assertEqual(self.perfume._label_token(), "parfum")

    def test_label_token_lists_annex_iii_other_individually(self):
        """A substance flagged for individual listing keeps its INCI name."""
        self.perfume.requires_individual_listing = True
        self.assertEqual(
            self.perfume._label_token(), "TEST FRAGRANCE COMPOSITION"
        )

    def test_prohibited_is_computed_from_annex_ii(self):
        """Linking an Annex II entry marks the ingredient as prohibited."""
        restriction = self.restriction_model.create(
            {
                "annex": "ii",
                "reference_number": "1",
                "substance_name": "Test prohibited substance",
                "source_reference": "Test consolidated text",
                "consolidation_date": date(2026, 1, 21),
            }
        )
        self.glycerin.restriction_ids = [(4, restriction.id)]
        self.assertTrue(self.glycerin.prohibited)

    def test_annex_ii_entry_cannot_carry_a_numeric_limit(self):
        """A prohibited substance has no permitted concentration."""
        with self.assertRaises(ValidationError):
            self.restriction_model.create(
                {
                    "annex": "ii",
                    "reference_number": "2",
                    "substance_name": "Test prohibited substance",
                    "source_reference": "Test consolidated text",
                    "consolidation_date": date(2026, 1, 21),
                    "has_numeric_limit": True,
                    "max_concentration": 0.5,
                }
            )

    def test_numeric_limit_requires_positive_value(self):
        """A declared numeric limit must be greater than zero."""
        with self.assertRaises(ValidationError):
            self.restriction_model.create(
                {
                    "annex": "v",
                    "reference_number": "29",
                    "substance_name": "Test preservative",
                    "source_reference": "Test consolidated text",
                    "consolidation_date": date(2026, 1, 21),
                    "has_numeric_limit": True,
                    "max_concentration": 0.0,
                }
            )

    def test_applicability_window_is_ordered(self):
        """An applicability window cannot end before it starts."""
        with self.assertRaises(ValidationError):
            self.restriction_model.create(
                {
                    "annex": "iii",
                    "reference_number": "98",
                    "substance_name": "Test restricted substance",
                    "source_reference": "Test consolidated text",
                    "consolidation_date": date(2026, 1, 21),
                    "date_from": date(2026, 6, 1),
                    "date_to": date(2026, 1, 1),
                }
            )

    def test_is_applicable_on_filters_by_date(self):
        """Only entries in force on the tested date are returned."""
        entry = self.restriction_model.create(
            {
                "annex": "iii",
                "reference_number": "99",
                "substance_name": "Test restricted substance",
                "source_reference": "Test consolidated text",
                "consolidation_date": date(2026, 1, 21),
                "date_from": date(2026, 6, 1),
            }
        )
        self.assertFalse(entry._is_applicable_on(date(2026, 1, 1)))
        self.assertEqual(entry._is_applicable_on(date(2026, 7, 1)), entry)
