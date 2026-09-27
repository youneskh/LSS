# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0.html).
"""Tests for the Algerian prior authorisation dossier."""

from datetime import date, timedelta

from odoo.exceptions import UserError, ValidationError
from odoo.tests import tagged

from ..models import constants
from .common import LsCosmeticsCommon


@tagged("post_install", "-at_install")
class TestLsCosmeticDzAuthorization(LsCosmeticsCommon):
    """Verify the dossier checklist and the procedural deadlines."""

    def _draft_dossier(self, complete=True, **overrides):
        """Create a draft dossier, optionally with every item ticked."""
        values = {
            "name": "Creme hydratante",
            "authorization_type": "fabrication",
            "operator_partner_id": self.responsible_partner.id,
            "product_tmpl_id": self.product.id,
        }
        if complete:
            for suffix, _label in constants.DZ_DOSSIER_ITEMS:
                values[f"doc_{suffix}"] = True
        values.update(overrides)
        return self.dz_model.create(values)

    def test_sequence_assigns_reference(self):
        """A created dossier receives a reference from the sequence."""
        dossier = self._draft_dossier()
        self.assertTrue(dossier.code.startswith("DZA/"))

    def test_dossier_has_sixteen_items(self):
        """The checklist reproduces the sixteen published items."""
        self.assertEqual(len(constants.DZ_DOSSIER_ITEMS), 16)
        dossier = self._draft_dossier()
        self.assertEqual(dossier.dossier_item_count, 16)
        self.assertTrue(dossier.dossier_complete)

    def test_incomplete_dossier_cannot_be_submitted(self):
        """Submission is refused while an item is missing."""
        dossier = self._draft_dossier(complete=False)
        with self.assertRaises(UserError):
            dossier.with_user(self.user_manager).action_submit()

    def test_missing_items_are_named(self):
        """Every missing item is reported by its published label."""
        dossier = self._draft_dossier(complete=False)
        self.assertEqual(len(dossier._missing_dossier_items()), 16)

    def test_decision_due_date_is_forty_five_days(self):
        """The decision period runs forty-five days from the receipt."""
        dossier = self._draft_dossier(receipt_date=date(2026, 3, 1))
        self.assertEqual(
            dossier.decision_due_date,
            date(2026, 3, 1) + timedelta(days=constants.DZ_DECISION_DELAY_DAYS),
        )

    def test_full_procedure(self):
        """A dossier can be submitted, receipted and granted."""
        dossier = self._draft_dossier()
        manager_dossier = dossier.with_user(self.user_manager)
        manager_dossier.action_submit()
        self.assertEqual(dossier.state, "submitted")
        dossier.receipt_date = date.today()
        dossier.receipt_reference = "REC/2026/001"
        manager_dossier.action_register_receipt()
        self.assertEqual(dossier.state, "receipt")
        dossier.authorization_reference = "AUT/2026/001"
        manager_dossier.action_grant()
        self.assertEqual(dossier.state, "granted")
        self.assertEqual(dossier.decision_date, date.today())

    def test_receipt_requires_a_date(self):
        """The receipt cannot be registered without its date."""
        dossier = self._draft_dossier()
        dossier.with_user(self.user_manager).action_submit()
        with self.assertRaises(UserError):
            dossier.with_user(self.user_manager).action_register_receipt()

    def test_grant_requires_a_reference(self):
        """An authorisation cannot be recorded without its reference."""
        dossier = self._draft_dossier(receipt_date=date.today())
        dossier.with_user(self.user_manager).action_submit()
        dossier.with_user(self.user_manager).action_register_receipt()
        with self.assertRaises(UserError):
            dossier.with_user(self.user_manager).action_grant()

    def test_refusal_must_be_reasoned(self):
        """A refusal without a recorded reason is refused."""
        dossier = self._draft_dossier(receipt_date=date.today())
        dossier.with_user(self.user_manager).action_submit()
        dossier.with_user(self.user_manager).action_register_receipt()
        with self.assertRaises(UserError):
            dossier.with_user(self.user_manager).action_refuse()

    def test_formal_notice_deadline_is_one_month(self):
        """The compliance period runs thirty days from the notice."""
        dossier = self._draft_dossier(notice_date=date(2026, 3, 1))
        self.assertEqual(
            dossier.notice_deadline,
            date(2026, 3, 1) + timedelta(days=constants.DZ_COMPLIANCE_DELAY_DAYS),
        )

    def test_formal_notice_requires_a_subject(self):
        """A formal notice must record what has to be brought into conformity."""
        dossier = self._draft_dossier(receipt_date=date.today())
        manager_dossier = dossier.with_user(self.user_manager)
        manager_dossier.action_submit()
        manager_dossier.action_register_receipt()
        dossier.authorization_reference = "AUT/2026/002"
        manager_dossier.action_grant()
        dossier.notice_date = date.today()
        with self.assertRaises(UserError):
            manager_dossier.action_register_notice()

    def test_chronology_is_enforced(self):
        """The deposit receipt cannot predate the submission."""
        with self.assertRaises(ValidationError):
            self._draft_dossier(
                submission_date=date(2026, 3, 1), receipt_date=date(2026, 1, 1)
            )

    def test_submitted_dossier_cannot_be_deleted(self):
        """A dossier that has been submitted is retained."""
        dossier = self._draft_dossier()
        dossier.with_user(self.user_manager).action_submit()
        with self.assertRaises(UserError):
            dossier.unlink()

    def test_cron_posts_overdue_notices(self):
        """The deadline cron posts a message on overdue dossiers."""
        past = date.today() - timedelta(days=90)
        dossier = self._draft_dossier()
        manager_dossier = dossier.with_user(self.user_manager)
        manager_dossier.action_submit()
        dossier.write({"submission_date": past, "receipt_date": past})
        manager_dossier.action_register_receipt()
        before = len(dossier.message_ids)
        count = self.dz_model._cron_monitor_deadlines()
        self.assertGreaterEqual(count, 1)
        self.assertGreater(len(dossier.message_ids), before)
