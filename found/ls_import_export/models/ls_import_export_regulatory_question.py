# Part of the Life Sciences Suite for Odoo 19 Community Edition.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Regulatory question.

A regulatory question records an expectation about a requirement that
has not yet been verified against an official source. Rather than guess
the answer (which would violate the Truth Protocol), the expectation is
kept as an open question, to be closed by recording a cited provision.

Twenty-five questions are seeded on first install from
``data/ls_import_export_regulatory_questions_data.xml`` (status
``open``); they mirror ``doc/02_regulatory_analysis.md`` section 3.
"""

from odoo import fields, models

from .constants import (
    REGULATORY_QUESTION_STATUS_SELECTION,
    REGULATORY_QUESTION_TYPE_SELECTION,
)


class LsImportExportRegulatoryQuestion(models.Model):
    """An open question about an unverified regulatory requirement."""

    _name = "ls.import_export.regulatory.question"
    _description = "Import & Export Compliance Regulatory Question"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "status, sequence, id"
    _check_company_auto = True

    sequence = fields.Integer(default=10)
    name = fields.Char(
        string="Question",
        required=True,
        tracking=True,
    )
    code = fields.Char(
        string="Reference",
        readonly=True,
        copy=False,
        index=True,
        default="New",
    )
    question_type = fields.Selection(
        selection=REGULATORY_QUESTION_TYPE_SELECTION,
        default="other",
        required=True,
        tracking=True,
    )
    context = fields.Text(
        string="Context",
        help="Why the question is open and what depends on the answer.",
    )
    expected_provision_ref = fields.Char(
        string="Expected Provision Reference",
        help="The reference the answer is expected to cite, if known.",
    )
    status = fields.Selection(
        selection=REGULATORY_QUESTION_STATUS_SELECTION,
        default="open",
        required=True,
        tracking=True,
        index=True,
    )
    answer_provision_id = fields.Many2one(
        comodel_name="ls.import_export.provision",
        string="Answering Provision",
        tracking=True,
        help="The cited provision that answers this question. Filled "
             "when the question is closed.",
    )
    company_id = fields.Many2one(
        comodel_name="res.company",
        required=True,
        index=True,
        default=lambda self: self.env.company,
    )
    active = fields.Boolean(default=True)

    def name_get(self):
        return [(rec.id, f"[{rec.code}] {rec.name}") for rec in self]
