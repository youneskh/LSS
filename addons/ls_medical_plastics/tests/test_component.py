# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Tests for the component register."""

from odoo.exceptions import ValidationError
from odoo.tests import tagged

from .common import MedicalPlasticsCommon


@tagged("post_install", "-at_install")
class TestComponent(MedicalPlasticsCommon):
    """Component classification, constraints and release workflow."""

    def test_primary_packaging_computed_from_category(self):
        """Closure and cap components are flagged as primary packaging."""
        self.assertTrue(self.component.is_primary_packaging)

    def test_non_packaging_category_not_flagged(self):
        """A secondary packaging component is not primary packaging."""
        component = self.env["ls.mp.component"].create(
            {
                "name": "Carton Insert",
                "code": "INS-01",
                "product_id": self.product_component.id,
                "category": "secondary_component",
            }
        )
        self.assertFalse(component.is_primary_packaging)

    def test_primary_grade_must_be_approved(self):
        """The primary grade must be listed among the approved grades."""
        with self.assertRaises(ValidationError):
            self.component.write(
                {"primary_material_grade_id": self.grade_unqualified.id}
            )

    def test_sterile_requires_method(self):
        """A component supplied sterile must declare a sterilisation method."""
        with self.assertRaises(ValidationError):
            self.component.write({"sterile_supply": True, "sterilization_method": "none"})

    def test_sterile_with_method_accepted(self):
        """Declaring a method allows the component to be supplied sterile."""
        self.component.write({"sterile_supply": True, "sterilization_method": "gamma"})
        self.assertEqual(self.component.sterilization_method, "gamma")

    def test_release_requires_material_grade(self):
        """A component without approved grades cannot be released."""
        component = self.env["ls.mp.component"].create(
            {
                "name": "No Grade",
                "code": "NOGRD",
                "product_id": self.product_component.id,
                "category": "closure_cap",
            }
        )
        with self.assertRaises(ValidationError):
            component.action_release()

    def test_hold_requires_released_state(self):
        """Only a released component can be placed on hold."""
        component = self.env["ls.mp.component"].create(
            {
                "name": "Draft Component",
                "code": "DRFT",
                "product_id": self.product_component.id,
                "category": "closure_cap",
            }
        )
        with self.assertRaises(ValidationError):
            component.action_hold()

    def test_hold_and_re_release(self):
        """A released component can be held and released again."""
        self.component.action_hold()
        self.assertEqual(self.component.state, "on_hold")
        self.component.action_release()
        self.assertEqual(self.component.state, "released")

    def test_counts_reflect_relations(self):
        """Smart-button counters reflect tools, specifications and runs."""
        self.assertEqual(self.component.tool_count, 1)
        self.assertEqual(self.component.parameter_spec_count, 1)
        self.assertEqual(self.component.approved_spec_count, 1)

    def test_onchange_sterile_clears_method(self):
        """Clearing the sterile flag resets the sterilisation method."""
        # A form record (not saved): on a saved record the constraint
        # "sterile supply requires a method" is checked before the onchange.
        component = self.component.new(
            {"sterile_supply": True, "sterilization_method": "eto"}
        )
        component.sterile_supply = False
        component._onchange_sterile_supply()
        self.assertEqual(component.sterilization_method, "none")
