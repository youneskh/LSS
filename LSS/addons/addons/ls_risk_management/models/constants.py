# Part of the Life Sciences Suite. See LICENSE file for full copyright
# and licensing details.
"""Shared constants for the ``ls_risk_management`` module.

Centralising selection lists and numeric bounds here keeps them identical
across models, wizards, views and tests, and gives a single place to audit
them during computer system validation.

Verification notes
------------------
* The ISO 14971:2019 clause numbers referenced in this module are taken from
  the publicly published table of contents of the standard. The normative
  text of ISO 14971:2019 is not publicly available and was not retrieved;
  no wording of the standard is reproduced or paraphrased as a requirement.
* ISO 14971:2019 requires the manufacturer to establish objective criteria
  for risk acceptability but does not itself prescribe acceptable risk
  levels. Consequently this module never hardcodes acceptability
  thresholds: they are configuration data held on ``ls.risk.matrix``.
* The 1-10 severity / occurrence / detection scales used by the FMEA models
  are a widely used industry convention. They are NOT an ISO 14971
  requirement. This information could not be verified from official
  documentation as a normative requirement of any standard, and is
  therefore implemented as a configurable convention only.
"""

# ---------------------------------------------------------------------------
# Risk register
# ---------------------------------------------------------------------------

#: Lifecycle states of a risk register entry.
RISK_STATES = [
    ("draft", "Draft"),
    ("assessed", "Assessed"),
    ("control", "Risk Control"),
    ("monitoring", "Monitoring"),
    ("closed", "Closed"),
    ("cancelled", "Cancelled"),
]

#: States in which a risk is considered open and subject to periodic review.
RISK_OPEN_STATES = ("assessed", "control", "monitoring")

#: Subject area a risk relates to. Kept deliberately generic so that the
#: module carries no dependency on ``product``, ``stock``, ``mrp`` or ``hr``.
RISK_TYPES = [
    ("product", "Product"),
    ("process", "Process"),
    ("equipment", "Equipment"),
    ("facility", "Facility"),
    ("utility", "Utility"),
    ("material", "Material"),
    ("supplier", "Supplier"),
    ("computerised_system", "Computerised System"),
    ("laboratory", "Laboratory"),
    ("packaging", "Packaging"),
    ("regulatory", "Regulatory"),
    ("occupational", "Occupational Health and Safety"),
]

# ---------------------------------------------------------------------------
# Risk matrix
# ---------------------------------------------------------------------------

#: The two ordinal scales that make up a risk matrix.
#:
#: Detectability is deliberately absent: ISO 14971:2019 estimates risk from
#: severity of harm and probability of occurrence of harm. Detectability is
#: an FMEA construct and lives on ``ls.risk.fmea.line`` instead.
MATRIX_SCALES = [
    ("severity", "Severity"),
    ("probability", "Probability"),
]

#: Fixed set of ordinal risk bands. The mapping from a (severity,
#: probability) pair to a band is configuration data on
#: ``ls.risk.matrix.cell``; only the band vocabulary is fixed, so that
#: reports, filters and group-by remain stable across configurations.
RISK_LEVELS = [
    ("negligible", "Negligible"),
    ("low", "Low"),
    ("medium", "Medium"),
    ("high", "High"),
    ("very_high", "Very High"),
]

#: Ordering of :data:`RISK_LEVELS` from least to most severe, used to
#: determine the highest band present in a set of records.
RISK_LEVEL_ORDER = ["negligible", "low", "medium", "high", "very_high"]

#: Acceptability decision attached to a matrix cell. The organisation
#: defines which cells carry which decision in its risk management plan.
ACCEPTABILITY = [
    ("acceptable", "Acceptable"),
    ("acceptable_with_control", "Acceptable Only With Risk Control"),
    ("not_acceptable", "Not Acceptable"),
]

#: Acceptability values that forbid closing a risk without an explicit,
#: recorded residual risk acceptance decision.
ACCEPTABILITY_REQUIRING_DECISION = ("acceptable_with_control", "not_acceptable")

#: Lifecycle states of a risk matrix. Only ``approved`` matrices may be used
#: on new assessments.
MATRIX_STATES = [
    ("draft", "Draft"),
    ("approved", "Approved"),
    ("obsolete", "Obsolete"),
]

# ---------------------------------------------------------------------------
# Risk assessment
# ---------------------------------------------------------------------------

#: Why an assessment was performed. ``initial`` corresponds to the first
#: risk estimation, ``residual`` to re-estimation after risk control
#: measures, ``periodic`` to scheduled review, and ``post_production`` to
#: re-estimation triggered by production or post-production information.
ASSESSMENT_TYPES = [
    ("initial", "Initial"),
    ("residual", "Residual (after risk control)"),
    ("periodic", "Periodic Review"),
    ("post_production", "Production / Post-Production Information"),
]

#: Lifecycle states of an assessment. Approval is segregated from
#: assessment: see ``ls.risk.assessment.action_approve``.
ASSESSMENT_STATES = [
    ("draft", "Draft"),
    ("confirmed", "Confirmed"),
    ("approved", "Approved"),
    ("cancelled", "Cancelled"),
]

