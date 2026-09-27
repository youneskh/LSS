# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0.html).
"""Tests for cosmetic claims and the six common criteria."""

from datetime import date

from odoo.exceptions import UserError, ValidationError
from odoo.tests import tagged

from .common import LsCosmeticsCommon


@tagged("post_install", "-at_install")
class TestLsCosmeticClaim(LsCosmeticsCommon):
    """Verify substantiation, criteria gating and evidence rules."""

    def _draft_claim(self, **overrides):
        """Create a draft claim on the shared product."""
        values = {
            "name": "Hydrates for 24 hours",
            "product_tmpl_id": self.product.id,
        }
        values.update(overrides)
        return self.claim_model.create(values)

    def _all_criteria_values(self):
        """Return values marking the six criteria as met with justifications."""
        values = {}
        for field_name, note_field in self.claim_model._CRITERION_FIELDS:
            values[field_name] = True
            values[note_field] = "Justification recorded during substantiation."
        return values

    def test_sequence_assigns_reference(self):
        """A created claim receives a reference from the sequence."""
        claim = self._draft_claim()
        self.assertTrue(claim.code.startswith("CLM/"))

    def test_criteria_counter(self):
        """The counter reflects how many criteria are marked as met."""
        claim = self._draft_claim(criterion_legal=True, criterion_truth=True)
        self.assertEqual(claim.criteria_met_count, 2)
        self.assertFalse(claim.all_criteria_met)

    def test_approval_requires_every_criterion(self):
        """A claim with an unjustified criterion cannot be approved."""
        claim = self._draft_claim(criterion_legal=True)
        claim.with_user(self.user_formulator).action_start_substantiation()
        with self.assertRaises(ValidationError):
            claim.with_user(self.user_manager).action_approve()

    def test_evidential_support_requires_evidence(self):
        """A claim marked as evidentially supported must carry evidence."""
        claim = self._draft_claim(**self._all_criteria_values())
        claim.with_user(self.user_formulator).action_start_substantiation()
        with self.assertRaises(UserError):
            claim.with_user(self.user_manager).action_approve()

    def test_approval_with_evidence_succeeds(self):
        """A fully justified and evidenced claim can be approved."""
        claim = self._draft_claim(**self._all_criteria_values())
        self.env["ls.cosmetic.claim.evidence"].create(
            {
                "claim_id": claim.id,
                "reference": "STUDY-001",
                "evidence_type": "experimental",
                "evidence_date": date(2026, 1, 15),
                "subject_count": 30,
                "summary": "Corneometry showed sustained hydration at 24 hours.",
            }
        )
        claim.with_user(self.user_formulator).action_start_substantiation()
        claim.with_user(self.user_manager).action_approve()
        self.assertEqual(claim.state, "approved")

    def test_segregation_of_duties_on_claim_approval(self):
        """The assessor of a claim cannot approve it."""
        claim = self._draft_claim(**self._all_criteria_values())
        claim.criterion_evidence = False
        claim.with_user(self.user_manager).action_start_substantiation()
        with self.assertRaises(UserError):
            claim.with_user(self.user_manager).action_approve()

    def test_animal_testing_claim_requires_declaration(self):
        """An Article 20(3) claim needs the supplier declarations recorded."""
        values = self._all_criteria_values()
        values["is_no_animal_testing_claim"] = True
        values["criterion_evidence"] = False
        claim = self._draft_claim(**values)
        claim.with_user(self.user_formulator).action_start_substantiation()
        with self.assertRaises(ValidationError):
            claim.with_user(self.user_manager).action_approve()

    def test_study_evidence_requires_subject_count(self):
        """An experimental study must record the number of subjects."""
        claim = self._draft_claim()
        with self.assertRaises(ValidationError):
            self.env["ls.cosmetic.claim.evidence"].create(
                {
                    "claim_id": claim.id,
                    "reference": "STUDY-002",
                    "evidence_type": "perception",
                    "evidence_date": date(2026, 1, 15),
                    "summary": "Consumers reported improved comfort.",
                }
            )

    def test_evidence_cannot_be_dated_in_the_future(self):
        """Evidence dated after today is refused."""
        claim = self._draft_claim()
        with self.assertRaises(ValidationError):
            self.env["ls.cosmetic.claim.evidence"].create(
                {
                    "claim_id": claim.id,
                    "reference": "STUDY-003",
                    "evidence_type": "published",
                    "evidence_date": date(2099, 1, 1),
                    "summary": "Published review of humectants.",
                }
            )

    def test_non_draft_claim_cannot_be_deleted(self):
        """A claim that has left the draft state is retained."""
        claim = self._draft_claim()
        claim.with_user(self.user_formulator).action_start_substantiation()
        with self.assertRaises(UserError):
            claim.unlink()
