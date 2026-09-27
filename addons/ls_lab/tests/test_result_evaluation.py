# Part of the Life Sciences Suite. See LICENSE file for full copyright and licensing details.
"""Tests for result evaluation, which must always derive from the specification."""

from odoo.exceptions import UserError, ValidationError
from odoo.tests import tagged

from .common import LsLabCommon


@tagged("post_install", "-at_install")
class TestLsLabResultEvaluation(LsLabCommon):
    """Cover BRU-08, BRU-09, BRU-10, BRU-16 and BRU-28."""

    def _sample_open_for_entry(self, lines=None):
        """Return a sample already open for result entry."""
        specification = self._create_approved_specification(lines=lines)
        sample = self._create_sample(specification)
        sample.action_start()
        sample.action_start_testing()
        return sample

    def test_draft_result_is_pending(self):
        """An unentered result never evaluates, even with a zero value."""
        sample = self._sample_open_for_entry()
        result = sample.result_ids[0]
        self.assertEqual(result.evaluation, "pending")
        self.assertEqual(result.result_numeric, 0.0)

    def test_value_inside_range_conforms(self):
        """A value within the acceptance range conforms."""
        sample = self._sample_open_for_entry()
        result = sample.result_ids[0]
        result.write({"result_numeric": 99.5})
        result.action_enter()
        self.assertEqual(result.evaluation, "conform")

    def test_value_outside_range_does_not_conform(self):
        """A value outside the acceptance range fails and raises an OOS."""
        sample = self._sample_open_for_entry()
        result = sample.result_ids[0]
        result.write({"result_numeric": 80.0})
        result.action_enter()
        self.assertEqual(result.evaluation, "non_conform")
        self.assertTrue(result.oos_id)
        self.assertEqual(result.oos_id.oos_type, "oos")

    def test_range_boundaries_are_inclusive(self):
        """Values exactly on the bounds conform."""
        sample = self._sample_open_for_entry()
        result = sample.result_ids[0]
        result.write({"result_numeric": 95.0})
        result.action_enter()
        self.assertEqual(result.evaluation, "conform")

    def test_evaluation_is_not_user_writable(self):
        """Writing the evaluation directly does not survive recomputation."""
        sample = self._sample_open_for_entry()
        result = sample.result_ids[0]
        result.write({"result_numeric": 80.0})
        result.action_enter()
        result.invalidate_recordset(["evaluation"])
        self.assertEqual(result.evaluation, "non_conform")

    def test_text_criterion_is_case_insensitive(self):
        """Text comparison ignores case and surrounding whitespace."""
        method = self._create_approved_method(name="Appearance", result_type="text")
        sample = self._sample_open_for_entry(lines=[{
            "test_method_id": method.id,
            "criterion_type": "text",
            "text_criterion": "White powder",
        }])
        result = sample.result_ids[0]
        result.write({"result_text": "  white POWDER "})
        result.action_enter()
        self.assertEqual(result.evaluation, "conform")

    def test_boolean_fail_raises_investigation(self):
        """A failing pass/fail result is non-conforming."""
        method = self._create_approved_method(name="Sterility", result_type="boolean")
        sample = self._sample_open_for_entry(lines=[{
            "test_method_id": method.id,
            "criterion_type": "boolean",
        }])
        result = sample.result_ids[0]
        result.write({"result_boolean": "fail"})
        result.action_enter()
        self.assertEqual(result.evaluation, "non_conform")
        self.assertTrue(result.oos_id)

    def test_informative_criterion_never_fails(self):
        """An informative criterion records a value without judging it."""
        method = self._create_approved_method(name="Observation")
        sample = self._sample_open_for_entry(lines=[{
            "test_method_id": method.id,
            "criterion_type": "informative",
        }])
        result = sample.result_ids[0]
        result.write({"result_numeric": 12345.0})
        result.action_enter()
        self.assertEqual(result.evaluation, "informative")
        self.assertFalse(result.oos_id)

    def test_max_criterion(self):
        """A not-more-than criterion fails above its bound."""
        method = self._create_approved_method(name="Impurity")
        sample = self._sample_open_for_entry(lines=[{
            "test_method_id": method.id,
            "criterion_type": "max",
            "max_value": 0.5,
        }])
        result = sample.result_ids[0]
        result.write({"result_numeric": 0.7})
        result.action_enter()
        self.assertEqual(result.evaluation, "non_conform")

    def test_analyst_cannot_review_own_result(self):
        """Second-person review is enforced on results (BRU-10)."""
        sample = self._sample_open_for_entry()
        result = sample.result_ids[0]
        result.with_user(self.analyst).write({"result_numeric": 100.0})
        result.with_user(self.analyst).action_enter()
        with self.assertRaises(UserError):
            result.with_user(self.analyst).action_review()

    def test_reviewed_result_cannot_be_modified(self):
        """A reviewed result is locked against value changes."""
        sample = self._sample_open_for_entry()
        result = sample.result_ids[0]
        result.with_user(self.analyst).write({"result_numeric": 100.0})
        result.with_user(self.analyst).action_enter()
        result.with_user(self.reviewer).action_review()
        with self.assertRaises(UserError):
            result.write({"result_numeric": 101.0})

    def test_entry_refused_when_sample_not_open(self):
        """A result cannot be entered before testing starts (BRU-09)."""
        specification = self._create_approved_specification()
        sample = self._create_sample(specification)
        result = sample.result_ids[0]
        result.write({"result_numeric": 100.0})
        with self.assertRaises(UserError):
            result.action_enter()

    def test_oot_requires_justification(self):
        """An out-of-trend flag without justification is refused (BRU-28)."""
        sample = self._sample_open_for_entry()
        result = sample.result_ids[0]
        with self.assertRaises(ValidationError):
            result.write({"is_oot": True})

    def test_oot_with_justification_raises_investigation(self):
        """A justified out-of-trend result raises an OOT investigation."""
        sample = self._sample_open_for_entry()
        result = sample.result_ids[0]
        result.write({
            "result_numeric": 100.0,
            "is_oot": True,
            "oot_justification": "Outside the historical control band for this test",
        })
        result.action_enter()
        self.assertEqual(result.evaluation, "conform")
        self.assertTrue(result.oos_id)
        self.assertEqual(result.oos_id.oos_type, "oot")

    def test_entered_result_cannot_be_deleted(self):
        """A result carrying data cannot be deleted."""
        sample = self._sample_open_for_entry()
        result = sample.result_ids[0]
        result.write({"result_numeric": 100.0})
        result.action_enter()
        with self.assertRaises(UserError):
            result.unlink()
