# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0.html).
"""Tests for the Article 11 product information file."""

from datetime import date

from dateutil.relativedelta import relativedelta

from odoo import fields
from odoo.exceptions import UserError, ValidationError
from odoo.tests import tagged

from .common import LsCosmeticsCommon


@tagged("post_install", "-at_install")
class TestLsCosmeticPif(LsCosmeticsCommon):
    """Verify the five Article 11(2) items and the ten year retention clock."""

    def setUp(self):
        """Build an approved safety report before each test."""
        super().setUp()
        self.assessment = self._build_approved_assessment()

    def _draft_pif(self, **overrides):
        """Create a draft file carrying the applicable Article 11(2) items."""
        values = {
            "name": "Hydrating cream information file",
            "product_tmpl_id": self.product.id,
            "responsible_person_id": self.responsible_partner.id,
            "responsible_person_basis": "manufacturer",
            "file_address": "2 Responsibility Road, Algiers",
            "product_description": "White cream in a 50 ml airless bottle.",
            "safety_assessment_id": self.assessment.id,
            "manufacturing_method": "Hot emulsion followed by cold phase addition.",
            "gmp_statement": "Manufactured in accordance with ISO 22716:2007.",
            "no_claims_justification": "No effect is claimed for this product.",
            "no_animal_testing": True,
        }
        values.update(overrides)
        return self.pif_model.create(values)

    def test_sequence_assigns_reference(self):
        """A created file receives a reference from the sequence."""
        pif = self._draft_pif()
        self.assertTrue(pif.code.startswith("PIF/"))

    def test_activation_requires_every_item(self):
        """A file missing an Article 11(2) item cannot be activated."""
        pif = self._draft_pif(product_description=False)
        with self.assertRaises(UserError):
            pif.with_user(self.user_manager).action_activate()

    def test_complete_file_is_activated(self):
        """A complete file reaches the active state."""
        pif = self._draft_pif()
        pif.with_user(self.user_manager).action_activate()
        self.assertEqual(pif.state, "active")
        self.assertEqual(pif.activated_by_id, self.user_manager)

    def test_unapproved_claim_blocks_activation(self):
        """A claim attached to the file must itself be approved."""
        claim = self.claim_model.create(
            {"name": "Reduces the look of fine lines", "product_tmpl_id": self.product.id}
        )
        pif = self._draft_pif(claim_ids=[(6, 0, [claim.id])])
        with self.assertRaises(UserError):
            pif.with_user(self.user_manager).action_activate()

    def test_animal_testing_item_must_be_documented(self):
        """The file states either the data or that no testing was performed.

        ``action_activate`` reports the missing Article 11(2)(e) item and
        raises UserError before the constraint is reached; the constraint is
        covered separately below.
        """
        pif = self._draft_pif(no_animal_testing=False)
        with self.assertRaises(UserError):
            pif.with_user(self.user_manager).action_activate()

    def test_animal_testing_constraint_blocks_direct_write(self):
        """The constraint refuses activation even when the gate is bypassed."""
        pif = self._draft_pif(no_animal_testing=False)
        with self.assertRaises(ValidationError):
            pif.sudo().write({"state": "active"})

    def test_unsafe_conclusion_blocks_activation(self):
        """A file cannot be activated on a report concluding 'not safe'."""
        pif = self._draft_pif()
        self.assessment.sudo().write({"state": "part_b"})
        self.assessment.sudo().write({"conclusion": "not_safe"})
        self.assessment.sudo().write({"state": "approved"})
        with self.assertRaises(ValidationError):
            pif.with_user(self.user_manager).action_activate()

    def test_unapproved_report_blocks_activation(self):
        """A file cannot be activated on a report that is not approved."""
        pif = self._draft_pif()
        self.assessment.sudo().write({"state": "part_b"})
        with self.assertRaises(ValidationError):
            pif.with_user(self.user_manager).action_activate()

    def test_retention_end_date_is_ten_years(self):
        """The retention clock adds ten years to the last batch date."""
        pif = self._draft_pif(last_batch_market_date=date(2026, 3, 1))
        self.assertEqual(pif.retention_end_date, date(2036, 3, 1))

    def test_retention_requires_the_last_batch_date(self):
        """A file cannot enter retention without the last batch date."""
        pif = self._draft_pif()
        pif.with_user(self.user_manager).action_activate()
        with self.assertRaises(UserError):
            pif.with_user(self.user_manager).action_enter_retention()

    def test_archiving_before_the_end_of_retention_is_refused(self):
        """A file cannot be archived while the ten years are running."""
        pif = self._draft_pif(last_batch_market_date=date.today())
        pif.with_user(self.user_manager).action_activate()
        pif.with_user(self.user_manager).action_enter_retention()
        with self.assertRaises(UserError):
            pif.with_user(self.user_manager).action_archive_file()

    def test_archiving_after_retention_succeeds(self):
        """A file may be archived once the ten years have elapsed."""
        elapsed = fields.Date.context_today(self.pif_model) - relativedelta(
            years=11
        )
        pif = self._draft_pif(
            first_placed_date=elapsed, last_batch_market_date=elapsed
        )
        pif.with_user(self.user_manager).action_activate()
        pif.with_user(self.user_manager).action_enter_retention()
        pif.with_user(self.user_manager).action_archive_file()
        self.assertEqual(pif.state, "archived")

    def test_market_dates_are_ordered(self):
        """The last batch cannot precede the first placing on the market."""
        with self.assertRaises(ValidationError):
            self._draft_pif(
                first_placed_date=date(2026, 6, 1),
                last_batch_market_date=date(2026, 1, 1),
            )

    def test_active_file_cannot_be_deleted(self):
        """A file that has left the draft state is retained."""
        pif = self._draft_pif()
        pif.with_user(self.user_manager).action_activate()
        with self.assertRaises(UserError):
            pif.unlink()

    def test_retention_elapsed_search(self):
        """The retention search helper returns the expected records."""
        elapsed = fields.Date.context_today(self.pif_model) - relativedelta(
            years=11
        )
        pif = self._draft_pif(last_batch_market_date=elapsed)
        found = self.pif_model.search([("retention_elapsed", "=", True)])
        self.assertIn(pif, found)

    def test_cron_posts_a_retention_notice(self):
        """The retention cron posts one message per elapsed file."""
        elapsed = fields.Date.context_today(self.pif_model) - relativedelta(
            years=11
        )
        pif = self._draft_pif(
            first_placed_date=elapsed, last_batch_market_date=elapsed
        )
        pif.with_user(self.user_manager).action_activate()
        pif.with_user(self.user_manager).action_enter_retention()
        before = len(pif.message_ids)
        count = self.pif_model._cron_monitor_retention()
        self.assertGreaterEqual(count, 1)
        self.assertGreater(len(pif.message_ids), before)
