# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0.html).
"""Constants shared by the ``ls_cosmetics`` module.

Every selection list, numeric limit and regulatory reference used by the
module is declared here so that a single file can be reviewed against the
source legislation during qualification.

Sources used to build this file
-------------------------------
* Regulation (EC) No 1223/2009 on cosmetic products (recast).  The article
  and Annex I wording was read from the consolidated text published on
  ``legislation.gov.uk/eur/2009/1223`` (assimilated UK version, which
  reproduces the recast technical requirements) and cross-checked against
  the EUR-Lex record ``eli/reg/2009/1223``.
* Commission Regulation (EU) No 655/2013 laying down common criteria for
  the justification of claims used in relation to cosmetic products.
* ISO 22716:2007, *Cosmetics - Good Manufacturing Practices (GMP) -
  Guidelines on Good Manufacturing Practices*: clause numbering taken from
  the published table of contents of the standard.
* Decret executif n° 97-37 of 14 January 1997 (JO n° 4/1997) as modified
  and completed by decret executif n° 10-114 of 18 April 2010
  (JO n° 26/2010), and the dossier / procedure description published by the
  Algerian Ministere du Commerce.

Nothing in this file is derived from an unverified source.  Where a list is
deliberately left empty (for example the substance annexes) the docstring
of the corresponding model explains why.
"""

# ---------------------------------------------------------------------------
# Regulatory reference strings
# ---------------------------------------------------------------------------
REG_EU_COSMETICS = "Regulation (EC) No 1223/2009"
REG_EU_CLAIMS = "Commission Regulation (EU) No 655/2013"
STD_ISO_22716 = "ISO 22716:2007"
DZ_DECREE_9737 = "Decret executif n° 97-37 du 14 janvier 1997"
DZ_DECREE_10114 = "Decret executif n° 10-114 du 18 avril 2010"

# ---------------------------------------------------------------------------
# Article 11(1): the product information file is kept for ten years following
# the date on which the last batch was placed on the market.
# ---------------------------------------------------------------------------
PIF_RETENTION_YEARS = 10

# ---------------------------------------------------------------------------
# Article 19(1)(c): indication of the date of minimum durability is not
# mandatory where minimum durability exceeds 30 months; a period-after-opening
# is indicated instead.
# ---------------------------------------------------------------------------
MIN_DURABILITY_THRESHOLD_MONTHS = 30

# ---------------------------------------------------------------------------
# Article 19(1)(g): ingredients in concentrations of less than 1 % may be
# listed in any order after those in concentrations of more than 1 %.
# ---------------------------------------------------------------------------
INCI_ORDERING_THRESHOLD_PERCENT = 1.0

# ---------------------------------------------------------------------------
# A formulation is expressed in % w/w and must total 100 %.  Floating point
# accumulation of user-entered values requires a tolerance; the value below is
# an engineering choice, not a regulatory value.
# ---------------------------------------------------------------------------
FORMULATION_TOTAL_PERCENT = 100.0
FORMULATION_TOTAL_TOLERANCE = 0.05

# ---------------------------------------------------------------------------
# Article 19(1)(g): perfume and aromatic compositions and their raw materials
# are referred to by the terms 'parfum' or 'aroma'.
# ---------------------------------------------------------------------------
INCI_PERFUME_TERM = "parfum"
INCI_AROMA_TERM = "aroma"
INCI_NANO_SUFFIX = "(nano)"
INCI_LIST_PREFIX = "Ingredients"
INCI_MAY_CONTAIN_MARKER = "+/-"

# ---------------------------------------------------------------------------
# Ministere du Commerce (Algeria): the Minister notifies the decision within
# forty-five (45) days from the date the deposit receipt was issued.  Where an
# element on which the authorisation was granted subsequently fails, the
# operator is formally notified and has one (1) month to comply.
# ---------------------------------------------------------------------------
DZ_DECISION_DELAY_DAYS = 45
DZ_COMPLIANCE_DELAY_DAYS = 30

# ---------------------------------------------------------------------------
# Selections
# ---------------------------------------------------------------------------

#: Article 2(1)(l), (m) and (n) define exactly three functional categories of
#: substance that are subject to positive lists.  Any other function is
#: recorded as free text on the ingredient (``technical_function``); no
#: additional category is invented here.
INGREDIENT_REGULATORY_CATEGORY = [
    ("preservative", "Preservative - Article 2(1)(l)"),
    ("colorant", "Colorant - Article 2(1)(m)"),
    ("uv_filter", "UV-filter - Article 2(1)(n)"),
    ("none", "None of the above"),
]

#: Annexes II to VI of Regulation (EC) No 1223/2009 as referenced by
#: Article 14(1).
RESTRICTION_ANNEX = [
    ("ii", "Annex II - Prohibited substances"),
    ("iii", "Annex III - Restricted substances"),
    ("iv", "Annex IV - Colorants"),
    ("v", "Annex V - Preservatives"),
    ("vi", "Annex VI - UV-filters"),
]

#: Article 15 / Regulation (EC) No 1272/2008 classification categories that
#: Article 15(1) refers to.
CMR_CATEGORY = [
    ("1a", "CMR 1A"),
    ("1b", "CMR 1B"),
    ("2", "CMR 2"),
]

FORMULATION_STATE = [
    ("draft", "Draft"),
    ("review", "Under Review"),
    ("approved", "Approved"),
    ("superseded", "Superseded"),
    ("cancelled", "Cancelled"),
]

