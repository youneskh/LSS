# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0.html).
"""Tests for the two transient models."""

from odoo.exceptions import UserError
from odoo.tests import tagged

from .common import LsCosmeticsCommon


@tagged("post_install", "-at_install")
class TestLsCosmeticWizards(LsCosmeticsCommon):
    """Verify formulation revision and ingredient list generation."""

    def setUp(self):
        """Approve the shared formulation before each test."""
        super().setUp()
        if self.formulation.state != "approved":
            self._approve_formulation()

    def _revise_wizard(self, **overrides):
        """Instantiate the revision wizard on the shared formulation."""
        values = {
            "formulation_id": self.formulation.id,
            "change_reason": "Preservative concentration reduced.",
        }
        values.update(overrides)
        return self.env["ls.cosmetic.formulation.revise"].create(values)

    def test_new_version_number_is_proposed(self):
        """The wizard proposes the next version of the same code."""
        wizard = self._revise_wizard()
        self.assertEqual(wizard.new_version, self.formulation.version + 1)

    def test_revision_copies_the_composition(self):
        """The new version carries the same composition by default."""
        wizard = self._revise_wizard()
        action = wizard.action_revise()
        revision = self.formulation_model.browse(action["res_id"])
        self.assertEqual(revision.state, "draft")
        self.assertEqual(revision.code, self.formulation.code)
        self.assertEqual(len(revision.line_ids), len(self.formulation.line_ids))
        self.assertEqual(revision.predecessor_id, self.formulation)
        self.assertEqual(self.formulation.successor_id, revision)

    def test_revision_can_start_empty(self):
        """Unticking the option starts the new version without lines."""
        wizard = self._revise_wizard(copy_lines=False)
        action = wizard.action_revise()
        revision = self.formulation_model.browse(action["res_id"])
        self.assertFalse(revision.line_ids)

    def test_second_revision_is_refused(self):
        """A formulation can only be revised once."""
        self._revise_wizard().action_revise()
        with self.assertRaises(UserError):
            self._revise_wizard().action_revise()

    def test_predecessor_is_superseded_on_approval(self):
        """Approving a revision supersedes the previous version."""
        action = self._revise_wizard().action_revise()
        revision = self.formulation_model.browse(action["res_id"])
        revision.with_user(self.user_formulator).action_submit_review()
        revision.with_user(self.user_manager).action_approve()
        self.assertEqual(self.formulation.state, "superseded")

    def test_draft_formulation_cannot_be_revised(self):
        """Only an approved formulation can be revised."""
        draft = self.formulation_model.create(
            {
                "name": "Draft base",
                "line_ids": [
                    (0, 0, {"ingredient_id": self.aqua.id, "concentration": 100.0})
                ],
            }
        )
        with self.assertRaises(UserError):
            draft.action_open_revise_wizard()

    def test_label_generation_wizard_preview(self):
        """The generation wizard previews the list before applying it."""
        label = self.label_model.create(
            {"name": "Preview label", "formulation_id": self.formulation.id}
        )
        wizard = self.env["ls.cosmetic.label.generate"].create(
            {"label_id": label.id}
        )
        self.assertIn("AQUA", wizard.preview)
        wizard.action_apply()
        self.assertEqual(label.ingredient_list, wizard.preview)

    def test_label_generation_wizard_options_are_stored(self):
        """The colorant options chosen in the wizard are written to the label."""
        label = self.label_model.create(
            {"name": "Option label", "formulation_id": self.formulation.id}
        )
        wizard = self.env["ls.cosmetic.label.generate"].create(
            {"label_id": label.id, "colorants_last": True, "may_contain": True}
        )
        wizard.action_apply()
        self.assertTrue(label.colorants_last)
        self.assertTrue(label.may_contain)
