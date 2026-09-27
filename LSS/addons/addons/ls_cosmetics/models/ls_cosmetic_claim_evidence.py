# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0.html).
"""Evidence supporting a cosmetic product claim."""

from odoo import api, fields, models
from odoo.exceptions import ValidationError

from . import constants


class LsCosmeticClaimEvidence(models.Model):
    """A single item of evidence supporting a claim.

    Article 11(2)(d) of Regulation (EC) No 1223/2009 requires the product
    information file to contain, where justified by the nature or the effect
    of the cosmetic product, proof of the effect claimed.  Article 2 of
    Commission Regulation (EU) No 655/2013 requires the wording of the claim
    to be consistent with that documentation.

    The three evidence types offered are those described in the best
    practices annex of the Commission guidelines to Regulation (EU)
    No 655/2013: experimental studies, consumer perception tests and
    published information.
    """

    _name = "ls.cosmetic.claim.evidence"
    _description = "Cosmetic Claim Evidence"
    _order = "claim_id, evidence_date desc, id desc"
    _rec_name = "reference"

    claim_id = fields.Many2one(comodel_name="ls.cosmetic.claim", required=True,
                               ondelete="cascade",
                               index=True,)
    company_id = fields.Many2one(
        related="claim_id.company_id",
        store=True,
        index=True,
    )
    reference = fields.Char(
        string="Evidence Reference",
        required=True,
        help="Study number, report number or bibliographic citation.",
    )
    evidence_type = fields.Selection(selection=constants.CLAIM_EVIDENCE_TYPE, required=True,)
    evidence_date = fields.Date(required=True)
    performed_by = fields.Char(help="Laboratory, institute or author responsible for the evidence.",)
    summary = fields.Text(
        string="Summary of Findings",
        required=True,
        help="What the evidence demonstrates, in terms that can be compared "
             "with the wording of the claim.",
    )
    subject_count = fields.Integer(
        string="Number of Subjects",
        help="Applicable to experimental studies and consumer perception "
             "tests. Leave at zero for published information.",
    )
    is_statistically_significant = fields.Boolean(
        string="Statistically Significant",
        help="Tick only where the evidence itself reports a statistically "
             "significant result.",
    )
    attachment_ids = fields.Many2many(
        comodel_name="ir.attachment",
        relation="ls_cosmetic_claim_evidence_attachment_rel",
        column1="evidence_id",
        column2="attachment_id",
        string="Attachments",
    )
    note = fields.Text()

    _subject_count_positive = models.Constraint(
        "CHECK(subject_count >= 0)",
        "The number of subjects cannot be negative.",
    )
    _reference_unique = models.Constraint(
        "UNIQUE(claim_id, reference)",
        "This evidence reference is already recorded on the claim.",
    )

    @api.constrains("evidence_type", "subject_count")
    def _check_subject_count(self):
        """Require a subject count for the two study-based evidence types."""
        study_types = ("experimental", "perception")
        for evidence in self:
            if evidence.evidence_type in study_types and evidence.subject_count <= 0:
                raise ValidationError(
                    self.env._(
                        "Evidence %(reference)s is a study and must record the "
                        "number of subjects.",
                        reference=evidence.reference,
                    )
                )

    @api.constrains("evidence_date")
    def _check_evidence_date(self):
        """Refuse evidence dated in the future."""
        today = fields.Date.context_today(self)
        for evidence in self:
            if evidence.evidence_date and evidence.evidence_date > today:
                raise ValidationError(
                    self.env._(
                        "Evidence %(reference)s cannot be dated in the future.",
                        reference=evidence.reference,
                    )
                )
