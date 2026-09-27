# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0.html).
"""Revision and rejection wizards."""

from odoo.exceptions import UserError

from .common import LsQmsCommon


class TestWizards(LsQmsCommon):
    """Context handling and effects of the two wizards."""

    def test_01_new_revision_wizard(self):
        """The wizard creates the next revision and opens it."""
        sop = self._publish(self._create_sop())
        wizard_model = (
            self.env["ls.qms.new.revision.wizard"]
            .with_user(self.user_author)
            .with_context(active_model="ls.qms.sop", active_id=sop.id)
        )
        defaults = wizard_model.default_get(
            ["res_model", "res_id", "document_name"]
        )
        self.assertEqual(defaults["res_model"], "ls.qms.sop")
        self.assertEqual(defaults["res_id"], sop.id)
        wizard = wizard_model.create(
            dict(defaults, reason_for_change="Clarification of step two.")
        )
        action = wizard.action_create_revision()
        self.assertEqual(action["res_model"], "ls.qms.sop")
        revision = self.env["ls.qms.sop"].browse(action["res_id"])
        self.assertEqual(revision.version, 2)
        self.assertEqual(
            revision.reason_for_change, "Clarification of step two."
        )
        self.assertEqual(sop.state, "under_revision")

    def test_02_new_revision_wizard_requires_a_context(self):
        """Without an active record the wizard refuses to open."""
        with self.assertRaises(UserError):
            self.env["ls.qms.new.revision.wizard"].default_get(["res_model"])

    def test_03_new_revision_wizard_rejects_foreign_models(self):
        """Only controlled documents can be revised."""
        partner = self.env["res.partner"].create({"name": "Foreign"})
        with self.assertRaises(UserError):
            self.env["ls.qms.new.revision.wizard"].with_context(
                active_model="res.partner", active_id=partner.id
            ).default_get(["res_model"])

    def test_04_reject_wizard(self):
        """The wizard returns the document to draft with a reason."""
        sop = self._create_sop()
        sop.with_user(self.user_author).action_submit_for_review()
        wizard_model = (
            self.env["ls.qms.reject.wizard"]
            .with_user(self.user_approver)
            .with_context(active_model="ls.qms.sop", active_id=sop.id)
        )
        defaults = wizard_model.default_get(
            ["res_model", "res_id", "document_name"]
        )
        wizard = wizard_model.create(
            dict(defaults, reason="The scope is incomplete.")
        )
        wizard.action_reject()
        self.assertEqual(sop.state, "draft")
        bodies = sop.message_ids.mapped("body")
        self.assertTrue(
            any("The scope is incomplete." in body for body in bodies)
        )

    def test_05_reject_wizard_requires_a_context(self):
        """Without an active record the rejection wizard refuses to open."""
        with self.assertRaises(UserError):
            self.env["ls.qms.reject.wizard"].default_get(["res_model"])

    def test_06_revision_wizard_from_the_document_action(self):
        """The document action returns the wizard action dictionary."""
        sop = self._publish(self._create_sop())
        action = sop.with_user(self.user_author).action_open_new_revision_wizard()
        self.assertEqual(action["res_model"], "ls.qms.new.revision.wizard")
        self.assertEqual(action["context"]["active_id"], sop.id)
