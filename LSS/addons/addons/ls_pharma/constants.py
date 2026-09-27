# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Static, non-configurable constants used across the ``ls_pharma`` module.

Every regulatory citation recorded in this file has been taken from the
official source named in the accompanying comment.  No value in this file
is inferred, estimated or assumed.

Sources
-------
* 21 CFR Part 211 Subpart F and Subpart J -- Electronic Code of Federal
  Regulations, https://www.ecfr.gov/current/title-21/chapter-I/subchapter-C/part-211
* GS1 Application Identifiers -- GS1 General Specifications, Section 3.
* ICH Q1A(R2) -- Stability Testing of New Drug Substances and Products.
* ICH M4(R4) -- Organisation of the Common Technical Document.
* Commission Delegated Regulation (EU) 2016/161.
"""

# ---------------------------------------------------------------------------
# Batch life cycle
# ---------------------------------------------------------------------------

#: Ordered state machine of :class:`~odoo.addons.ls_pharma.models.
#: ls_pharma_batch.LsPharmaBatch`.
BATCH_STATES = [
    ("draft", "Planned"),
    ("in_process", "In Production"),
    ("manufactured", "Manufacturing Complete"),
    ("quarantine", "Quarantine"),
    ("under_review", "QA Record Review"),
    ("released", "Released"),
    ("rejected", "Rejected"),
    ("cancelled", "Cancelled"),
]

#: States in which a batch is considered closed for production data entry.
BATCH_CLOSED_STATES = ("released", "rejected", "cancelled")

#: States from which a batch may still be cancelled.
BATCH_CANCELLABLE_STATES = ("draft", "in_process")

BATCH_TYPES = [
    ("bulk", "Bulk / Intermediate"),
    ("packaging", "Packaging"),
    ("finished", "Finished Product"),
]

# ---------------------------------------------------------------------------
# Electronic batch record life cycle
# ---------------------------------------------------------------------------

BATCH_RECORD_STATES = [
    ("draft", "Draft"),
    ("in_execution", "In Execution"),
    ("completed", "Execution Complete"),
    ("under_review", "Under QA Review"),
    ("approved", "Approved"),
    ("rejected", "Rejected"),
]

BATCH_RECORD_TYPES = [
    ("manufacturing", "Manufacturing"),
    ("packaging", "Packaging and Labelling"),
]

#: Line-clearance moments required by 21 CFR 211.188(b)(6), which requires
#: documentation of the "inspection of the packaging and labeling area before
#: and after use".
CLEARANCE_MOMENTS = [
    ("before", "Before Use"),
    ("after", "After Use"),
]

DISCREPANCY_STATES = [
    ("open", "Open"),
    ("under_investigation", "Under Investigation"),
    ("closed", "Closed"),
]

#: Sample categories.  ``reserve`` implements the reserve sample concept of
#: 21 CFR 211.170.
SAMPLE_TYPES = [
    ("in_process", "In-Process Sample"),
    ("finished", "Finished Product Sample"),
    ("reserve", "Reserve Sample"),
    ("stability", "Stability Sample"),
    ("microbiological", "Microbiological Sample"),
    ("environmental", "Environmental Sample"),
]

# ---------------------------------------------------------------------------
# Batch release
# ---------------------------------------------------------------------------

RELEASE_DECISIONS = [
    ("released", "Released for Distribution"),
    ("rejected", "Rejected"),
]

#: Mapping between each release checklist field and the regulatory provision
#: that the check is intended to support.  The mapping is rendered on the
#: release certificate so that the reason for every check is auditable.
#:
#: Each tuple is ``(field name, label, regulatory reference)``.
RELEASE_CHECKLIST = [
    (
        "check_record_reviewed",
        "Batch production and control records reviewed and approved",
        "21 CFR 211.192",
    ),
    (
        "check_discrepancies_closed",
        "All discrepancies investigated and closed with written conclusion",
        "21 CFR 211.192",
    ),
    (
        "check_yield_within_limits",
        "Actual yield within the established percentage limits",
        "21 CFR 211.103 and 21 CFR 211.192",
    ),
    (
        "check_components_verified",
        "Component charge-in verified by a second person",
        "21 CFR 211.101(c) and 21 CFR 211.101(d)",
    ),
    (
        "check_qc_conform",
        "Finished product laboratory results conform to specification",
        "21 CFR 211.165",
    ),
    (
        "check_labeling_reconciled",
        "Labelling issued, used, returned and destroyed quantities reconciled",
        "21 CFR 211.125 and 21 CFR 211.188(b)(8)",
    ),
    (
        "check_reserve_samples",
        "Reserve samples collected and retained",
        "21 CFR 211.170",
    ),
    (
        "check_stability_programme",
        "Batch covered by the written stability testing programme",
        "21 CFR 211.166",
    ),
]

#: Field names of the release checklist, derived from RELEASE_CHECKLIST so
#: that the two can never drift apart.
RELEASE_CHECKLIST_FIELDS = tuple(item[0] for item in RELEASE_CHECKLIST)

#: Fields of ``ls.pharma.batch.release`` that become immutable once the
#: release decision has been recorded.
RELEASE_IMMUTABLE_FIELDS = (
    "batch_id",
    "decision",
    "decision_date",
    "decided_by_user_id",
    "statement",
    "integrity_hash",
) + RELEASE_CHECKLIST_FIELDS

# ---------------------------------------------------------------------------
# Material master data
# ---------------------------------------------------------------------------

MATERIAL_STATES = [
    ("draft", "Draft"),
    ("qualified", "Qualified"),
    ("restricted", "Restricted"),
    ("obsolete", "Obsolete"),
]

PHARMACOPOEIA = [
    ("ph_eur", "European Pharmacopoeia (Ph. Eur.)"),
    ("usp_nf", "United States Pharmacopeia / National Formulary (USP-NF)"),
    ("bp", "British Pharmacopoeia (BP)"),
    ("jp", "Japanese Pharmacopoeia (JP)"),
    ("ip", "International Pharmacopoeia (Ph. Int.)"),
    ("in_house", "In-House Specification"),
]

#: Basis on which the assay of an active pharmaceutical ingredient is
#: expressed, used to compute the compensated charge quantity.
POTENCY_BASIS = [
    ("as_is", "As Is"),
    ("anhydrous", "Anhydrous Basis"),
    ("dried", "Dried Basis"),
    ("active_moiety", "Active Moiety Basis"),
]

EXCIPIENT_FUNCTIONS = [
    ("diluent", "Diluent / Filler"),
    ("binder", "Binder"),
    ("disintegrant", "Disintegrant"),
    ("lubricant", "Lubricant"),
    ("glidant", "Glidant"),
    ("coating", "Coating Agent"),
    ("plasticiser", "Plasticiser"),
    ("preservative", "Preservative"),
    ("antioxidant", "Antioxidant"),
    ("colorant", "Colorant"),
    ("flavour", "Flavour / Sweetener"),
    ("solvent", "Solvent / Vehicle"),
    ("buffer", "Buffering Agent"),
    ("surfactant", "Surfactant"),
    ("tonicity", "Tonicity Agent"),
]

DOSAGE_FORMS = [
    ("tablet", "Tablet"),
    ("coated_tablet", "Coated Tablet"),
    ("capsule_hard", "Hard Capsule"),
    ("capsule_soft", "Soft Capsule"),
    ("powder", "Powder / Granules"),
    ("effervescent", "Effervescent Form"),
    ("oral_solution", "Oral Solution"),
    ("oral_suspension", "Oral Suspension"),
    ("syrup", "Syrup"),
    ("emulsion", "Emulsion"),
    ("injectable_ampoule", "Injectable - Ampoule"),
    ("injectable_vial", "Injectable - Vial"),
    ("injectable_syringe", "Injectable - Pre-Filled Syringe"),
    ("lyophilised", "Lyophilised Product"),
    ("ophthalmic", "Ophthalmic Preparation"),
    ("irrigation", "Sterile Irrigation Solution"),
    ("cream", "Cream"),
    ("ointment", "Ointment"),
    ("gel", "Gel"),
    ("paste", "Paste"),
    ("suppository", "Suppository"),
    ("transdermal", "Transdermal Patch"),
    ("vaccine", "Vaccine"),
    ("biopharmaceutical", "Biopharmaceutical"),
    ("blood_derived", "Blood-Derived Product"),
    ("cell_gene", "Cell or Gene Therapy Product"),
]

# ---------------------------------------------------------------------------
# Stability -- ICH Q1A(R2)
# ---------------------------------------------------------------------------

STABILITY_STUDY_TYPES = [
    ("registration", "Registration / Primary Stability"),
    ("ongoing", "Ongoing (On-Going) Stability"),
    ("follow_up", "Follow-Up Stability"),
    ("post_change", "Post-Change Stability"),
]

STABILITY_STUDY_STATES = [
    ("draft", "Draft"),
    ("scheduled", "Scheduled"),
    ("ongoing", "Ongoing"),
    ("completed", "Completed"),
    ("terminated", "Terminated"),
]

STABILITY_CONDITION_TYPES = [
    ("long_term", "Long Term"),
    ("intermediate", "Intermediate"),
    ("accelerated", "Accelerated"),
    ("other", "Other"),
]

TIMEPOINT_STATES = [
    ("scheduled", "Scheduled"),
    ("pulled", "Pulled"),
    ("tested", "Tested"),
    ("completed", "Completed"),
    ("out_of_specification", "Out of Specification"),
    ("missed", "Missed"),
]

STABILITY_SAMPLE_STATES = [
    ("stored", "In Storage"),
    ("pulled", "Pulled"),
    ("consumed", "Consumed"),
    ("discarded", "Discarded"),
]

#: Testing frequencies published in ICH Q1A(R2).
#:
#: * Long term: "every 3 months over the first year, every 6 months over the
#:   second year, and annually thereafter through the proposed shelf life".
#: * Accelerated: "a minimum of three time points, including the initial and
#:   final time points (e.g., 0, 3, and 6 months), from a 6-month study".
#: * Intermediate: "a minimum of four time points, including the initial and
#:   final time points (e.g., 0, 6, 9, 12 months), from a 12-month study".
#:
#: Source: ICH Q1A(R2), reproduced by the FDA as Guidance for Industry
#: Q1A(R2) Stability Testing of New Drug Substances and Products,
#: https://www.fda.gov/media/71707/download
ICH_ACCELERATED_TIMEPOINTS = (0, 3, 6)
ICH_INTERMEDIATE_TIMEPOINTS = (0, 6, 9, 12)

#: Month at which the long-term testing interval changes from 3 to 6 months.
ICH_LONG_TERM_QUARTERLY_UNTIL_MONTH = 12
#: Month at which the long-term testing interval changes from 6 to 12 months.
ICH_LONG_TERM_SEMESTRIAL_UNTIL_MONTH = 24

# ---------------------------------------------------------------------------
# Serialisation -- GS1 and Commission Delegated Regulation (EU) 2016/161
# ---------------------------------------------------------------------------

#: GS1 Application Identifiers used by this module.  Source: GS1 General
#: Specifications, Section 3, "GS1 Application Identifier Definitions".
AI_SSCC = "00"          # Serial Shipping Container Code,   N2+N18
AI_GTIN = "01"          # Global Trade Item Number,         N2+N14
AI_CONTENT = "02"       # GTIN of contained trade items,    N2+N14
AI_BATCH_LOT = "10"     # Batch or lot number,              N2+X..20
AI_PRODUCTION_DATE = "11"  # Production date (YYMMDD),      N2+N6
AI_EXPIRY_DATE = "17"   # Expiration date (YYMMDD),         N2+N6
AI_SERIAL = "21"        # Serial number,                    N2+X..20
AI_COUNT = "37"         # Count of trade items,             N2+N..8

#: Fixed lengths of the GS1 identification keys handled by this module.
GTIN14_LENGTH = 14
SSCC_LENGTH = 18

#: Maximum length of the variable-length AI (10) and AI (21) data fields.
AI_VARIABLE_MAX_LENGTH = 20

#: Character set permitted in AI (21) serial numbers by this module.  The GS1
#: General Specifications permit the wider GS1 AI encodable character set 82;
#: this module restricts generated serial numbers to upper-case alphanumerics
#: in order to remain unambiguous in human-readable interpretation.  Manually
#: entered serial numbers are validated against length only.
SERIAL_ALPHABET = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"

SERIALIZATION_STATES = [
    ("generated", "Generated"),
    ("commissioned", "Commissioned"),
    ("aggregated", "Aggregated"),
    ("shipped", "Shipped"),
    ("decommissioned", "Decommissioned"),
    ("destroyed", "Destroyed"),
    ("sampled", "Sampled"),
    ("returned", "Returned"),
]

#: States in which a serialised unit is no longer available for commercial
#: distribution.
SERIALIZATION_TERMINAL_STATES = (
    "decommissioned",
    "destroyed",
    "sampled",
)

AGGREGATION_LEVELS = [
    ("bundle", "Bundle"),
    ("case", "Case / Shipper"),
    ("pallet", "Pallet"),
]

AGGREGATION_STATES = [
    ("draft", "Draft"),
    ("packed", "Packed"),
    ("shipped", "Shipped"),
    ("disaggregated", "Disaggregated"),
]

# ---------------------------------------------------------------------------
# CTD dossier -- ICH M4(R4)
# ---------------------------------------------------------------------------

#: The five CTD modules defined by ICH M4(R4).  Module 1 is region specific;
#: Modules 2 to 5 are common to all ICH regions.
CTD_MODULES = [
    ("1", "Module 1 - Administrative Information and Prescribing Information"),
    ("2", "Module 2 - Common Technical Document Summaries"),
    ("3", "Module 3 - Quality"),
    ("4", "Module 4 - Nonclinical Study Reports"),
    ("5", "Module 5 - Clinical Study Reports"),
]

CTD_DOSSIER_TYPES = [
    ("new", "New Marketing Authorisation Application"),
    ("variation", "Variation"),
    ("renewal", "Renewal"),
    ("transfer", "Transfer of Marketing Authorisation"),
]

CTD_DOSSIER_STATES = [
    ("draft", "Draft"),
    ("in_preparation", "In Preparation"),
    ("ready", "Ready for Submission"),
    ("submitted", "Submitted"),
    ("deficiency", "Deficiency Received"),
    ("approved", "Approved"),
    ("withdrawn", "Withdrawn"),
]

CTD_SECTION_STATES = [
    ("not_started", "Not Started"),
    ("in_preparation", "In Preparation"),
    ("ready", "Ready"),
    ("submitted", "Submitted"),
    ("deficiency", "Deficiency"),
    ("complete", "Complete"),
]

# ---------------------------------------------------------------------------
# Integrity hashing
# ---------------------------------------------------------------------------

#: Separator used when building the canonical string that is hashed to make a
#: batch release decision tamper evident.  A control character is used so that
#: it cannot occur inside any user-supplied value stored by this module.
HASH_FIELD_SEPARATOR = "\x1f"

#: Digest algorithm used for the release integrity hash.
HASH_ALGORITHM = "sha256"
