# Part of the Life Sciences Suite for Odoo 19 Community Edition.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Shared selection values and field groupings for the Recall module.

Every selection value below is annotated with its provenance:

``[REG]``
    The value and its meaning are taken from a published regulatory text.
    The citation is given in the comment. The module reproduces the
    *structure* defined by that text; it does not assert that any given
    organisation is compliant with it.
``[OPS]``
    The value is an operational value chosen for this implementation. It
    has no direct regulatory source.

Keeping these lists in one module guarantees that the Python code, the
views, the QWeb reports and the tests all use identical technical values.
"""

# --- Action types -----------------------------------------------------
# [REG] "recall", "market withdrawal" and "stock recovery" are distinct,
#       separately defined terms in 21 CFR 7.3(g), 7.3(j) and 7.3(k).
# [REG] "fsca" (field safety corrective action) is defined in Regulation
#       (EU) 2017/745 Article 2(68).
# [OPS] "mock_recall" supports the periodic effectiveness evaluation of
#       recall arrangements described in EudraLex Volume 4 Part I
#       Chapter 8. It is excluded from all regulatory KPI reporting.
ACTION_TYPE_SELECTION = [
    ("recall", "Recall"),
    ("market_withdrawal", "Market Withdrawal"),
    ("stock_recovery", "Stock Recovery"),
    ("fsca", "Field Safety Corrective Action"),
    ("mock_recall", "Mock Recall"),
]

#: Action types that represent a real field action rather than a rehearsal.
REAL_ACTION_TYPES = ("recall", "market_withdrawal", "stock_recovery", "fsca")

# --- Health hazard classification -------------------------------------
# [REG] 21 CFR 7.3(m). The wording of the help text on the field
#       reproduces the substance of the three statutory definitions.
CLASSIFICATION_SELECTION = [
    ("not_classified", "Not Classified"),
    ("class_i", "Class I"),
    ("class_ii", "Class II"),
    ("class_iii", "Class III"),
]

CLASSIFICATION_HELP = (
    "Health hazard classification. The three classes below follow the "
    "structure of 21 CFR 7.3(m):\n"
    "- Class I: a reasonable probability that use of, or exposure to, the "
    "product will cause serious adverse health consequences or death.\n"
    "- Class II: use of, or exposure to, the product may cause temporary "
    "or medically reversible adverse health consequences, or the "
    "probability of serious adverse health consequences is remote.\n"
    "- Class III: use of, or exposure to, the product is not likely to "
    "cause adverse health consequences.\n"
    "Under 21 CFR 7.41 the classification is assigned by the competent "
    "authority. The value recorded here is the organisation's own "
    "assessment and, where applicable, the classification communicated "
    "by the authority."
)

# --- Depth of recall --------------------------------------------------
# [REG] 21 CFR 7.42(b)(1) requires the recall strategy to specify the
#       level in the distribution chain to which the recall extends.
DEPTH_SELECTION = [
    ("wholesale", "Wholesale Level"),
    ("retail", "Retail Level"),
    ("consumer_user", "Consumer / User Level"),
]

# --- Effectiveness check level ----------------------------------------
# [REG] 21 CFR 7.42(b)(3) defines levels A to E as the percentage of the
#       total number of consignees to be contacted.
EFFECTIVENESS_LEVEL_SELECTION = [
    ("a", "Level A - 100% of consignees"),
    ("b", "Level B - more than 10% and less than 100% of consignees"),
    ("c", "Level C - 10% of consignees"),
    ("d", "Level D - 2% of consignees"),
    ("e", "Level E - no effectiveness checks"),
]

#: Nominal coverage per level, used to compute the planned sample size.
#: Level B has no fixed percentage in the regulation and is therefore
#: driven by the user-entered ``effectiveness_sample_pct`` field.
EFFECTIVENESS_LEVEL_COVERAGE = {
    "a": 100.0,
    "c": 10.0,
    "d": 2.0,
    "e": 0.0,
}

# --- Public warning ---------------------------------------------------
# [REG] 21 CFR 7.42(b)(2) distinguishes a general public warning through
#       the general news media from a warning through specialised media.
PUBLIC_WARNING_SELECTION = [
    ("none", "No Public Warning"),
    ("general_media", "General News Media"),
    ("specialised_media", "Specialised Media / Defined Population"),
]

# --- Execution workflow ----------------------------------------------
# [OPS] The six forward states are the states named in the Life Sciences
#       Suite Functional Specification v1.0 section 7.13. "cancelled" is
#       an addition; see doc/05_architecture_review.md, deviation D-04.
EXECUTION_STATE_SELECTION = [
    ("planned", "Planned"),
    ("initiated", "Initiated"),
    ("in_progress", "In Progress"),
    ("communication", "Communication"),
    ("effectiveness_check", "Effectiveness Check"),
    ("closed", "Closed"),
    ("cancelled", "Cancelled"),
]

#: Ordered forward path used to validate state transitions.
EXECUTION_FORWARD_PATH = [
    "planned",
    "initiated",
    "in_progress",
    "communication",
    "effectiveness_check",
    "closed",
]

#: States in which an execution is no longer operationally active.
EXECUTION_FINAL_STATES = ("closed", "cancelled")

#: Fields of ``ls.recall.execution`` that may not be modified once the
#: record has left the "planned" state. They describe the regulatory
#: decision itself and are therefore under change control.
EXECUTION_LOCKED_AFTER_INITIATION = (
    "action_type",
    "classification",
    "depth",
    "product_id",
    "company_id",
    "plan_id",
)

# --- Plan workflow ----------------------------------------------------
# [OPS] Standard controlled-document lifecycle.
PLAN_STATE_SELECTION = [
    ("draft", "Draft"),
    ("under_review", "Under Review"),
    ("approved", "Approved"),
    ("obsolete", "Obsolete"),
]

# --- Communication ----------------------------------------------------
# [REG] "recall_notice" corresponds to the recall communication of
#       21 CFR 7.49; "field_safety_notice" corresponds to the field
#       safety notice of Regulation (EU) 2017/745 Article 89(8).
# [OPS] The remaining values are operational document types.
COMMUNICATION_TYPE_SELECTION = [
    ("recall_notice", "Recall Notice"),
    ("field_safety_notice", "Field Safety Notice"),
    ("authority_notification", "Authority Notification"),
    ("public_warning", "Public Warning"),
    ("reminder", "Reminder"),
    ("status_update", "Status Update"),
    ("closure_notice", "Closure Notice"),
]

# [REG] 21 CFR 7.49(b) names telegrams, mailgrams and first class letters
#       and states that telephone calls or other personal contacts should
#       ordinarily be confirmed in writing.
# [OPS] "email" and "portal" are contemporary equivalents.
COMMUNICATION_CHANNEL_SELECTION = [
    ("letter", "Letter"),
    ("email", "E-mail"),
    ("phone", "Telephone"),
    ("fax", "Fax"),
    ("courier", "Courier"),
    ("portal", "Customer Portal"),
    ("other", "Other"),
]

COMMUNICATION_STATE_SELECTION = [
    ("draft", "Draft"),
    ("approved", "Approved"),
    ("sent", "Sent"),
    ("acknowledged", "Acknowledged"),
    ("cancelled", "Cancelled"),
]

#: Content elements that must be confirmed before a recall notice is
#: recorded as sent.
#: [REG] Derived from 21 CFR 7.49(a), which lists the elements a recall
#: communication is to contain.
COMMUNICATION_CONTENT_FLAGS = (
    "content_identifies_product",
    "content_states_reason",
    "content_gives_instructions",
    "content_requests_response",
    "content_gives_contact",
)

# --- Effectiveness check ----------------------------------------------
# [REG] 21 CFR 7.42(b)(3) states that consignees may be contacted by
#       personal visits, telephone calls, letters, or a combination.
EFFECTIVENESS_METHOD_SELECTION = [
    ("phone", "Telephone Call"),
    ("email", "E-mail"),
    ("letter", "Letter"),
    ("visit", "Personal Visit"),
    ("portal", "Customer Portal"),
]

# [OPS] Outcome vocabulary for the effectiveness check.
EFFECTIVENESS_OUTCOME_SELECTION = [
    ("action_taken", "Contacted - Action Taken"),
    ("no_action", "Contacted - No Action Taken"),
    ("no_stock", "Contacted - Product Not Held"),
    ("not_reachable", "Consignee Not Reachable"),
]

#: Outcomes that count as a successful effectiveness check.
EFFECTIVENESS_SUCCESS_OUTCOMES = ("action_taken", "no_stock")

EFFECTIVENESS_STATE_SELECTION = [
    ("planned", "Planned"),
    ("performed", "Performed"),
    ("escalated", "Escalated"),
    ("cancelled", "Cancelled"),
]

# --- Consignee line ---------------------------------------------------
# [OPS] Reconciliation status of a single consignee/lot combination.
LINE_STATUS_SELECTION = [
    ("pending", "Pending Notification"),
    ("notified", "Notified"),
    ("responded", "Response Received"),
    ("reconciled", "Reconciled"),
    ("discrepancy", "Discrepancy"),
]

# --- Recall report ----------------------------------------------------
# [REG] 21 CFR 7.53 describes periodic recall status reports and the
#       information they contain.
REPORT_TYPE_SELECTION = [
    ("initial", "Initial Report"),
    ("status", "Status Report"),
    ("final", "Final Report"),
]

REPORT_STATE_SELECTION = [
    ("draft", "Draft"),
    ("reviewed", "Reviewed"),
    ("approved", "Approved"),
    ("submitted", "Submitted"),
]

#: Once a report reaches one of these states its content is frozen.
REPORT_FROZEN_STATES = ("approved", "submitted")
