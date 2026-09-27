# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Shared constants for the ``ls_medical_device`` module.

Every regulatory value declared in this file carries an explicit source
reference in its comment. Values without a verifiable source are NOT declared
here; they are exposed as user-editable configuration data instead.

Sources used in this file:

* Regulation (EU) 2017/745 (MDR), Article 27  -- UDI system components.
* Regulation (EU) 2017/745 (MDR), Article 61(11) -- annual update of the PMCF
  evaluation report for class III and implantable devices.
* Regulation (EU) 2017/745 (MDR), Article 85 -- post-market surveillance report
  (PMSR) for class I devices.
* Regulation (EU) 2017/745 (MDR), Article 86 -- periodic safety update report
  (PSUR); class IIb and class III updated at least annually, class IIa updated
  when necessary and at least every two years.
* Regulation (EU) 2017/745 (MDR), Article 87(3)(4)(5) -- serious incident
  reporting upper limits of 15, 2 and 10 days respectively.
"""

# ---------------------------------------------------------------------------
# Module-level identifiers
# ---------------------------------------------------------------------------

MODULE_NAME = "ls_medical_device"

GROUP_VIEWER = "ls_medical_device.group_ls_md_viewer"
GROUP_USER = "ls_medical_device.group_ls_md_user"
GROUP_REGULATORY = "ls_medical_device.group_ls_md_regulatory"
GROUP_MANAGER = "ls_medical_device.group_ls_md_manager"

# ---------------------------------------------------------------------------
# Periodic reporting intervals (MDR Article 85 and Article 86)
# ---------------------------------------------------------------------------

#: Periodic report kind required per device class code. Class I devices are
#: outside the PSUR scope and use a post-market surveillance report instead
#: (MDR Article 85). Class IIa, IIb and III devices require a PSUR
#: (MDR Article 86(1)).
PERIODIC_REPORT_PMSR = "pmsr"
PERIODIC_REPORT_PSUR = "psur"

#: Minimum PSUR update interval expressed in months, keyed by the *type* of
#: obligation rather than by a hard-coded class code, so that the shipped
#: configuration records remain the single source of truth.
#: MDR Article 86(1): class IIb and class III at least annually.
PSUR_INTERVAL_MONTHS_ANNUAL = 12
#: MDR Article 86(1): class IIa when necessary and at least every two years.
PSUR_INTERVAL_MONTHS_BIENNIAL = 24

#: MDR Article 61(11): for class III devices and implantable devices, the PMCF
#: evaluation report shall be updated at least annually.
PMCF_ANNUAL_UPDATE_MONTHS = 12

# ---------------------------------------------------------------------------
# Technical documentation retention (MDR Article 10(8))
# ---------------------------------------------------------------------------

#: Years the technical documentation must be kept available after the last
#: device covered by the EU declaration of conformity has been placed on the
#: market. MDR Article 10(8) sets ten years, and fifteen years for implantable
#: devices.
TECHNICAL_DOC_RETENTION_YEARS = 10
TECHNICAL_DOC_RETENTION_YEARS_IMPLANTABLE = 15

# ---------------------------------------------------------------------------
# Selections
# ---------------------------------------------------------------------------

#: Lifecycle of a device master record. These states are a design decision of
#: this module; the MDR does not prescribe a device lifecycle state machine.
DEVICE_STATE_SELECTION = [
    ("draft", "Draft"),
    ("development", "Under Development"),
    ("conformity_assessment", "Conformity Assessment"),
    ("on_market", "On the Market"),
    ("suspended", "Suspended"),
    ("withdrawn", "Withdrawn"),
]

#: States in which a device is considered to be commercially available and
#: therefore subject to post-market surveillance obligations.
DEVICE_STATES_ON_MARKET = ("on_market",)

#: Generic controlled-document lifecycle reused by the regulatory records of
#: this module (clinical evaluation, technical file, PMS plan, periodic
#: reports, PMCF evaluation, risk management file).
REGULATORY_DOC_STATE_SELECTION = [
    ("draft", "Draft"),
    ("under_review", "Under Review"),
    ("approved", "Approved"),
    ("superseded", "Superseded"),
    ("cancelled", "Cancelled"),
]

#: States from which a controlled record may still be edited freely.
REGULATORY_DOC_EDITABLE_STATES = ("draft",)

#: Terminal states of a controlled record.
REGULATORY_DOC_CLOSED_STATES = ("superseded", "cancelled")

#: UDI identifier kinds. MDR Article 27(1)(a) defines the UDI-DI and the
#: UDI-PI; MDR Annex VI Part C defines the Basic UDI-DI.
UDI_KIND_SELECTION = [
    ("basic_udi_di", "Basic UDI-DI"),
    ("udi_di", "UDI-DI"),
]

#: Issuing entities designated by the European Commission to operate a UDI
#: assignment system. The list is configuration data and is intentionally kept
#: open-ended through the "other" entry so that no designation is asserted that
#: has not been confirmed against the applicable Commission Implementing
#: Decision at the time of use.
UDI_ISSUING_ENTITY_SELECTION = [
    ("gs1", "GS1"),
    ("hibcc", "HIBCC"),
    ("iccbba", "ICCBBA"),
    ("ifa", "IFA"),
    ("other", "Other (record in notes)"),
]

#: Packaging level to which a UDI record applies. MDR Article 27(1) requires a
#: UDI to be assigned to the device and to all higher levels of packaging.
UDI_PACKAGING_LEVEL_SELECTION = [
    ("unit_of_use", "Unit of Use"),
    ("primary", "Primary Packaging"),
    ("secondary", "Secondary Packaging"),
    ("tertiary", "Tertiary Packaging"),
]

#: Carrier technology used to present the UDI.
UDI_CARRIER_SELECTION = [
    ("linear", "Linear Barcode"),
    ("2d", "2D Data Matrix"),
    ("rfid", "RFID"),
    ("hri_only", "Human Readable Interface Only"),
]

#: Lifecycle of a UDI record.
UDI_STATE_SELECTION = [
    ("draft", "Draft"),
    ("assigned", "Assigned"),
    ("published", "Published to Database"),
    ("obsolete", "Obsolete"),
]

#: Conformity assessment routes. The annex references are those of Regulation
#: (EU) 2017/745. The applicable route for a given device must be determined by
#: the manufacturer and, where required, agreed with the notified body.
CONFORMITY_ROUTE_SELECTION = [
    ("annex_ix", "Annex IX - QMS and technical documentation assessment"),
    ("annex_x", "Annex X - Type examination"),
    ("annex_xi", "Annex XI - Product conformity verification"),
    ("annex_xiii", "Annex XIII - Custom-made devices"),
    ("self_declaration", "Self-declaration (no notified body involvement)"),
]

#: Lifecycle of a CE marking / declaration of conformity record.
CE_MARKING_STATE_SELECTION = [
    ("draft", "Draft"),
    ("submitted", "Submitted to Notified Body"),
    ("issued", "Certificate Issued"),
    ("valid", "Valid"),
    ("suspended", "Suspended"),
    ("withdrawn", "Withdrawn"),
    ("expired", "Expired"),
]

#: ISO 14971:2019 risk control option categories, in the order of priority
#: given by the standard: inherently safe design and manufacture, protective
#: measures in the device itself or in the manufacturing process, and
#: information for safety together with training where appropriate.
RISK_CONTROL_OPTION_SELECTION = [
    ("inherent_safety", "Inherently Safe Design and Manufacture"),
    ("protective_measure", "Protective Measures in Device or Manufacturing"),
    ("information_safety", "Information for Safety and Training"),
]

#: Qualitative severity scale used by the shipped risk matrix. The scale is a
#: configuration default of this module. ISO 14971:2019 requires the
#: manufacturer to define its own severity and probability categories in the
#: risk management plan; the values below must be reviewed and, where needed,
#: replaced during implementation.
RISK_SEVERITY_SELECTION = [
    ("1", "1 - Negligible"),
    ("2", "2 - Minor"),
    ("3", "3 - Serious"),
    ("4", "4 - Critical"),
    ("5", "5 - Catastrophic"),
]

#: Qualitative probability scale used by the shipped risk matrix. See the note
#: on :data:`RISK_SEVERITY_SELECTION`.
RISK_PROBABILITY_SELECTION = [
    ("1", "1 - Improbable"),
    ("2", "2 - Remote"),
    ("3", "3 - Occasional"),
    ("4", "4 - Probable"),
    ("5", "5 - Frequent"),
]

#: Acceptability decision recorded for each residual risk.
RISK_ACCEPTABILITY_SELECTION = [
    ("acceptable", "Acceptable"),
    ("alarp", "Acceptable After Risk Reduction"),
    ("unacceptable", "Unacceptable"),
]

#: Default boundary of the shipped risk matrix, expressed as a risk index
#: (severity x probability). Values strictly below the first boundary are
#: proposed as acceptable, values at or above the second boundary are proposed
#: as unacceptable. These are configuration defaults, not regulatory values.
RISK_INDEX_ACCEPTABLE_BELOW = 5
RISK_INDEX_UNACCEPTABLE_FROM = 15

#: Sections of the technical documentation defined by MDR Annex II. The section
#: titles below are shipped as editable template data and are reproduced in the
#: numbering used by the Regulation. Section titles 1 to 5 were confirmed
#: against published renderings of Annex II. The title of section 6 could not
#: be re-verified from official documentation during preparation of this
#: module; implementers must confirm it against the Official Journal text.
TECHNICAL_FILE_ANNEX_SELECTION = [
    ("annex_ii", "Annex II - Technical Documentation"),
    ("annex_iii", "Annex III - Technical Documentation on Post-Market Surveillance"),
    ("annex_xiii", "Annex XIII - Custom-Made Devices"),
]

#: Kinds of periodic post-market report.
PERIODIC_REPORT_TYPE_SELECTION = [
    (PERIODIC_REPORT_PMSR, "Post-Market Surveillance Report (Article 85)"),
    (PERIODIC_REPORT_PSUR, "Periodic Safety Update Report (Article 86)"),
]

#: Conclusion recorded at the end of a periodic post-market report.
PERIODIC_REPORT_CONCLUSION_SELECTION = [
    ("favourable", "Benefit-Risk Determination Remains Favourable"),
    ("favourable_with_actions", "Favourable Subject to Identified Actions"),
    ("not_favourable", "Benefit-Risk Determination No Longer Favourable"),
]

# ---------------------------------------------------------------------------
# Vigilance reporting deadlines (MDR Article 87)
# ---------------------------------------------------------------------------
#
# This module does not implement a vigilance case model. The values below are
# published here so that an integrating module can reuse them without
# re-deriving them, and so that the documentation of this module can state the
# deadlines it deliberately does not enforce. See the Developer Manual,
# section "Extension points", for the rationale.

#: MDR Article 87(3): upper limit for reporting a serious incident.
VIGILANCE_DAYS_SERIOUS_INCIDENT = 15
#: MDR Article 87(4): upper limit in the event of a serious public health threat.
VIGILANCE_DAYS_PUBLIC_HEALTH_THREAT = 2
#: MDR Article 87(5): upper limit in the event of death or an unanticipated
#: serious deterioration in a person's state of health.
VIGILANCE_DAYS_DEATH_OR_DETERIORATION = 10

# ---------------------------------------------------------------------------
# Device lifecycle transition map
# ---------------------------------------------------------------------------

#: Permitted target statuses keyed by source status. The map is the single
#: definition of the device state machine; the form buttons and the status
#: change wizard both enforce it.
DEVICE_ALLOWED_TRANSITIONS = {
    "draft": ("development",),
    "development": ("conformity_assessment",),
    "conformity_assessment": ("on_market", "development"),
    "on_market": ("suspended", "withdrawn"),
    "suspended": ("on_market", "withdrawn"),
    "withdrawn": (),
}
