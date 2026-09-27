# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Shared constants for the ``ls_calibration`` module.

Every selection list, state machine transition map and numeric default used
by the module is declared here so that a single authoritative definition is
shared by models, wizards, views and tests.

No value in this file encodes a regulatory limit. Calibration intervals,
tolerance widths and criticality thresholds are business configuration and
must be established by the implementing organisation on the basis of its own
risk assessment. See ``docs/02_regulatory_analysis.md``.
"""

from typing import Dict, List, Tuple

# ---------------------------------------------------------------------------
# Interval units
# ---------------------------------------------------------------------------

INTERVAL_UOM_DAY: str = "day"
INTERVAL_UOM_WEEK: str = "week"
INTERVAL_UOM_MONTH: str = "month"
INTERVAL_UOM_YEAR: str = "year"

INTERVAL_UOM_SELECTION: List[Tuple[str, str]] = [
    (INTERVAL_UOM_DAY, "Day(s)"),
    (INTERVAL_UOM_WEEK, "Week(s)"),
    (INTERVAL_UOM_MONTH, "Month(s)"),
    (INTERVAL_UOM_YEAR, "Year(s)"),
]

#: Multiplier applied to convert an interval expressed in the given unit into
#: the ``relativedelta`` keyword argument used to compute the next due date.
INTERVAL_UOM_TO_RELATIVEDELTA_KEY: Dict[str, str] = {
    INTERVAL_UOM_DAY: "days",
    INTERVAL_UOM_WEEK: "weeks",
    INTERVAL_UOM_MONTH: "months",
    INTERVAL_UOM_YEAR: "years",
}

# ---------------------------------------------------------------------------
# Instrument criticality (GxP impact classification)
# ---------------------------------------------------------------------------

CRITICALITY_CRITICAL: str = "critical"
CRITICALITY_MAJOR: str = "major"
CRITICALITY_MINOR: str = "minor"

CRITICALITY_SELECTION: List[Tuple[str, str]] = [
    (CRITICALITY_CRITICAL, "Critical"),
    (CRITICALITY_MAJOR, "Major"),
    (CRITICALITY_MINOR, "Minor"),
]

# ---------------------------------------------------------------------------
# Instrument lifecycle state
# ---------------------------------------------------------------------------

INSTRUMENT_STATE_DRAFT: str = "draft"
INSTRUMENT_STATE_IN_SERVICE: str = "in_service"
INSTRUMENT_STATE_QUARANTINED: str = "quarantined"
INSTRUMENT_STATE_OUT_OF_SERVICE: str = "out_of_service"
INSTRUMENT_STATE_RETIRED: str = "retired"

INSTRUMENT_STATE_SELECTION: List[Tuple[str, str]] = [
    (INSTRUMENT_STATE_DRAFT, "Draft"),
    (INSTRUMENT_STATE_IN_SERVICE, "In Service"),
    (INSTRUMENT_STATE_QUARANTINED, "Quarantined"),
    (INSTRUMENT_STATE_OUT_OF_SERVICE, "Out of Service"),
    (INSTRUMENT_STATE_RETIRED, "Retired"),
]

#: Allowed instrument state transitions. Key is the source state, value is the
#: tuple of permitted target states.
INSTRUMENT_STATE_TRANSITIONS: Dict[str, Tuple[str, ...]] = {
    INSTRUMENT_STATE_DRAFT: (
        INSTRUMENT_STATE_IN_SERVICE,
        INSTRUMENT_STATE_RETIRED,
    ),
    INSTRUMENT_STATE_IN_SERVICE: (
        INSTRUMENT_STATE_QUARANTINED,
        INSTRUMENT_STATE_OUT_OF_SERVICE,
        INSTRUMENT_STATE_RETIRED,
    ),
    INSTRUMENT_STATE_QUARANTINED: (
        INSTRUMENT_STATE_IN_SERVICE,
        INSTRUMENT_STATE_OUT_OF_SERVICE,
        INSTRUMENT_STATE_RETIRED,
    ),
    INSTRUMENT_STATE_OUT_OF_SERVICE: (
        INSTRUMENT_STATE_IN_SERVICE,
        INSTRUMENT_STATE_RETIRED,
    ),
    INSTRUMENT_STATE_RETIRED: (),
}

# ---------------------------------------------------------------------------
# Calibration status (computed, derived from the due date)
# ---------------------------------------------------------------------------

CAL_STATUS_NEVER: str = "never"
CAL_STATUS_OK: str = "ok"
CAL_STATUS_DUE_SOON: str = "due_soon"
CAL_STATUS_OVERDUE: str = "overdue"

CAL_STATUS_SELECTION: List[Tuple[str, str]] = [
    (CAL_STATUS_NEVER, "Never Calibrated"),
    (CAL_STATUS_OK, "OK"),
    (CAL_STATUS_DUE_SOON, "Due Soon"),
    (CAL_STATUS_OVERDUE, "Overdue"),
]

#: Default number of calendar days before the due date at which an instrument
#: is reported as "Due Soon". Configurable per instrument.
DEFAULT_DUE_SOON_THRESHOLD_DAYS: int = 30

# ---------------------------------------------------------------------------
# Calibration plan state
# ---------------------------------------------------------------------------

PLAN_STATE_DRAFT: str = "draft"
PLAN_STATE_APPROVED: str = "approved"
PLAN_STATE_SUSPENDED: str = "suspended"
PLAN_STATE_CLOSED: str = "closed"

PLAN_STATE_SELECTION: List[Tuple[str, str]] = [
    (PLAN_STATE_DRAFT, "Draft"),
    (PLAN_STATE_APPROVED, "Approved"),
    (PLAN_STATE_SUSPENDED, "Suspended"),
    (PLAN_STATE_CLOSED, "Closed"),
]

PLAN_STATE_TRANSITIONS: Dict[str, Tuple[str, ...]] = {
    PLAN_STATE_DRAFT: (PLAN_STATE_APPROVED, PLAN_STATE_CLOSED),
    PLAN_STATE_APPROVED: (PLAN_STATE_SUSPENDED, PLAN_STATE_CLOSED),
    PLAN_STATE_SUSPENDED: (PLAN_STATE_APPROVED, PLAN_STATE_CLOSED),
    PLAN_STATE_CLOSED: (),
}

#: Upper bound on the number of calibration records a single plan may
#: generate in one run. Acts as a guard against a mis-configured interval
#: combined with a distant horizon date producing an unbounded write.
MAX_GENERATED_RECORDS_PER_PLAN: int = 500

# ---------------------------------------------------------------------------
# Calibration record state
# ---------------------------------------------------------------------------

RECORD_STATE_DRAFT: str = "draft"
RECORD_STATE_IN_PROGRESS: str = "in_progress"
RECORD_STATE_PERFORMED: str = "performed"
RECORD_STATE_UNDER_REVIEW: str = "under_review"
RECORD_STATE_APPROVED: str = "approved"
RECORD_STATE_REJECTED: str = "rejected"
RECORD_STATE_CANCELLED: str = "cancelled"

RECORD_STATE_SELECTION: List[Tuple[str, str]] = [
    (RECORD_STATE_DRAFT, "Draft"),
    (RECORD_STATE_IN_PROGRESS, "In Progress"),
    (RECORD_STATE_PERFORMED, "Performed"),
    (RECORD_STATE_UNDER_REVIEW, "Under Review"),
    (RECORD_STATE_APPROVED, "Approved"),
    (RECORD_STATE_REJECTED, "Rejected"),
    (RECORD_STATE_CANCELLED, "Cancelled"),
]

RECORD_STATE_TRANSITIONS: Dict[str, Tuple[str, ...]] = {
    RECORD_STATE_DRAFT: (RECORD_STATE_IN_PROGRESS, RECORD_STATE_CANCELLED),
    RECORD_STATE_IN_PROGRESS: (RECORD_STATE_PERFORMED, RECORD_STATE_CANCELLED),
    RECORD_STATE_PERFORMED: (RECORD_STATE_UNDER_REVIEW, RECORD_STATE_CANCELLED),
    RECORD_STATE_UNDER_REVIEW: (RECORD_STATE_APPROVED, RECORD_STATE_REJECTED),
    RECORD_STATE_APPROVED: (),
    RECORD_STATE_REJECTED: (RECORD_STATE_IN_PROGRESS, RECORD_STATE_CANCELLED),
    RECORD_STATE_CANCELLED: (),
}

#: States in which a calibration record is considered final and its data must
#: no longer be editable through the user interface or the ORM.
RECORD_LOCKED_STATES: Tuple[str, ...] = (
    RECORD_STATE_APPROVED,
    RECORD_STATE_CANCELLED,
)

#: Fields that remain writable on a locked record. Every other field is
#: rejected by ``ls.calibration.record.write``.
RECORD_LOCKED_WRITABLE_FIELDS: Tuple[str, ...] = (
    "message_follower_ids",
    "message_ids",
    "message_main_attachment_id",
    "activity_ids",
    "certificate_ids",
    "oot_ids",
    "message_partner_ids",
    "message_attachment_count",
    "message_has_error",
    "message_has_error_counter",
    "message_needaction",
    "message_needaction_counter",
    "message_is_follower",
    "activity_state",
    "activity_user_id",
    "activity_type_id",
    "activity_type_icon",
    "activity_date_deadline",
    "my_activity_date_deadline",
    "activity_summary",
    "activity_exception_decoration",
    "activity_exception_icon",
    "rating_ids",
    "website_message_ids",
    "message_has_sms_error",
)

# ---------------------------------------------------------------------------
# Calibration result
# ---------------------------------------------------------------------------

RESULT_NOT_APPLICABLE: str = "not_applicable"
RESULT_PASS: str = "pass"
RESULT_FAIL: str = "fail"

RESULT_SELECTION: List[Tuple[str, str]] = [
    (RESULT_NOT_APPLICABLE, "Not Applicable"),
    (RESULT_PASS, "Pass"),
    (RESULT_FAIL, "Fail"),
]

OVERALL_RESULT_PASS: str = "pass"
OVERALL_RESULT_PASS_AFTER_ADJUSTMENT: str = "pass_after_adjustment"
OVERALL_RESULT_FAIL: str = "fail"
OVERALL_RESULT_NOT_APPLICABLE: str = "not_applicable"

OVERALL_RESULT_SELECTION: List[Tuple[str, str]] = [
    (OVERALL_RESULT_NOT_APPLICABLE, "Not Applicable"),
    (OVERALL_RESULT_PASS, "Pass"),
    (OVERALL_RESULT_PASS_AFTER_ADJUSTMENT, "Pass After Adjustment"),
    (OVERALL_RESULT_FAIL, "Fail"),
]

# ---------------------------------------------------------------------------
# Tolerance
# ---------------------------------------------------------------------------

TOLERANCE_ABSOLUTE: str = "absolute"
TOLERANCE_PERCENT_OF_READING: str = "percent_of_reading"
TOLERANCE_PERCENT_OF_SPAN: str = "percent_of_span"

TOLERANCE_TYPE_SELECTION: List[Tuple[str, str]] = [
    (TOLERANCE_ABSOLUTE, "Absolute"),
    (TOLERANCE_PERCENT_OF_READING, "% of Reading"),
    (TOLERANCE_PERCENT_OF_SPAN, "% of Span"),
]

#: Number of decimal digits used for every measured value, limit and
#: deviation stored by this module.
MEASUREMENT_DIGITS: Tuple[int, int] = (16, 6)

# ---------------------------------------------------------------------------
# Calibration provider
# ---------------------------------------------------------------------------

PROVIDER_INTERNAL: str = "internal"
PROVIDER_EXTERNAL: str = "external"

PROVIDER_SELECTION: List[Tuple[str, str]] = [
    (PROVIDER_INTERNAL, "Internal"),
    (PROVIDER_EXTERNAL, "External"),
]

CERTIFICATE_TYPE_SELECTION: List[Tuple[str, str]] = [
    (PROVIDER_INTERNAL, "Internal Certificate"),
    (PROVIDER_EXTERNAL, "External Certificate"),
]

# ---------------------------------------------------------------------------
# Out-of-tolerance (OOT) event
# ---------------------------------------------------------------------------

OOT_STATE_OPEN: str = "open"
OOT_STATE_UNDER_ASSESSMENT: str = "under_assessment"
OOT_STATE_ASSESSED: str = "assessed"
OOT_STATE_CLOSED: str = "closed"

OOT_STATE_SELECTION: List[Tuple[str, str]] = [
    (OOT_STATE_OPEN, "Open"),
    (OOT_STATE_UNDER_ASSESSMENT, "Under Assessment"),
    (OOT_STATE_ASSESSED, "Assessed"),
    (OOT_STATE_CLOSED, "Closed"),
]

OOT_STATE_TRANSITIONS: Dict[str, Tuple[str, ...]] = {
    OOT_STATE_OPEN: (OOT_STATE_UNDER_ASSESSMENT,),
    OOT_STATE_UNDER_ASSESSMENT: (OOT_STATE_ASSESSED,),
    OOT_STATE_ASSESSED: (OOT_STATE_CLOSED,),
    OOT_STATE_CLOSED: (),
}

OOT_PRODUCT_IMPACT_NONE: str = "none"
OOT_PRODUCT_IMPACT_POTENTIAL: str = "potential"
OOT_PRODUCT_IMPACT_CONFIRMED: str = "confirmed"

OOT_PRODUCT_IMPACT_SELECTION: List[Tuple[str, str]] = [
    (OOT_PRODUCT_IMPACT_NONE, "No Impact"),
    (OOT_PRODUCT_IMPACT_POTENTIAL, "Potential Impact"),
    (OOT_PRODUCT_IMPACT_CONFIRMED, "Confirmed Impact"),
]

OOT_DISPOSITION_SELECTION: List[Tuple[str, str]] = [
    ("no_action", "No Further Action"),
    ("further_investigation", "Further Investigation Required"),
    ("product_quarantine", "Quarantine Affected Product"),
    ("product_reject", "Reject Affected Product"),
    ("recalculate", "Recalculate / Re-evaluate Affected Data"),
]

# ---------------------------------------------------------------------------
# Sequence codes
# ---------------------------------------------------------------------------

SEQUENCE_CODE_INSTRUMENT: str = "ls.calibration.instrument"
SEQUENCE_CODE_RECORD: str = "ls.calibration.record"
SEQUENCE_CODE_CERTIFICATE: str = "ls.calibration.certificate"
SEQUENCE_CODE_OOT: str = "ls.calibration.oot"

#: Placeholder assigned to the ``name`` field before the sequence is drawn.
NEW_SEQUENCE_PLACEHOLDER: str = "/"

# ---------------------------------------------------------------------------
# Security group XML identifiers
# ---------------------------------------------------------------------------

GROUP_VIEWER: str = "ls_calibration.group_ls_calibration_viewer"
GROUP_TECHNICIAN: str = "ls_calibration.group_ls_calibration_technician"
GROUP_APPROVER: str = "ls_calibration.group_ls_calibration_approver"
GROUP_MANAGER: str = "ls_calibration.group_ls_calibration_manager"