#: Annex I Part B, section 1 requires a statement on the safety of the
#: cosmetic product in relation to Article 3.  The three outcomes below make
#: the statement machine-readable; the full wording is held in
#: ``conclusion_statement``.
SAFETY_CONCLUSION = [
    ("safe", "Safe under normal and reasonably foreseeable conditions of use"),
    ("safe_conditions", "Safe subject to the stated conditions and warnings"),
    ("not_safe", "Not safe - product must not be placed on the market"),
]

SAFETY_ASSESSMENT_STATE = [
    ("draft", "Draft"),
    ("part_a", "Part A in Preparation"),
    ("part_b", "Part B in Assessment"),
    ("approved", "Approved"),
    ("superseded", "Superseded"),
    ("cancelled", "Cancelled"),
]

PIF_STATE = [
    ("draft", "Draft"),
    ("active", "Active"),
    ("retention", "Retention Period"),
    ("archived", "Archived"),
]

CLAIM_STATE = [
    ("draft", "Draft"),
    ("substantiation", "Under Substantiation"),
    ("approved", "Approved"),
    ("rejected", "Rejected"),
    ("withdrawn", "Withdrawn"),
]

#: Annex II (best practices) of the Commission guidelines to Regulation (EU)
#: No 655/2013 describes experimental studies, consumer perception tests and
#: published information as the categories of supporting evidence.
CLAIM_EVIDENCE_TYPE = [
    ("experimental", "Experimental study"),
    ("perception", "Consumer perception test"),
    ("published", "Published information"),
]

LABEL_STATE = [
    ("draft", "Draft"),
    ("review", "Under Review"),
    ("approved", "Approved"),
    ("superseded", "Superseded"),
]

#: Article 19(1)(c).
DURABILITY_MODE = [
    ("min_durability", "Date of minimum durability - Article 19(1)(c)"),
    ("pao", "Period after opening - Article 19(1)(c)"),
    ("not_relevant", "Durability after opening not relevant"),
]

#: Article 4 determines who the responsible person is.  The selection records
#: which of those situations applies to the product.
RESPONSIBLE_PERSON_BASIS = [
    ("manufacturer", "Manufacturer established in the Union"),
    ("importer", "Importer placing the product on the market"),
    ("mandated", "Person designated by written mandate"),
    ("distributor", "Distributor placing under own name or modifying"),
]

#: Decret executif n° 97-37 as modified: the prior authorisation covers
#: manufacture, packaging and importation.
DZ_AUTHORIZATION_TYPE = [
    ("fabrication", "Fabrication"),
    ("conditionnement", "Conditionnement"),
    ("importation", "Importation"),
]

DZ_AUTHORIZATION_STATE = [
    ("draft", "Draft"),
    ("submitted", "Submitted"),
    ("receipt", "Deposit Receipt Issued"),
    ("granted", "Authorisation Granted"),
    ("refused", "Refused"),
    ("notice", "Formal Notice Issued"),
    ("withdrawn", "Withdrawn"),
]

#: The sixteen dossier items published by the Ministere du Commerce for a
#: prior authorisation application covering cosmetic and body hygiene
#: products.  The tuple is (field suffix, label).  Field names are built as
#: ``doc_<suffix>`` on ``ls.cosmetic.dz_authorization``.
DZ_DOSSIER_ITEMS = [
    ("rc", "1. Copy of the commercial register extract"),
    ("fiscal", "2. Copy of the tax identification number"),
    ("statutes", "3. Copy of the company statutes"),
    ("accounts", "4. Copy of the CNRC social accounts filing certificate"),
    ("tax_roll", "5. Cleared tax roll extract (extrait de role apure)"),
    ("social", "6. CNAS and/or CASNOS up-to-date certificate"),
    ("denomination", "7. Product denomination and designation per Annexe I"),
    ("usage", "8. Use and directions for use of the product"),
    ("composition", "9. Qualitative composition and raw material quality"),
    ("analyses", "10. Analysis results for raw materials and finished product"),
    ("toxicity", "11. Cutaneous, transcutaneous and mucosal toxicity testing"),
    ("batch_id", "12. Method of identifying manufacturing batches"),
    ("precautions", "13. Particular precautions for use"),
    ("label_model", "14. Label model and/or artwork"),
    ("responsible", "15. Name, function and qualification of responsible persons"),
    ("trademark", "16. Trademark registration or exploitation authorisation"),
]

#: ISO 22716:2007 clause numbering, used by the GMP statement recorded in the
#: product information file (Article 11(2)(c)).
ISO_22716_CLAUSES = [
    ("3", "3 - Personnel"),
    ("4", "4 - Premises"),
    ("5", "5 - Equipment"),
    ("6", "6 - Raw materials and packaging materials"),
    ("7", "7 - Production"),
    ("8", "8 - Finished products"),
    ("9", "9 - Quality control laboratory"),
    ("10", "10 - Treatment of product that is out of specification"),
    ("11", "11 - Wastes"),
    ("12", "12 - Subcontracting"),
    ("13", "13 - Deviations"),
    ("14", "14 - Complaints and recalls"),
    ("15", "15 - Change control"),
    ("16", "16 - Internal audit"),
    ("17", "17 - Documentation"),
]

#: The six common criteria of Commission Regulation (EU) No 655/2013.  The
#: tuple is (field suffix, label); boolean and text fields are declared
#: explicitly on ``ls.cosmetic.claim`` so that the model remains readable.
CLAIM_COMMON_CRITERIA = [
    ("legal", "1. Legal compliance"),
    ("truth", "2. Truthfulness"),
    ("evidence", "3. Evidential support"),
    ("honesty", "4. Honesty"),
    ("fairness", "5. Fairness"),
    ("informed", "6. Informed decision-making"),
]
