# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0.html).
"""Access right and record rule tests."""

from odoo.exceptions import AccessError
from odoo.tests import tagged

from .common import LsCosmeticsCommon


@tagged("post_install", "-at_install")
class TestLsCosmeticSecurity(LsCosmeticsCommon):
    """Verify that each group has the access the design intends."""

    def test_reader_can_read_but_not_write(self):
        """The read-only group cannot modify a formulation."""
        formulation = self.formulation.with_user(self.user_reader)
        self.assertTrue(formulation.name)
        with self.assertRaises(AccessError):
            formulation.write({"name": "Renamed by a reader"})

    def test_reader_cannot_create_ingredients(self):
        """The read-only group cannot extend the ingredient register."""
        with self.assertRaises(AccessError):
            self.ingredient_model.with_user(self.user_reader).create(
                {"inci_name": "TEST READER INGREDIENT"}
            )

    def test_formulator_can_create_ingredients(self):
        """The formulator group maintains the ingredient register."""
        ingredient = self.ingredient_model.with_user(self.user_formulator).create(
            {"inci_name": "TEST FORMULATOR INGREDIENT"}
        )
        self.assertTrue(ingredient.id)

    def test_formulator_cannot_delete_ingredients(self):
        """Deleting register entries is reserved to the regulatory manager."""
        ingredient = self.ingredient_model.with_user(self.user_formulator).create(
            {"inci_name": "TEST DELETABLE INGREDIENT"}
        )
        with self.assertRaises(AccessError):
            ingredient.unlink()

    def test_formulator_cannot_write_safety_reports(self):
        """Safety reports are not writable by the formulator group."""
        assessment = self._build_approved_assessment()
        with self.assertRaises(AccessError):
            assessment.with_user(self.user_formulator).write({"note": "edited"})

    def test_assessor_cannot_write_formulations(self):
        """The assessor group reads compositions but does not edit them."""
        with self.assertRaises(AccessError):
            self.formulation.with_user(self.user_assessor).write({"note": "edited"})

    def test_formulator_cannot_manage_information_files(self):
        """Product information files are reserved to the regulatory manager."""
        with self.assertRaises(AccessError):
            self.pif_model.with_user(self.user_formulator).create(
                {
                    "name": "Unauthorised file",
                    "product_tmpl_id": self.product.id,
                    "responsible_person_id": self.responsible_partner.id,
                    "responsible_person_basis": "manufacturer",
                    "file_address": "Nowhere",
                }
            )

    def test_formulator_cannot_maintain_annex_data(self):
        """Annex restriction data is reserved to the regulatory manager."""
        with self.assertRaises(AccessError):
            self.restriction_model.with_user(self.user_formulator).create(
                {
                    "annex": "iii",
                    "reference_number": "999",
                    "substance_name": "Unauthorised entry",
                    "source_reference": "Test",
                    "consolidation_date": "2026-01-21",
                }
            )

    def test_manager_has_full_access(self):
        """The regulatory manager can create records on every model."""
        restriction = self.restriction_model.with_user(self.user_manager).create(
            {
                "annex": "iv",
                "reference_number": "1000",
                "substance_name": "Manager entry",
                "source_reference": "Test",
                "consolidation_date": "2026-01-21",
            }
        )
        self.assertTrue(restriction.id)
        restriction.unlink()

    def test_records_are_scoped_to_the_company(self):
        """A record of another company is not visible."""
        other_company = self.env["res.company"].create({"name": "Other Cosmetics SARL"})
        other_formulation = self.formulation_model.create(
            {
                "name": "Other company base",
                "company_id": other_company.id,
                "line_ids": [
                    (0, 0, {"ingredient_id": self.aqua.id, "concentration": 100.0})
                ],
            }
        )
        visible = self.formulation_model.with_user(self.user_reader).search([])
        self.assertNotIn(other_formulation, visible)
