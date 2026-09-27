# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Centralised constants for the ``ls_medical_plastics`` module.

Every selection vocabulary, threshold and technical default used by the module
is declared here so that the values are defined exactly once and can be reused
by models, wizards and tests without duplication.

Terminology note
----------------
The polymer abbreviations and moulding defect names used below are standard
engineering terminology in plastics processing. They are shipped as
configurable vocabularies. They are **not** regulatory classifications and
carry no compliance meaning of their own.
"""

# ---------------------------------------------------------------------------
# Material grade register
# ---------------------------------------------------------------------------

POLYMER_TYPES = [
    ("pp", "PP - Polypropylene"),
    ("pe_ld", "LDPE - Low Density Polyethylene"),
    ("pe_hd", "HDPE - High Density Polyethylene"),
    ("ps", "PS - Polystyrene"),
    ("abs", "ABS - Acrylonitrile Butadiene Styrene"),
    ("pc", "PC - Polycarbonate"),
    ("pet", "PET - Polyethylene Terephthalate"),
    ("pvc", "PVC - Polyvinyl Chloride"),
    ("pom", "POM - Polyoxymethylene"),
    ("pmma", "PMMA - Poly(methyl methacrylate)"),
    ("pa", "PA - Polyamide"),
    ("tpe", "TPE - Thermoplastic Elastomer"),
    ("sebs", "SEBS - Styrene Ethylene Butylene Styrene"),
    ("coc_cop", "COC/COP - Cyclic Olefin (Co)Polymer"),
    ("silicone", "LSR - Liquid Silicone Rubber"),
    ("masterbatch", "Masterbatch / Colorant"),
    ("other", "Other"),
]

MATERIAL_QUALIFICATION_STATES = [
    ("draft", "Draft"),
    ("under_evaluation", "Under Evaluation"),
    ("qualified", "Qualified"),
    ("conditionally_qualified", "Conditionally Qualified"),
    ("rejected", "Rejected"),
    ("obsolete", "Obsolete"),
]

#: Material states in which a grade may be consumed by a moulding run.
MATERIAL_USABLE_STATES = ("qualified", "conditionally_qualified")

# ---------------------------------------------------------------------------
# Component register
# ---------------------------------------------------------------------------

COMPONENT_CATEGORIES = [
    ("primary_packaging", "Primary Packaging Component"),
    ("closure_cap", "Closure / Cap"),
    ("syringe_barrel", "Syringe Barrel"),
    ("syringe_plunger", "Syringe Plunger / Stopper"),
    ("pen_component", "Injection Pen Component"),
    ("dropper", "Dropper / Nozzle"),
    ("measuring_device", "Measuring Device"),
    ("oral_dispenser", "Oral Dispenser"),
    ("device_component", "Medical Device Component"),
    ("secondary_component", "Secondary Packaging Component"),
    ("other", "Other"),
]

#: Categories treated as primary packaging for menu filtering and reporting.
PRIMARY_PACKAGING_CATEGORIES = (
    "primary_packaging",
    "closure_cap",
    "syringe_barrel",
    "syringe_plunger",
    "dropper",
    "measuring_device",
    "oral_dispenser",
)

STERILIZATION_METHODS = [
    ("none", "Not Sterilised"),
    ("eto", "Ethylene Oxide"),
    ("gamma", "Gamma Irradiation"),
    ("e_beam", "Electron Beam"),
    ("steam", "Moist Heat / Steam"),
    ("dry_heat", "Dry Heat"),
    ("other", "Other"),
]

CRITICALITY_LEVELS = [
    ("critical", "Critical"),
    ("major", "Major"),
    ("minor", "Minor"),
]

COMPONENT_STATES = [
    ("draft", "Draft"),
    ("released", "Released"),
    ("on_hold", "On Hold"),
    ("obsolete", "Obsolete"),
]

# ---------------------------------------------------------------------------
# Tool register
# ---------------------------------------------------------------------------

TOOL_TYPES = [
    ("injection_mold", "Injection Mould"),
    ("family_mold", "Family Mould"),
    ("insert", "Mould Insert"),
    ("hot_runner", "Hot Runner System"),
    ("core_pin", "Core Pin Set"),
    ("fixture", "Fixture"),
    ("trim_tool", "Trim Tool"),
    ("other", "Other"),
]

TOOL_STATES = [
    ("draft", "Draft"),
    ("qualified", "Qualified"),
    ("in_service", "In Service"),
    ("maintenance", "Under Maintenance"),
    ("quarantined", "Quarantined"),
    ("decommissioned", "Decommissioned"),
]

#: The only tool state in which a moulding run may be executed.
TOOL_PRODUCTION_STATE = "in_service"

TOOL_MAINTENANCE_STATUS = [
    ("not_applicable", "Not Applicable"),
    ("ok", "OK"),
    ("due_soon", "Due Soon"),
    ("overdue", "Overdue"),
]

CAVITY_STATES = [
    ("active", "Active"),
    ("blocked", "Blocked"),
    ("removed", "Removed"),
]

MAINTENANCE_TYPES = [
    ("preventive", "Preventive Maintenance"),
    ("corrective", "Corrective Maintenance"),
    ("cleaning", "Cleaning"),
    ("repair", "Repair"),
    ("modification", "Modification"),
    ("requalification", "Requalification"),
]

MAINTENANCE_STATES = [
    ("draft", "Draft"),
    ("in_progress", "In Progress"),
    ("done", "Done"),
    ("cancelled", "Cancelled"),
]

#: Fraction of the preventive maintenance interval after which the tool is
#: flagged as "due soon". 0.9 means the warning is raised once 90% of the
#: interval has elapsed. This is a configurable engineering default, not a
#: regulatory threshold.
MAINTENANCE_WARNING_RATIO = 0.9

#: Number of days before the requalification / review due date at which a
#: record is flagged as "due soon".
DUE_SOON_DAYS = 30

# ---------------------------------------------------------------------------
# Moulding parameter specification
# ---------------------------------------------------------------------------

PARAMETER_SPEC_STATES = [
    ("draft", "Draft"),
    ("review", "Under Review"),
    ("approved", "Approved"),
    ("superseded", "Superseded"),
    ("obsolete", "Obsolete"),
    ("cancelled", "Cancelled"),
]

#: The only specification state usable to execute a moulding run.
PARAMETER_SPEC_EFFECTIVE_STATE = "approved"

PARAMETER_VALUE_TYPES = [
    ("numeric", "Numeric"),
    ("qualitative", "Qualitative"),
]

MONITORING_FREQUENCIES = [
    ("setup_only", "At Setup Only"),
    ("per_startup", "At Start-up Verification"),
    ("hourly", "Hourly"),
    ("per_shift", "Once per Shift"),
    ("per_lot", "Once per Lot"),
    ("continuous", "Continuous (automated)"),
]

#: Monitoring frequencies whose parameters must carry a recorded value before
#: a run may leave the start-up verification state.
STARTUP_REQUIRED_FREQUENCIES = ("setup_only", "per_startup")

# ---------------------------------------------------------------------------
# Moulding run
# ---------------------------------------------------------------------------

RUN_STATES = [
    ("draft", "Draft"),
    ("setup", "Setup"),
    ("startup_check", "Start-up Verification"),
    ("running", "Running"),
    ("completed", "Completed"),
    ("reviewed", "Reviewed"),
    ("closed", "Closed"),
    ("cancelled", "Cancelled"),
]

#: States in which the run record is frozen against further modification.
RUN_LOCKED_STATES = ("closed",)

#: States from which a run may still be cancelled.
RUN_CANCELLABLE_STATES = ("draft", "setup", "startup_check")

#: States in which a run record may be deleted.
RUN_DELETABLE_STATES = ("draft", "cancelled")

READING_TYPES = [
    ("setup", "Setup"),
    ("startup", "Start-up Verification"),
    ("in_process", "In-Process"),
    ("end_of_run", "End of Run"),
]

PRODUCTION_SHIFTS = [
    ("shift_1", "Shift 1"),
    ("shift_2", "Shift 2"),
    ("shift_3", "Shift 3"),
]

# ---------------------------------------------------------------------------
# Scrap and defect classification
# ---------------------------------------------------------------------------

SCRAP_CATEGORIES = [
    ("dimensional", "Dimensional"),
    ("cosmetic", "Cosmetic"),
    ("contamination", "Contamination"),
    ("process", "Process Defect"),
    ("material", "Material Defect"),
    ("setup", "Setup / Purge"),
    ("handling", "Handling Damage"),
    ("other", "Other"),
]

# ---------------------------------------------------------------------------
# Field size limits
# ---------------------------------------------------------------------------

#: Maximum number of characters accepted in a short code field.
CODE_MAX_LENGTH = 32

#: Digits used for quantity fields (total, decimal).
QUANTITY_DIGITS = (16, 3)

#: Digits used for measured parameter values (total, decimal).
MEASUREMENT_DIGITS = (16, 4)
