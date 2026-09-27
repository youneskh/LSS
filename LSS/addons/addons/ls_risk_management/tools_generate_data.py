#!/usr/bin/env python3
"""Generate the category and matrix data files of ``ls_risk_management``.

XML data files whose records cross-reference each other by external
identifier are generated programmatically so that every ``ref=`` is derived
from the same source of truth as the record it points at.

Run from the module root::

    python3 tools_generate_data.py
"""

import textwrap
from xml.sax.saxutils import escape
import logging

_logger = logging.getLogger(__name__)


HEADER = """<?xml version="1.0" encoding="utf-8"?>
<!-- Part of the Life Sciences Suite. See LICENSE file for full copyright
     and licensing details.

     GENERATED FILE - produced by tools_generate_data.py. Edit the generator
     rather than this file. -->
"""

# ---------------------------------------------------------------------------
# Risk categories
# ---------------------------------------------------------------------------
# (xmlid suffix, code, name, parent xmlid suffix or None, description)
CATEGORIES = [
    ("product_quality", "PQ", "Product Quality", None,
     "Risks whose harm is a reduction in the quality of the product."),
    ("pq_identity", "PQ-ID", "Identity", "product_quality",
     "Risk that the product is not the product it is declared to be."),
    ("pq_purity", "PQ-PU", "Purity", "product_quality",
     "Risk of contamination, cross-contamination or degradation."),
    ("pq_potency", "PQ-PO", "Potency", "product_quality",
     "Risk that the content of the active substance is outside specification."),
    ("patient_safety", "PS", "Patient Safety", None,
     "Risks whose harm is injury or damage to the health of a patient or user."),
    ("data_integrity", "DI", "Data Integrity", None,
     "Risks to the attributability, legibility, contemporaneity, "
     "originality and accuracy of regulated records."),
    ("supply", "SC", "Supply Continuity", None,
     "Risks to the continuity of supply of materials or finished product."),
    ("regulatory", "RG", "Regulatory Compliance", None,
     "Risks of non-conformance with an authorisation, registration or "
     "applicable regulation."),
    ("occupational", "OH", "Occupational Health and Safety", None,
     "Risks whose harm is injury to personnel."),
    ("environmental", "EN", "Environment", None,
     "Risks whose harm is damage to the environment."),
]

# ---------------------------------------------------------------------------
# Example risk matrix
# ---------------------------------------------------------------------------
# ISO 14971:2019 requires the manufacturer to establish objective criteria for
# risk acceptability and does not prescribe acceptable risk levels. The matrix
# below is therefore shipped as an unapproved EXAMPLE that the organisation
# must review, adapt and approve. It is created in the `draft` state and is
# NOT flagged as the default matrix, so it cannot be used on an assessment
# until a Risk Manager has approved it deliberately.
SEVERITY_LEVELS = [
    (1, "Negligible", "EXAMPLE. No effect on product quality or patient."),
    (2, "Minor", "EXAMPLE. Detectable, no effect on safety or efficacy."),
    (3, "Moderate", "EXAMPLE. Rework, reprocessing or extra testing needed."),
    (4, "Major", "EXAMPLE. Out of specification, or reversible injury."),
    (5, "Critical", "EXAMPLE. Irreversible injury, death, or recall."),
]

PROBABILITY_LEVELS = [
    (1, "Improbable", "EXAMPLE. Not expected during the product lifecycle."),
    (2, "Remote", "EXAMPLE. Unlikely but conceivable."),
    (3, "Occasional", "EXAMPLE. May occur a few times in the lifecycle."),
    (4, "Probable", "EXAMPLE. Expected to occur several times."),
    (5, "Frequent", "EXAMPLE. Expected to occur routinely."),
]

#: Reminder appended to the matrix description rather than to every level, so
#: that generated data lines stay within the static checker's length limit.
LEVEL_REMINDER = (
    "Every level definition above is an EXAMPLE. Replace each one with the "
    "objective definition recorded in this organisation's risk management plan."
)

#: Illustrative banding of the ordinal product, used only to populate the
#: example matrix. These boundaries are an example, not a regulatory
#: requirement, and carry no claim of suitability for any organisation.
BAND_BOUNDARIES = [
    (3, "negligible", "acceptable"),
    (6, "low", "acceptable"),
    (10, "medium", "acceptable_with_control"),
    (15, "high", "acceptable_with_control"),
    (25, "very_high", "not_acceptable"),
]


def band_for(severity, probability):
    """Return the example risk band and acceptability for a cell.

    :param int severity: severity ordinal value.
    :param int probability: probability ordinal value.
    :return: tuple of risk level key and acceptability key.
    :rtype: tuple
    """
    score = severity * probability
    for upper, level, acceptability in BAND_BOUNDARIES:
        if score <= upper:
            return level, acceptability
    raise ValueError(f"No band defined for score {score}")


