# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Unit tests for the pure evaluation engine.

These tests import only the pure modules and therefore run without a database.
They are the primary verification of the limit comparison rules, which are the
most compliance-sensitive logic in the module.
"""

import unittest

from ..models import evaluation
from ..models.constants import (
    DIRECTION_LOWER,
    DIRECTION_UPPER,
    EVAL_ACTION,
    EVAL_ALERT,
    EVAL_NO_LIMIT,
    EVAL_NOT_EVALUATED,
    EVAL_SPEC,
    EVAL_WITHIN,
    EVALUATION_SEVERITY,
    EVALUATIONS,
    QUALITATIVE_FAIL,
    QUALITATIVE_PASS,
    TREND_DIRECTION_DECREASING,
    TREND_DIRECTION_INCREASING,
    TREND_DIRECTION_INSUFFICIENT,
    TREND_DIRECTION_STABLE,
)


class TestConstants(unittest.TestCase):
    """The vocabulary must be internally consistent."""

    def test_every_evaluation_has_a_severity(self):
        self.assertEqual(
            set(dict(EVALUATIONS)),
            set(EVALUATION_SEVERITY),
            "every evaluation code must have a severity rank",
        )

    def test_severity_ranks_are_distinct(self):
        ranks = list(EVALUATION_SEVERITY.values())
        self.assertEqual(len(ranks), len(set(ranks)))


class TestIsBreach(unittest.TestCase):
    """Threshold comparison, including the boundary case."""

    def test_upper_bound_above_threshold_is_a_breach(self):
        self.assertTrue(evaluation.is_breach(11.0, 10.0, DIRECTION_UPPER))

    def test_upper_bound_equal_to_threshold_is_compliant(self):
        self.assertFalse(evaluation.is_breach(10.0, 10.0, DIRECTION_UPPER))

    def test_lower_bound_below_threshold_is_a_breach(self):
        self.assertTrue(evaluation.is_breach(9.0, 10.0, DIRECTION_LOWER))

    def test_lower_bound_equal_to_threshold_is_compliant(self):
        self.assertFalse(evaluation.is_breach(10.0, 10.0, DIRECTION_LOWER))

    def test_unset_threshold_is_never_breached(self):
        self.assertFalse(evaluation.is_breach(1000.0, None, DIRECTION_UPPER))

    def test_absent_value_is_never_a_breach(self):
        self.assertFalse(evaluation.is_breach(None, 1.0, DIRECTION_UPPER))

    def test_unknown_direction_is_rejected(self):
        with self.assertRaises(ValueError):
            evaluation.is_breach(1.0, 1.0, "sideways")


class TestEvaluateQuantitative(unittest.TestCase):
    """The most severe breached threshold determines the outcome."""

    def test_most_severe_threshold_wins(self):
        self.assertEqual(
            evaluation.evaluate_quantitative(
                150.0, DIRECTION_UPPER, alert=100.0, action=140.0, spec=200.0),
            EVAL_ACTION,
        )

    def test_specification_outranks_action(self):
        self.assertEqual(
            evaluation.evaluate_quantitative(
                250.0, DIRECTION_UPPER, alert=100.0, action=140.0, spec=200.0),
            EVAL_SPEC,
        )

    def test_alert_only(self):
        self.assertEqual(
            evaluation.evaluate_quantitative(
                110.0, DIRECTION_UPPER, alert=100.0, action=140.0, spec=200.0),
            EVAL_ALERT,
        )

    def test_within_limits(self):
        self.assertEqual(
            evaluation.evaluate_quantitative(
                50.0, DIRECTION_UPPER, alert=100.0),
            EVAL_WITHIN,
        )

    def test_no_threshold_configured(self):
        self.assertEqual(
            evaluation.evaluate_quantitative(50.0, DIRECTION_UPPER),
            EVAL_NO_LIMIT,
        )

    def test_no_value_recorded(self):
        self.assertEqual(
            evaluation.evaluate_quantitative(None, DIRECTION_UPPER, alert=1.0),
            EVAL_NOT_EVALUATED,
        )

    def test_zero_is_a_recorded_value_not_a_missing_one(self):
        self.assertEqual(
            evaluation.evaluate_quantitative(0.0, DIRECTION_UPPER, alert=1.0),
            EVAL_WITHIN,
        )

    def test_lower_bound_direction(self):
        self.assertEqual(
            evaluation.evaluate_quantitative(5.0, DIRECTION_LOWER, action=10.0),
            EVAL_ACTION,
        )
        self.assertEqual(
            evaluation.evaluate_quantitative(15.0, DIRECTION_LOWER, action=10.0),
            EVAL_WITHIN,
        )


class TestEvaluateQualitative(unittest.TestCase):
    """A qualitative failure is treated as an action exceedance."""

    def test_pass(self):
        self.assertEqual(
            evaluation.evaluate_qualitative(QUALITATIVE_PASS), EVAL_WITHIN)

    def test_fail(self):
        self.assertEqual(
            evaluation.evaluate_qualitative(QUALITATIVE_FAIL), EVAL_ACTION)

    def test_nothing_recorded(self):
        self.assertEqual(
            evaluation.evaluate_qualitative(None), EVAL_NOT_EVALUATED)


class TestWorstEvaluation(unittest.TestCase):
    """Roll-up of result outcomes to the parent sample."""

    def test_picks_the_most_severe(self):
        self.assertEqual(
            evaluation.worst_evaluation(
                [EVAL_WITHIN, EVAL_ALERT, EVAL_WITHIN]),
            EVAL_ALERT,
        )

    def test_empty_input(self):
        self.assertEqual(evaluation.worst_evaluation([]), EVAL_NOT_EVALUATED)

    def test_unknown_code_is_rejected(self):
        with self.assertRaises(ValueError):
            evaluation.worst_evaluation(["not_a_code"])


class TestStatistics(unittest.TestCase):
    """Descriptive statistics, including undefined cases."""

    def test_mean(self):
        self.assertEqual(evaluation.mean([1, 2, 3]), 2.0)
        self.assertIsNone(evaluation.mean([]))

    def test_median_odd_and_even(self):
        self.assertEqual(evaluation.median([3, 1, 2]), 2.0)
        self.assertEqual(evaluation.median([1, 2, 3, 4]), 2.5)
        self.assertIsNone(evaluation.median([]))

    def test_standard_deviation_is_undefined_for_one_value(self):
        self.assertIsNone(evaluation.standard_deviation([5]))

    def test_standard_deviation_known_value(self):
        self.assertAlmostEqual(
            evaluation.standard_deviation([2, 4, 4, 4, 5, 5, 7, 9]),
            2.13808993,
            places=6,
        )

    def test_exceedance_rate(self):
        self.assertEqual(evaluation.exceedance_rate(4, 1), 0.25)
        self.assertEqual(evaluation.exceedance_rate(0, 0), 0.0)

    def test_exceedance_rate_rejects_inconsistent_counts(self):
        with self.assertRaises(ValueError):
            evaluation.exceedance_rate(1, 2)
        with self.assertRaises(ValueError):
            evaluation.exceedance_rate(-1, 0)

    def test_summarise_empty(self):
        summary = evaluation.summarise([])
        self.assertEqual(summary["count"], 0)
        self.assertIsNone(summary["mean"])
        self.assertIsNone(summary["minimum"])
        self.assertIsNone(summary["maximum"])
        self.assertIsNone(summary["median"])
        self.assertIsNone(summary["standard_deviation"])

    def test_summarise_populated(self):
        summary = evaluation.summarise([2.0, 4.0, 6.0, 8.0])
        self.assertEqual(summary["count"], 4)
        self.assertEqual(summary["minimum"], 2.0)
        self.assertEqual(summary["maximum"], 8.0)
        self.assertEqual(summary["mean"], 5.0)
        self.assertEqual(summary["median"], 5.0)
        self.assertAlmostEqual(
            summary["standard_deviation"], 2.5819889, places=6)

    def test_summarise_single_value_reports_undefined_deviation(self):
        summary = evaluation.summarise([7.0])
        self.assertEqual(summary["count"], 1)
        self.assertEqual(summary["mean"], 7.0)
        self.assertIsNone(summary["standard_deviation"])


class TestTrendDirection(unittest.TestCase):
    """Direction is descriptive and refuses to report on thin data."""

    def test_too_few_values(self):
        self.assertEqual(
            evaluation.trend_direction([1, 1, 1], 0.2),
            TREND_DIRECTION_INSUFFICIENT,
        )

    def test_increasing(self):
        self.assertEqual(
            evaluation.trend_direction([1, 1, 1, 5, 5, 5], 0.2),
            TREND_DIRECTION_INCREASING,
        )

    def test_decreasing(self):
        self.assertEqual(
            evaluation.trend_direction([5, 5, 5, 1, 1, 1], 0.2),
            TREND_DIRECTION_DECREASING,
        )

    def test_stable(self):
        self.assertEqual(
            evaluation.trend_direction([1, 1, 1, 1, 1, 1], 0.2),
            TREND_DIRECTION_STABLE,
        )

    def test_zero_baseline_is_reported_as_insufficient(self):
        self.assertEqual(
            evaluation.trend_direction([0, 0, 0, 1, 1, 1], 0.2),
            TREND_DIRECTION_INSUFFICIENT,
        )

    def test_negative_threshold_is_rejected(self):
        with self.assertRaises(ValueError):
            evaluation.trend_direction([1, 2, 3, 4, 5, 6], -0.1)
