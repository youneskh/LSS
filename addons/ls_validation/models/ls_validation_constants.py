# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Shared selection lists and constants for the Validation Management module.

Centralising the selections keeps the labels identical across models, views,
reports and tests (DRY principle) and gives a single place to extend the
vocabulary of the module.
"""

# --------------------------------------------------------------------------
# Validation subjects
# --------------------------------------------------------------------------
ITEM_TYPES = [
    ("equipment", "Equipment"),
    ("utility", "Utility"),
    ("facility", "Facility / Area"),
    ("process", "Manufacturing Process"),
    ("cleaning", "Cleaning Procedure"),
    ("computerised_system", "Computerised System"),
    ("analytical_method", "Analytical Method"),
    ("transport", "Transport / Shipping Lane"),
]

GXP_IMPACT = [
    ("none", "No GxP Impact"),
    ("indirect", "Indirect Impact"),
    ("direct", "Direct Impact"),
]

CRITICALITY = [
    ("low", "Low"),
    ("medium", "Medium"),
    ("high", "High"),
]

VALIDATION_STATE = [
    ("not_validated", "Not Validated"),
    ("in_validation", "In Validation"),
    ("validated", "Validated"),
    ("expiring", "Expiring Soon"),
    ("expired", "Expired"),
    ("retired", "Retired"),
]

# --------------------------------------------------------------------------
# Protocols
# --------------------------------------------------------------------------
PROTOCOL_TYPES = [
    ("dq", "DQ - Design Qualification"),
    ("iq", "IQ - Installation Qualification"),
    ("oq", "OQ - Operational Qualification"),
    ("pq", "PQ - Performance Qualification"),
    ("pv", "PV - Process Validation"),
    ("cv", "CV - Cleaning Validation"),
    ("csv", "CSV - Computerised System Validation"),
    ("mv", "MV - Analytical Method Validation"),
]

# --------------------------------------------------------------------------
# Results and discrepancies
# --------------------------------------------------------------------------
RESULT_VERDICT = [
    ("pending", "Pending"),
    ("pass", "Pass"),
    ("fail", "Fail"),
    ("na", "Not Applicable"),
]

DISCREPANCY_CLASSIFICATION = [
    ("minor", "Minor"),
    ("major", "Major"),
    ("critical", "Critical"),
]

# --------------------------------------------------------------------------
# Validation summary report
# --------------------------------------------------------------------------
REPORT_CONCLUSION = [
    ("validated", "Validated"),
    ("validated_restricted", "Validated with Restrictions"),
    ("not_validated", "Not Validated"),
]

# --------------------------------------------------------------------------
# Configuration parameter keys (ir.config_parameter)
# --------------------------------------------------------------------------
PARAM_PASSWORD_REQUIRED = "ls_validation.signature_password_required"
PARAM_EXPIRY_NOTICE_DAYS = "ls_validation.expiry_notice_days"

DEFAULT_EXPIRY_NOTICE_DAYS = 60