def field(name, value):
    """Render a simple XML field element.

    :param str name: field name.
    :param value: field value, rendered with ``str``.
    :return: the rendered element.
    :rtype: str
    """
    return f'        <field name="{name}">{escape(str(value))}</field>'


def wrapped_field(name, value, width=100):
    """Render a field whose text is wrapped across several lines.

    Used for long prose values, where emitting a single very long line would
    hurt readability of the data file. The wrapping introduces newlines into
    the stored value, which is acceptable for descriptive text fields.

    :param str name: field name.
    :param str value: text value.
    :param int width: maximum width of each wrapped line.
    :return: the rendered element.
    :rtype: str
    """
    lines = textwrap.wrap(escape(str(value)), width=width)
    body = "\n".join(lines)
    return f'        <field name="{name}">{body}</field>'


def build_categories():
    """Return the rendered category data file.

    :return: the complete XML document.
    :rtype: str
    """
    parts = [HEADER, '<odoo noupdate="1">\n']
    for suffix, code, name, parent, description in CATEGORIES:
        parts.append(f'    <record id="risk_category_{suffix}" model="ls.risk.category">')
        parts.append(field("name", name))
        parts.append(field("code", code))
        parts.append(field("description", description))
        if parent:
            parts.append(f'        <field name="parent_id" ref="risk_category_{parent}"/>')
        parts.append("    </record>\n")
    parts.append("</odoo>\n")
    return "\n".join(parts)


def build_matrix():
    """Return the rendered example matrix data file.

    :return: the complete XML document.
    :rtype: str
    """
    parts = [HEADER, '<odoo noupdate="1">\n']
    parts.append('    <record id="risk_matrix_example" model="ls.risk.matrix">')
    parts.append(field("name", "EXAMPLE 5x5 Risk Matrix - review and approve before use"))
    parts.append(field("code", "EXAMPLE-5X5"))
    parts.append(wrapped_field(
        "description",
        "EXAMPLE matrix supplied as a starting template only. ISO 14971:2019 "
        "requires the manufacturer to establish objective criteria for risk "
        "acceptability and does not prescribe acceptable risk levels. Review "
        "every level definition and every cell against the organisation's own "
        "risk management plan, then approve the matrix. This record is "
        "delivered in the Draft state and is not flagged as the default "
        "matrix, so it cannot be used on an assessment until it is approved. "
        + LEVEL_REMINDER,
    ))
    parts.append(field("reference_document", "To be completed by the organisation"))
    parts.append('        <field name="state">draft</field>')
    parts.append('        <field name="is_default" eval="False"/>')
    parts.append("    </record>\n")

    for value, name, description in SEVERITY_LEVELS:
        parts.append(
            f'    <record id="risk_matrix_example_sev_{value}" model="ls.risk.matrix.level">'
        )
        parts.append('        <field name="matrix_id" ref="risk_matrix_example"/>')
        parts.append('        <field name="scale">severity</field>')
        parts.append(field("value", value))
        parts.append(field("name", name))
        parts.append(field("description", description))
        parts.append("    </record>")
    parts.append("")

    for value, name, description in PROBABILITY_LEVELS:
        parts.append(
            f'    <record id="risk_matrix_example_prob_{value}" model="ls.risk.matrix.level">'
        )
        parts.append('        <field name="matrix_id" ref="risk_matrix_example"/>')
        parts.append('        <field name="scale">probability</field>')
        parts.append(field("value", value))
        parts.append(field("name", name))
        parts.append(field("description", description))
        parts.append("    </record>")
    parts.append("")

    for severity, _sev_name, _sev_desc in SEVERITY_LEVELS:
        for probability, _prob_name, _prob_desc in PROBABILITY_LEVELS:
            level, acceptability = band_for(severity, probability)
            parts.append(
                f'    <record id="risk_matrix_example_cell_{severity}_{probability}" '
                'model="ls.risk.matrix.cell">'
            )
            parts.append('        <field name="matrix_id" ref="risk_matrix_example"/>')
            parts.append(field("severity_value", severity))
            parts.append(field("probability_value", probability))
            parts.append(f'        <field name="risk_level">{level}</field>')
            parts.append(f'        <field name="acceptability">{acceptability}</field>')
            parts.append("    </record>")
    parts.append("")
    parts.append("</odoo>\n")
    return "\n".join(parts)


def main():
    """Write both generated data files."""
    with open("data/ls_risk_category_data.xml", "w", encoding="utf-8") as handle:
        handle.write(build_categories())
    with open("data/ls_risk_matrix_data.xml", "w", encoding="utf-8") as handle:
        handle.write(build_matrix())
    _logger.info("Generated data/ls_risk_category_data.xml")
    _logger.info("Generated data/ls_risk_matrix_data.xml")


if __name__ == "__main__":
    main()
