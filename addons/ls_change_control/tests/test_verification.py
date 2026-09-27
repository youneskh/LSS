# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Tests of the effectiveness verification."""

from odoo.exceptions import AccessError, UserError
from odoo.tests import tagged

from .common import ChangeControlCommon


@tagged("post_install", "-at_install")
class TestVerification(ChangeControlCommon):
    """Verify the completion rules of the effectiveness verification."""

    def setUp(self):
        """Bring one request to the Implementation state, actions closed."""
        super().setUp()
        self.request = self._create_request(user=self.user_requester)
        self._to_approved(self.request)
        self.action = self._add_implementation(self.request)
        self.request.with_user(self.user_manager).action_start_implementation()
        self.action.with_user(self.user_manager).write(
            {"evidence_reference": "EV-1"}
        )
        self.action.with_user(self.user_requester).action_done()
        self.verification = self._add_verification(self.request)

    def test_completion_requires_a_conclusion(self):
        """A verification cannot be concluded without a conclusion."""
        with self.assertRaises(UserError):
            self.verification.with_user(
                self.user_requester
            ).action_complete_effective()

    def test_only_verifier_or_manager_may_complete(self):
        """A third party cannot complete a verification."""
        self.verification.with_user(self.user_manager).write(
            {"conclusion": "The procedure is applied."}
        )
        with self.assertRaises(AccessError):
            self.verification.with_user(
                self.user_other_requester
            ).action_complete_effective()

    def test_effective_conclusion_unlocks_the_verified_state(self):
        """An effective verification allows the request to be verified."""
        self.verification.with_user(self.user_manager).write(
            {"conclusion": "The procedure is applied."}
        )
        self.verification.with_user(
            self.user_requester
        ).action_complete_effective()
        self.assertEqual(self.verification.result, "effective")
        self.assertEqual(self.verification.state, "completed")
        self.request.with_user(self.user_manager).action_verify()
        self.assertEqual(self.request.state, "verified")

    def test_not_effective_requires_a_follow_up(self):
        """A failed verification must request a follow-up."""
        self.verification.with_user(self.user_manager).write(
            {"conclusion": "The procedure is not applied."}
        )
        with self.assertRaises(UserError):
            self.verification.with_user(
                self.user_requester
            ).action_complete_not_effective()

    def test_not_effective_blocks_the_verified_state(self):
        """A change judged not effective cannot be declared verified."""
        self.verification.with_user(self.user_manager).write(
            {
                "conclusion": "The procedure is not applied.",
                "follow_up_required": True,
                "follow_up_reference": "CAPA-2026-0007",
            }
        )
        self.verification.with_user(
            self.user_requester
        ).action_complete_not_effective()
        self.assertEqual(self.verification.result, "not_effective")
        with self.assertRaises(UserError):
            self.request.with_user(self.user_manager).action_verify()

    def test_completed_verification_is_immutable(self):
        """A completed verification can no longer be modified or deleted."""
        self.verification.with_user(self.user_manager).write(
            {"conclusion": "The procedure is applied."}
        )
        self.verification.with_user(
            self.user_requester
        ).action_complete_effective()
        with self.assertRaises(UserError):
            self.verification.with_user(self.user_manager).write(
                {"conclusion": "Rewritten."}
            )
        with self.assertRaises(UserError):
            self.verification.with_user(self.user_manager).unlink()

    def test_result_cannot_be_written_directly(self):
        """The verification result is only set by the workflow."""
        with self.assertRaises(AccessError):
            self.verification.with_user(self.user_manager).write(
                {"result": "effective"}
            )

    def test_verification_is_waived_when_the_category_says_so(self):
        """A category may waive the effectiveness verification."""
        self.category.requires_verification = False
        self.assertFalse(self.request._is_verification_required())
        self.request.with_user(self.user_manager).action_verify()
        self.assertEqual(self.request.state, "verified")

    def test_verification_is_waived_when_the_company_says_so(self):
        """The company parameter can waive the effectiveness verification."""
        self.company.ls_cc_require_verification = False
        self.assertFalse(self.request._is_verification_required())
        self.request.with_user(self.user_manager).action_verify()
        self.assertEqual(self.request.state, "verified")
