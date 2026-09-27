# Part of the Life Sciences Suite. See LICENSE file for full copyright and licensing details.
"""Tests for specifications and their acceptance criteria."""

from odoo.exceptions import UserError, ValidationError
from odoo.tests import tagged

from .common import LsLabCommon


@tagged("post_install", "-at_install")
class TestLsLabSpecification(LsLabCommon):
    """Cover BRU-02 to BRU-05 and BRU-30."""

    def test_only_approved_methods_may_be_referenced(self):
        """A draft method cannot be used in a specification (BRU-04)."""
        draft_method = self.env["ls.lab.test_method"].create({"name": "Draft method"})
        with self.assertRaises(ValidationError):
            self.env["ls.lab.specification"].create({
                "name": "Invalid specification",
                "product_id": self.product.id,
                "line_ids": [(0, 0, {
                    "test_method_id": draft_method.id,
                    "criterion_type": "range",
                    "min_value": 1.0,
                    "max_value": 2.0,
                })],
            })

    def test_range_minimum_cannot_exceed_maximum(self):
        """An inverted numeric range is refused (BRU-30)."""
        method = self._create_approved_method(name="Range method")
        with self.assertRaises(ValidationError):
            self.env["ls.lab.specification"].create({
                "name": "Inverted range",
                "product_id": self.product.id,
                "line_ids": [(0, 0, {
                    "test_method_id": method.id,
                    "criterion_type": "range",
                    "min_value": 10.0,
                    "max_value": 5.0,
                })],
            })

    def test_text_criterion_requires_expected_text(self):
        """A text criterion without expected text is refused (BRU-30)."""
        method = self._create_approved_method(name="Text method", result_type="text")
        with self.assertRaises(ValidationError):
            self.env["ls.lab.specification"].create({
                "name": "Missing expected text",
                "product_id": self.product.id,
                "line_ids": [(0, 0, {
                    "test_method_id": method.id,
                    "criterion_type": "text",
                })],
            })

    def test_specification_without_lines_cannot_be_approved(self):
        """An empty specification cannot be approved."""
        specification = self.env["ls.lab.specification"].create({
            "name": "Empty specification",
            "product_id": self.product.id,
        })
        specification.action_submit_review()
        with self.assertRaises(ValidationError):
            specification.with_user(self.manager).action_approve()

    def test_single_approved_version_per_scope(self):
        """Two approved specifications cannot coexist for one scope (BRU-05)."""
        self._create_approved_specification()
        method = self._create_approved_method(name="Second method")
        duplicate = self.env["ls.lab.specification"].create({
            "name": "Competing specification",
            "product_id": self.product.id,
            "spec_type": "finished_product",
            "line_ids": [(0, 0, {
                "test_method_id": method.id,
                "criterion_type": "min",
                "min_value": 1.0,
            })],
        })
        duplicate.action_submit_review()
        with self.assertRaises(ValidationError):
            duplicate.with_user(self.manager).action_approve()

    def test_approved_specification_lines_are_frozen(self):
        """Lines of an approved specification cannot change (BRU-03)."""
        specification = self._create_approved_specification()
        line = specification.line_ids[0]
        with self.assertRaises(UserError):
            line.write({"min_value": 90.0})
        with self.assertRaises(UserError):
            line.unlink()

    def test_line_cannot_be_added_to_approved_specification(self):
        """New lines cannot be added once approved (BRU-03)."""
        specification = self._create_approved_specification()
        method = self._create_approved_method(name="Late addition")
        with self.assertRaises(UserError):
            self.env["ls.lab.specification_line"].create({
                "specification_id": specification.id,
                "test_method_id": method.id,
                "criterion_type": "max",
                "max_value": 1.0,
            })

    def test_criterion_display_renders_range(self):
        """The readable criterion is rendered from the numeric bounds."""
        specification = self._create_approved_specification()
        line = specification.line_ids[0]
        self.assertIn("95.00", line.criterion_display)
        self.assertIn("105.00", line.criterion_display)

    def test_revision_copies_lines(self):
        """A specification revision carries its acceptance criteria forward."""
        specification = self._create_approved_specification()
        action = specification.with_user(self.manager).action_create_revision()
        successor = self.env["ls.lab.specification"].browse(action["res_id"])
        self.assertEqual(len(successor.line_ids), len(specification.line_ids))
        self.assertEqual(successor.state, "draft")
