# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Limit evaluation and descriptive trend statistics.

Every function in this module is a pure function over plain Python values and
imports nothing from Odoo. The evaluation rules that determine whether a
monitoring result is acceptable are the most compliance-sensitive logic in the
module, so they are isolated here to be directly verifiable by unit tests that
do not need a database.

Threshold values are supplied by the caller. This module never supplies a
default threshold and contains no regulatory figures.
"""

from .constants import (
    DIRECTION_LOWER,
    DIRECTION_UPPER,
    EVAL_ACTION,
    EVAL_ALERT,
    EVAL_NO_LIMIT,
    EVAL_NOT_EVALUATED,
    EVAL_SPEC,
    EVAL_WITHIN,
    EVALUATION_SEVERITY,
    QUALITATIVE_FAIL,
    QUALITATIVE_PASS,
    TREND_DIRECTION_DECREASING,
    TREND_DIRECTION_INCREASING,
    TREND_DIRECTION_INSUFFICIENT,
    TREND_DIRECTION_STABLE,
    TREND_MINIMUM_SAMPLE_COUNT,
)


def is_breach(value, threshold, direction):
    """Return whether ``value`` breaches ``threshold`` in ``direction``.

    A threshold of ``None`` is not configured and can never be breached.

    The comparison is deliberately strict. A value exactly equal to the
    threshold is reported as compliant, which matches the usual reading of a
    limit expressed as "not more than" or "not less than". Organisations that
    require the opposite convention must configure the threshold accordingly.

    :param value: measured value, or ``None`` when no value was recorded
    :param threshold: configured threshold, or ``None`` when not configured
    :param str direction: :data:`~.constants.DIRECTION_UPPER` or
        :data:`~.constants.DIRECTION_LOWER`
    :returns: ``True`` when the value breaches the threshold
    :rtype: bool
    :raises ValueError: when ``direction`` is not a recognised direction
    """
    if value is None or threshold is None:
        return False
    if direction == DIRECTION_UPPER:
        return value > threshold
    if direction == DIRECTION_LOWER:
        return value < threshold
    raise ValueError("Unknown limit direction: %r" % (direction,))


def evaluate_quantitative(value, direction, alert=None, action=None, spec=None):
    """Evaluate a numeric result against up to three thresholds.

    The most severe breached threshold determines the outcome, so a value that
    breaches both the alert and the action threshold is reported as an action
    exceedance rather than an alert exceedance.

    :param value: measured value, or ``None``
    :param str direction: bound direction applied to all three thresholds
    :param alert: alert threshold, or ``None`` when not configured
    :param action: action threshold, or ``None`` when not configured
    :param spec: specification threshold, or ``None`` when not configured
    :returns: one of the evaluation codes defined in :mod:`.constants`
    :rtype: str
    """
    if value is None:
        return EVAL_NOT_EVALUATED
    if alert is None and action is None and spec is None:
        return EVAL_NO_LIMIT
    if is_breach(value, spec, direction):
        return EVAL_SPEC
    if is_breach(value, action, direction):
        return EVAL_ACTION
    if is_breach(value, alert, direction):
        return EVAL_ALERT
    return EVAL_WITHIN


def evaluate_qualitative(value):
    """Evaluate a pass/fail result.

    A recorded failure is treated as an action exceedance because a qualitative
    parameter carries no intermediate alert level.

    :param value: :data:`~.constants.QUALITATIVE_PASS`,
        :data:`~.constants.QUALITATIVE_FAIL`, or ``None``
    :returns: one of the evaluation codes defined in :mod:`.constants`
    :rtype: str
    """
    if value == QUALITATIVE_PASS:
        return EVAL_WITHIN
    if value == QUALITATIVE_FAIL:
        return EVAL_ACTION
    return EVAL_NOT_EVALUATED


def worst_evaluation(evaluations):
    """Return the most severe evaluation code in ``evaluations``.

    Used to roll individual result outcomes up to their parent sample.

    :param evaluations: iterable of evaluation codes
    :returns: the most severe code, or :data:`~.constants.EVAL_NOT_EVALUATED`
        when the iterable is empty
    :rtype: str
    """
    worst = EVAL_NOT_EVALUATED
    worst_rank = EVALUATION_SEVERITY[EVAL_NOT_EVALUATED]
    for evaluation in evaluations:
        rank = EVALUATION_SEVERITY.get(evaluation)
        if rank is None:
            raise ValueError("Unknown evaluation code: %r" % (evaluation,))
        if rank > worst_rank:
            worst = evaluation
            worst_rank = rank
    return worst


def mean(values):
    """Return the arithmetic mean of ``values``, or ``None`` when empty.

    :param values: sequence of numbers
    :rtype: float or None
    """
    values = list(values)
    if not values:
        return None
    return sum(values) / float(len(values))


def median(values):
    """Return the median of ``values``, or ``None`` when empty.

    For an even-sized sequence the mean of the two central values is returned.

    :param values: sequence of numbers
    :rtype: float or None
    """
    ordered = sorted(values)
    count = len(ordered)
    if not count:
        return None
    midpoint = count // 2
    if count % 2:
        return float(ordered[midpoint])
    return (ordered[midpoint - 1] + ordered[midpoint]) / 2.0


def standard_deviation(values):
    """Return the sample standard deviation of ``values``.

    The sample standard deviation uses the Bessel-corrected denominator
    ``n - 1`` and is therefore undefined for fewer than two values, in which
    case ``None`` is returned rather than a misleading zero.

    :param values: sequence of numbers
    :rtype: float or None
    """
    values = list(values)
    count = len(values)
    if count < 2:
        return None
    average = sum(values) / float(count)
    variance = sum((value - average) ** 2 for value in values) / float(count - 1)
    return variance ** 0.5


def exceedance_rate(total, exceeded):
    """Return the proportion of results that exceeded a threshold.

    The value is returned as a ratio in the closed interval ``[0, 1]`` rather
    than a percentage, so that it can be rendered with the Odoo ``percentage``
    widget without further scaling.

    :param int total: number of evaluated results
    :param int exceeded: number of results that breached the threshold
    :rtype: float
    :raises ValueError: when the counts are negative or inconsistent
    """
    if total < 0 or exceeded < 0:
        raise ValueError("Counts must not be negative.")
    if exceeded > total:
        raise ValueError("Exceeded count must not be greater than total count.")
    if total == 0:
        return 0.0
    return exceeded / float(total)


def trend_direction(values, change_threshold):
    """Classify the direction of a chronologically ordered series.

    The series is split into two halves and the mean of the later half is
    compared with the mean of the earlier half. This is a descriptive
    indicator intended to support review, not a statistical hypothesis test,
    and it makes no claim about statistical significance.

    Fewer than :data:`~.constants.TREND_MINIMUM_SAMPLE_COUNT` values, or an
    earlier-half mean of zero, are reported as insufficient data because the
    relative change is undefined or unreliable in those cases.

    :param values: numbers in chronological order, oldest first
    :param float change_threshold: relative change above which the series is
        classified as increasing or decreasing, expressed as a ratio
    :returns: one of the trend direction codes defined in :mod:`.constants`
    :rtype: str
    :raises ValueError: when ``change_threshold`` is negative
    """
    if change_threshold < 0:
        raise ValueError("Change threshold must not be negative.")
    values = list(values)
    if len(values) < TREND_MINIMUM_SAMPLE_COUNT:
        return TREND_DIRECTION_INSUFFICIENT
    midpoint = len(values) // 2
    earlier_mean = mean(values[:midpoint])
    later_mean = mean(values[midpoint:])
    if not earlier_mean:
        return TREND_DIRECTION_INSUFFICIENT
    relative_change = (later_mean - earlier_mean) / abs(earlier_mean)
    if relative_change > change_threshold:
        return TREND_DIRECTION_INCREASING
    if relative_change < -change_threshold:
        return TREND_DIRECTION_DECREASING
    return TREND_DIRECTION_STABLE


def summarise(values):
    """Return descriptive statistics for ``values``.

    :param values: sequence of numbers
    :returns: mapping with the keys ``count``, ``minimum``, ``maximum``,
        ``mean``, ``median`` and ``standard_deviation``. Every statistic other
        than ``count`` is ``None`` when it is undefined for the input.
    :rtype: dict
    """
    values = list(values)
    if not values:
        return {
            "count": 0,
            "minimum": None,
            "maximum": None,
            "mean": None,
            "median": None,
            "standard_deviation": None,
        }
    return {
        "count": len(values),
        "minimum": min(values),
        "maximum": max(values),
        "mean": mean(values),
        "median": median(values),
        "standard_deviation": standard_deviation(values),
    }
