# Part of the Life Sciences Suite for Odoo 19 Community Edition.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Shared selection values for the Import & Export Compliance module.

Every selection value is annotated with its provenance, following the
suite convention (see ``ls_recall/models/constants.py``):

``[REG]``
    The value reproduces the *structure* defined by a published text.
    The citation is given in the comment. The module does not assert
    that any given organisation is compliant with it.
``[OPS]``
    The value is an operational choice for this implementation. It has
    no direct regulatory source.

Truth Protocol note. The authority and instrument-type lists below are
``[OPS]`` master data: they name bodies and instrument kinds the
registry *can* hold, not a claim that any body has issued any specific
provision. A provision record is asserted as in force only when a
human has recorded it with a cited source and a status of ``in_force``.
"""

# --- Authorities (registry master data, not a regulatory claim) -------
# [OPS] The authorities below are the bodies likely to issue provisions
#       relevant to regulated life-sciences foreign trade in or from
#       Algeria. The list is editable master data; it asserts nothing
#       about any specific provision.
AUTHORITY_SELECTION = [
    ("anpp", "ANPP"),
    ("ministry_pharma", "Ministry of Pharmaceutical Industry"),
    ("customs", "Customs (DGD)"),
    ("bank_of_algeria", "Bank of Algeria"),
    ("ministry_of_trade", "Ministry of Trade"),
    ("other", "Other"),
]

# --- Instrument types -------------------------------------------------
# [OPS] Kinds of regulatory instrument the registry can record.
INSTRUMENT_TYPE_SELECTION = [
    ("law", "Law"),
    ("decree", "Decree"),
    ("order", "Order"),
    ("instruction", "Instruction"),
    ("circular", "Circular"),
    ("tariff_schedule", "Tariff Schedule"),
    ("regulation", "Regulation"),
    ("other", "Other"),
]

# --- Provision status -------------------------------------------------
# [OPS] Lifecycle of a provision within the registry. ``in_force`` is
#       the only status for which the compliance engine will evaluate
#       a requirement; any other status yields a *registry gap*.
PROVISION_STATUS_SELECTION = [
    ("in_force", "In Force"),
    ("amended", "Amended"),
    ("repealed", "Repealed"),
    ("under_review", "Under Review"),
]

# --- Operation type scope --------------------------------------------
# [OPS] Whether a provision/requirement applies to imports, exports or
#       both. ``none`` is permitted for provisions that are recorded
#       for reference but not yet scoped.
OPERATION_TYPE_SCOPE_SELECTION = [
    ("import", "Import"),
    ("export", "Export"),
    ("both", "Both"),
    ("none", "Not Scoped"),
]

# --- Requirement types ------------------------------------------------
# [OPS] The kinds of enforceable requirement the engine evaluates.
REQUIREMENT_TYPE_SELECTION = [
    ("document", "Document"),
    ("authorization", "Authorization"),
    ("cost_component", "Cost Component"),
    ("threshold", "Threshold"),
    ("deadline", "Deadline"),
    ("procedure", "Procedure"),
]

# --- Citation quote types --------------------------------------------
# [REG-structure] A citation is either verbatim or a paraphrase, so
#       that the registry reader can tell how closely the recorded
#       text follows the source.
CITATION_QUOTE_TYPE_SELECTION = [
    ("verbatim", "Verbatim"),
    ("paraphrase", "Paraphrase"),
]

# --- Regulatory question status --------------------------------------
# [OPS] Lifecycle of an open question. ``open`` until answered by a
#       cited provision, or marked ``wont_answer`` with a reason.
REGULATORY_QUESTION_STATUS_SELECTION = [
    ("open", "Open"),
    ("answered", "Answered"),
    ("wont_answer", "Will Not Answer"),
]

# --- Regulatory question types ---------------------------------------
# [OPS] Mirrors the requirement types so a question can be resolved
#       into a requirement of the same kind.
REGULATORY_QUESTION_TYPE_SELECTION = [
    ("document_required", "Document Required"),
    ("authorization_required", "Authorization Required"),
    ("threshold", "Threshold"),
    ("deadline", "Deadline"),
    ("procedure", "Procedure"),
    ("cost_component", "Cost Component"),
    ("other", "Other"),
]

#: Authorities for which a provision is considered active for evaluation.
ACTIVE_PROVISION_STATUSES = ("in_force",)
