# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Shared vocabulary for the environmental monitoring module.

This module contains no Odoo imports so that every value defined here can be
imported and exercised by plain Python unit tests without an Odoo runtime.

No numeric regulatory limit is defined in this file. Alert, action and
specification limits are configuration data owned by the implementing
organisation and are captured on ``ls.env.limit`` records.
"""

# ---------------------------------------------------------------------------
# Occupancy state of a monitored area at the moment of sampling.
# ---------------------------------------------------------------------------
OCCUPANCY_AT_REST = "at_rest"
OCCUPANCY_IN_OPERATION = "in_operation"
OCCUPANCY_ANY = "any"

OCCUPANCY_STATES = [
    (OCCUPANCY_AT_REST, "At Rest"),
    (OCCUPANCY_IN_OPERATION, "In Operation"),
]

#: ``any`` is only selectable on limit records, where it means the limit
#: applies regardless of the occupancy state recorded on the sample.
LIMIT_OCCUPANCY_STATES = OCCUPANCY_STATES + [(OCCUPANCY_ANY, "Any State")]

# ---------------------------------------------------------------------------
# Parameter classification.
# ---------------------------------------------------------------------------
PARAMETER_TYPES = [
    ("viable_air_active", "Viable - Active Air Sampling"),
    ("viable_air_passive", "Viable - Settle Plate"),
    ("viable_surface", "Viable - Surface / Contact Plate"),
    ("viable_personnel", "Viable - Personnel Monitoring"),
    ("nonviable_particle", "Non-Viable Particle Count"),
    ("temperature", "Temperature"),
    ("relative_humidity", "Relative Humidity"),
    ("differential_pressure", "Differential Pressure"),
    ("air_velocity", "Air Velocity"),
    ("air_change_rate", "Air Change Rate"),
    ("other", "Other"),
]

RESULT_TYPE_QUANTITATIVE = "quantitative"
RESULT_TYPE_QUALITATIVE = "qualitative"

RESULT_TYPES = [
    (RESULT_TYPE_QUANTITATIVE, "Quantitative"),
    (RESULT_TYPE_QUALITATIVE, "Qualitative (Pass / Fail)"),
]

QUALITATIVE_PASS = "pass"
QUALITATIVE_FAIL = "fail"

QUALITATIVE_VALUES = [
    (QUALITATIVE_PASS, "Pass"),
    (QUALITATIVE_FAIL, "Fail"),
]

# ---------------------------------------------------------------------------
# Limits.
# ---------------------------------------------------------------------------
DIRECTION_UPPER = "upper"
DIRECTION_LOWER = "lower"

LIMIT_DIRECTIONS = [
    (DIRECTION_UPPER, "Upper Bound (breach when value is above)"),
    (DIRECTION_LOWER, "Lower Bound (breach when value is below)"),
]

LIMIT_STATE_DRAFT = "draft"
LIMIT_STATE_APPROVED = "approved"
LIMIT_STATE_SUPERSEDED = "superseded"

LIMIT_STATES = [
    (LIMIT_STATE_DRAFT, "Draft"),
    (LIMIT_STATE_APPROVED, "Approved"),
    (LIMIT_STATE_SUPERSEDED, "Superseded"),
]

# ---------------------------------------------------------------------------
# Result evaluation outcomes, ordered from least to most severe.
# ---------------------------------------------------------------------------
EVAL_NOT_EVALUATED = "not_evaluated"
EVAL_NO_LIMIT = "no_limit"
EVAL_WITHIN = "within_limits"
EVAL_ALERT = "alert_exceeded"
EVAL_ACTION = "action_exceeded"
EVAL_SPEC = "spec_exceeded"

EVALUATIONS = [
    (EVAL_NOT_EVALUATED, "Not Evaluated"),
    (EVAL_NO_LIMIT, "No Approved Limit"),
    (EVAL_WITHIN, "Within Limits"),
    (EVAL_ALERT, "Alert Limit Exceeded"),
    (EVAL_ACTION, "Action Limit Exceeded"),
    (EVAL_SPEC, "Specification Exceeded"),
]

#: Severity ranking used to pick the worst outcome across several thresholds
#: and to roll individual results up to their parent sample.
EVALUATION_SEVERITY = {
    EVAL_NOT_EVALUATED: 0,
    EVAL_NO_LIMIT: 1,
    EVAL_WITHIN: 2,
    EVAL_ALERT: 3,
    EVAL_ACTION: 4,
    EVAL_SPEC: 5,
}

#: Outcomes that represent a breach of a configured threshold.
BREACH_EVALUATIONS = (EVAL_ALERT, EVAL_ACTION, EVAL_SPEC)

#: Outcomes that always require a formal excursion record.
MANDATORY_EXCURSION_EVALUATIONS = (EVAL_ACTION, EVAL_SPEC)

# ---------------------------------------------------------------------------
# Sample lifecycle.
# ---------------------------------------------------------------------------
SAMPLE_DRAFT = "draft"
SAMPLE_SCHEDULED = "scheduled"
SAMPLE_COLLECTED = "collected"
SAMPLE_IN_ANALYSIS = "in_analysis"
SAMPLE_RESULTS_ENTERED = "results_entered"
SAMPLE_REVIEWED = "reviewed"
SAMPLE_APPROVED = "approved"
SAMPLE_CANCELLED = "cancelled"

SAMPLE_STATES = [
    (SAMPLE_DRAFT, "Draft"),
    (SAMPLE_SCHEDULED, "Scheduled"),
    (SAMPLE_COLLECTED, "Collected"),
    (SAMPLE_IN_ANALYSIS, "In Analysis"),
    (SAMPLE_RESULTS_ENTERED, "Results Entered"),
    (SAMPLE_REVIEWED, "Reviewed"),
    (SAMPLE_APPROVED, "Approved"),
    (SAMPLE_CANCELLED, "Cancelled"),
]

#: Permitted sample state transitions. Any transition not listed is rejected.
SAMPLE_TRANSITIONS = {
    SAMPLE_DRAFT: (SAMPLE_SCHEDULED, SAMPLE_CANCELLED),
    SAMPLE_SCHEDULED: (SAMPLE_COLLECTED, SAMPLE_CANCELLED),
    SAMPLE_COLLECTED: (SAMPLE_IN_ANALYSIS, SAMPLE_CANCELLED),
    SAMPLE_IN_ANALYSIS: (SAMPLE_RESULTS_ENTERED, SAMPLE_CANCELLED),
    SAMPLE_RESULTS_ENTERED: (SAMPLE_REVIEWED, SAMPLE_IN_ANALYSIS, SAMPLE_CANCELLED),
    SAMPLE_REVIEWED: (
        SAMPLE_APPROVED,
        SAMPLE_RESULTS_ENTERED,
        SAMPLE_IN_ANALYSIS,
        SAMPLE_CANCELLED,
    ),
    SAMPLE_APPROVED: (),
    SAMPLE_CANCELLED: (),
}

#: States in which the sample record is considered closed for data entry.
SAMPLE_LOCKED_STATES = (SAMPLE_APPROVED, SAMPLE_CANCELLED)

# ---------------------------------------------------------------------------
# Monitoring plan lifecycle.
# ---------------------------------------------------------------------------
PLAN_DRAFT = "draft"
PLAN_APPROVED = "approved"
PLAN_SUPERSEDED = "superseded"
PLAN_CANCELLED = "cancelled"

PLAN_STATES = [
    (PLAN_DRAFT, "Draft"),
    (PLAN_APPROVED, "Approved"),
    (PLAN_SUPERSEDED, "Superseded"),
    (PLAN_CANCELLED, "Cancelled"),
]

# ---------------------------------------------------------------------------
# Excursion lifecycle.
# ---------------------------------------------------------------------------
EXCURSION_OPEN = "open"
EXCURSION_ASSESSMENT = "assessment"
EXCURSION_INVESTIGATION = "investigation"
EXCURSION_PENDING_CLOSURE = "pending_closure"
EXCURSION_CLOSED = "closed"
EXCURSION_CANCELLED = "cancelled"

EXCURSION_STATES = [
    (EXCURSION_OPEN, "Open"),
    (EXCURSION_ASSESSMENT, "Impact Assessment"),
    (EXCURSION_INVESTIGATION, "Investigation"),
    (EXCURSION_PENDING_CLOSURE, "Pending Closure"),
    (EXCURSION_CLOSED, "Closed"),
    (EXCURSION_CANCELLED, "Cancelled"),
]

EXCURSION_TRANSITIONS = {
    EXCURSION_OPEN: (EXCURSION_ASSESSMENT, EXCURSION_CANCELLED),
    EXCURSION_ASSESSMENT: (
        EXCURSION_INVESTIGATION,
        EXCURSION_PENDING_CLOSURE,
        EXCURSION_CANCELLED,
    ),
    EXCURSION_INVESTIGATION: (EXCURSION_PENDING_CLOSURE, EXCURSION_CANCELLED),
    EXCURSION_PENDING_CLOSURE: (EXCURSION_CLOSED, EXCURSION_INVESTIGATION),
    EXCURSION_CLOSED: (),
    EXCURSION_CANCELLED: (),
}

EXCURSION_SEVERITIES = [
    ("minor", "Minor"),
    ("major", "Major"),
    ("critical", "Critical"),
]

# ---------------------------------------------------------------------------
# Trend analysis lifecycle.
# ---------------------------------------------------------------------------
TREND_DRAFT = "draft"
TREND_COMPUTED = "computed"
TREND_REVIEWED = "reviewed"

TREND_STATES = [
    (TREND_DRAFT, "Draft"),
    (TREND_COMPUTED, "Computed"),
    (TREND_REVIEWED, "Reviewed"),
]

TREND_DIRECTION_INSUFFICIENT = "insufficient_data"
TREND_DIRECTION_INCREASING = "increasing"
TREND_DIRECTION_STABLE = "stable"
TREND_DIRECTION_DECREASING = "decreasing"

TREND_DIRECTIONS = [
    (TREND_DIRECTION_INSUFFICIENT, "Insufficient Data"),
    (TREND_DIRECTION_INCREASING, "Increasing"),
    (TREND_DIRECTION_STABLE, "Stable"),
    (TREND_DIRECTION_DECREASING, "Decreasing"),
]

#: Minimum number of results required before a trend direction is reported.
#: Below this count the direction is reported as ``insufficient_data`` rather
#: than a value that the data cannot support.
TREND_MINIMUM_SAMPLE_COUNT = 6

#: Relative change of the second-half mean versus the first-half mean, above
#: which the series is reported as increasing or decreasing. This threshold is
#: an implementation default exposed to the user on the trend wizard; it is not
#: derived from any regulatory text.
TREND_DEFAULT_CHANGE_THRESHOLD = 0.20

# ---------------------------------------------------------------------------
# Scheduling frequency units.
# ---------------------------------------------------------------------------
FREQUENCY_DAY = "day"
FREQUENCY_WEEK = "week"
FREQUENCY_MONTH = "month"
FREQUENCY_YEAR = "year"

FREQUENCY_UNITS = [
    (FREQUENCY_DAY, "Day(s)"),
    (FREQUENCY_WEEK, "Week(s)"),
    (FREQUENCY_MONTH, "Month(s)"),
    (FREQUENCY_YEAR, "Year(s)"),
]

#: Number of days represented by one unit, for the units that map onto a fixed
#: number of days. ``month`` and ``year`` are handled by calendar arithmetic
#: instead and are deliberately absent from this mapping.
FREQUENCY_DAYS = {
    FREQUENCY_DAY: 1,
    FREQUENCY_WEEK: 7,
}

#: Upper bound on the number of samples a single scheduling run may generate.
#: Prevents an operator mistake on the date range from creating an unbounded
#: number of records in one transaction.
MAX_SAMPLES_PER_SCHEDULING_RUN = 5000