# ---------------------------------------------------------------------------
# Risk control measures (mitigations)
# ---------------------------------------------------------------------------

#: Risk control options. ISO 14971:2019 clause 7.1 requires a risk control
#: option analysis; the three option categories below are those named in
#: the standard's publicly documented structure and are applied in the
#: listed order of priority.
CONTROL_OPTIONS = [
    ("inherent_safety", "Inherent Safety by Design"),
    ("protective_measure", "Protective Measure in the Device or Manufacturing Process"),
    ("information_for_safety", "Information for Safety"),
]

#: Priority order of :data:`CONTROL_OPTIONS`, lowest number applied first.
CONTROL_OPTION_PRIORITY = {
    "inherent_safety": 1,
    "protective_measure": 2,
    "information_for_safety": 3,
}

#: Lifecycle states of a risk control measure.
MITIGATION_STATES = [
    ("draft", "Draft"),
    ("approved", "Approved"),
    ("in_progress", "In Progress"),
    ("implemented", "Implemented"),
    ("verified", "Verified"),
    ("cancelled", "Cancelled"),
]

#: States in which a risk control measure is not yet fully evidenced.
MITIGATION_PENDING_STATES = ("draft", "approved", "in_progress", "implemented")

# ---------------------------------------------------------------------------
# FMEA
# ---------------------------------------------------------------------------

#: Scope of an FMEA worksheet.
FMEA_TYPES = [
    ("design", "Design FMEA"),
    ("process", "Process FMEA"),
    ("system", "System FMEA"),
    ("use", "Use / Application FMEA"),
]

#: Lifecycle states of an FMEA worksheet.
FMEA_STATES = [
    ("draft", "Draft"),
    ("in_progress", "In Progress"),
    ("review", "Under Review"),
    ("approved", "Approved"),
    ("closed", "Closed"),
    ("cancelled", "Cancelled"),
]

#: Inclusive lower bound of the FMEA severity / occurrence / detection scales.
FMEA_SCALE_MIN = 1

#: Inclusive upper bound of the FMEA severity / occurrence / detection scales.
FMEA_SCALE_MAX = 10

#: Lowest possible Risk Priority Number (FMEA_SCALE_MIN cubed).
FMEA_RPN_MIN = FMEA_SCALE_MIN ** 3

#: Highest possible Risk Priority Number (FMEA_SCALE_MAX cubed).
FMEA_RPN_MAX = FMEA_SCALE_MAX ** 3

# ---------------------------------------------------------------------------
# Sequences and cron
# ---------------------------------------------------------------------------

#: ``ir.sequence`` code used to number risk register entries.
SEQUENCE_RISK = "ls.risk.register"

#: ``ir.sequence`` code used to number risk assessments.
SEQUENCE_ASSESSMENT = "ls.risk.assessment"

#: ``ir.sequence`` code used to number risk control measures.
SEQUENCE_MITIGATION = "ls.risk.mitigation"

#: ``ir.sequence`` code used to number FMEA worksheets.
SEQUENCE_FMEA = "ls.risk.fmea"

#: Placeholder shown while a record has not yet been assigned a number.
SEQUENCE_PLACEHOLDER = "/"

#: Default number of months between periodic risk reviews.
DEFAULT_REVIEW_INTERVAL_MONTHS = 12

#: ``mail.activity.type`` external identifier used when scheduling review
#: activities. Resolved with ``raise_if_not_found=False``; when the record
#: is absent the module posts a chatter message instead of an activity.
ACTIVITY_TYPE_TODO_XMLID = "mail.mail_activity_data_todo"

# ---------------------------------------------------------------------------
# Regulatory traceability
# ---------------------------------------------------------------------------

#: Maps this module's implementation points to the clause of ISO 14971:2019
#: whose implementation they support. Clause numbers are taken from the
#: published table of contents of the standard. Presence in this map is a
#: statement about which process step a field supports, and is not a claim
#: of compliance or certification with ISO 14971:2019 or any other
#: framework.
ISO_14971_CLAUSE_MAP = {
    "4.4": "ls.risk.matrix (risk acceptability criteria recorded and approved)",
    "4.5": "ls.risk.register (risk record with linked assessments and controls)",
    "5.2": "ls.risk.register.intended_use",
    "5.3": "ls.risk.register.safety_characteristics",
    "5.4": "ls.risk.register.hazard / hazardous_situation / sequence_of_events / harm",
    "5.5": "ls.risk.assessment (severity and probability estimation)",
    "6": "ls.risk.matrix.cell.acceptability (risk evaluation against criteria)",
    "7.1": "ls.risk.mitigation.control_option",
    "7.2": "ls.risk.mitigation implementation verification fields",
    "7.3": "ls.risk.register residual risk acceptance fields",
    "7.4": "ls.risk.register.benefit_risk_analysis",
    "7.5": "ls.risk.mitigation.introduces_new_risk / new_risk_description",
    "7.6": "ls.risk.register.control_completeness_confirmed",
    "8": "ls.risk.register.overall_residual_risk_assessment",
    "9": "ls.risk.assessment with assessment_type 'periodic'",
    "10.2": "ls.risk.assessment with assessment_type 'post_production'",
    "10.3": "ls.risk.register.next_review_date and the review cron",
}
